"""update cases table

Revision ID: b4bb60bc3dc6
Revises: 8e4d487025d3
Create Date: 2025-03-05 11:35:02.457643

"""
from alembic import op
import sqlalchemy as sa

from app.alembic.alembic_utils import _table_has_column


# revision identifiers, used by Alembic.
revision = 'b4bb60bc3dc6'
down_revision = '8e4d487025d3'
branch_labels = None
depends_on = None


def upgrade():
    if not _table_has_column("cases", "reason"):
        op.add_column('cases',
                      sa.Column('reason',
                                sa.Text, nullable=True),
                      )

    if not _table_has_column("cases", "original_name"):
        op.add_column('cases',
                      sa.Column('original_name',
                                sa.Text, nullable=True),
                      )

def downgrade():
    if _table_has_column("cases", "reason"):
        op.drop_column('cases', 'reason')

    if _table_has_column("cases", "original_name"):
        op.drop_column('cases', 'original_name')