from __future__ import absolute_import

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declared_attr
import sqlalchemy.orm as saorm

import flask_user

from .entities import (
    UserGroup,
    joined_permission_query,
    make_user_to_user_group_link,
    user_group_bundle_map,
    user_group_permission_map,
)


class UserMixin(flask_user.UserMixin):
    """A mixin that adds permission facilities to a SQLAlchemy declarative user entity.

    A class which mixes this in must provide one of the following:
        * An `id` column member which represents the primary key. The actual column may have any
          name and any type.
        * Or, a `primary_key_column` class variable that gives the name of the primary key column
          as a string.
    """

    # Instances will shadow this when populating their own cache.
    _cached_permissions = None

    primary_key_column = 'id'  # Name of the primary key. Subclasses can override this default.

    @declared_attr
    def user_groups(cls):
        return saorm.relationship(UserGroup,
                                  secondary=cls.user_user_group_map,
                                  cascade='all',
                                  passive_deletes=True,
                                  backref='users')

    @declared_attr
    def user_user_group_map(cls):
        """A linking (mapping) table between users and user groups."""
        return make_user_to_user_group_link(getattr(cls, cls.primary_key_column))

    def get_all_permissions(self):
        """Get all permissions that are joined to this User, whether directly, through
           permission bundles, or through user groups."""
        self._cached_permissions = self._cached_permissions or \
            frozenset(joined_permission_query().join(
                    self.user_user_group_map,
                    sa.or_(
                        self.user_user_group_map.c.user_group_id
                            == user_group_permission_map.c.user_group_id,  # noqa
                        self.user_user_group_map.c.user_group_id
                            == user_group_bundle_map.c.user_group_id  # noqa
                    )
                ).filter(
                    self.user_user_group_map.c.user_id
                        == getattr(self, self.primary_key_column),  # noqa
                ))
        return self._cached_permissions

    def has_permissions(self, *tokens):
        """Returns True IFF every given permission token is present in the user's permission set."""
        return frozenset(tokens) <= {x.token for x in self.get_all_permissions()}

    def has_any_permissions(self, *tokens):
        """Returns True IFF any of the given permission tokens are present in the user's permission
        set."""
        return not frozenset(tokens).isdisjoint(x.token for x in self.get_all_permissions())

    def reset_permission_cache(self):
        self._cached_permissions = None
