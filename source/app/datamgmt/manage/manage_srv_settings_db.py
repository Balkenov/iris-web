from sqlalchemy import text
from sqlalchemy import and_
from datetime import datetime

from app import db
from app.models import ServerSettings
from app.schema.marshables import ServerSettingsSchema
from app.models.cases import Cases, CasesEvent, CaseTags
from app.models.alerts import Alert, AlertCaseAssociation
from app.models.models import (
    CaseAssets, Ioc, Comments, CaseTasks, Notes, CaseEventsIoc, IocLink,
    DataStorePath, DataStoreFile, CaseReceivedFile, CaseKanban, IrisReport,
    UserActivity, CaseEventsAssets, CaseEventCategory, CaseGraphAssets, CaseGraphLinks,
    CasesAssetsExt, NotesGroup, NotesGroupLink, TaskAssignee, TaskComments,
    IocComments, AssetComments, EvidencesComments, NotesComments, EventComments
)


def get_srv_settings():
    return ServerSettings.query.first()


def get_server_settings_as_dict():
    srv_settings = ServerSettings.query.first()
    if srv_settings:

        sc = ServerSettingsSchema()
        return sc.dump(srv_settings)

    else:
        return {}


def get_alembic_revision():
    with db.engine.connect() as con:
        version_num = con.execute(text("SELECT version_num FROM alembic_version")).first()[0]
    return version_num or None


def check_cases_for_deletion(start_date, end_date):
    """
    Check how many cases and alerts would be deleted in the given date range
    Excludes the primary case (case_id = 1) from deletion
    """
    try:
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Count cases in the date range, excluding the primary case
        cases_count = Cases.query.filter(
            and_(
                Cases.initial_date >= start_dt,
                Cases.initial_date <= end_dt,
                Cases.case_id != 1  # Exclude primary case
            )
        ).count()
        
        # Count alerts associated with cases in the date range, excluding primary case
        alerts_count = db.session.query(Alert).join(
            AlertCaseAssociation
        ).join(
            Cases
        ).filter(
            and_(
                Cases.initial_date >= start_dt,
                Cases.initial_date <= end_dt,
                Cases.case_id != 1  # Exclude primary case
            )
        ).count()
        
        return cases_count, alerts_count
        
    except Exception as e:
        raise Exception(f"Error checking cases for deletion: {str(e)}")


