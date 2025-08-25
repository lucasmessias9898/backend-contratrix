from http import HTTPStatus
from typing import Annotated
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from contratrix_api.database import get_session
from contratrix_api.models import Planos, User
from contratrix_api.schemas import Message, PlanoPaginated, PlanoPublic, PlanoUpdate, PlanoSchema
from contratrix_api.security import get_current_user
from contratrix_api.settings import Settings

router = APIRouter()

Session = Annotated[Session, Depends(get_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]

router = APIRouter(prefix='/planos', tags=['Planos'])


@router.post('/', status_code=HTTPStatus.CREATED, response_model=PlanoPublic)
def create_plano(
    plano: PlanoSchema,
    session: Session,
    user: CurrentUser
):

    db_planos = Planos(
        nome=plano.nome,
        descricao=plano.descricao,
        preco_cents=plano.preco_cents,
        ciclo_faturamento=plano.ciclo_faturamento,
        pagarme_planoId=plano.pagarme_planoId,
        status='active',
    )

    session.add(db_planos)
    session.commit()
    session.refresh(db_planos)

    return db_planos


@router.get('/', status_code=HTTPStatus.OK, response_model=PlanoPaginated)
def planos(  # noqa
    session: Session,
    user: CurrentUser,
    nome: str = Query(None),
    status: str = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100)
):
    
    query = select(Planos).where(Planos.status != 'deleted')

    if nome:
        query = query.filter(Planos.nome.contains(nome))

    if status:
        query = query.filter(Planos.status.contains(status))

    total = session.scalar(select(func.count()).select_from(query.subquery()))

    offset = (page - 1) * limit
    planos = session.scalars(query.offset(offset).limit(limit)).all()

    pages = (total + limit - 1) // limit if total else 1

    return {
        'total': total,
        'page': page,
        'size': limit,
        'pages': pages,
        'planos': planos,
    }


@router.get('/{plano_id}', status_code=HTTPStatus.OK, response_model=PlanoPublic)
def plano_details(  # noqa
    session: Session,
    plano_id: UUID,
    user: CurrentUser
):  

    db_plano = session.query(Planos).where(Planos.id == plano_id).first()

    if not db_plano:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Plano não encontrado.'
        )

    return db_plano


@router.patch('/{plano_id}', status_code=HTTPStatus.OK, response_model=PlanoPublic)
def patch_plano(
    plano_id: UUID,
    plano: PlanoUpdate,
    session: Session,
    user: CurrentUser
):  

    db_plano = session.query(Planos).where(Planos.id == plano_id).first()

    if not db_plano:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Plano não encontrado.'
        )

    for key, value in plano.model_dump(exclude_unset=True).items():
        setattr(db_plano, key, value)

    session.commit()
    session.refresh(db_plano)

    return db_plano


@router.delete("/{plano_id}", status_code=HTTPStatus.OK, response_model=Message)
def delete_plano(
    plano_id: UUID, 
    session: Session,
    user: CurrentUser
):

    db_plano = session.query(Planos).filter_by(id=plano_id).first()

    if not db_plano:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Plano não encontrado.'
        )

    db_plano.status = 'deleted'

    session.commit()

    return {'message': 'Plano deletado.'}