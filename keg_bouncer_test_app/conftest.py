from __future__ import absolute_import

from keg_bouncer_test_app.app import KegBouncerTestApp


def pytest_configure(config):
    KegBouncerTestApp.testing_prep()
