"""Add index on cases initial_date

Revision ID: 7a8b9c0d1e2f
Revises: 626c71ca17d5
Create Date: 2025-01-07 10:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy import text

from app.alembic.alembic_utils import _has_table, index_exists

# revision identifiers, used by Alembic.
revision = '7a8b9c0d1e2f'
down_revision = '626c71ca17d5'
branch_labels = None
depends_on = None


def upgrade():
    # Add indexes for better performance during deletion operations
    
    # Force the migration to run by checking if indexes actually exist
    # This handles the case where Alembic thinks the migration is applied but indexes don't exist
    
    # Primary index for case deletion queries
    if _has_table('cases'):
        if not index_exists("cases", "ix_cases_initial_date"):
            op.create_index('ix_cases_initial_date', 'cases', ['initial_date'])
            print("✓ Created index on cases.initial_date for better deletion performance")
        else:
            print("✓ Index ix_cases_initial_date already exists")
    
    # Indexes for foreign key relationships to speed up cascading deletes
    
    # Alert-related indexes
    if _has_table('alert_case_association'):
        if not index_exists('alert_case_association', 'ix_alert_case_association_case_id'):
            op.create_index('ix_alert_case_association_case_id', 'alert_case_association', ['case_id'])
            print("✓ Created index on alert_case_association.case_id")
        if not index_exists('alert_case_association', 'ix_alert_case_association_alert_id'):
            op.create_index('ix_alert_case_association_alert_id', 'alert_case_association', ['alert_id'])
            print("✓ Created index on alert_case_association.alert_id")
    
    if _has_table('alert_similarity'):
        if not index_exists('alert_similarity', 'ix_alert_similarity_alert_id'):
            op.create_index('ix_alert_similarity_alert_id', 'alert_similarity', ['alert_id'])
            print("✓ Created index on alert_similarity.alert_id")
        if not index_exists('alert_similarity', 'ix_alert_similarity_similar_alert_id'):
            op.create_index('ix_alert_similarity_similar_alert_id', 'alert_similarity', ['similar_alert_id'])
            print("✓ Created index on alert_similarity.similar_alert_id")
    
    if _has_table('similar_alerts_cache'):
        if not index_exists('similar_alerts_cache', 'ix_similar_alerts_cache_alert_id'):
            op.create_index('ix_similar_alerts_cache_alert_id', 'similar_alerts_cache', ['alert_id'])
            print("✓ Created index on similar_alerts_cache.alert_id")
    
    if _has_table('alert_assets_association'):
        if not index_exists('alert_assets_association', 'ix_alert_assets_association_alert_id'):
            op.create_index('ix_alert_assets_association_alert_id', 'alert_assets_association', ['alert_id'])
            print("✓ Created index on alert_assets_association.alert_id")
    
    if _has_table('alert_iocs_association'):
        if not index_exists('alert_iocs_association', 'ix_alert_iocs_association_alert_id'):
            op.create_index('ix_alert_iocs_association_alert_id', 'alert_iocs_association', ['alert_id'])
            print("✓ Created index on alert_iocs_association.alert_id")
    
    if _has_table('alerts'):
        if not index_exists('alerts', 'ix_alerts_alert_id'):
            op.create_index('ix_alerts_alert_id', 'alerts', ['alert_id'])
            print("✓ Created index on alerts.alert_id")
    
    # Case-related indexes
    if _has_table('case_assets'):
        if not index_exists('case_assets', 'ix_case_assets_case_id'):
            op.create_index('ix_case_assets_case_id', 'case_assets', ['case_id'])
            print("✓ Created index on case_assets.case_id")
    
    if _has_table('ioc_link'):
        if not index_exists('ioc_link', 'ix_ioc_link_case_id'):
            op.create_index('ix_ioc_link_case_id', 'ioc_link', ['case_id'])
            print("✓ Created index on ioc_link.case_id")
    
    if _has_table('object_state'):
        if not index_exists('object_state', 'ix_object_state_object_case_id'):
            op.create_index('ix_object_state_object_case_id', 'object_state', ['object_case_id'])
            print("✓ Created index on object_state.object_case_id")
    
    if _has_table('organisation_case_access'):
        if not index_exists('organisation_case_access', 'ix_organisation_case_access_case_id'):
            op.create_index('ix_organisation_case_access_case_id', 'organisation_case_access', ['case_id'])
            print("✓ Created index on organisation_case_access.case_id")
    
    if _has_table('group_case_access'):
        if not index_exists('group_case_access', 'ix_group_case_access_case_id'):
            op.create_index('ix_group_case_access_case_id', 'group_case_access', ['case_id'])
            print("✓ Created index on group_case_access.case_id")
    
    if _has_table('user_case_access'):
        if not index_exists('user_case_access', 'ix_user_case_access_case_id'):
            op.create_index('ix_user_case_access_case_id', 'user_case_access', ['case_id'])
            print("✓ Created index on user_case_access.case_id")
    
    if _has_table('user_case_effective_access'):
        if not index_exists('user_case_effective_access', 'ix_user_case_effective_access_case_id'):
            op.create_index('ix_user_case_effective_access_case_id', 'user_case_effective_access', ['case_id'])
            print("✓ Created index on user_case_effective_access.case_id")
    
    if _has_table('comments'):
        if not index_exists('comments', 'ix_comments_comment_case_id'):
            op.create_index('ix_comments_comment_case_id', 'comments', ['comment_case_id'])
            print("✓ Created index on comments.comment_case_id")
    
    if _has_table('cases_events'):
        if not index_exists('cases_events', 'ix_cases_events_case_id'):
            op.create_index('ix_cases_events_case_id', 'cases_events', ['case_id'])
            print("✓ Created index on cases_events.case_id")
    
    if _has_table('case_tasks'):
        if not index_exists('case_tasks', 'ix_case_tasks_task_case_id'):
            op.create_index('ix_case_tasks_task_case_id', 'case_tasks', ['task_case_id'])
            print("✓ Created index on case_tasks.task_case_id")
    
    if _has_table('notes'):
        if not index_exists('notes', 'ix_notes_note_case_id'):
            op.create_index('ix_notes_note_case_id', 'notes', ['note_case_id'])
            print("✓ Created index on notes.note_case_id")
    
    if _has_table('case_tags'):
        if not index_exists('case_tags', 'ix_case_tags_case_id'):
            op.create_index('ix_case_tags_case_id', 'case_tags', ['case_id'])
            print("✓ Created index on case_tags.case_id")
    
    # Data store and file indexes
    if _has_table('data_store_file'):
        if not index_exists('data_store_file', 'ix_data_store_file_file_case_id'):
            op.create_index('ix_data_store_file_file_case_id', 'data_store_file', ['file_case_id'])
            print("✓ Created index on data_store_file.file_case_id")
    
    if _has_table('data_store_path'):
        if not index_exists('data_store_path', 'ix_data_store_path_path_case_id'):
            op.create_index('ix_data_store_path_path_case_id', 'data_store_path', ['path_case_id'])
            print("✓ Created index on data_store_path.path_case_id")
    
    if _has_table('case_received_file'):
        if not index_exists('case_received_file', 'ix_case_received_file_case_id'):
            op.create_index('ix_case_received_file_case_id', 'case_received_file', ['case_id'])
            print("✓ Created index on case_received_file.case_id")
    
    if _has_table('case_kanban'):
        if not index_exists('case_kanban', 'ix_case_kanban_case_id'):
            op.create_index('ix_case_kanban_case_id', 'case_kanban', ['case_id'])
            print("✓ Created index on case_kanban.case_id")
    
    if _has_table('iris_reports'):
        if not index_exists('iris_reports', 'ix_iris_reports_case_id'):
            op.create_index('ix_iris_reports_case_id', 'iris_reports', ['case_id'])
            print("✓ Created index on iris_reports.case_id")
    
    if _has_table('user_activity'):
        if not index_exists('user_activity', 'ix_user_activity_case_id'):
            op.create_index('ix_user_activity_case_id', 'user_activity', ['case_id'])
            print("✓ Created index on user_activity.case_id")
    
    # Additional case-related indexes
    if _has_table('case_events_assets'):
        if not index_exists('case_events_assets', 'ix_case_events_assets_case_id'):
            op.create_index('ix_case_events_assets_case_id', 'case_events_assets', ['case_id'])
            print("✓ Created index on case_events_assets.case_id")
    
    if _has_table('case_graph_links'):
        if not index_exists('case_graph_links', 'ix_case_graph_links_case_id'):
            op.create_index('ix_case_graph_links_case_id', 'case_graph_links', ['case_id'])
            print("✓ Created index on case_graph_links.case_id")
    
    if _has_table('case_graph_assets'):
        if not index_exists('case_graph_assets', 'ix_case_graph_assets_case_id'):
            op.create_index('ix_case_graph_assets_case_id', 'case_graph_assets', ['case_id'])
            print("✓ Created index on case_graph_assets.case_id")
    
    if _has_table('cases_assets_ext'):
        if not index_exists('cases_assets_ext', 'ix_cases_assets_ext_case_id'):
            op.create_index('ix_cases_assets_ext_case_id', 'cases_assets_ext', ['case_id'])
            print("✓ Created index on cases_assets_ext.case_id")
    
    if _has_table('notes_group_link'):
        if not index_exists('notes_group_link', 'ix_notes_group_link_case_id'):
            op.create_index('ix_notes_group_link_case_id', 'notes_group_link', ['case_id'])
            print("✓ Created index on notes_group_link.case_id")
    
    if _has_table('notes_group'):
        if not index_exists('notes_group', 'ix_notes_group_group_case_id'):
            op.create_index('ix_notes_group_group_case_id', 'notes_group', ['group_case_id'])
            print("✓ Created index on notes_group.group_case_id")
    
    # Comment association indexes
    if _has_table('task_comments'):
        if not index_exists('task_comments', 'ix_task_comments_comment_task_id'):
            op.create_index('ix_task_comments_comment_task_id', 'task_comments', ['comment_task_id'])
            print("✓ Created index on task_comments.comment_task_id")
    
    if _has_table('ioc_comments'):
        if not index_exists('ioc_comments', 'ix_ioc_comments_comment_ioc_id'):
            op.create_index('ix_ioc_comments_comment_ioc_id', 'ioc_comments', ['comment_ioc_id'])
            print("✓ Created index on ioc_comments.comment_ioc_id")
    
    if _has_table('asset_comments'):
        if not index_exists('asset_comments', 'ix_asset_comments_comment_asset_id'):
            op.create_index('ix_asset_comments_comment_asset_id', 'asset_comments', ['comment_asset_id'])
            print("✓ Created index on asset_comments.comment_asset_id")
    
    if _has_table('evidence_comments'):
        if not index_exists('evidence_comments', 'ix_evidence_comments_comment_evidence_id'):
            op.create_index('ix_evidence_comments_comment_evidence_id', 'evidence_comments', ['comment_evidence_id'])
            print("✓ Created index on evidence_comments.comment_evidence_id")
    
    if _has_table('note_comments'):
        if not index_exists('note_comments', 'ix_note_comments_comment_note_id'):
            op.create_index('ix_note_comments_comment_note_id', 'note_comments', ['comment_note_id'])
            print("✓ Created index on note_comments.comment_note_id")
    
    if _has_table('event_comments'):
        if not index_exists('event_comments', 'ix_event_comments_comment_event_id'):
            op.create_index('ix_event_comments_comment_event_id', 'event_comments', ['comment_event_id'])
            print("✓ Created index on event_comments.comment_event_id")


def downgrade():
    # Drop all the indexes created in upgrade
    
    # Primary index
    if _has_table('cases'):
        if index_exists('cases', 'ix_cases_initial_date'):
            op.drop_index('ix_cases_initial_date', table_name='cases')
            print("✓ Dropped index on cases.initial_date")
    
    # Alert-related indexes
    if _has_table('alert_case_association'):
        if index_exists('alert_case_association', 'ix_alert_case_association_case_id'):
            op.drop_index('ix_alert_case_association_case_id', table_name='alert_case_association')
            print("✓ Dropped index on alert_case_association.case_id")
        if index_exists('alert_case_association', 'ix_alert_case_association_alert_id'):
            op.drop_index('ix_alert_case_association_alert_id', table_name='alert_case_association')
            print("✓ Dropped index on alert_case_association.alert_id")
    
    if _has_table('alert_similarity'):
        if index_exists('alert_similarity', 'ix_alert_similarity_alert_id'):
            op.drop_index('ix_alert_similarity_alert_id', table_name='alert_similarity')
            print("✓ Dropped index on alert_similarity.alert_id")
        if index_exists('alert_similarity', 'ix_alert_similarity_similar_alert_id'):
            op.drop_index('ix_alert_similarity_similar_alert_id', table_name='alert_similarity')
            print("✓ Dropped index on alert_similarity.similar_alert_id")
    
    if _has_table('similar_alerts_cache'):
        if index_exists('similar_alerts_cache', 'ix_similar_alerts_cache_alert_id'):
            op.drop_index('ix_similar_alerts_cache_alert_id', table_name='similar_alerts_cache')
            print("✓ Dropped index on similar_alerts_cache.alert_id")
    
    if _has_table('alert_assets_association'):
        if index_exists('alert_assets_association', 'ix_alert_assets_association_alert_id'):
            op.drop_index('ix_alert_assets_association_alert_id', table_name='alert_assets_association')
            print("✓ Dropped index on alert_assets_association.alert_id")
    
    if _has_table('alert_iocs_association'):
        if index_exists('alert_iocs_association', 'ix_alert_iocs_association_alert_id'):
            op.drop_index('ix_alert_iocs_association_alert_id', table_name='alert_iocs_association')
            print("✓ Dropped index on alert_iocs_association.alert_id")
    
    if _has_table('alerts'):
        if index_exists('alerts', 'ix_alerts_alert_id'):
            op.drop_index('ix_alerts_alert_id', table_name='alerts')
            print("✓ Dropped index on alerts.alert_id")
    
    # Case-related indexes
    if _has_table('case_assets'):
        if index_exists('case_assets', 'ix_case_assets_case_id'):
            op.drop_index('ix_case_assets_case_id', table_name='case_assets')
            print("✓ Dropped index on case_assets.case_id")
    
    if _has_table('ioc_link'):
        if index_exists('ioc_link', 'ix_ioc_link_case_id'):
            op.drop_index('ix_ioc_link_case_id', table_name='ioc_link')
            print("✓ Dropped index on ioc_link.case_id")
    
    if _has_table('object_state'):
        if index_exists('object_state', 'ix_object_state_object_case_id'):
            op.drop_index('ix_object_state_object_case_id', table_name='object_state')
            print("✓ Dropped index on object_state.object_case_id")
    
    if _has_table('organisation_case_access'):
        if index_exists('organisation_case_access', 'ix_organisation_case_access_case_id'):
            op.drop_index('ix_organisation_case_access_case_id', table_name='organisation_case_access')
            print("✓ Dropped index on organisation_case_access.case_id")
    
    if _has_table('group_case_access'):
        if index_exists('group_case_access', 'ix_group_case_access_case_id'):
            op.drop_index('ix_group_case_access_case_id', table_name='group_case_access')
            print("✓ Dropped index on group_case_access.case_id")
    
    if _has_table('user_case_access'):
        if index_exists('user_case_access', 'ix_user_case_access_case_id'):
            op.drop_index('ix_user_case_access_case_id', table_name='user_case_access')
            print("✓ Dropped index on user_case_access.case_id")
    
    if _has_table('user_case_effective_access'):
        if index_exists('user_case_effective_access', 'ix_user_case_effective_access_case_id'):
            op.drop_index('ix_user_case_effective_access_case_id', table_name='user_case_effective_access')
            print("✓ Dropped index on user_case_effective_access.case_id")
    
    if _has_table('comments'):
        if index_exists('comments', 'ix_comments_comment_case_id'):
            op.drop_index('ix_comments_comment_case_id', table_name='comments')
            print("✓ Dropped index on comments.comment_case_id")
    
    if _has_table('cases_events'):
        if index_exists('cases_events', 'ix_cases_events_case_id'):
            op.drop_index('ix_cases_events_case_id', table_name='cases_events')
            print("✓ Dropped index on cases_events.case_id")
    
    if _has_table('case_tasks'):
        if index_exists('case_tasks', 'ix_case_tasks_task_case_id'):
            op.drop_index('ix_case_tasks_task_case_id', table_name='case_tasks')
            print("✓ Dropped index on case_tasks.task_case_id")
    
    if _has_table('notes'):
        if index_exists('notes', 'ix_notes_note_case_id'):
            op.drop_index('ix_notes_note_case_id', table_name='notes')
            print("✓ Dropped index on notes.note_case_id")
    
    if _has_table('case_tags'):
        if index_exists('case_tags', 'ix_case_tags_case_id'):
            op.drop_index('ix_case_tags_case_id', table_name='case_tags')
            print("✓ Dropped index on case_tags.case_id")
    
    # Data store and file indexes
    if _has_table('data_store_file'):
        if index_exists('data_store_file', 'ix_data_store_file_file_case_id'):
            op.drop_index('ix_data_store_file_file_case_id', table_name='data_store_file')
            print("✓ Dropped index on data_store_file.file_case_id")
    
    if _has_table('data_store_path'):
        if index_exists('data_store_path', 'ix_data_store_path_path_case_id'):
            op.drop_index('ix_data_store_path_path_case_id', table_name='data_store_path')
            print("✓ Dropped index on data_store_path.path_case_id")
    
    if _has_table('case_received_file'):
        if index_exists('case_received_file', 'ix_case_received_file_case_id'):
            op.drop_index('ix_case_received_file_case_id', table_name='case_received_file')
            print("✓ Dropped index on case_received_file.case_id")
    
    if _has_table('case_kanban'):
        if index_exists('case_kanban', 'ix_case_kanban_case_id'):
            op.drop_index('ix_case_kanban_case_id', table_name='case_kanban')
            print("✓ Dropped index on case_kanban.case_id")
    
    if _has_table('iris_reports'):
        if index_exists('iris_reports', 'ix_iris_reports_case_id'):
            op.drop_index('ix_iris_reports_case_id', table_name='iris_reports')
            print("✓ Dropped index on iris_reports.case_id")
    
    if _has_table('user_activity'):
        if index_exists('user_activity', 'ix_user_activity_case_id'):
            op.drop_index('ix_user_activity_case_id', table_name='user_activity')
            print("✓ Dropped index on user_activity.case_id")
    
    # Additional case-related indexes
    if _has_table('case_events_assets'):
        if index_exists('case_events_assets', 'ix_case_events_assets_case_id'):
            op.drop_index('ix_case_events_assets_case_id', table_name='case_events_assets')
            print("✓ Dropped index on case_events_assets.case_id")
    
    if _has_table('case_graph_links'):
        if index_exists('case_graph_links', 'ix_case_graph_links_case_id'):
            op.drop_index('ix_case_graph_links_case_id', table_name='case_graph_links')
            print("✓ Dropped index on case_graph_links.case_id")
    
    if _has_table('case_graph_assets'):
        if index_exists('case_graph_assets', 'ix_case_graph_assets_case_id'):
            op.drop_index('ix_case_graph_assets_case_id', table_name='case_graph_assets')
            print("✓ Dropped index on case_graph_assets.case_id")
    
    if _has_table('cases_assets_ext'):
        if index_exists('cases_assets_ext', 'ix_cases_assets_ext_case_id'):
            op.drop_index('ix_cases_assets_ext_case_id', table_name='cases_assets_ext')
            print("✓ Dropped index on cases_assets_ext.case_id")
    
    if _has_table('notes_group_link'):
        if index_exists('notes_group_link', 'ix_notes_group_link_case_id'):
            op.drop_index('ix_notes_group_link_case_id', table_name='notes_group_link')
            print("✓ Dropped index on notes_group_link.case_id")
    
    if _has_table('notes_group'):
        if index_exists('notes_group', 'ix_notes_group_group_case_id'):
            op.drop_index('ix_notes_group_group_case_id', table_name='notes_group')
            print("✓ Dropped index on notes_group.group_case_id")
    
    # Comment association indexes
    if _has_table('task_comments'):
        if index_exists('task_comments', 'ix_task_comments_comment_task_id'):
            op.drop_index('ix_task_comments_comment_task_id', table_name='task_comments')
            print("✓ Dropped index on task_comments.comment_task_id")
    
    if _has_table('ioc_comments'):
        if index_exists('ioc_comments', 'ix_ioc_comments_comment_ioc_id'):
            op.drop_index('ix_ioc_comments_comment_ioc_id', table_name='ioc_comments')
            print("✓ Dropped index on ioc_comments.comment_ioc_id")
    
    if _has_table('asset_comments'):
        if index_exists('asset_comments', 'ix_asset_comments_comment_asset_id'):
            op.drop_index('ix_asset_comments_comment_asset_id', table_name='asset_comments')
            print("✓ Dropped index on asset_comments.comment_asset_id")
    
    if _has_table('evidence_comments'):
        if index_exists('evidence_comments', 'ix_evidence_comments_comment_evidence_id'):
            op.drop_index('ix_evidence_comments_comment_evidence_id', table_name='evidence_comments')
            print("✓ Dropped index on evidence_comments.comment_evidence_id")
    
    if _has_table('note_comments'):
        if index_exists('note_comments', 'ix_note_comments_comment_note_id'):
            op.drop_index('ix_note_comments_comment_note_id', table_name='note_comments')
            print("✓ Dropped index on note_comments.comment_note_id")
    
    if _has_table('event_comments'):
        if index_exists('event_comments', 'ix_event_comments_comment_event_id'):
            op.drop_index('ix_event_comments_comment_event_id', table_name='event_comments')
            print("✓ Dropped index on event_comments.comment_event_id") 