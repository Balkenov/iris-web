from datetime import datetime

import marshmallow
from flask import redirect, url_for, render_template, Blueprint, request
from flask_login import current_user
from flask_wtf import FlaskForm

from app.datamgmt.case.case_db import get_case
from app.datamgmt.manage.manage_access_control_db import user_has_client_access
from app.iris_engine.module_handler.module_handler import call_modules_hook
from app.models.authorization import CaseAccessLevel

from app.util import ac_case_requires, add_obj_history_entry

from app.util import response_error

from app.util import response_success

from app.datamgmt.case.case_comments import get_case_comments, delete_case_comment, get_case_comment

from app.schema.marshables import CommentSchema
from app import db
from app.blueprints.case.case_comments import case_comment_update

case_comments_blueprint = Blueprint(
    'case_comments',
    __name__,
    template_folder='templates'
)

@case_comments_blueprint.route('/case/comments/<int:cur_id>/comments/list', methods=['GET'])
@ac_case_requires(CaseAccessLevel.read_only, CaseAccessLevel.full_access)
def case_comment_list(cur_id, caseid, url_redir):

    evidence_comments = get_case_comments(caseid)
    if evidence_comments is None:
        return response_error('Invalid evidence ID')

    return response_success(data=CommentSchema(many=True).dump(evidence_comments))


@case_comments_blueprint.route('/case/comments/<int:cur_id>/comments/modal', methods=['GET'])
@ac_case_requires(CaseAccessLevel.read_only, CaseAccessLevel.full_access)
def case_comment_modal(cur_id, caseid, url_redir):
    """
    Get the modal for the alert comments

    args:
        cur_id (int): The alert id
        caseid (str): The case id

    returns:
        Response: The response
    """
    # if url_redir:
    #     return redirect(url_for('alerts.alerts_list_view_route', cid=caseid, redirect=True)) # todo

    # if not user_has_client_access(current_user.id, alert.alert_customer_id):
    #     return response_error('User not entitled to update alerts for the client', status=403)

    return render_template("modal_conversation.html", element_id=caseid, element_type='comments',
                           title=f" case #{caseid}")


@case_comments_blueprint.route('/case/comments/<int:caseid>/comments/add', methods=['POST'])
@ac_case_requires(CaseAccessLevel.read_only, CaseAccessLevel.full_access)
def case_comment_add(caseid, url_redir):
    """
    Add a comment to a case

    args:
        alert_id (int): The alert id
        caseid (str): The case id

    returns:
        Response: The response
    """
    try:
        case = get_case(caseid)
        if not case:
            return response_error('Invalid case ID')

        # if not user_has_client_access(current_user.id, case.client_id):
        #     return response_error('User not entitled to read alerts for the client', status=403) todo

        comment_schema = CommentSchema()

        comment = comment_schema.load(request.get_json())
        # comment.comment_alert_id = alert_id
        comment.comment_case_id = caseid
        comment.comment_user_id = current_user.id
        comment.comment_date = datetime.now()
        comment.comment_update_date = datetime.now()
        db.session.add(comment)
        db.session.commit()

        add_obj_history_entry(case, 'commented')

        db.session.commit()

        # hook_data = {
        #     "comment": comment_schema.dump(comment),
        #     "alert": AlertSchema().dump(alert)
        # } todo
        # call_modules_hook('on_postload_alert_commented', data=hook_data)

        # track_activity(f"alert \"{alert.alert_id}\" commented", ctx_less=True)
        return response_success("Alert commented", data=comment_schema.dump(comment))

    except marshmallow.exceptions.ValidationError as e:
        return response_error(msg="Data error", data=e.normalized_messages())


@case_comments_blueprint.route('/case/comments/<int:caseid>/comments/<int:com_id>/delete', methods=['POST'])
@ac_case_requires(CaseAccessLevel.read_only, CaseAccessLevel.full_access)
def case_comment_delete(caseid, com_id, url_redir):
    """
    Delete a comment for an alert

    args:
        caseid (int): The alert id
        com_id (int): The comment id
        caseid (str): The case id

    returns:
        Response: The response
    """
    # Check if the user has access to the client
    case = get_case(caseid)
    if not case:
        return response_error('Invalid case ID')

    # if not user_has_client_access(current_user.id, case.client_id):
    #     return response_error('User not entitled to read alerts for the client', status=403)

    success, msg = delete_case_comment(comment_id=com_id, caseid=caseid)
    if not success:
        return response_error(msg)

    # call_modules_hook('on_postload_alert_comment_delete', data=com_id)

    # track_activity(f"comment {com_id} on alert {alert_id} deleted", ctx_less=True)

    return response_success(msg)

@case_comments_blueprint.route('/case/comments/<int:caseid>/comments/<int:com_id>/edit', methods=['POST'])
@ac_case_requires(CaseAccessLevel.read_only, CaseAccessLevel.full_access)
def case_comment_edit(caseid: int, com_id, url_redir):
    """
    Edit a comment for an alert

    args:
        alert_id (int): The alert id
        com_id (int): The comment id
        caseid (str): The case id

    returns:
        Response: The response
    """
    case = get_case(caseid)
    if not case:
        return response_error('Invalid case ID')

    # if not user_has_client_access(current_user.id, alert.alert_customer_id):
    #     return response_error('User not entitled to read alerts for the client', status=403)

    return case_comment_update(com_id, 'events', None)


@case_comments_blueprint.route('/case/comments/<int:caseid>/comments/<int:com_id>', methods=['GET'])
@ac_case_requires(CaseAccessLevel.read_only, CaseAccessLevel.full_access)
def alert_comment_get(caseid, com_id, url_redir):
    """
    Get a comment for an alert

    args:
        cur_id (int): The alert id
        com_id (int): The comment id
        caseid (str): The case id

    returns:
        Response: The response
    """
    # Check if the user has access to the client
    case = get_case(caseid)
    if not case:
        return response_error('Invalid case ID')

    # if not user_has_client_access(current_user.id, alert.alert_customer_id):
    #     return response_error('User not entitled to read alerts for the client', status=403)

    comment = get_case_comment(com_id, caseid)
    if not comment:
        return response_error("Invalid comment ID")

    return response_success(data=CommentSchema().dump(comment))