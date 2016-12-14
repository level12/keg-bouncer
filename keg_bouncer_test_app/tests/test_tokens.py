from datetime import timedelta

from itsdangerous import TimestampSigner
from pytest import raises

from keg_bouncer.tokens import TokenManager


class TestTokenManager(object):
    def test_isomorphism(self):
        expected = b'some data'

        for key in [b'secret key 12345', 'other key 123456',
                    '\u0391\u0392\u0393\u0394\u0395\u0396\u0397\u0398']:
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
        tm = TokenManager(b'secret key 12345', timestamp_signer=MockTimestampSigner)
        token = tm.generate_token(b'some data')

        timestamp = 10000  # pretend much time has passed
        is_expired, data = tm.verify_token(
            token,
            expiration_timedelta=timedelta(seconds=0)
        )

        assert is_expired
        assert data is None

    def test_invalid_token(self):
        is_expired, data = TokenManager(b'secret key 12345').verify_token(
            'blah',
            expiration_timedelta=timedelta(seconds=1)
        )
        assert not is_expired
        assert data is None

    def test_key_too_short(self):
        with raises(ValueError) as exc_info:
            TokenManager(b'secret key')
        assert str(exc_info.value) == 'Key must be at least 16 bytes long'
