"""Base classes representing the interfaces that KegBouncer provides."""


class HasPermissions:
    """between_year_months_expression for classes that allow interaction with permissions."""

    def get_all_permissions(self):
        """Get all permissions that are joined to this User, whether directly, through permission
        bundles, or through user groups.
        """
        raise NotImplementedError()  # pragma: no cover

    def has_permissions(self, *tokens):
        """Returns True IFF every given permission token is present in the user's permission set.
        """
        raise NotImplementedError()  # pragma: no cover

    def has_any_permissions(self, *tokens):
        """Returns True IFF any of the given permission tokens are present in the user's permission
        set.

        Warning: Calling this method on a deleted entity may raise
        :class:`sqlalchemy.orm.exc.ObjectDeletedError`.
        """
        raise NotImplementedError()  # pragma: no cover


class HasPassword:
    """Base for classes that allow interaction with a password."""

    def verify_password(self, password):
        """Returns True IFF the password matches the current password."""
        raise NotImplementedError()  # pragma: no cover

    def set_password(self, password, **kwargs):
        """Sets a new password.

        :param password: is the new password, in plaintext.
        :param kwargs: any other fields to provide when setting a new password (implemention
                       specific).
        """
        raise NotImplementedError()  # pragma: no cover
