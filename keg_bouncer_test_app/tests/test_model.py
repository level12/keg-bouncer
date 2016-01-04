from __future__ import absolute_import

import pytest
import sqlalchemy as sa

from keg.db import db

from keg_bouncer.model.entities import Permission, PermissionBundle, UserGroup

from ..model.entities import User
from ..utils import in_session


class TestPermissions(object):
    def setup_method(self, _):
        User.query.delete()
        UserGroup.query.delete()
        PermissionBundle.query.delete()
        Permission.query.delete()

        assert Permission.query.count() == 0
        assert PermissionBundle.query.count() == 0
        assert UserGroup.query.count() == 0
        assert User.query.count() == 0

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
        users = in_session([User(name=x) for x in [u'you', u'him']])
        assert User.query.count() == len(users)
        assert {x.name for x in User.query} == {x.name for x in users}

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
