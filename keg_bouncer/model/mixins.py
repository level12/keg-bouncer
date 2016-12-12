from __future__ import absolute_import

from six import text_type
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.inspection import inspect
import sqlalchemy.orm as saorm

from . import entities as ents
from . import interfaces


class KegBouncerMixin(object):
    _invalid_primary_key_error = AttributeError(
        'This KegBouncer mixin requires your entity class to have exactly 1 primary key field.')

    @classmethod
    def _primary_key_column(cls):
        pk_attrs = [value for value in cls.__dict__.values()
                    if getattr(value, 'primary_key', None) is True]
        if len(pk_attrs) != 1:
            raise cls._invalid_primary_key_error
        return pk_attrs[0]

    def _primary_key_value(self):
        """
        Warning: Calling this method on a deleted entity may raise
        :class:`sqlalchemy.orm.exc.ObjectDeletedError`.
        """
        values = inspect(self.__class__).primary_key_from_instance(self)
        if len(values) != 1:  # pragma: no cover
            raise self._invalid_primary_key_error
        return values[0]

    @hybrid_property
    def _primary_key(self):
        return self._primary_key_value()

    @_primary_key.expression
    def _primary_key(cls):
        return cls._primary_key_column()


class PermissionMixin(interfaces.HasPermissions, KegBouncerMixin):
    """A mixin that adds permission facilities to a SQLAlchemy declarative user entity.

    A class which mixes this in must provide one of the following:
        * An `id` column member which represents the primary key. The actual column may have any
          name and any type.
        * Or, a `primary_key_column` class variable that gives the name of the primary key column
          as a string.
    """

    # Instances will shadow this when populating their own cache.
    _cached_permissions = None

    @declared_attr
    def user_groups(cls):
        return saorm.relationship(ents.UserGroup,
                                  secondary=cls.user_user_group_map,
                                  cascade='all',
                                  passive_deletes=True,
                                  backref='users')

    @declared_attr
    def user_user_group_map(cls):
        """A linking (mapping) table between users and user groups."""
        return ents.make_user_to_user_group_link(cls._primary_key_column(), cls.__tablename__)

    @hybrid_property
    def user_mapping_column(self):
        return self.user_user_group_map.c.user_id

    @hybrid_property
    def permissions_query(self):
        """A query that maps users to permissions through all possible avenues."""
        return ents.joined_permission_query().join(
            self.user_user_group_map,
            sa.or_(
                self.user_user_group_map.c.user_group_id
                    == ents.user_group_permission_map.c.user_group_id,  # noqa
                self.user_user_group_map.c.user_group_id
                    == ents.user_group_bundle_map.c.user_group_id  # noqa
            )
        )

    @hybrid_property
    def permissions_with_user_id_query(self):
        """
        Like `permissions_query` but adds a column called `user_id` that can be used to
        filter/join on a particular user ID or user ID column.
        """
        return self.permissions_query.add_columns(
            self.user_mapping_column.label('user_id')
        )

    def get_all_permissions_without_cache(self):
        """Get all permissions that are joined to this User, whether directly, through permission
        bundles, or through user groups.

        Warning: Calling this method on a deleted entity may raise
        :class:`sqlalchemy.orm.exc.ObjectDeletedError`.
        """
        return frozenset(self.permissions_query.filter(
            self.user_mapping_column == self._primary_key
        ))

    def get_all_permissions(self):
        """Same as `get_all_permissions_without_cache` but uses a cached result after the first
        call.

        Warning: Calling this method on a deleted entity may raise
        :class:`sqlalchemy.orm.exc.ObjectDeletedError`.
        """
        self._cached_permissions = (self._cached_permissions
                                    or self.get_all_permissions_without_cache())
        return self._cached_permissions

    def has_permissions(self, *tokens):
        """Returns True IFF every given permission token is present in the user's permission set.

        Warning: Calling this method on a deleted entity may raise
        :class:`sqlalchemy.orm.exc.ObjectDeletedError`.
        """
        return frozenset(tokens) <= {x.token for x in self.get_all_permissions()}

    def has_any_permissions(self, *tokens):
        """Returns True IFF any of the given permission tokens are present in the user's permission
        set.

        Warning: Calling this method on a deleted entity may raise
        :class:`sqlalchemy.orm.exc.ObjectDeletedError`.
        """
        return not frozenset(tokens).isdisjoint(x.token for x in self.get_all_permissions())

    def reset_permission_cache(self):
        self._cached_permissions = None


