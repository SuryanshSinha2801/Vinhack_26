import argparse
from getpass import getpass

from sqlalchemy import select

from api.app.core.security import hash_password
from api.app.database import SessionLocal
from api.app.models import User


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or promote a local MindTrail administrator.")
    parser.add_argument("username")
    parser.add_argument("--display-name", default="MindTrail Administrator")
    args = parser.parse_args()
    username = args.username.strip().lower()
    if len(username) < 3 or not username.replace("_", "").replace("-", "").isalnum():
        raise SystemExit("Username must use 3+ letters, numbers, underscores, or hyphens.")
    password = getpass("Admin password: ")
    if len(password) < 12:
        raise SystemExit("Admin password must contain at least 12 characters.")
    if password != getpass("Confirm password: "):
        raise SystemExit("Passwords do not match.")

    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.username == username))
        if user:
            user.display_name = args.display_name
            user.password_hash = hash_password(password)
            user.role = "admin"
            user.is_active = True
            action = "Updated"
        else:
            user = User(
                username=username,
                display_name=args.display_name,
                password_hash=hash_password(password),
                role="admin",
            )
            db.add(user)
            action = "Created"
        db.commit()
    print(f"{action} administrator: {username}")


if __name__ == "__main__":
    main()
