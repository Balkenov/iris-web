#  IRIS Source Code
#  Copyright (C) 2021 - Airbus CyberSecurity (SAS)
#  ir@cyberactionlab.net
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 3 of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
import tempfile
import os

import marshmallow
from datetime import datetime
from datetime import timedelta

from flask import Blueprint
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for
from flask_login import current_user
from flask_login import logout_user
from flask_wtf import FlaskForm
from flask import jsonify, send_file
from io import BytesIO
import zipfile

from app import app
from app import db
from app import oidc_client
from app.datamgmt.dashboard.dashboard_db import get_global_task, list_user_cases, list_user_reviews
from app.datamgmt.dashboard.dashboard_db import get_tasks_status
from app.datamgmt.dashboard.dashboard_db import list_global_tasks
from app.datamgmt.dashboard.dashboard_db import list_user_tasks
from app.forms import CaseGlobalTaskForm
from app.iris_engine.access_control.utils import ac_get_user_case_counts
from app.iris_engine.module_handler.module_handler import call_modules_hook
from app.iris_engine.reporter.reporter import IrisMakeDocReport
from app.iris_engine.utils.tracker import track_activity
from app.models.authorization import User
from app.models.cases import Cases
from app.models.models import CaseTasks
from app.models.models import GlobalTasks
from app.models.models import TaskStatus
from app.schema.marshables import CaseTaskSchema, CaseDetailsSchema
from app.schema.marshables import GlobalTasksSchema
from app.util import ac_api_requires, regenerate_session
from app.util import ac_requires_case_identifier
from app.util import ac_requires
from app.util import not_authenticated_redirection_url
from app.util import response_error
from app.util import response_success
from app.util import is_authentication_oidc
from app.datamgmt.manage.manage_case_state_db import get_case_states_list
from app.datamgmt.manage.manage_cases_db import build_filter_case_query
from app.datamgmt.case.case_db import get_case_report_template

from oic.oauth2.exception import GrantError

log = app.logger


# CONTENT ------------------------------------------------
dashboard_blueprint = Blueprint(
    'index',
    __name__,
    template_folder='templates'
)


# Logout user
@dashboard_blueprint.route('/logout')
def logout():
    """
    Logout function. Erase its session and redirect to index i.e login
    :return: Page
    """
    if session['current_case']:
        current_user.ctx_case = session['current_case']['case_id']
        current_user.ctx_human_case = session['current_case']['case_name']
        db.session.commit()

    if is_authentication_oidc():
        if oidc_client.provider_info.get("end_session_endpoint"):
            try:
                logout_request = oidc_client.construct_EndSessionRequest(state=session["oidc_state"])
                logout_url = logout_request.request(oidc_client.provider_info["end_session_endpoint"])
                track_activity("user '{}' is being logged out".format(current_user.user), ctx_less=True, display_in_ui=False)
                logout_user()
                session.clear()
                return redirect(logout_url)
            except GrantError:
                track_activity(
                    f"no oidc session found for user '{current_user.user}', skipping oidc provider logout and continuing to logout local user",
                    ctx_less=True,
                    display_in_ui=False
                )
            except Exception as e:
                log.error(f"Error logging out: {e}")
                log.warning(f'Will continue to local logout')

    track_activity("user '{}' is being logged out".format(current_user.user), ctx_less=True, display_in_ui=False)

    logout_user()
    session.clear()

    return redirect(not_authenticated_redirection_url('/'))


@dashboard_blueprint.route('/dashboard/case_charts', methods=['GET'])
@ac_api_requires()
def get_cases_charts():
    """
    Get case charts
    :return: JSON
    """

    res = Cases.query.with_entities(
        Cases.open_date
    ).filter(
        Cases.open_date > (datetime.utcnow() - timedelta(days=365))
    ).order_by(
        Cases.open_date
    ).all()
    retr = [[], []]
    rk = {}
    for case in res:
        month = "{}/{}/{}".format(case.open_date.day, case.open_date.month, case.open_date.year)

        if month in rk:
            rk[month] += 1
        else:
            rk[month] = 1

        retr = [list(rk.keys()), list(rk.values())]

    return response_success("", retr)


