from __future__ import absolute_import

import flask
from flask_webtest import TestApp as WebTestApp


class TestViewBase(object):
    def setup_method(self, _):
        self.ta = WebTestApp(flask.current_app)

    def get(self, url):
        return self.ta.get(url, expect_errors=True)

    def post(self, url):
        return self.ta.post(url, expect_errors=True)


class TestPublicView(TestViewBase):
    def test_not_logged_in(self):
        response = self.get('/public-view')
        assert response.status_code == 200
        assert 'GET' in str(response.body)

        response = self.post('/public-view')
        assert response.status_code == 200
        assert 'POST' in str(response.body)

    def test_logged_in(self):
        assert self.get('/login-with/useless-permission')

        response = self.get('/public-view')
        assert response.status_code == 200
        assert 'GET' in str(response.body)

        response = self.post('/public-view')
        assert response.status_code == 200
        assert 'POST' in str(response.body)


class TestSecretView(TestViewBase):
    def test_not_logged_in(self):
        assert self.get('/secret-view').status_code == 401
        assert self.post('/secret-view').status_code == 401
        assert self.get('/secret-decorated-view').status_code == 401

    def test_logged_in_unauthorized(self):
        assert self.get('/login-with/useless-permission').status_code == 200
        assert self.get('/secret-view').status_code == 403
        assert self.get('/secret-decorated-view').status_code == 403
        assert self.post('/secret-view').status_code == 403

    def test_logged_in_authorized_for_secret(self):
        assert self.get('/login-with/view-secret').status_code == 200

        response = self.get('/secret-view')
        assert response.status_code == 200
        assert 'GET' in str(response.body)

        response = self.post('/secret-view')
        assert response.status_code == 200
        assert 'POST' in str(response.body)

    def test_logged_in_authorized_for_decorated_secret(self):
        assert self.get('/login-with/view-decorated-secret').status_code == 200

        response = self.get('/secret-decorated-view')
        assert response.status_code == 200
        assert 'GET' in str(response.body)
