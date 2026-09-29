import os

from .base import *  # noqa: F403

DEBUG = False
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

PRIVATE_LOGIN_RATE_LIMIT_ATTEMPTS = 1000
PRIVATE_LOGIN_RATE_LIMIT_STATE_PATH = f"/tmp/lowcost-europa-private-login-test-{os.getpid()}.json"
PRIVATE_LOGIN_RATE_LIMIT_LOCK_PATH = f"/tmp/lowcost-europa-private-login-test-{os.getpid()}.lock"

CATALOG_MAINTENANCE_LOCK_PATH = f"/tmp/lowcost-europa-maintenance-test-{os.getpid()}.lock"
