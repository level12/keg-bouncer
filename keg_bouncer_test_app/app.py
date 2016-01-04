from __future__ import absolute_import

import flask
from flask_user import UserManager, SQLAlchemyAdapter
from keg.app import Keg
from keg.db import db

from .model.entities import User
from .views import blueprint


class KegBouncerTestApp(Keg):
    import_name = 'keg_bouncer_test_app'
    db_enabled = True
    use_blueprints = [blueprint]
    keyring_enable = False

    def init(self, *args, **kwargs):
        super(KegBouncerTestApp, self).init(*args, **kwargs)
        self.user_manager = UserManager(
            SQLAlchemyAdapter(db, User),
            self,
            password_validator=lambda _: True,
            user_profile_view_function=lambda *args, **kwargs: flask.abort(401),
        )
        return self


if __name__ == '__main__':
    KegBouncerTestApp.cli_run()