def make_password_mixin(history_entity_mixin=object, crypt_context=None):
    """Returns a mixin that adds password history and utility functions for working with passwords.

    :param history_entity_mixin: is an optional mixin to add to the password history entity.
                                 Supply a mixin if you want to include customized meta-information
                                 for each password in the history log.
    :param crypt_context: is an optional default :class:`CryptContext` object for hashing passwords.
                          If not supplied you must override the `get_crypt_context` method to
                          provide one.
    """
    class PasswordMixin(interfaces.HasPassword, KegBouncerMixin):
        default_crypt_context = crypt_context

        def get_crypt_context(self):
            """Returns a passlib :class:`CryptContext` object for hashing passwords.

            If you supplied a default :class:`CryptContext` when building the mixin, this will
            return it. Otherwise you need to override this method to return one.
            """
            if not self.default_crypt_context:  # pragma: no cover
                raise NotImplementedError(
                    'You must specify class-member `default_crypt_context` or override this method'
                    ' to provide a CryptContext for password hashing.')
            return self.default_crypt_context

        @declared_attr
        def password_history(cls):
            entity = cls.password_history_entity
            return saorm.relationship(
                entity,
                order_by=entity.created_at.desc(),
                cascade='all'
            )

        @declared_attr
        def password_history_entity(cls):
            return ents.make_password_history_entity(
                cls._primary_key_column(),
                cls.__tablename__,
                history_entity_mixin
            )

        def verify_password(self, password):
            crypt_context = self.get_crypt_context()
            return (crypt_context.verify(text_type(password), self.password_history[0].password)
                    if self.password_history else False)

        def is_password_used_previously(self, password):
            crypt_context = self.get_crypt_context()
            return any(crypt_context.verify(text_type(password), x.password)
                       for x in self.password_history)

        def set_password(self, password, **kwargs):
            """Sets a new password by adding it to the password history log.

            :param password: is the new password, in plaintext. It will be hashed by the
                             CryptContext from `get_crypt_context`.
            :param kwargs: any other fields to pass to the password history entity (if you set a
                           custom mixin for it).
            """
            crypt_context = self.get_crypt_context()
            password_entry = self.password_history_entity(
                password=crypt_context.encrypt(text_type(password)),
                **kwargs
            )

            # Assume the new password is more recent than the others and insert it at the head.
            self.password_history.insert(0, password_entry)

            # If we have timestamps for all history, we can sort them.
            if not any(x.created_at is None for x in self.password_history):
                self.password_history.sort(key=lambda x: x.created_at, reverse=True)

    return PasswordMixin


def make_login_history_mixin(history_entity_mixin=object):
    """Returns a mixin that adds login history relationships.

    :param history_entity_mixin: an optional mixin to add to the login history entity. Supply a
                                 mixin if you want to include customized meta-information for each
                                 entry in the history log.
    """
    class LoginHistoryMixin(KegBouncerMixin):
        @declared_attr
        def login_history(cls):
            """Relationship to login history entity."""
            entity = cls.login_history_entity
            return saorm.relationship(
                entity,
                order_by=entity.created_at.desc(),
                cascade='all, delete, delete-orphan'
            )

        @declared_attr
        def login_history_entity(cls):
            """A login history entity for this entity."""
            return ents.make_login_history_entity(
                cls._primary_key_column(),
                cls.__tablename__,
                history_entity_mixin
            )

    return LoginHistoryMixin
