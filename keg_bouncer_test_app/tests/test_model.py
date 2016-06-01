from __future__ import absolute_import

from datetime import datetime
from random import shuffle

import pytest
import sqlalchemy as sa

from keg.db import db

from keg_bouncer.model.entities import (
    Permission,
    PermissionBundle,
    UserGroup,
)
from keg_bouncer.model import mixins

from ..model import entities as ents
from ..utils import in_session


class TestPermissions(object):
    def setup_method(self, _):
        ents.User.query.delete()
        UserGroup.query.delete()
        PermissionBundle.query.delete()
        Permission.query.delete()

        assert Permission.query.count() == 0
        assert PermissionBundle.query.count() == 0
        assert UserGroup.query.count() == 0
        assert ents.User.query.count() == 0

    def test_permission_entity(self):
        permissions = in_session([Permission(token=token, description=u'Permission ' + token)
                                 for token in [u'a', u'b', u'c']])
        assert Permission.query.count() == len(permissions)
        assert {x.token for x in Permission.query} == {x.token for x in permissions}

    def test_permission_bundle_entity(self):
        bundles = in_session([PermissionBundle(label=x) for x in [u'B1', u'B2', u'B3']])
        assert PermissionBundle.query.count() == len(bundles)
        assert {x.label for x in PermissionBundle.query} == {x.label for x in bundles}

        [p1, p2, p3] = in_session([Permission(token=x, description=x)
                                   for x in [u'p1', u'p2', u'p3']])

        [b1, b2, b3] = bundles
        b1.permissions = [p1]
        b2.permissions = [p2]
        b3.permissions = [p1, p3]

        assert set(b1.permissions) == {p1}
        assert set(b2.permissions) == {p2}
        assert set(b3.permissions) == {p1, p3}

    def make_permission_grid(self):
        permissions = in_session([Permission(token=x, description=x)
                                  for x in [u'p1', u'p2', u'p3']])
        bundles = in_session([PermissionBundle(label=x) for x in [u'B1', u'B2']])
        groups = in_session([UserGroup(label=x) for x in [u'G1', u'G2', u'G3']])

        [b1, b2] = bundles
        [p1, p2, p3] = permissions
        [g1, g2, g3] = groups

        b1.permissions = [p2]
        b2.permissions = [p2, p3]

        g1.permissions = [p1, p3]
        g1.bundles = []

        g2.permissions = []
        g2.bundles = [b1]

        g3.permissions = [p1, p2]
        g3.bundles = [b1, b2]

        return groups, bundles, permissions

    def test_user_group_entities(self):
        groups, bundles, permissions = self.make_permission_grid()
        assert UserGroup.query.count() == len(groups)
        assert {x.label for x in UserGroup.query} == {x.label for x in groups}

        [b1, b2] = bundles
        [p1, p2, p3] = permissions
        [g1, g2, g3] = groups

        b1.permissions = [p2]
        b2.permissions = [p2, p3]

        g1.permissions = [p1, p3]
        g1.bundles = []

        g2.permissions = []
        g2.bundles = [b1]

        g3.permissions = [p1, p2]
        g3.bundles = [b1, b2]

        [p1, p2, p3] = permissions
        [g1, g2, g3] = groups
        assert g1.get_all_permissions() == {p1, p3}
        assert g2.get_all_permissions() == {p2}
        assert g3.get_all_permissions() == {p1, p2, p3}

    def test_permission_unique_token(self):
        with pytest.raises(sa.exc.IntegrityError):
            try:
                in_session([Permission(token='a'), Permission(token='a')])
            except:
                db.session.rollback()
                raise

    def test_user_entity(self):
        users = in_session([ents.User(name=x) for x in [u'you', u'him']])
        assert ents.User.query.count() == len(users)
        assert {x.name for x in ents.User.query} == {x.name for x in users}

        groups, bundles, permissions = self.make_permission_grid()
        [p1, p2, p3] = permissions
        [g1, g2, g3] = groups
        [you, him] = users

        you.user_groups = [g1, g2]
        him.user_groups = [g3]

        assert you.get_all_permissions() == {p1, p2, p3}
        assert him.get_all_permissions() == {p1, p2, p3}

        assert you.has_permissions(p1.token, p2.token)
        assert not you.has_permissions(p1.token, 'not-a-permission')
        assert you.has_any_permissions(p1.token, 'not-a-permission')
        assert not you.has_any_permissions('not-a-permission')

        # Test caching
        assert you.get_all_permissions() == {p1, p2, p3}
        you.user_groups = []
        assert you.get_all_permissions() == {p1, p2, p3}
        you.reset_permission_cache()
        assert you.get_all_permissions() == frozenset()


