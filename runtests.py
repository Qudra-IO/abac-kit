"""Test runner for abac-kit."""

from __future__ import annotations

import os
import sys

import django
from django.conf import settings
from django.test.utils import get_runner


def main() -> int:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")
    django.setup()
    TestRunner = get_runner(settings)
    runner = TestRunner()
    failures = runner.run_tests(["tests"])
    return int(bool(failures))


if __name__ == "__main__":
    sys.exit(main())