@dashboard_blueprint.route('/')
def root():
    if app.config['DEMO_MODE_ENABLED'] == 'True':
        return redirect(url_for('demo-landing.demo_landing'))

    return redirect(url_for('index.index'))


@dashboard_blueprint.route('/dashboard')
@ac_requires()
def index(caseid, url_redir):
    """
    Index page. Load the dashboard data, create the add customer form
    :return: Page
    """
    if url_redir:
        return redirect(url_for('index.index', cid=caseid if caseid is not None else 1, redirect=True))

    msg = None

    acgucc = ac_get_user_case_counts(current_user.id)

    data = {
        "user_open_count": acgucc[2],
        "cases_open_count": acgucc[1],
        "cases_count": acgucc[0],
    }

    # Create the customer form to be able to quickly add a customer
    form = FlaskForm()

    return render_template('index.html', data=data, form=form, msg=msg)


@dashboard_blueprint.route('/global/tasks/list', methods=['GET'])
@ac_api_requires()
def get_gtasks():

    tasks_list = list_global_tasks()

    if tasks_list:
        output = [c._asdict() for c in tasks_list]
    else:
        output = []

    ret = {
        "tasks_status": get_tasks_status(),
        "tasks": output
    }

    return response_success("", data=ret)


@dashboard_blueprint.route('/user/cases/list', methods=['GET'])
@ac_api_requires()
def list_own_cases():

    cases = list_user_cases(
        request.args.get('show_closed', 'false', type=str).lower() == 'true'
    )

    return response_success("", data=CaseDetailsSchema(many=True).dump(cases))


@dashboard_blueprint.route('/global/tasks/<int:cur_id>', methods=['GET'])
@ac_api_requires()
def view_gtask(cur_id):

    task = get_global_task(task_id=cur_id)
    if not task:
        return response_error(f'Global task ID {cur_id} not found')

    return response_success("", data=task._asdict())


@dashboard_blueprint.route('/user/tasks/list', methods=['GET'])
@ac_api_requires()
def get_utasks():

    ct = list_user_tasks()

    if ct:
        output = [c._asdict() for c in ct]
    else:
        output = []

    ret = {
        "tasks_status": get_tasks_status(),
        "tasks": output
    }

    return response_success("", data=ret)


@dashboard_blueprint.route('/user/reviews/list', methods=['GET'])
@ac_api_requires()
def get_reviews():

    ct = list_user_reviews()

    if ct:
        output = [c._asdict() for c in ct]
    else:
        output = []


    return response_success("", data=output)


@dashboard_blueprint.route('/user/tasks/status/update', methods=['POST'])
@ac_api_requires()
@ac_requires_case_identifier()
def utask_statusupdate(caseid):
    jsdata = request.get_json()
    if not jsdata:
        return response_error("Invalid request")

    jsdata = request.get_json()
    if not jsdata:
        return response_error("Invalid request")

    case_id = jsdata.get('case_id') if jsdata.get('case_id') else caseid
    task_id = jsdata.get('task_id')
    task = CaseTasks.query.filter(CaseTasks.id == task_id, CaseTasks.task_case_id == case_id).first()
    if not task:
        return response_error(f"Invalid case task ID {task_id} for case {case_id}")

    status_id = jsdata.get('task_status_id')
    status = TaskStatus.query.filter(TaskStatus.id == status_id).first()
    if not status:
        return response_error(f"Invalid task status ID {status_id}")

    task.task_status_id = status_id
    try:

        db.session.commit()

    except Exception as e:
        return response_error(f"Unable to update task. Error {e}")

    task_schema = CaseTaskSchema()
    return response_success("Updated", data=task_schema.dump(task))


