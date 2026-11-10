"""Settings used exclusively for running the automated test suite.

Run the tests with::

    python manage.py test --settings=core.test_settings
"""

import os

# Tests must not depend on a developer's local ``.env`` file. This throwaway
# key is only ever set by this module; ``core.settings`` still refuses to start
# without a real ``SECRET_KEY`` in every other context.
os.environ.setdefault('SECRET_KEY', 'test-only-secret-key-not-for-production')

from .settings import *  # noqa: E402,F401,F403  pylint: disable=wrong-import-position,wildcard-import,unused-wildcard-import

# A fast, insecure hasher removes the password hashing overhead (the default
# hashers are deliberately slow). Never use this outside of tests.
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]