class TestPasswordHistory(object):
    def test_password_history(self):
        user = in_session(ents.UserWithPasswordHistory(name=u'VIP'))
        user2 = in_session(ents.UserWithPasswordHistory(name=u'Not VIP'))

        assert user.password_history == []
        assert not user.verify_password('test')
        assert not user.is_password_used_previously('test')

        user.set_password('mariobros')
        assert [x.password for x in user.password_history] == ['mariobros:hashed']
        assert not user.verify_password('test')
        assert not user.is_password_used_previously('test')
        assert not user.verify_password('mariobros:hashed')
        assert user.verify_password('mariobros')
        assert user.is_password_used_previously('mariobros')

        user.set_password('cheese steak')
        assert [x.password for x in user.password_history] == [
            'cheese steak:hashed',
            'mariobros:hashed',
        ]
        assert not user.verify_password('mariobros')
        assert user.verify_password('cheese steak')
        assert user.is_password_used_previously('mariobros')
        assert user.is_password_used_previously('cheese steak')

        user.set_password('Filet 34__')
        assert [x.password for x in user.password_history] == [
            'Filet 34__:hashed',
            'cheese steak:hashed',
            'mariobros:hashed',
        ]
        assert not user.verify_password('mariobros')
        assert not user.verify_password('cheese steak')
        assert user.verify_password('Filet 34__')
        assert user.is_password_used_previously('mariobros')
        assert user.is_password_used_previously('cheese steak')
        assert user.is_password_used_previously('Filet 34__')
        assert not user.is_password_used_previously('test')

        db.session.flush()
        db.session.expire_all()

        # Get a shuffled history
        history = user.password_history[:]
        while history == user.password_history:
            shuffle(history)

        # Sort it by date and compare
        assert [x.password for x in sorted(history, key=lambda x: x.created_at)] == [
            'mariobros:hashed',
            'cheese steak:hashed',
            'Filet 34__:hashed',
        ]

        # One person's history does not affect another's
        assert user2.password_history == []

    def test_password_history_with_mixin(self):
        user = in_session(ents.UserWithPasswordHistoryWithNotes(name=u'VIP'))
        user2 = in_session(ents.UserWithPasswordHistoryWithNotes(name=u'Not VIP'))

        get_pw_table = lambda obj: [(x.password, x.note) for x in obj.password_history]

        assert user.password_history == []
        user.set_password('mariobros')
        assert get_pw_table(user) == [('mariobros:hashed', None)]

        user.set_password('cheese steak', note='Set by admin')
        assert get_pw_table(user) == [
            ('cheese steak:hashed', 'Set by admin'),
            ('mariobros:hashed',    None),
        ]

        # One person's history does not affect another's
        assert user2.password_history == []

    def test_password_history_delete_cascade(self):
        ents.UserWithPasswordHistory.query.delete()
        ents.UserWithPasswordHistory.password_history_entity.query.delete()

        user = in_session(ents.UserWithPasswordHistory(name=u'VIP'))
        user2 = in_session(ents.UserWithPasswordHistory(name=u'Not VIP'))

        assert ents.UserWithPasswordHistory.password_history_entity.query.count() == 0

        user.set_password('pass1')
        user2.set_password('pass2')

        assert ents.UserWithPasswordHistory.password_history_entity.query.count() == 2

        db.session.delete(user)

        assert ents.UserWithPasswordHistory.password_history_entity.query.count() == 1

    def test_password_history_unicode(self):
        user = in_session(ents.UserWithPasswordHistory(name=u'VIP'))
        pw = u'\u2615coffee-\u26A1-bolt'
        assert not user.verify_password(pw)
        user.set_password(pw)
        assert user.verify_password(pw)

    def test_password_history_ordering(self):
        user = in_session(ents.UserWithPasswordHistory(name=u'VIP'))

        # Add passwords out of order.
        user.set_password('test1', created_at=datetime(2016, 2, 1))
        user.set_password('test2', created_at=datetime(2015, 12, 31))
        user.set_password('test3', created_at=datetime(2016, 1, 1))

        assert user.verify_password('test1')  # this is the most recent
        assert [x.password for x in user.password_history] == [
            'test1:hashed',
            'test3:hashed',
            'test2:hashed',
        ]


