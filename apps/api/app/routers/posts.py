from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Post, XAccount
from app.routers.deps import get_current_user
from app.schemas.posts import PostResponse


router = APIRouter(prefix="/posts", tags=["posts"])


@router.get("", response_model=list[PostResponse])
def list_posts(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> list[PostResponse]:
    posts = db.scalars(
        select(Post)
        .join(XAccount, Post.x_account_id == XAccount.id)
        .where(XAccount.workspace_id == user.workspace_id)
    ).all()
    return [PostResponse.model_validate(post) for post in posts]
