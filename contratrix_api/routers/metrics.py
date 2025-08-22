from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from contratrix_api.database import get_session
from contratrix_api.models import User, Item, Look
from contratrix_api.schemas import Message, MetricsPublic
from contratrix_api.security import (get_current_user)

router = APIRouter(prefix='/metrics', tags=['Metrics'])
Session = Annotated[Session, Depends(get_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get('/', status_code=HTTPStatus.OK, response_model=MetricsPublic)
def Metrics(  # noqa
    session: Session,
    user: CurrentUser
):  

    if user.role not in ['admin', 'stylist']:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail='User unauthorized'
        )

    total_users = session.scalar(select(func.count()).select_from(User))
    active_users = session.scalar(select(func.count()).select_from(User).where(User.status == 'active'))
    active_clothes = session.scalar(select(func.count()).select_from(Item).where(Item.status == 'active'))
    total_looks_generated = session.scalar(select(func.count()).select_from(Look).where(Look.status == 'generated'))
    total_users_premium = session.scalar(select(func.count()).select_from(User).where(User.status == 'active', User.role == 'user', User.plan == 'premium'))
    total_premium = session.scalar(select(func.count()).select_from(User).where(User.status == 'active', User.role != 'user', User.plan == 'premium'))

    return { 
        'total_users': total_users, 
        'total_active_users': active_users,
        'total_active_clothes': active_clothes,
        'total_looks_generated': total_looks_generated,
        'total_users_premium': total_users_premium,
        'total_premium': total_premium
    }
