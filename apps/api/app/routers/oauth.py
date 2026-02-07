from __future__ import annotations

import base64
import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import encrypt_token
from app.db.session import get_db
from app.models import OAuthState, XAccount
from app.routers.deps import get_current_user


router = APIRouter(prefix="/oauth/x", tags=["oauth"])
logger = logging.getLogger("app.oauth")


def _require_oauth_settings() -> None:
    if not settings.x_client_id or not settings.x_oauth_redirect_uri:
        raise HTTPException(status_code=500, detail="X OAuth is not configured")


def _build_pkce() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)
    verifier = verifier[:128]
    digest = hashlib.sha256(verifier.encode("utf-8")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")
    return verifier, challenge


def _redirect_url(status: str, account_id: str | None = None, reason: str | None = None) -> str:
    params: dict[str, str] = {"oauth": status}
    if account_id:
        params["account_id"] = account_id
    if reason:
        params["reason"] = reason
    return f"{settings.admin_web_url}?{urlencode(params)}"


@router.get("/start")
def start_oauth(
    account_id: str = Query(..., alias="account_id"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> dict:
    _require_oauth_settings()

    account = db.get(XAccount, account_id)
    if not account or account.workspace_id != user.workspace_id:
        raise HTTPException(status_code=404, detail="Account not found")

    state = secrets.token_urlsafe(32)
    code_verifier, code_challenge = _build_pkce()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

    db.execute(delete(OAuthState).where(OAuthState.x_account_id == account.id))
    db.add(
        OAuthState(
            provider="x",
            state=state,
            code_verifier=code_verifier,
            workspace_id=user.workspace_id,
            x_account_id=account.id,
            expires_at=expires_at,
        )
    )
    db.commit()

    params = {
        "response_type": "code",
        "client_id": settings.x_client_id,
        "redirect_uri": settings.x_oauth_redirect_uri,
        "scope": settings.x_oauth_scopes,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    auth_url = f"{settings.x_oauth_authorize_url}?{urlencode(params)}"
    return {"authorization_url": auth_url}


@router.get("/callback")
async def oauth_callback(
    request: Request,
    state: str | None = None,
    code: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
    db: Session = Depends(get_db),
):
    try:
        _require_oauth_settings()
    except HTTPException:
        return RedirectResponse(_redirect_url("error", reason="oauth_not_configured"))

    if error:
        return RedirectResponse(_redirect_url("error", reason=error))
    if not state or not code:
        return RedirectResponse(_redirect_url("error", reason="missing_code"))

    oauth_state = db.scalar(select(OAuthState).where(OAuthState.state == state))
    if not oauth_state:
        return RedirectResponse(_redirect_url("error", reason="invalid_state"))

    if oauth_state.expires_at < datetime.now(timezone.utc):
        db.delete(oauth_state)
        db.commit()
        return RedirectResponse(_redirect_url("error", reason="expired_state"))

    account = db.get(XAccount, oauth_state.x_account_id)
    if not account:
        db.delete(oauth_state)
        db.commit()
        return RedirectResponse(_redirect_url("error", reason="account_missing"))

    db.delete(oauth_state)

    token_payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.x_oauth_redirect_uri,
        "client_id": settings.x_client_id,
        "code_verifier": oauth_state.code_verifier,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    if settings.x_client_secret:
        basic = base64.b64encode(
            f"{settings.x_client_id}:{settings.x_client_secret}".encode("utf-8")
        ).decode("utf-8")
        headers["Authorization"] = f"Basic {basic}"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            token_resp = await client.post(settings.x_oauth_token_url, data=token_payload, headers=headers)
    except Exception:
        logger.exception("X OAuth token exchange failed")
        db.commit()
        return RedirectResponse(_redirect_url("error", reason="token_exchange_failed"))

    if token_resp.status_code >= 400:
        logger.warning("X OAuth token exchange error: %s", token_resp.text)
        db.commit()
        return RedirectResponse(_redirect_url("error", reason="token_exchange_error"))

    token_data = token_resp.json()
    access_token = token_data.get("access_token")
    if not access_token:
        db.commit()
        return RedirectResponse(_redirect_url("error", reason="missing_access_token"))

    refresh_token = token_data.get("refresh_token")
    expires_in = token_data.get("expires_in")

    account.oauth_access_token_enc = encrypt_token(access_token)
    account.oauth_refresh_token_enc = encrypt_token(refresh_token or "")
    account.oauth_token_type = token_data.get("token_type")
    account.oauth_scopes = token_data.get("scope")
    if expires_in:
        try:
            expires_seconds = int(expires_in)
        except (TypeError, ValueError):
            expires_seconds = None
        if expires_seconds:
            account.oauth_expires_at = datetime.now(timezone.utc) + timedelta(
                seconds=expires_seconds
            )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            me_resp = await client.get(
                settings.x_oauth_me_url,
                headers={"Authorization": f"Bearer {access_token}"},
            )
        if me_resp.status_code < 400:
            me_data = me_resp.json().get("data")
            if isinstance(me_data, dict):
                username = me_data.get("username")
                name = me_data.get("name")
                if username:
                    account.handle = username
                if name:
                    account.name = name
    except Exception:
        logger.exception("X OAuth users/me fetch failed")

    db.commit()

    return RedirectResponse(_redirect_url("success", account_id=str(account.id)))
