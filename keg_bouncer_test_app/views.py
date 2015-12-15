from __future__ import absolute_import

import flask
from flask_login import login_user
from keg.web import BaseView, rule
from keg_bouncer.model.entities import Permission, UserGroup
from keg_bouncer.auth import ProtectedBaseView, current_user_has_permissions, requires_permissions

from .model.entities import User
from .utils import in_session

blueprint = flask.Blueprint('my', __name__)


class LoginView(BaseView):
    blueprint = blueprint
    rule('/login-with/<permission_token>')

    def get(self, permission_token):
        permission = (Permission.query.filter(Permission.token == permission_token).one_or_none()
                      or Permission(token=permission_token,
                                    description='Permission '+permission_token))
        group = UserGroup(label='Group with '+permission_token, permissions=[permission])
        user = in_session(User(name='User with '+permission_token, user_groups=[group]))
        login_user(user)
        is_logged_in_correctly = current_user_has_permissions(permission_token)
        assert is_logged_in_correctly
        return 'Logged in' if is_logged_in_correctly else 'FAILED'


class PublicView(BaseView):
    blueprint = blueprint
    rule('/public-view', post=True)

    def get(self):
        return 'Public access (GET)'

    def post(self):
        return 'Public access (POST)'


class SecretView(ProtectedBaseView):
    blueprint = blueprint
    rule('/secret-view', post=True)

    requires_permission = 'view-secret'

    def get(self):
        return 'Access granted (GET)'

    def post(self):
        return 'Access granted (POST)'


class SecretDecoratedView(BaseView):
    blueprint = blueprint
    rule = ('/secret-decorated-view')

    @requires_permissions('view-decorated-secret')
    def get(self):
        return 'Access granted (GET)'
