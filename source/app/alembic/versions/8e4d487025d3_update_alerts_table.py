"""update alerts table

Revision ID: 8e4d487025d3
Revises: d5a720d1b99b
Create Date: 2025-02-24 20:08:25.919795

"""
from alembic import op
import sqlalchemy as sa

from app.alembic.alembic_utils import _table_has_column
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = '8e4d487025d3'
down_revision = 'd5a720d1b99b'
branch_labels = None
depends_on = None


def upgrade():
    if not _table_has_column("alerts", "alert_reason"):
        op.add_column('alerts',
                      sa.Column('alert_reason',
                                sa.Text, nullable=True),
                      )

    if not _table_has_column("alerts", "alert_mitre"):
        op.add_column('alerts',
                      sa.Column('alert_mitre',
                                sa.Text)
                      )

    if not _table_has_column("alerts", "alert_host_name"):
        op.add_column('alerts',
                      sa.Column('alert_host_name',
                                sa.Text)
                      )

    if not _table_has_column("alerts", "alert_host_ip"):
        op.add_column('alerts',
                      sa.Column('alert_host_ip',
                                sa.Text)
                      )

    if not _table_has_column("alerts", "alert_agent_id"):
        op.add_column('alerts',
                      sa.Column('alert_agent_id',
                                sa.Text)
                      )

    if not _table_has_column("alerts", "alert_user_name"):
        op.add_column('alerts',
                      sa.Column('alert_user_name',
                                sa.Text)
                      )

    if not _table_has_column("alerts", "alert_required_fields"):
        op.add_column('alerts',
                      sa.Column('alert_required_fields',
                                sa.Text)
                      )

    if not _table_has_column("alerts", "alert_customer_space"):
        op.add_column('alerts',
                      sa.Column('alert_customer_space',
                                sa.Text)
                      )
def downgrade():
    if _table_has_column("alerts", "alert_reason"):
        op.drop_column('alerts', 'alert_reason')
    if _table_has_column("alerts", "alert_mitre"):
        op.drop_column('alerts', 'alert_mitre')
    if _table_has_column("alerts", "alert_host_name"):
        op.drop_column('alerts', 'alert_host_name')
    if _table_has_column("alerts", "alert_host_ip"):
        op.drop_column('alerts', 'alert_host_ip')
    if _table_has_column("alerts", "alert_agent_id"):
        op.drop_column('alerts', 'alert_agent_id')
    if _table_has_column("alerts", "alert_user_name"):
        op.drop_column('alerts', 'alert_user_name')
    if _table_has_column("alerts", "alert_required_fields"):
        op.drop_column('alerts', 'alert_required_fields')
    if _table_has_column("alerts", "alert_customer_space"):
        op.drop_column('alerts', 'alert_customer_space')