@dashboard_blueprint.route('/global/tasks/add/modal', methods=['GET'])
@ac_api_requires()
def add_gtask_modal():
    task = GlobalTasks()

    form = CaseGlobalTaskForm()

    form.task_assignee_id.choices = [(user.id, user.name) for user in User.query.filter(User.active == True).order_by(User.name).all()]
    form.task_status_id.choices = [(a.id, a.status_name) for a in get_tasks_status()]

    return render_template("modal_add_global_task.html", form=form, task=task, uid=current_user.id, user_name=None)


@dashboard_blueprint.route('/global/tasks/add', methods=['POST'])
@ac_api_requires()
@ac_requires_case_identifier()
def add_gtask(caseid):

    try:

        gtask_schema = GlobalTasksSchema()

        request_data = call_modules_hook('on_preload_global_task_create', data=request.get_json(), caseid=caseid)

        gtask = gtask_schema.load(request_data)

    except marshmallow.exceptions.ValidationError as e:
        return response_error(msg="Data error", data=e.messages)

    gtask.task_userid_update = current_user.id
    gtask.task_open_date = datetime.utcnow()
    gtask.task_last_update = datetime.utcnow()
    gtask.task_last_update = datetime.utcnow()

    try:

        db.session.add(gtask)
        db.session.commit()

    except Exception as e:
        return response_error(msg="Data error", data=e.__str__())

    gtask = call_modules_hook('on_postload_global_task_create', data=gtask, caseid=caseid)
    track_activity("created new global task \'{}\'".format(gtask.task_title), caseid=caseid)

    return response_success('Task added', data=gtask_schema.dump(gtask))


@dashboard_blueprint.route('/global/tasks/update/<int:cur_id>/modal', methods=['GET'])
@ac_api_requires()
def edit_gtask_modal(cur_id):
    form = CaseGlobalTaskForm()
    task = GlobalTasks.query.filter(GlobalTasks.id == cur_id).first()
    form.task_assignee_id.choices = [(user.id, user.name) for user in
                                     User.query.filter(User.active == True).order_by(User.name).all()]
    form.task_status_id.choices = [(a.id, a.status_name) for a in get_tasks_status()]

    # Render the task
    form.task_title.render_kw = {'value': task.task_title}
    form.task_description.data = task.task_description
    user_name, = User.query.with_entities(User.name).filter(User.id == task.task_userid_update).first()

    return render_template("modal_add_global_task.html", form=form, task=task,
                           uid=task.task_assignee_id, user_name=user_name)


@dashboard_blueprint.route('/global/tasks/update/<int:cur_id>', methods=['POST'])
@ac_api_requires()
@ac_requires_case_identifier()
def edit_gtask(cur_id, caseid):

    form = CaseGlobalTaskForm()
    task = GlobalTasks.query.filter(GlobalTasks.id == cur_id).first()
    form.task_assignee_id.choices = [(user.id, user.name) for user in User.query.filter(User.active == True).order_by(User.name).all()]
    form.task_status_id.choices = [(a.id, a.status_name) for a in get_tasks_status()]

    if not task:
        return response_error(msg="Data error", data="Invalid task ID")

    try:
        gtask_schema = GlobalTasksSchema()

        request_data = call_modules_hook('on_preload_global_task_update', data=request.get_json(),
                                         caseid=caseid)

        gtask = gtask_schema.load(request_data, instance=task)
        gtask.task_userid_update = current_user.id
        gtask.task_last_update = datetime.utcnow()

        db.session.commit()

        gtask = call_modules_hook('on_postload_global_task_update', data=gtask, caseid=caseid)

    except marshmallow.exceptions.ValidationError as e:
        return response_error(msg="Data error", data=e.messages)

    track_activity("updated global task {} (status {})".format(task.task_title, task.task_status_id), caseid=caseid)

    return response_success('Task updated', data=gtask_schema.dump(gtask))


