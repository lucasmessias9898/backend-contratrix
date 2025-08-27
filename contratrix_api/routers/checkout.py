from http import HTTPStatus
from typing import Annotated
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from datetime import datetime
import pagarme

from contratrix_api.database import get_session
from contratrix_api.models import User, Planos, Cupom, Transacoes
from contratrix_api.schemas import Message, CheckoutSchema
from contratrix_api.security import get_current_user
from contratrix_api.settings import Settings

router = APIRouter()

Session = Annotated[Session, Depends(get_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]

router = APIRouter(prefix='/checkout', tags=['Checkout'])


@router.post('/avulso', status_code=HTTPStatus.CREATED, response_model=Message)
def create_cupom(
    checkout: CheckoutSchema,
    session: Session,
    user: CurrentUser
):

    user = session.query(User).filter_by(id=checkout.userId).first()
    plano = session.query(Planos).filter_by(id=checkout.planoId).first()

    if not user or not plano:
        raise HTTPException(status_code=404, detail="Usuário ou Plano não encontrado")
    
    valor_final = plano.preco_cents

    cupom = None

    if checkout.cupom_code:
        cupom = session.query(Cupom).filter_by(code=checkout.cupom_code, status="ativo").first()
        if not cupom:
            raise HTTPException(status_code=400, detail="Cupom inválido")
        if not (cupom.inicio <= datetime.utcnow() <= cupom.termino):
            raise HTTPException(status_code=400, detail="Cupom expirado")

        # aplicar desconto
        if cupom.tipo_desconto == "percentual":
            valor_final -= int(valor_final * (cupom.valor_desconto / 100))
        elif cupom.tipo_desconto == "fixo":
            valor_final -= cupom.valor_desconto

        if valor_final < 0:
            valor_final = 0

    db_transacao = Transacoes(
        tipo_transacao="avulso",
        valor_cents=valor_final,
        pagarme_transacao_id="",
        status="pendente",
        user_id=user.id,
        plano_id=plano.id,
        cupom_id=cupom.id if cupom else None
    )

    session.add(db_transacao)
    session.commit()
    session.refresh(db_transacao)

    pagarme.authentication_key("SUA_CHAVE_API_PAGARME")

    transaction_data = {
        "amount": valor_final,
        "payment_method": "credit_card",
        "customer": {
            "external_id": str(user.id),
            "name": user.nome,
            "email": user.email,
            "type": "individual",
            "country": "br",
        },
        "postback_url": "https://seuservidor.com/webhook/pagarme"
    }

    transaction = pagarme.transaction.create(transaction_data)

    # Atualizar transacao com ID da pagarme
    db_transacao.pagarme_transacao_id = transaction["id"]
    db_transacao.commit()

    return { 'message': transaction.get("checkout_url", "") }


@router.post('/assinatura', status_code=HTTPStatus.CREATED, response_model=Message)
def create_cupom(
    checkout: CheckoutSchema,
    session: Session,
    user: CurrentUser
):

    user = session.query(User).filter_by(id=checkout.userId).first()
    plano = session.query(Planos).filter_by(id=checkout.planoId).first()

    if not user or not plano:
        raise HTTPException(status_code=404, detail="Usuário ou Plano não encontrado")
    
    valor_final = plano.preco_cents

    cupom = None

    if checkout.cupom_code:
        cupom = session.query(Cupom).filter_by(code=checkout.cupom_code, status="ativo").first()
        if not cupom:
            raise HTTPException(status_code=400, detail="Cupom inválido")
        if not (cupom.inicio <= datetime.utcnow() <= cupom.termino):
            raise HTTPException(status_code=400, detail="Cupom expirado")

        # aplicar desconto
        if cupom.tipo_desconto == "percentual":
            valor_final -= int(valor_final * (cupom.valor_desconto / 100))
        elif cupom.tipo_desconto == "fixo":
            valor_final -= cupom.valor_desconto

        if valor_final < 0:
            valor_final = 0

    db_transacao = Transacoes(
        tipo_transacao="assinatura",
        valor_cents=valor_final,
        pagarme_transacao_id="",
        status="pendente",
        user_id=user.id,
        plano_id=plano.id,
        cupom_id=cupom.id if cupom else None
    )

    session.add(db_transacao)
    session.commit()
    session.refresh(db_transacao)

    pagarme.authentication_key("SUA_CHAVE_API_PAGARME")

    subscription_data = {
        "plan_id": plano.pagarme_planoId,
        "customer": {
            "external_id": str(user.id),
            "name": user.nome,
            "email": user.email,
        },
        "postback_url": "https://seuservidor.com/webhook/pagarme"
    }

    subscription = pagarme.subscription.create(subscription_data)

    # Atualizar transacao com ID da pagarme
    db_transacao.pagarme_transacao_id = subscription["id"]
    db_transacao.commit()

    return { 'message': subscription.get("checkout_url", "") }