from sqlalchemy import text
from sqlalchemy import and_
from datetime import datetime

from app import db
from app.models import ServerSettings
from app.schema.marshables import ServerSettingsSchema
from app.models.cases import Cases, CasesEvent, CaseTags
from app.models.alerts import Alert, AlertCaseAssociation, SimilarAlertsCache, AlertSimilarity
from app.models.models import (
    CaseAssets, Ioc, Comments, CaseTasks, Notes, CaseEventsIoc, IocLink,
    DataStorePath, DataStoreFile, CaseReceivedFile, CaseKanban, IrisReport,
    UserActivity, CaseEventsAssets, CaseEventCategory, CaseGraphAssets, CaseGraphLinks,
    CasesAssetsExt, NotesGroup, NotesGroupLink, TaskAssignee, TaskComments,
    IocComments, AssetComments, EvidencesComments, NotesComments, EventComments,
    ObjectState, alert_assets_association, alert_iocs_association
)
from app.models.authorization import OrganisationCaseAccess, GroupCaseAccess, UserCaseAccess, UserCaseEffectiveAccess


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
    Uses optimized raw SQL for maximum performance
    """
    try:
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Single optimized query to get both counts
        result = db.session.execute(text("""
            WITH case_ids AS (
                SELECT case_id FROM cases 
                WHERE initial_date >= :start_date 
                AND initial_date <= :end_date 
                AND case_id != 1
            ),
            alert_count AS (
                SELECT COUNT(DISTINCT a.alert_id) as count
                FROM alerts a 
                JOIN alert_case_association aca ON a.alert_id = aca.alert_id 
                JOIN case_ids ci ON aca.case_id = ci.case_id
            )
            SELECT 
                (SELECT COUNT(*) FROM case_ids) as cases_count,
                (SELECT count FROM alert_count) as alerts_count
        """), {'start_date': start_dt, 'end_date': end_dt})
        
        row = result.fetchone()
        cases_count = row[0] if row[0] else 0
        alerts_count = row[1] if row[1] else 0
        
        return cases_count, alerts_count
        
    except Exception as e:
        raise Exception(f"Error checking cases for deletion: {str(e)}")


def delete_cases_by_date_range(start_date, end_date):
    """
    Delete cases and all related data within the specified date range
    This function is designed to handle hundreds of thousands of cases efficiently
    Excludes the primary case (case_id = 1) from deletion
    Uses ultra-optimized raw SQL with single transaction approach
    """
    try:
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Get case IDs and count alerts in single query for maximum efficiency
        case_data_result = db.session.execute(text("""
            WITH case_ids AS (
                SELECT case_id FROM cases 
                WHERE initial_date >= :start_date 
                AND initial_date <= :end_date 
                AND case_id != 1
            ),
            alert_count AS (
                SELECT COUNT(DISTINCT a.alert_id) as count
                FROM alerts a 
                JOIN alert_case_association aca ON a.alert_id = aca.alert_id 
                JOIN case_ids ci ON aca.case_id = ci.case_id
            )
            SELECT 
                (SELECT COUNT(*) FROM case_ids) as cases_count,
                (SELECT count FROM alert_count) as alerts_count
        """), {'start_date': start_dt, 'end_date': end_dt})
        
        result = case_data_result.fetchone()
        cases_count = result[0] if result[0] else 0
        alerts_count = result[1] if result[1] else 0
        
        if cases_count == 0:
            return 0, 0
        
        # Use optimized bulk deletion with proper foreign key handling
        # This ensures all related objects are deleted in the correct order
        
        # First, get all case IDs for the date range
        case_ids_result = db.session.execute(text("""
            SELECT case_id FROM cases 
            WHERE initial_date >= :start_date 
            AND initial_date <= :end_date 
            AND case_id != 1
        """), {'start_date': start_dt, 'end_date': end_dt})
        
        case_ids = [row[0] for row in case_ids_result]
        
        if not case_ids:
            return 0, 0
        
        # Use large batches for better performance while ensuring complete deletion
        batch_size = 10000  # Much larger batches for better performance
        
        for i in range(0, len(case_ids), batch_size):
            batch_case_ids = case_ids[i:i + batch_size]
            batch_case_ids_str = ','.join(map(str, batch_case_ids))
            
            # Delete in proper order to handle foreign key constraints efficiently

            # Get alert IDs for this batch and delete related alert data
            alert_ids_result = db.session.execute(text(f"""
                SELECT DISTINCT alert_id 
                FROM alert_case_association 
                WHERE case_id IN ({batch_case_ids_str})
            """))
            
            # Delete alert associations and alerts first
            db.session.execute(text(f"""
                DELETE FROM alert_case_association WHERE case_id IN ({batch_case_ids_str})
            """))


            alert_ids = [row[0] for row in alert_ids_result]
            if alert_ids:
                alert_ids_str = ','.join(map(str, alert_ids))
                
                # Delete alert similarity records
                db.session.execute(text(f"""
                    DELETE FROM alert_similarity WHERE alert_id IN ({alert_ids_str})
                """))
                
                db.session.execute(text(f"""
                    DELETE FROM alert_similarity WHERE similar_alert_id IN ({alert_ids_str})
                """))
                
                # Delete alert similarity cache
                db.session.execute(text(f"""
                    DELETE FROM similar_alerts_cache WHERE alert_id IN ({alert_ids_str})
                """))
                
                # Delete alert associations
                db.session.execute(text(f"""
                    DELETE FROM alert_assets_association WHERE alert_id IN ({alert_ids_str})
                """))
                
                db.session.execute(text(f"""
                    DELETE FROM alert_iocs_association WHERE alert_id IN ({alert_ids_str})
                """))
                
                # Delete the alerts themselves
                db.session.execute(text(f"""
                    DELETE FROM alerts WHERE alert_id IN ({alert_ids_str})
                """))
            
            # 2. Delete case-related data in proper order
            db.session.execute(text(f"""
                DELETE FROM case_assets WHERE case_id IN ({batch_case_ids_str})
            """))
            
            db.session.execute(text(f"""
                DELETE FROM ioc_link WHERE case_id IN ({batch_case_ids_str})
            """))
            
            db.session.execute(text(f"""
                DELETE FROM object_state WHERE object_case_id IN ({batch_case_ids_str})
            """))
            
            db.session.execute(text(f"""
                DELETE FROM organisation_case_access WHERE case_id IN ({batch_case_ids_str})
            """))
            
            db.session.execute(text(f"""
                DELETE FROM group_case_access WHERE case_id IN ({batch_case_ids_str})
            """))
            
            db.session.execute(text(f"""
                DELETE FROM user_case_access WHERE case_id IN ({batch_case_ids_str})
            """))
            
            db.session.execute(text(f"""
                DELETE FROM user_case_effective_access WHERE case_id IN ({batch_case_ids_str})
            """))
            
            # 3. Delete comments and other case data
            db.session.execute(text(f"""
                DELETE FROM comments WHERE comment_case_id IN ({batch_case_ids_str})
            """))
            
            db.session.execute(text(f"""
                DELETE FROM cases_events WHERE case_id IN ({batch_case_ids_str})
            """))
            
            db.session.execute(text(f"""
                DELETE FROM case_tasks WHERE task_case_id IN ({batch_case_ids_str})
            """))
            
            db.session.execute(text(f"""
                DELETE FROM notes WHERE note_case_id IN ({batch_case_ids_str})
            """))
            
            db.session.execute(text(f"""
                DELETE FROM case_tags WHERE case_id IN ({batch_case_ids_str})
            """))
            
            # 4. Delete data store and other files
            db.session.execute(text(f"""
                DELETE FROM data_store_file WHERE file_case_id IN ({batch_case_ids_str})
            """))
            
            db.session.execute(text(f"""
                DELETE FROM data_store_path WHERE path_case_id IN ({batch_case_ids_str})
            """))
            
            db.session.execute(text(f"""
                DELETE FROM case_received_file WHERE case_id IN ({batch_case_ids_str})
            """))
            
            db.session.execute(text(f"""
                DELETE FROM case_kanban WHERE case_id IN ({batch_case_ids_str})
            """))
            
            db.session.execute(text(f"""
                DELETE FROM iris_reports WHERE case_id IN ({batch_case_ids_str})
            """))
            
            db.session.execute(text(f"""
                DELETE FROM user_activity WHERE case_id IN ({batch_case_ids_str})
            """))
            
            # 5. Delete remaining case-related data
            db.session.execute(text(f"""
                DELETE FROM case_events_assets WHERE case_id IN ({batch_case_ids_str})
            """))
            
            db.session.execute(text(f"""
                DELETE FROM case_events_category WHERE event_id IN (
                    SELECT event_id FROM cases_events WHERE case_id IN ({batch_case_ids_str})
                )
            """))
            
            db.session.execute(text(f"""
                DELETE FROM case_graph_links WHERE case_id IN ({batch_case_ids_str})
            """))
            
            db.session.execute(text(f"""
                DELETE FROM case_graph_assets WHERE case_id IN ({batch_case_ids_str})
            """))
            
            db.session.execute(text(f"""
                DELETE FROM cases_assets_ext WHERE case_id IN ({batch_case_ids_str})
            """))
            
            db.session.execute(text(f"""
                DELETE FROM notes_group_link WHERE case_id IN ({batch_case_ids_str})
            """))
            
            db.session.execute(text(f"""
                DELETE FROM notes_group WHERE group_case_id IN ({batch_case_ids_str})
            """))
            
            # 6. Delete comment associations
            db.session.execute(text(f"""
                DELETE FROM task_comments WHERE comment_task_id IN (
                    SELECT id FROM case_tasks WHERE task_case_id IN ({batch_case_ids_str})
                )
            """))
            
            db.session.execute(text(f"""
                DELETE FROM ioc_comments WHERE comment_ioc_id IN (
                    SELECT ioc_id FROM ioc_link WHERE case_id IN ({batch_case_ids_str})
                )
            """))
            
            db.session.execute(text(f"""
                DELETE FROM asset_comments WHERE comment_asset_id IN (
                    SELECT asset_id FROM case_assets WHERE case_id IN ({batch_case_ids_str})
                )
            """))
            
            db.session.execute(text(f"""
                DELETE FROM evidence_comments WHERE comment_evidence_id IN (
                    SELECT id FROM case_received_file WHERE case_id IN ({batch_case_ids_str})
                )
            """))
            
            db.session.execute(text(f"""
                DELETE FROM note_comments WHERE comment_note_id IN (
                    SELECT note_id FROM notes WHERE note_case_id IN ({batch_case_ids_str})
                )
            """))
            
            db.session.execute(text(f"""
                DELETE FROM event_comments WHERE comment_event_id IN (
                    SELECT event_id FROM cases_events WHERE case_id IN ({batch_case_ids_str})
                )
            """))
            
            # 7. Finally delete the cases themselves
            db.session.execute(text(f"""
                DELETE FROM cases WHERE case_id IN ({batch_case_ids_str})
            """))
            
            # Commit each batch to avoid memory issues
            db.session.commit()
        
        return cases_count, alerts_count
        
    except Exception as e:
        db.session.rollback()
        raise Exception(f"Error deleting cases: {str(e)}")
