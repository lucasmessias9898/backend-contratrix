from http import HTTPStatus
from typing import Annotated
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from contratrix_api.database import get_session
from contratrix_api.models import Prestador, User
from contratrix_api.schemas import Message, PrestadorPublic, PrestadorUpdate, PrestadorSchema
from contratrix_api.security import get_current_user
from contratrix_api.settings import Settings

router = APIRouter()

Session = Annotated[Session, Depends(get_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]

router = APIRouter(prefix='/prestador', tags=['Prestador'])


@router.post('/', status_code=HTTPStatus.CREATED, response_model=PrestadorPublic)
def create_prestador(
    prestador: PrestadorSchema,
    session: Session,
    user: CurrentUser
):
    endereco = {
        'cep': prestador.endereco_prestador.cep,
        'rua': prestador.endereco_prestador.rua,
        'numero': prestador.endereco_prestador.numero,
        'complemento': prestador.endereco_prestador.complemento,
        'bairro': prestador.endereco_prestador.bairro,
        'cidade': prestador.endereco_prestador.cidade,
        'uf': prestador.endereco_prestador.uf,
        'pais': prestador.endereco_prestador.pais
    }

    db_prestador = Prestador(
        tipo_prestador=prestador.tipo_prestador,
        nome_prestador=prestador.nome_prestador, 
        sobrenome_prestador=prestador.sobrenome_prestador, 
        cpf_prestador=prestador.cpf_prestador, 
        email_prestador=prestador.email_prestador, 
        telefone_prestador=prestador.telefone_prestador, 
        razao_social_prestador=prestador.razao_social_prestador, 
        nome_fantasia_prestador=prestador.nome_fantasia_prestador, 
        cnpj_prestador=prestador.cnpj_prestador, 
        endereco_prestador=endereco,
        logo_prestador=prestador.logo_prestador, 
        status_prestador='active',
        user_id=user.id
    )

    session.add(db_prestador)
    session.commit()
    session.refresh(db_prestador)

    return db_prestador


@router.get('/', status_code=HTTPStatus.OK, response_model=PrestadorPublic)
def prestador_details(  # noqa
    session: Session,
    user: CurrentUser
):  

    db_prestador = session.query(Prestador).where(Prestador.user_id == user.id).first()

    if not db_prestador:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Prestador não encontrado.'
        )


    return db_prestador


@router.patch('/{prestador_id}', status_code=HTTPStatus.OK, response_model=PrestadorPublic)
def patch_prestador(
    prestador_id: UUID,
    cliente: PrestadorUpdate,
    session: Session,
    user: CurrentUser
):  

    db_prestador = session.query(Prestador).where(Prestador.user_id == user.id).filter_by(id=prestador_id).first()

    if not db_prestador:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Cliente não encontrado.'
        )

    for key, value in cliente.model_dump(exclude_unset=True).items():
        setattr(db_prestador, key, value)

    session.commit()
    session.refresh(db_prestador)

    return db_prestador



@router.delete("/{prestador_id}", status_code=HTTPStatus.OK, response_model=Message)
def delete_prestador(
    prestador_id: UUID, 
    session: Session,
    user: CurrentUser
):

    db_prestador = session.query(Prestador).filter_by(id=prestador_id).first()

    if not db_prestador:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Prestador não encontrado.'
        )

    if user.id != db_prestador.user_id:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Usuário não autorizado para realizar esse tipo de operação.'
        )

    db_prestador.status_prestador = 'deleted'

    session.commit()

    return {'message': 'Prestador deletado.'}