from __future__ import absolute_import

import sqlalchemy as sa
import sqlalchemy.orm as saorm
from keg.db import db
from keg_elements.db.mixins import MethodsMixin


class Permission(db.Model, MethodsMixin):
    """An entity that describes an authentication boundary which can be used directly
    in the application to permit or deny access to something.

    As a whole, the set of Permission entities describes every possible authentication
    boundary within the application.

    An "authentication boundary" is a decision point where the question arises,
    "Is the current user of this application authorized to access this feature?"

    Permissions have two touchpoints with the application:
      1) They touch the source code directly.
      2) They touch the user of the application directly.

    Source code includes decision points where a particular permission can be required
    for a user to access something. To facilitate this touchpoint, each permission has
    a unique `token` string which allows the code to refer to the permission itself.
    This is the only way, in fact, that source code can refer to a permission.

    Permissions also directly touch users of the application in that users can be
    granted any number of permissions. These represent the authority possesed by the
    user. To facilitate this touchpoint, each permission has a string description that
    provides a helpful, human-oriented description of the permission.
    """
    __tablename__ = 'permissions'
    id = sa.Column(sa.Integer, primary_key=True)
    token = sa.Column(sa.String(255), nullable=False, unique=True)
    description = sa.Column(sa.Text, nullable=False)


class PermissionBundle(db.Model, MethodsMixin):
    """An entity which groups permissions under a common label.

    It is often the case that a set of fine-grained permissions will all relate to a
    common task or component. Permission bundles allow the system to represent this
    commonality explicitly.
    """
    __tablename__ = 'permission_bundles'
    id = sa.Column(sa.Integer, primary_key=True)
    label = sa.Column(sa.Text, nullable=False)
    permissions = saorm.relationship(Permission,
                                     secondary=lambda: bundle_permission_map,
                                     cascade='all',
                                     passive_deletes=True,
                                     backref='parent_bundles')


class UserGroup(db.Model, MethodsMixin):
    """An entity which groups users under a common label.

    In addition to grouping permissions, it is also often necessary to describe
    how users of a system are grouped for the sake of the business. For example,
    a business might have a team of auditors who need to view many reports, but
    never make changes. Additionally the business has a team of editors who
    need to make changes but rarely view reports.

    These different "roles" within the business can be represented with user groups.

    User groups may contain permissions directy and/or through permission bundles.
    """
    __tablename__ = 'user_groups'
    id = sa.Column(sa.Integer, primary_key=True)
    label = sa.Column(sa.Text, nullable=False)
    permissions = saorm.relationship(Permission,
                                     secondary=lambda: user_group_permission_map,
                                     cascade='all',
                                     passive_deletes=True,
                                     backref='parent_user_groups')
    bundles = saorm.relationship(PermissionBundle,
                                 secondary=lambda: user_group_bundle_map,
                                 cascade='all',
                                 passive_deletes=True,
                                 backref='parent_user_groups')

    def get_all_permissions(self):
        """Calculates the join of all permissions within this user group, some of which are derived
        directly and some indirectly (through permission bundles).
        """
        return frozenset(joined_permission_query().filter(
            sa.or_(
                user_group_permission_map.c.user_group_id == self.id,
                user_group_bundle_map.c.user_group_id == self.id
            )
        ))


def make_link(name, from_column_name, from_column, to_column_name, to_column):
    """Returns a table which represents a many-to-many relationship between two columns.

    :param name: is the name of the linking table.
    :from_column_name: is the desired name of the linking table's left column.
    :from_column: is the column object to which the linking table's left column should refer.
    :to_column_name: ditto, for the right column.
    :to_column: ditto, for the right column.
    """
    return db.Table(
        name,
        sa.Column(
            from_column_name,
            from_column.type,
            sa.ForeignKey(from_column, ondelete='CASCADE'),
            nullable=False,
            primary_key=True),
        sa.Column(
            to_column_name,
            to_column.type,
            sa.ForeignKey(to_column, ondelete='CASCADE'),
            nullable=False,
            primary_key=True)
    )


user_group_permission_map = make_link('user_group_permission_map',
                                      'user_group_id', UserGroup.id,
                                      'permission_id', Permission.id)

user_group_bundle_map = make_link('user_group_bundle_map',
                                  'user_group_id', UserGroup.id,
                                  'permission_bundle_id', PermissionBundle.id)

bundle_permission_map = make_link('bundle_permission_map',
                                  'permission_bundle_id', PermissionBundle.id,
                                  'permission_id', Permission.id)


# A query that joins user groups with their related permissions, permission bundles, and the
# bundles' permissions. Filter/join the query further to find all related permissions for the user
# groups and bundles you care about.
joined_permission_query = lambda: Permission.query.outerjoin(
    bundle_permission_map
).outerjoin(
    user_group_bundle_map,
    user_group_bundle_map.c.permission_bundle_id == bundle_permission_map.c.permission_bundle_id
).outerjoin(
    user_group_permission_map
)
