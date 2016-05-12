from __future__ import absolute_import

from flask_login import LoginManager
from keg.app import Keg

from .model import entities as ents
from .views import blueprint


class KegBouncerTestApp(Keg):
    import_name = 'keg_bouncer_test_app'
    db_enabled = True
    use_blueprints = [blueprint]
    keyring_enable = False

    def init(self, *args, **kwargs):
        super(KegBouncerTestApp, self).init(*args, **kwargs)

        self.login_manager = LoginManager()
        self.login_manager.user_loader(
            lambda user_id: ents.User.query.filter(ents.User.id == int(user_id)).one()
        )
        self.login_manager.login_view = 'keg_login.login-view'
        self.login_manager.init_app(self)

        return self


if __name__ == '__main__':
    KegBouncerTestApp.cli_run()
