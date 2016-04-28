from datetime import timedelta

from itsdangerous import TimestampSigner

from keg_bouncer.tokens import TokenManager


class TestTokenManager(object):
    def test_isomorphism(self):
        expected = b'some data'

        for key in [b'secret key', 'other key']:
            tm = TokenManager(key)
            token = tm.generate_token(expected)
            is_expired, data = tm.verify_token(
                token,
                expiration_timedelta=timedelta(seconds=10)
            )
            assert not is_expired
            assert data == expected

    def test_expired_token(self):
        timestamp = 0

        class MockTimestampSigner(TimestampSigner):
            def get_timestamp(self):
                return timestamp

        timestamp = 0  # pretend we're at the beginning of time
        tm = TokenManager(b'secret key', timestamp_signer=MockTimestampSigner)
        token = tm.generate_token(b'some data')

        timestamp = 10000  # pretend much time has passed
        is_expired, data = tm.verify_token(
            token,
            expiration_timedelta=timedelta(seconds=0)
        )

        assert is_expired
        assert data is None

    def test_invalid_token(self):
        is_expired, data = TokenManager(b'secret key').verify_token(
            'blah',
            expiration_timedelta=timedelta(seconds=1)
        )
        assert not is_expired
        assert data is None
