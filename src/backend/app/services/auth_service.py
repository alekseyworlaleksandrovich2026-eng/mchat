"""Auth service - business logic for authentication."""

import secrets
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import TokenResponse, UserResponse


class AuthService:
    """Handles authentication business logic."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def login(self, username: str, password: str) -> TokenResponse:
        """Authenticate user and return JWT token."""
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )

        if not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )

        access_token = create_access_token(
            data={"sub": user.id, "username": user.username, "role": user.role}
        )

        return TokenResponse(
            access_token=access_token,
            user=self.user_response(user),
        )

    async def register(
        self,
        username: str,
        password: str,
        display_name: str | None = None,
        avatar_url: str | None = None,
    ) -> TokenResponse:
        """Register a new agent user."""
        # Check if username exists
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        if result.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already exists",
            )

        user = User(
            username=username,
            password_hash=get_password_hash(password),
            role="agent",
            display_name=display_name or username,
            avatar_url=avatar_url,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)

        access_token = create_access_token(
            data={"sub": user.id, "username": user.username, "role": user.role}
        )

        return TokenResponse(
            access_token=access_token,
            user=self.user_response(user),
        )

    async def signup(
        self,
        username: str,
        password: str,
        email: str | None = None,
        display_name: str | None = None,
    ) -> TokenResponse:
        """Register a new public user with role='user'."""
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        if result.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already exists",
            )
        if email:
            result = await self.db.execute(
                select(User).where(User.email == email)
            )
            if result.scalar_one_or_none() is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already registered",
                )

        user = User(
            username=username,
            email=email,
            password_hash=get_password_hash(password),
            role="user",
            display_name=display_name or username,
            account_status="active",
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)

        access_token = create_access_token(
            data={"sub": user.id, "username": user.username, "role": user.role}
        )
        return TokenResponse(
            access_token=access_token,
            user=self.user_response(user),
        )

    async def create_default_admin(
        self, username: str, password: str
    ) -> User | None:
        """Create default admin user if not exists."""
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        if result.scalar_one_or_none() is not None:
            return None

        user = User(
            username=username,
            password_hash=get_password_hash(password),
            role="admin",
            display_name="Admin",
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    @staticmethod
    def user_response(user: User) -> UserResponse:
        data = UserResponse.model_validate(user)
        data.can_set_password = not bool(getattr(user, "external_provider", None))
        return data

    async def change_password(
        self,
        user: User,
        current_password: str,
        new_password: str,
    ) -> None:
        """Change password for the authenticated user."""
        if getattr(user, "external_provider", None):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="9235 账号请使用 9235.net 修改密码",
            )
        if not verify_password(current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )
        user.password_hash = get_password_hash(new_password)
        await self.db.flush()

    async def set_password(
        self,
        user: User,
        new_password: str,
        current_password: str | None = None,
    ) -> None:
        """Portal: set password; 9235-linked accounts cannot set here."""
        if getattr(user, "external_provider", None):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="9235 账号请使用 9235.net 修改密码",
            )
        if current_password:
            if not verify_password(current_password, user.password_hash):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is incorrect",
                )
        elif user.role in ("admin", "agent"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is required",
            )
        user.password_hash = get_password_hash(new_password)
        await self.db.flush()

    async def list_users(self) -> list[User]:
        """List all users (admin)."""
        result = await self.db.execute(
            select(User).order_by(User.created_at.desc())
        )
        return list(result.scalars().all())

    async def create_user(
        self,
        username: str,
        password: str,
        role: str = "agent",
        display_name: str | None = None,
    ) -> User:
        """Create a user (admin)."""
        if role not in ("admin", "agent", "user"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role",
            )
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        if result.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already exists",
            )
        user = User(
            username=username,
            password_hash=get_password_hash(password),
            role=role,
            display_name=display_name or username,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def update_user(
        self,
        user_id: str,
        *,
        role: str | None = None,
        display_name: str | None = None,
        password: str | None = None,
    ) -> User:
        """Update user fields (admin)."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        if role is not None:
            if role not in ("admin", "agent", "user"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid role",
                )
            user.role = role
        if display_name is not None:
            user.display_name = display_name
        if password is not None:
            user.password_hash = get_password_hash(password)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def delete_user(self, user_id: str, *, actor_id: str) -> None:
        """Delete a user (admin). Cannot delete self."""
        if user_id == actor_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account",
            )
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        await self.db.delete(user)
        await self.db.flush()

    async def signup_by_phone(self, phone: str) -> TokenResponse:
        """Register portal user with verified phone; email/nickname optional later."""
        result = await self.db.execute(select(User).where(User.phone == phone))
        if result.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Phone already registered",
            )
        result = await self.db.execute(select(User).where(User.username == phone))
        if result.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already exists",
            )

        now = datetime.now(timezone.utc)
        user = User(
            username=phone,
            phone=phone,
            phone_verified_at=now,
            password_hash=get_password_hash(secrets.token_urlsafe(32)),
            role="user",
            display_name=phone,
            account_status="active",
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        access_token = create_access_token(
            data={"sub": user.id, "username": user.username, "role": user.role}
        )
        return TokenResponse(
            access_token=access_token,
            user=self.user_response(user),
        )

    async def login_or_link_9235(
        self,
        *,
        account: str,
        external_id: str | None = None,
        email: str | None = None,
        display_name: str | None = None,
    ) -> TokenResponse:
        """JIT login: link 9235 account by phone/external_id or create mchat user."""
        from cloud.services.patent9235_auth import PROVIDER

        phone = account if account.isdigit() or account.startswith("1") else None
        user: User | None = None

        if external_id:
            result = await self.db.execute(
                select(User).where(
                    User.external_provider == PROVIDER,
                    User.external_id == str(external_id),
                )
            )
            user = result.scalar_one_or_none()

        if user is None and phone:
            result = await self.db.execute(select(User).where(User.phone == phone))
            user = result.scalar_one_or_none()
        if user is None:
            result = await self.db.execute(
                select(User).where(
                    or_(User.username == account, User.email == account)
                )
            )
            user = result.scalar_one_or_none()

        now = datetime.now(timezone.utc)
        if user is None:
            uname = phone or account
            user = User(
                username=uname,
                phone=phone,
                phone_verified_at=now if phone else None,
                email=email,
                password_hash=get_password_hash(secrets.token_urlsafe(32)),
                role="user",
                display_name=display_name or uname,
                account_status="active",
                external_provider=PROVIDER,
                external_id=str(external_id) if external_id else None,
            )
            self.db.add(user)
        else:
            if phone and not user.phone:
                user.phone = phone
                user.phone_verified_at = now
            if email and not user.email:
                user.email = email
            if display_name and not user.display_name:
                user.display_name = display_name
            if external_id:
                user.external_provider = PROVIDER
                user.external_id = str(external_id)

        await self.db.flush()
        await self.db.refresh(user)
        access_token = create_access_token(
            data={"sub": user.id, "username": user.username, "role": user.role}
        )
        return TokenResponse(
            access_token=access_token,
            user=self.user_response(user),
        )
