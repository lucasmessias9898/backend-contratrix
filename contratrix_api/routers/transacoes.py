from http import HTTPStatus
from typing import Annotated
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from contratrix_api.database import get_session
from contratrix_api.models import Transacoes, User
from contratrix_api.schemas import Message, TransacaoPaginated, TransacaoPublic, TransacaoUpdate, TransacaoSchema
from contratrix_api.security import get_current_user
from contratrix_api.settings import Settings

router = APIRouter()

Session = Annotated[Session, Depends(get_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]

router = APIRouter(prefix='/cupons', tags=['Cupons'])


@router.post('/', status_code=HTTPStatus.CREATED, response_model=TransacaoPublic)
def create_transacao(
    transacao: TransacaoSchema,
    session: Session,
    user: CurrentUser
):

    db_transacao = Transacoes(
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

    session.add(db_transacao)
    session.commit()
    session.refresh(db_transacao)

    return db_transacao


@router.get('/', status_code=HTTPStatus.OK, response_model=TransacaoPaginated)
def transacoes(  # noqa
    session: Session,
    user: CurrentUser,
    status: str = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100)
):
    
    query = select(Transacoes).where(Transacoes.status != 'deleted')

    if status:
        query = query.filter(Transacoes.status.contains(status))

    total = session.scalar(select(func.count()).select_from(query.subquery()))

    offset = (page - 1) * limit
    transacoes = session.scalars(query.offset(offset).limit(limit)).all()

    pages = (total + limit - 1) // limit if total else 1

    return {
        'total': total,
        'page': page,
        'size': limit,
        'pages': pages,
        'transacoes': transacoes,
    }


@router.get('/{transacao_id}', status_code=HTTPStatus.OK, response_model=TransacaoPublic)
def cupom_transacao(  # noqa
    session: Session,
    transacao_id: UUID,
    user: CurrentUser
):  

    db_transacao = session.query(Transacoes).where(Transacoes.id == transacao_id).first()

    if not db_transacao:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Transação não encontrada.'
        )

    return db_transacao


@router.delete("/{transacao_id}", status_code=HTTPStatus.OK, response_model=Message)
def delete_transacao(
    transacao_id: UUID, 
    session: Session,
    user: CurrentUser
):

    db_transacao = session.query(Transacoes).filter_by(id=transacao_id).first()

    if not db_transacao:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Transação não encontrado.'
        )

    db_transacao.status = 'deleted'

    session.commit()

    return {'message': 'Transação deletado.'}