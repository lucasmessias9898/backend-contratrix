from http import HTTPStatus
from typing import Annotated
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, Query, HTTPException, File, Form, UploadFile
from sqlalchemy import select, func
from sqlalchemy.orm import Session, joinedload

from contratrix_api.database import get_session
from contratrix_api.models import Cliente, User
from contratrix_api.schemas import Message, ClienteList, ClientePublic, ClienteUpdate, ClienteSchema, MessageUpload, ClientePaginated
from contratrix_api.security import get_current_user
from contratrix_api.settings import Settings
import boto3

router = APIRouter()

Session = Annotated[Session, Depends(get_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]

router = APIRouter(prefix='/clientes', tags=['Clientes'])


@router.post('/', status_code=HTTPStatus.CREATED, response_model=ClientePublic)
def create_cliente(
    cliente: ClienteSchema,
    session: Session,
    user: CurrentUser
):
    
    endereco = {
        'cep': cliente.endereco_cliente.cep,
        'rua': cliente.endereco_cliente.rua,
        'numero': cliente.endereco_cliente.numero,
        'complemento': cliente.endereco_cliente.complemento,
        'bairro': cliente.endereco_cliente.bairro,
        'cidade': cliente.endereco_cliente.cidade,
        'uf': cliente.endereco_cliente.uf,
        'pais': cliente.endereco_cliente.pais
    }

    db_cliente = Cliente(
        tipo_cliente=cliente.tipo_cliente,
        nome_cliente=cliente.nome_cliente, 
        sobrenome_cliente=cliente.sobrenome_cliente, 
        cpf_cliente=cliente.cpf_cliente, 
        email_cliente=cliente.email_cliente, 
        telefone_cliente=cliente.telefone_cliente, 
        razao_social_cliente=cliente.razao_social_cliente, 
        nome_fantasia_cliente=cliente.nome_fantasia_cliente, 
        cnpj_cliente=cliente.cnpj_cliente, 
        endereco_cliente=endereco,
        logo_cliente=cliente.logo_cliente, 
        status_cliente='active',
        user_id=user.id
    )

    session.add(db_cliente)
    session.commit()
    session.refresh(db_cliente)

    return db_cliente


@router.get('/', status_code=HTTPStatus.OK, response_model=ClientePaginated)
def clientes(  # noqa
    session: Session,
    user: CurrentUser,
    tipo_cliente: str = Query(None),
    nome: str = Query(None),
    razao_social: str = Query(None),
    nome_fantasia: str = Query(None),
    cpf: str = Query(None),
    cnpj: str = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100)
):
    
    query = select(Cliente).where(Cliente.user_id == user.id)

    if tipo_cliente:
        query = query.filter(Cliente.tipo_cliente.contains(tipo_cliente))
    
    if nome:
        query = query.filter(Cliente.nome_cliente.contains(nome))

    if razao_social:
        query = query.filter(Cliente.razao_social_cliente.contains(razao_social))

    if nome_fantasia:
        query = query.filter(Cliente.nome_fantasia_cliente.contains(nome_fantasia))

    if cpf:
        query = query.filter(Cliente.cpf_cliente.contains(cpf))

    if cnpj:
        query = query.filter(Cliente.cnpj_cliente.contains(cnpj))

    total = session.scalar(select(func.count()).select_from(query.subquery()))

    offset = (page - 1) * limit
    clientes = session.scalars(query.offset(offset).limit(limit)).all()

    pages = (total + limit - 1) // limit if total else 1

    return {
        'total': total,
        'page': page,
        'size': limit,
        'pages': pages,
        'clientes': clientes,
    }


@router.get('/{cliente_id}', status_code=HTTPStatus.OK, response_model=ClientePublic)
def cliente_details(  # noqa
    session: Session,
    cliente_id: UUID,
    user: CurrentUser
):  

    db_cliente = session.query(Cliente).where(Cliente.user_id == user.id).filter_by(id=cliente_id).first()

    if not db_cliente:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Cliente não encontrado.'
        )


    return db_cliente


@router.patch('/{cliente_id}', status_code=HTTPStatus.OK, response_model=ClientePublic)
def patch_item(
    cliente_id: UUID,
    cliente: ClienteUpdate,
    session: Session,
    user: CurrentUser
):  

    db_cliente = session.query(Cliente).where(Cliente.user_id == user.id).filter_by(id=cliente_id).first()

    if not db_cliente:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Cliente não encontrado.'
        )

    for key, value in cliente.model_dump(exclude_unset=True).items():
        setattr(db_cliente, key, value)

    session.commit()
    session.refresh(db_cliente)

    return db_cliente


@router.delete("/{cliente_id}", status_code=HTTPStatus.OK, response_model=Message)
def delete_item(
    cliente_id: UUID, 
    session: Session,
    user: CurrentUser
):

    db_cliente = session.query(Cliente).filter_by(id=cliente_id).first()

    if not db_cliente:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Cliente não encontrado.'
        )

    if user.id != db_cliente.user_id:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Usuário não autorizado para realizar esse tipo de operação.'
        )

    db_cliente.status_cliente = 'deleted'

    session.commit()

    return {'message': 'Usuário deletado.'}