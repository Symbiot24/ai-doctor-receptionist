import re

from app.auth.security import hash_password
from app.auth.security import verify_password
from app.repositories.admin_repository import AdminRepository

MIN_PASSWORD_LENGTH = 8

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class AdminService:

    def __init__(self, db):

        self.db = db

        self.repository = AdminRepository(db)

    # ---------------- Validation ---------------- #

    @staticmethod
    def validate_email(email):

        if not email or not email.strip():

            raise ValueError("Email is required.")

        email = email.strip().lower()

        if not _EMAIL_RE.match(email):

            raise ValueError(f"Invalid email address {email!r}.")

        return email

    @staticmethod
    def validate_password(password):

        if not password:

            raise ValueError("Password is required.")

        if len(password) < MIN_PASSWORD_LENGTH:

            raise ValueError(
                f"Password must be at least {MIN_PASSWORD_LENGTH} "
                "characters long."
            )

        return password

    # ---------------- Create / Update ---------------- #

    def create_admin(
        self,
        email,
        password,
        name=None,
    ):

        email = self.validate_email(email)

        self.validate_password(password)

        if self.repository.get_by_email(email) is not None:

            raise ValueError(
                f"An admin with email {email!r} already exists."
            )

        return self.repository.create(
            {
                "email": email,
                "password_hash": hash_password(password),
                "name": name.strip() if name and name.strip() else None,
            }
        )

    def get_by_email(self, email):

        if not email:
            return None

        return self.repository.get_by_email(email)

    def get_by_id(self, admin_id):

        return self.repository.get_by_id(admin_id)

    def update_email(self, admin_id, new_email):

        admin = self.repository.get_by_id(admin_id)

        if admin is None:

            raise ValueError("Admin not found.")

        new_email = self.validate_email(new_email)

        existing = self.repository.get_by_email(new_email)

        if existing is not None and existing.id != admin.id:

            raise ValueError(
                f"An admin with email {new_email!r} already exists."
            )

        return self.repository.update_email(admin, new_email)

    def update_password(self, admin_id, new_password):

        admin = self.repository.get_by_id(admin_id)

        if admin is None:

            raise ValueError("Admin not found.")

        self.validate_password(new_password)

        return self.repository.update_password(
            admin,
            hash_password(new_password),
        )

    def update_profile(
        self,
        admin_id,
        name=None,
        email=None,
    ):

        admin = self.repository.get_by_id(admin_id)

        if admin is None:

            raise ValueError("Admin not found.")

        if name is not None:

            name = name.strip()

            if not name:

                raise ValueError("Name cannot be empty.")

            admin = self.repository.update_name(admin, name)

        if email is not None:

            admin = self.update_email(admin_id, email)

        return admin

    def change_password(
        self,
        admin_id,
        current_password,
        new_password,
        confirm_password,
    ):

        admin = self.repository.get_by_id(admin_id)

        if admin is None:

            raise ValueError("Admin not found.")

        if not current_password or not verify_password(
            current_password,
            admin.password_hash,
        ):

            raise ValueError("Current password is incorrect.")

        if new_password != confirm_password:

            raise ValueError("Passwords do not match.")

        self.validate_password(new_password)

        if verify_password(new_password, admin.password_hash):

            raise ValueError(
                "New password must be different from the current password."
            )

        return self.repository.update_password(
            admin,
            hash_password(new_password),
        )

    # ---------------- Verification ---------------- #

    def check_password(self, admin, password):
        """Return True when the password matches the stored hash."""

        return verify_password(password, admin.password_hash)
