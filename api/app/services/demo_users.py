from pathlib import Path

from openpyxl import load_workbook
from sqlalchemy import select

from api.app.core.security import hash_password
from api.app.database import SessionLocal
from api.app.models import User


WORKBOOK_PATH = Path(__file__).resolve().parents[3] / "data" / "demo" / "mindtrail_demo.xlsx"


def seed_demo_users() -> None:
    """Import the five explicitly fictional demo accounts from the workbook."""
    if not WORKBOOK_PATH.exists():
        return
    workbook = load_workbook(WORKBOOK_PATH, read_only=True, data_only=True)
    sheet = workbook["Demo Users"]
    with SessionLocal() as db:
        for username, password, display_name, _cohort, _use in sheet.iter_rows(
            min_row=6, max_row=10, min_col=1, max_col=5, values_only=True
        ):
            username = str(username).strip().lower()
            if not db.scalar(select(User).where(User.username == username)):
                db.add(
                    User(
                        username=username,
                        display_name=str(display_name),
                        password_hash=hash_password(str(password)),
                    )
                )
        db.commit()
    workbook.close()
