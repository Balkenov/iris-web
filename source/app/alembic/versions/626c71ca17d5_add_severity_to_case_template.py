"""add_severity_to_case_template

Revision ID: 626c71ca17d5
Revises: b4bb60bc3dc6
Create Date: 2025-05-04 13:58:46.235096

"""
from alembic import op
import sqlalchemy as sa

from app.alembic.alembic_utils import _table_has_column

# revision identifiers, used by Alembic.
revision = '626c71ca17d5'
down_revision = 'b4bb60bc3dc6'
branch_labels = None
depends_on = None


def upgrade():
    if not _table_has_column("case_template", "severity"):
        op.add_column('case_template',
                      sa.Column('severity',
                                sa.Text, nullable=True),
                      )


def downgrade():
    if _table_has_column("case_template", "severity"):
        op.drop_column('case_template', 'severity')
