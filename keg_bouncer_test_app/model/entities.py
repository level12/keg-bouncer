from __future__ import absolute_import

import sqlalchemy as sa

import flask_login

from keg.db import db
from keg_bouncer.model import mixins


class MockCryptContext(object):
    def encrypt(self, password):
        return password + ":hashed"

    def verify(self, password, hash):
        return self.encrypt(password) == hash


class UserMixin(flask_login.UserMixin):
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.Unicode(), nullable=False)


class User(UserMixin, mixins.PermissionMixin, db.Model):
    pass


class UserWithPasswordHistory(
    UserMixin,
    mixins.make_password_mixin(crypt_context=MockCryptContext()),
    db.Model,
):
    pass


class NotesMixin(object):
    note = sa.Column(sa.Text)


noted_password_mixin = mixins.make_password_mixin(NotesMixin, crypt_context=MockCryptContext())


class UserWithPasswordHistoryWithNotes(UserMixin, noted_password_mixin, db.Model):
    pass


class UserWithLoginHistory(UserMixin, mixins.make_login_history_mixin(), db.Model):
    pass


noted_login_mixin = mixins.make_login_history_mixin(NotesMixin)


class UserWithLoginHistoryWithNotes(UserMixin, noted_login_mixin, db.Model):
    pass
