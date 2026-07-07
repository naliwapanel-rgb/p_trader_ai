from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> User | None:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(User.email == email).first()

    def create(
        self,
        full_name: str,
        email: str,
        hashed_password: str,
    ) -> User:
        user = User(
            full_name=full_name,
            email=email,
            hashed_password=hashed_password,
        )

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        return user

    def update(
        self,
        user: User,
        full_name: str | None = None,
        email: str | None = None,
    ) -> User:
        if full_name is not None:
            user.full_name = full_name

        if email is not None:
            user.email = email

        self.db.commit()
        self.db.refresh(user)

        return user
    
    def update_password(
        self,
        user: User,
        hashed_password: str,
    ) -> User:
        user.hashed_password = hashed_password

        self.db.commit()
        self.db.refresh(user)

        return user
    
    def deactivate(
        self,
        user: User,
    ) -> User:
        user.is_active = False

        self.db.commit()
        self.db.refresh(user)

        return user