class TestLoginHistory(object):
    def test_login_history(self):
        user = in_session(ents.UserWithLoginHistory(name=u'VIP'))
        user2 = in_session(ents.UserWithLoginHistory(name=u'Not VIP'))

        assert user.login_history == []

        user.login_history.insert(0, user.login_history_entity(is_login_successful=True))

        assert [x.is_login_successful for x in user.login_history] == [True]

        user.login_history.insert(0, user.login_history_entity(is_login_successful=True))
        user.login_history.insert(0, user.login_history_entity(is_login_successful=False))
        user.login_history.insert(0, user.login_history_entity(is_login_successful=False))

        assert [x.is_login_successful for x in user.login_history] == [False, False, True, True]

        db.session.flush()
        db.session.expire_all()

        # Get a shuffled history
        history = user.login_history[:]
        while history == user.login_history:
            shuffle(history)

        assert [x.is_login_successful for x in sorted(history, key=lambda x: x.created_at)] == [
            True, True, False, False,
        ]

        # One person's history does not affect another person's
        assert user2.login_history == []

    def test_login_history_with_mixin(self):
        user = in_session(ents.UserWithLoginHistoryWithNotes(name=u'VIP'))
        user2 = in_session(ents.UserWithLoginHistoryWithNotes(name=u'Not VIP'))

        get_login_table = lambda obj: [(x.is_login_successful, x.note) for x in obj.login_history]

        assert user.login_history == []

        user.login_history.insert(0, user.login_history_entity(is_login_successful=True))

        assert get_login_table(user) == [(True, None)]

        user.login_history.insert(
            0,
            user.login_history_entity(is_login_successful=False, note='Test')
        )

        assert get_login_table(user) == [
            (False, 'Test'),
            (True,  None),
        ]

        # One person's history does not affect another person's
        assert user2.login_history == []

    def test_login_history_delete_cascade(self):
        ents.UserWithLoginHistory.query.delete()
        assert ents.UserWithLoginHistory.login_history_entity.query.delete()

        user = in_session(ents.UserWithLoginHistory(name=u'VIP'))
        user2 = in_session(ents.UserWithLoginHistory(name=u'Not VIP'))

        assert ents.UserWithLoginHistory.login_history_entity.query.count() == 0

        mk_entry = lambda: user.login_history_entity(is_login_successful=False)
        user.login_history.insert(0, mk_entry())
        user2.login_history.insert(0, mk_entry())
        assert ents.UserWithLoginHistory.login_history_entity.query.count() == 2

        db.session.delete(user)
        assert ents.UserWithLoginHistory.login_history_entity.query.count() == 1


class TestKegBouncerMixin(object):
    def test_mixins_require_more_than_one_pk(self):
        def make_entity_with_no_pk():
            class NoPk(mixins.KegBouncerMixin):
                pass
            return NoPk

        try:
            make_entity_with_no_pk()._primary_key_column()
            assert False, 'Did not throw'
        except AttributeError:
            pass

    def test_mixins_require_less_than_two_pks(self):
        def make_entity_with_two_pks():
            class TwoPks(mixins.KegBouncerMixin):
                pk1 = sa.Column(sa.Integer, primary_key=True)
                pk2 = sa.Column(sa.Integer, primary_key=True)
            return TwoPks

        try:
            make_entity_with_two_pks()._primary_key_column()
            assert False, 'Did not throw'
        except AttributeError:
            pass
