from typing import Annotated
from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging

from contratrix_api.database import get_session
from contratrix_api.models import User

logger = logging.getLogger(__name__)

Session = Annotated[Session, Depends(get_session)]

router = APIRouter(prefix='/webhook', tags=['WebHook'])

@router.post("/pagarme")
async def pagarme_webhook(request: Request, db: Session):
    try:
        payload = await request.json()
        event = payload.get("event")
        data = payload.get("data", {})

        logger.info(f"Webhook recebido: {event}")

        # Identificar usuário (a partir de metadata ou subscription_id/transaction_id)
        metadata = data.get("metadata", {})
        user_id = metadata.get("user_id")

        if not user_id:
            raise HTTPException(status_code=400, detail="Webhook sem user_id")

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")

        # Fluxo para pagamento avulso (transaction)
        if event == "transaction.paid":
            plano_id = metadata.get("plano_id")
            dias = int(metadata.get("dias", 30))  # pode mandar nos metadados
            user.inicio_plano = datetime.utcnow()
            user.fim_plano = datetime.utcnow() + timedelta(days=dias)
            user.plano_id = plano_id
            user.status = "ativo"
            db.commit()
            logger.info(f"Plano avulso ativado para usuário {user.email}")

        elif event == "transaction.refused":
            user.status = "pagamento_recusado"
            db.commit()
            logger.info(f"Pagamento recusado para usuário {user.email}")

        # Fluxo para assinatura (subscription)
        elif event == "subscription.created":
            user.assinatura_id = data.get("id")
            user.inicio_plano = datetime.utcnow()
            user.fim_plano = datetime.utcnow() + timedelta(days=30)
            user.plano_id = metadata.get("plano_id")
            user.status = "ativo"
            db.commit()
            logger.info(f"Assinatura criada para {user.email}")

        elif event == "subscription.payment_failed":
            user.status = "inadimplente"
            db.commit()
            logger.info(f"Assinatura com pagamento falhado para {user.email}")

        elif event == "subscription.canceled":
            user.status = "cancelado"
            user.fim_plano = datetime.utcnow()
            db.commit()
            logger.info(f"Assinatura cancelada para {user.email}")

        return {"status": "success"}

    except Exception as e:
        logger.error(f"Erro no webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))
