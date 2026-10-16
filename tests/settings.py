"""Minimal Django settings for the abac-kit test suite."""

from __future__ import annotations

SECRET_KEY = "abac-kit-tests"
DEBUG = True
USE_TZ = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "rest_framework",
    "abac_kit",
    "tests",
]

AUTH_USER_MODEL = "tests.TestUser"

MIDDLEWARE = []
ROOT_URLCONF = "tests.urls"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
