from __future__ import absolute_import

import flask
from flask_login import current_user
import wrapt

from keg.web import BaseView


def current_user_has_permissions(*tokens):
    """Returns True IFF the current session belongs to an authenticated user who has all of the
    given permission tokens."""
    return (current_user
            and current_user.is_authenticated
            and current_user.has_permissions(*tokens))


def requires_permissions(*tokens):
    """Decorates a view function and ensures that it is only accessed when the current user has
    all of the given permissions.

    :param tokens: any number of required permission tokens."""
    @wrapt.decorator
    def wrapper(fn, instance, args, kwargs):
        if not (current_user and current_user.is_authenticated):
            return flask.abort(401)
        elif not current_user.has_permissions(*tokens):
            return flask.abort(403)
        return fn(*args, **kwargs)
    return wrapper


class ProtectedBaseView(BaseView):
    """A Keg BaseView which requires that requests be made by an authenticated user with a
    given permission token.

    This class protects *all* HTTP methods with the same permission requirements. Any requests
    that fail to meet the requirement will receive a 401.

    Subclasses should set the following member either on the class or the instance:

        * `requires_permission` (str): The permission token that a requesting user must possess.
    """
    require_authentication = True  # TODO: This is from keg.web.BaseView but it's not being used.

    requires_permission = None

    def check_auth(self, *args, **kwargs):
        requires_permissions(self.requires_permission)(lambda: None)()