def delete_cases_by_date_range(start_date, end_date):
    """
    Delete cases and all related data within the specified date range
    This function is designed to handle tens of thousands of cases efficiently
    Excludes the primary case (case_id = 1) from deletion
    """
    try:
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Get all case IDs in the date range, excluding the primary case
        case_ids = db.session.query(Cases.case_id).filter(
            and_(
                Cases.initial_date >= start_dt,
                Cases.initial_date <= end_dt,
                Cases.case_id != 1  # Exclude primary case
            )
        ).all()
        
        case_ids = [case_id[0] for case_id in case_ids]
        
        if not case_ids:
            return 0, 0
        
        # Count alerts before deletion for reporting
        alerts_count = db.session.query(Alert).join(
            AlertCaseAssociation
        ).filter(
            AlertCaseAssociation.alert_id.in_(
                db.session.query(AlertCaseAssociation.alert_id).filter(
                    AlertCaseAssociation.case_id.in_(case_ids)
                )
            )
        ).count()
        
        # Delete in batches to handle large datasets efficiently
        batch_size = 1000
        
        for i in range(0, len(case_ids), batch_size):
            batch_case_ids = case_ids[i:i + batch_size]
            
            # Delete related data first (foreign key constraints)
            
            # Delete case assets
            db.session.query(CaseAssets).filter(
                CaseAssets.case_id.in_(batch_case_ids)
            ).delete(synchronize_session=False)
            
            # Delete case IOCs
            db.session.query(IocLink).filter(
                IocLink.case_id.in_(batch_case_ids)
            ).delete(synchronize_session=False)
            
            # Delete case comments
            db.session.query(Comments).filter(
                Comments.comment_case_id.in_(batch_case_ids)
            ).delete(synchronize_session=False)
            
            # Delete case events
            db.session.query(CasesEvent).filter(
                CasesEvent.case_id.in_(batch_case_ids)
            ).delete(synchronize_session=False)
            
            # Delete case tasks
            db.session.query(CaseTasks).filter(
                CaseTasks.task_case_id.in_(batch_case_ids)
            ).delete(synchronize_session=False)
            
            # Delete case notes
            db.session.query(Notes).filter(
                Notes.note_case_id.in_(batch_case_ids)
            ).delete(synchronize_session=False)
            
            # Delete case tags associations
            db.session.query(CaseTags).filter(
                CaseTags.case_id.in_(batch_case_ids)
            ).delete(synchronize_session=False)
            
            # Delete alert-case associations
            db.session.query(AlertCaseAssociation).filter(
                AlertCaseAssociation.case_id.in_(batch_case_ids)
            ).delete(synchronize_session=False)
            
            # Delete data store paths and files
            db.session.query(DataStoreFile).filter(
                DataStoreFile.file_case_id.in_(batch_case_ids)
            ).delete(synchronize_session=False)
            
            db.session.query(DataStorePath).filter(
                DataStorePath.path_case_id.in_(batch_case_ids)
            ).delete(synchronize_session=False)
            
            # Delete case received files
            db.session.query(CaseReceivedFile).filter(
                CaseReceivedFile.case_id.in_(batch_case_ids)
            ).delete(synchronize_session=False)
            
            # Delete case kanban
            db.session.query(CaseKanban).filter(
                CaseKanban.case_id.in_(batch_case_ids)
            ).delete(synchronize_session=False)
            
            # Delete iris reports
            db.session.query(IrisReport).filter(
                IrisReport.case_id.in_(batch_case_ids)
            ).delete(synchronize_session=False)
            
            # Delete user activities
            db.session.query(UserActivity).filter(
                UserActivity.case_id.in_(batch_case_ids)
            ).delete(synchronize_session=False)
            
            # Delete case events assets
            db.session.query(CaseEventsAssets).filter(
                CaseEventsAssets.case_id.in_(batch_case_ids)
            ).delete(synchronize_session=False)
            
            # Delete case event categories
            db.session.query(CaseEventCategory).filter(
                CaseEventCategory.event_id.in_(
                    db.session.query(CasesEvent.event_id).filter(
                        CasesEvent.case_id.in_(batch_case_ids)
                    )
                )
            ).delete(synchronize_session=False)
            
            # Delete case graph assets and links
            db.session.query(CaseGraphLinks).filter(
                CaseGraphLinks.case_id.in_(batch_case_ids)
            ).delete(synchronize_session=False)
            
            db.session.query(CaseGraphAssets).filter(
                CaseGraphAssets.case_id.in_(batch_case_ids)
            ).delete(synchronize_session=False)
            
            # Delete case assets ext
            db.session.query(CasesAssetsExt).filter(
                CasesAssetsExt.case_id.in_(batch_case_ids)
            ).delete(synchronize_session=False)
            
            # Delete notes groups and links
            db.session.query(NotesGroupLink).filter(
                NotesGroupLink.case_id.in_(batch_case_ids)
            ).delete(synchronize_session=False)
            
            db.session.query(NotesGroup).filter(
                NotesGroup.group_case_id.in_(batch_case_ids)
            ).delete(synchronize_session=False)
            
            # Delete task assignees
            db.session.query(TaskAssignee).filter(
                TaskAssignee.task_id.in_(
                    db.session.query(CaseTasks.id).filter(
                        CaseTasks.task_case_id.in_(batch_case_ids)
                    )
                )
            ).delete(synchronize_session=False)
            
            # Delete various comment associations
            db.session.query(TaskComments).filter(
                TaskComments.comment_task_id.in_(
                    db.session.query(CaseTasks.id).filter(
                        CaseTasks.task_case_id.in_(batch_case_ids)
                    )
                )
            ).delete(synchronize_session=False)
            
            db.session.query(IocComments).filter(
                IocComments.comment_ioc_id.in_(
                    db.session.query(IocLink.ioc_id).filter(
                        IocLink.case_id.in_(batch_case_ids)
                    )
                )
            ).delete(synchronize_session=False)
            
            db.session.query(AssetComments).filter(
                AssetComments.comment_asset_id.in_(
                    db.session.query(CaseAssets.asset_id).filter(
                        CaseAssets.case_id.in_(batch_case_ids)
                    )
                )
            ).delete(synchronize_session=False)
            
            db.session.query(EvidencesComments).filter(
                EvidencesComments.comment_evidence_id.in_(
                    db.session.query(CaseReceivedFile.id).filter(
                        CaseReceivedFile.case_id.in_(batch_case_ids)
                    )
                )
            ).delete(synchronize_session=False)
            
            db.session.query(NotesComments).filter(
                NotesComments.comment_note_id.in_(
                    db.session.query(Notes.note_id).filter(
                        Notes.note_case_id.in_(batch_case_ids)
                    )
                )
            ).delete(synchronize_session=False)
            
            db.session.query(EventComments).filter(
                EventComments.comment_event_id.in_(
                    db.session.query(CasesEvent.event_id).filter(
                        CasesEvent.case_id.in_(batch_case_ids)
                    )
                )
            ).delete(synchronize_session=False)
            
            # Delete the cases themselves
            db.session.query(Cases).filter(
                Cases.case_id.in_(batch_case_ids)
            ).delete(synchronize_session=False)
            
            # Commit each batch to avoid memory issues
            db.session.commit()
        
        return len(case_ids), alerts_count
        
    except Exception as e:
        db.session.rollback()
        raise Exception(f"Error deleting cases: {str(e)}")