@dashboard_blueprint.route('/global/tasks/delete/<int:cur_id>', methods=['POST'])
@ac_api_requires()
@ac_requires_case_identifier()
def gtask_delete(cur_id, caseid):

    call_modules_hook('on_preload_global_task_delete', data=cur_id, caseid=caseid)

    if not cur_id:
        return response_error("Missing parameter")

    data = GlobalTasks.query.filter(GlobalTasks.id == cur_id).first()
    if not data:
        return response_error("Invalid global task ID")

    GlobalTasks.query.filter(GlobalTasks.id == cur_id).delete()
    db.session.commit()

    call_modules_hook('on_postload_global_task_delete', data=request.get_json(), caseid=caseid)
    track_activity("deleted global task ID {}".format(cur_id), caseid=caseid)

    return response_success("Task deleted")


@dashboard_blueprint.route('/dashboard/case_states', methods=['GET'])
@ac_api_requires()
def get_case_states():
    """
    Returns all case states as JSON
    """
    return jsonify(get_case_states_list())


@dashboard_blueprint.route('/dashboard/generate_wordx_report', methods=['POST'])
@ac_api_requires()
def generate_wordx_report():
    """
    Generate a ZIP archive containing docx reports for each case matching the filters.
    """
    start_date = request.form.get('start_date') or None
    end_date = request.form.get('end_date') or None
    state_id = request.form.get('state_id') or None
    report_template_id = request.form.get('report_template_id')

    # Convert empty string to None for filters
    if not start_date:
        start_date = None
    if not end_date:
        end_date = None
    if not state_id:
        state_id = None
    else:
        state_id = int(state_id)

    if report_template_id:
        try:
            report_id = int(report_template_id)
        except Exception:
            # response_error("Invalid report template selected.", status=400)
            return jsonify({'error': 'Invalid report template selected.'}), 400
    else:
        # fallback to first available template
        report_templates = get_case_report_template()
        if not report_templates:
            return jsonify({'error': 'No report template found.'}), 404
        report_id = report_templates[0][0]

    # Query cases matching filters
    query = build_filter_case_query(current_user.id, start_open_date=start_date, end_open_date=end_date, case_state_id=state_id)
    cases = query.all()
    if not cases:
        return jsonify({'error': 'No cases found for the selected filters.'}), 404
    if len(cases) > 50:
        return jsonify({'error': 'Too many cases found for the selected filters.'}), 422
    # Generate reports in a temp dir
    tmp_dir = tempfile.mkdtemp()
    files = []
    for case in cases:
        caseid = case.case_id if hasattr(case, 'case_id') else case[0]  # support both ORM and tuple
        try:
            maker = IrisMakeDocReport(tmp_dir, report_id, caseid)
            fpath, logs = maker.generate_doc_report(doc_type="Investigation")
            if fpath and os.path.exists(fpath):
                with open(fpath, 'rb') as f:
                    files.append((os.path.basename(fpath), f.read()))
        except Exception as e:
            continue  # skip failed cases

    if not files:
        return jsonify({'error': 'Failed to generate any reports.'}), 500

    # Package files into a zip archive in memory
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for filename, filedata in files:
            zip_file.writestr(filename, filedata)
    zip_buffer.seek(0)

    # Clean up temp dir
    for filename, _ in files:
        try:
            os.remove(os.path.join(tmp_dir, filename))
        except Exception:
            pass
    try:
        os.rmdir(tmp_dir)
    except Exception:
        pass

    return send_file(
        zip_buffer,
        as_attachment=True,
        download_name='reports.zip',
        mimetype='application/zip'
    )


@dashboard_blueprint.route('/dashboard/report_templates', methods=['GET'])
@ac_api_requires()
def get_report_templates():
    """
    Returns a list of available report templates for Investigation reports.
    """
    templates = get_case_report_template()
    # templates: list of tuples (id, name, language, description)
    result = [
        {'id': t[0], 'name': t[1], 'language': t[2]} for t in templates
    ]
    return jsonify(result)
