import os
import tempfile
from pathlib import Path


_test_directory = tempfile.TemporaryDirectory(prefix="mindtrail-tests-")
_database_path = Path(_test_directory.name) / "mindtrail-test.db"

# This file loads before test modules import the application and its global settings.
# It guarantees that tests never connect to the database configured in the developer's .env.
os.environ["APP_DATABASE_URL"] = f"sqlite:///{_database_path.as_posix()}"
os.environ["APP_ENV"] = "test"
os.environ["CSRF_ENABLED"] = "false"
os.environ["RATE_LIMIT_ENABLED"] = "false"
os.environ["ALLOW_PUBLIC_REGISTRATION"] = "true"

from api.app.database import Base, engine  # noqa: E402
from api.app.services.demo_users import seed_demo_history, seed_demo_users  # noqa: E402
import api.app.models  # noqa: E402,F401


Base.metadata.create_all(bind=engine)
seed_demo_users()
seed_demo_history()


def pytest_sessionfinish(session, exitstatus):
    engine.dispose()
    _test_directory.cleanup()
