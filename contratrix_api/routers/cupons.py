from http import HTTPStatus
from typing import Annotated
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from contratrix_api.database import get_session
from contratrix_api.models import Cupom, User
from contratrix_api.schemas import Message, CupomPaginated, CupomPublic, CupomUpdate, CupomSchema
from contratrix_api.security import get_current_user
from contratrix_api.settings import Settings

router = APIRouter()

Session = Annotated[Session, Depends(get_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]

router = APIRouter(prefix='/cupons', tags=['Cupons'])


@router.post('/', status_code=HTTPStatus.CREATED, response_model=CupomPublic)
def create_cupom(
    plano: CupomSchema,
    session: Session,
    user: CurrentUser
):

    db_cupom = Cupom(
        code=plano.code,
        tipo_desconto=plano.tipo_desconto,
        valor_desconto=plano.valor_desconto,
        aplicavel=plano.aplicavel,
        quantidade_total=plano.quantidade_total,
        limit_uso_usuario=plano.limit_uso_usuario,
        inicio=plano.inicio,
        termino=plano.termino,
        observacao=plano.observacao,
        status='active',
    )

    session.add(db_cupom)
    session.commit()
    session.refresh(db_cupom)

    return db_cupom


@router.get('/', status_code=HTTPStatus.OK, response_model=CupomPaginated)
def cupons(  # noqa
    session: Session,
    user: CurrentUser,
    code: str = Query(None),
    status: str = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100)
):
    
    query = select(Cupom).where(Cupom.status != 'deleted')

    if code:
        query = query.filter(Cupom.code.contains(code))

    if status:
        query = query.filter(Cupom.status.contains(status))

    total = session.scalar(select(func.count()).select_from(query.subquery()))

    offset = (page - 1) * limit
    cupons = session.scalars(query.offset(offset).limit(limit)).all()

    pages = (total + limit - 1) // limit if total else 1

    return {
        'total': total,
        'page': page,
        'size': limit,
        'pages': pages,
        'cupons': cupons,
    }


@router.get('/{cupom_id}', status_code=HTTPStatus.OK, response_model=CupomPublic)
def cupom_details(  # noqa
    session: Session,
    cupom_id: UUID,
    user: CurrentUser
):  

    db_cupom = session.query(Cupom).where(Cupom.id == cupom_id).first()

    if not db_cupom:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Cupom não encontrado.'
        )

    return db_cupom


@router.patch('/{cupom_id}', status_code=HTTPStatus.OK, response_model=CupomPublic)
def patch_cupom(
    cupom_id: UUID,
    cupom: CupomUpdate,
    session: Session,
    user: CurrentUser
):  

    db_cupom = session.query(Cupom).where(Cupom.id == cupom_id).first()

    if not db_cupom:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Cupom não encontrado.'
        )

    for key, value in cupom.model_dump(exclude_unset=True).items():
        setattr(db_cupom, key, value)

    session.commit()
    session.refresh(db_cupom)

    return db_cupom


@router.delete("/{cupom_id}", status_code=HTTPStatus.OK, response_model=Message)
def delete_cupom(
    cupom_id: UUID, 
    session: Session,
    user: CurrentUser
):

    db_cupom = session.query(Cupom).filter_by(id=cupom_id).first()

    if not db_cupom:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Cupom não encontrado.'
        )

    db_cupom.status = 'deleted'

    session.commit()

    return {'message': 'Cupom deletado.'}