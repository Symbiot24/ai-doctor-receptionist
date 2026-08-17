from sqlalchemy import func

from app.database.models import AdminUser


class AdminRepository:

    def __init__(self, db):

        self.db = db

    # ---------------- Queries ---------------- #

    def get_by_id(self, admin_id):

        return self.db.get(AdminUser, admin_id)

    def get_by_email(self, email):

        if not email:
            return None

        return (
            self.db.query(AdminUser)
            .filter(
                func.lower(AdminUser.email) == email.strip().lower()
            )
            .first()
        )

    def get_all(self):

        return (
            self.db.query(AdminUser)
            .order_by(AdminUser.id)
            .all()
        )

    # ---------------- Create / Update ---------------- #

    def create(
        self,
        admin_data: dict,
    ):

        admin = AdminUser(**admin_data)

        self.db.add(admin)

        self.db.commit()

        self.db.refresh(admin)

        return admin

    def update_email(
        self,
        admin,
        new_email,
    ):

        admin.email = new_email

        self.db.commit()

        self.db.refresh(admin)

        return admin

    def update_name(
        self,
        admin,
        new_name,
    ):

        admin.name = new_name

        self.db.commit()

        self.db.refresh(admin)

        return admin

    def update_password(
        self,
        admin,
        new_password_hash,
    ):

        admin.password_hash = new_password_hash

        self.db.commit()

        self.db.refresh(admin)

        return admin
