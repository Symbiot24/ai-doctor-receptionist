"""Interactive CLI to create the clinic admin account.

Run:

    python -m app.auth.create_admin

The script asks for the admin name, email and password, validates the
input, hashes the password with Argon2id and inserts the admin into Neon.
No default/hardcoded account exists - the installer chooses the initial
credentials. The plaintext password is never stored or printed.
"""

import getpass
import sys

from app.database.db import SessionLocal
from app.database.migrations import ensure_admin_users_table
from app.services.admin_service import AdminService


def _ask(question):

    try:

        return input(question)

    except EOFError:

        return ""


def _ask_password(question):

    if sys.stdin is not None and sys.stdin.isatty():

        try:

            return getpass.getpass(question)

        except Exception:

            pass

    return input(question)


def main():

    ensure_admin_users_table()

    print("== Clinic Admin Setup ==")
    print("This creates the admin account for the clinic dashboard.")
    print()

    name = _ask("Admin name: ").strip()

    email = _ask("Admin email: ").strip()

    password = _ask_password("Admin password: ")

    confirm = _ask_password("Confirm password: ")

    if password != confirm:

        print("Error: passwords do not match.")
        sys.exit(1)

    db = SessionLocal()

    try:

        admin = AdminService(db).create_admin(
            email,
            password,
            name=name,
        )

    except ValueError as error:

        print(f"Error: {error}")
        sys.exit(1)

    finally:

        db.close()

    print()
    print("Admin account created successfully.")
    print(f"  ID        : {admin.id}")
    print(f"  Name      : {admin.name}")
    print(f"  Email     : {admin.email}")
    print(f"  is_active : {admin.is_active}")
    print(f"  created_at: {admin.created_at}")
    print()
    print("Use these credentials to sign in to the clinic dashboard.")


if __name__ == "__main__":

    main()
