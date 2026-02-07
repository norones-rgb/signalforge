from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import encrypt_token
from app.db.session import get_db
from app.models import AccountSettings, XAccount
from app.routers.deps import get_current_user
from app.schemas.accounts import (
    AccountSettingsCreate,
    AccountSettingsResponse,
    AccountSettingsUpdate,
    XAccountCreate,
    XAccountResponse,
    XAccountUpdate,
)


router = APIRouter(prefix="/accounts", tags=["accounts"])


def _upsert_settings(
    db: Session, account: XAccount, payload: AccountSettingsCreate | AccountSettingsUpdate | None
) -> AccountSettings:
    settings = account.settings
    if not settings:
        settings = AccountSettings(x_account_id=account.id)
        db.add(settings)

    if payload is not None:
        for field, value in payload.model_dump().items():
            setattr(settings, field, value)

    return settings


def _to_response(account: XAccount) -> XAccountResponse:
    response = XAccountResponse.model_validate(account)
    return response.model_copy(update={"is_connected": bool(account.oauth_access_token_enc)})


@router.get("", response_model=list[XAccountResponse])
def list_accounts(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> list[XAccountResponse]:
    accounts = db.scalars(select(XAccount).where(XAccount.workspace_id == user.workspace_id)).all()
    return [_to_response(account) for account in accounts]


@router.post("", response_model=XAccountResponse)
def create_account(
    payload: XAccountCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> XAccountResponse:
    if payload.workspace_id != str(user.workspace_id):
        raise HTTPException(status_code=403, detail="Invalid workspace")

    account = XAccount(
        workspace_id=user.workspace_id,
        handle=payload.handle,
        name=payload.name,
        is_enabled=payload.is_enabled,
        oauth_access_token_enc=encrypt_token(payload.oauth_access_token or ""),
        oauth_refresh_token_enc=encrypt_token(payload.oauth_refresh_token or ""),
        oauth_expires_at=payload.oauth_expires_at,
    )
    db.add(account)
    db.flush()

    _upsert_settings(db, account, payload.settings)

    db.commit()
    db.refresh(account)
    return _to_response(account)


@router.patch("/{account_id}", response_model=XAccountResponse)
def update_account(
    account_id: str,
    payload: XAccountUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> XAccountResponse:
    account = db.get(XAccount, account_id)
    if not account or account.workspace_id != user.workspace_id:
        raise HTTPException(status_code=404, detail="Account not found")

    data = payload.model_dump(exclude_unset=True)
    if "name" in data:
        account.name = data["name"]
    if "handle" in data and data["handle"]:
        account.handle = data["handle"]
    if "is_enabled" in data and data["is_enabled"] is not None:
        account.is_enabled = data["is_enabled"]
    if "oauth_access_token" in data:
        account.oauth_access_token_enc = encrypt_token(data["oauth_access_token"] or "")
    if "oauth_refresh_token" in data:
        account.oauth_refresh_token_enc = encrypt_token(data["oauth_refresh_token"] or "")
    if "oauth_expires_at" in data:
        account.oauth_expires_at = data["oauth_expires_at"]

    _upsert_settings(db, account, payload.settings)

    db.commit()
    db.refresh(account)
    return _to_response(account)
