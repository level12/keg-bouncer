"""Functions for use in Alembic migrations that integrate KegBouncer tables with
application-specific tables.
"""
from .entities import make_user_to_user_group_link, user_user_group_link_table_name


def link_user_to_user_groups(op, user_primary_key_column):
    """Creates a many-to-many linking table between the the User entity.

    WARNING: This migration utility assumes your database is at the most recent version of
    KegBouncer.

    :param op: must be the Alembic operations object.
    :param user_primary_key_column: must be a SQLAlchemy Column object representing the primary key
                                    of your User entity (the one which mixes in
                                    keg_bouncer.model.mixins.UserMixin).
    :returns: the SQLAlchemy Table object.
    """
    return make_user_to_user_group_link(user_primary_key_column, table_constructor=op.create_table)


def drop_link_from_user_to_user_groups(op):
    op.drop_table(user_user_group_link_table_name)
