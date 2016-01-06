"""Initial revision

Revision ID: 588daaa98ab1
Revises:
Create Date: 2016-01-06 15:06:51.080805

"""

# revision identifiers, used by Alembic.
revision = '588daaa98ab1'
down_revision = None
branch_labels = ('keg-bouncer',)
depends_on = None

from alembic import op
import sqlalchemy as sa

from keg_bouncer.model.utils import make_link


def create_label_table(op, name):
    return op.create_table(
        name,
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('label', sa.Text, unique=True, nullable=False)
    )


def upgrade():
    permission = op.create_table(
        'keg_bouncer_permissions',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('token', sa.String(255), nullable=False, unique=True),
        sa.Column('description', sa.Text, nullable=False)
    )

    permission_bundle = create_label_table(op, 'keg_bouncer_permission_bundles')
    user_group = create_label_table(op, 'keg_bouncer_user_groups')

    make_link('keg_bouncer_user_group_permission_map',
              'user_group_id', user_group.c.id,
              'permission_id', permission.c.id,
              table_constructor=op.create_table)

    make_link('keg_bouncer_user_group_bundle_map',
              'user_group_id', user_group.c.id,
              'permission_bundle_id', permission_bundle.c.id,
              table_constructor=op.create_table)

    make_link('keg_bouncer_bundle_permission_map',
              'permission_bundle_id', permission_bundle.c.id,
              'permission_id', permission.c.id,
              table_constructor=op.create_table)


def downgrade(op):
    op.drop_table('keg_bouncer_bundle_permission_map')
    op.drop_table('keg_bouncer_user_group_bundle_map')
    op.drop_table('keg_bouncer_user_group_permission_map')
    op.drop_table('keg_bouncer_user_groups')
    op.drop_table('keg_bouncer_permission_bundles')
    op.drop_table('keg_bouncer_permissions')
