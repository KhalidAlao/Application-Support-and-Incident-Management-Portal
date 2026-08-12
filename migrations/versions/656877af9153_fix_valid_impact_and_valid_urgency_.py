"""fix valid_impact and valid_urgency constraints to allow NULL

Revision ID: 656877af9153
Revises: de6cd683615b
Create Date: 2026-08-12 20:50:41.994111

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '656877af9153'
down_revision = 'de6cd683615b'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('incidents', schema=None) as batch_op:
        batch_op.drop_constraint('valid_impact', type_='check')
        batch_op.drop_constraint('valid_urgency', type_='check')
        batch_op.create_check_constraint(
            'valid_impact',
            "impact IS NULL OR impact IN ('low', 'medium', 'high')"
        )
        batch_op.create_check_constraint(
            'valid_urgency',
            "urgency IS NULL OR urgency IN ('low', 'medium', 'high')"
        )

def downgrade():
    with op.batch_alter_table('incidents', schema=None) as batch_op:
        batch_op.drop_constraint('valid_impact', type_='check')
        batch_op.drop_constraint('valid_urgency', type_='check')
        batch_op.create_check_constraint('valid_impact', "impact IN ('low', 'medium', 'high')")
        batch_op.create_check_constraint('valid_urgency', "urgency IN ('low', 'medium', 'high')")
