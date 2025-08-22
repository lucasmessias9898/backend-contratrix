from http import HTTPStatus
from typing import Annotated
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from contratrix_api.database import get_session
from contratrix_api.models import Documentos, Template, Cliente, Prestador, User
from contratrix_api.schemas import Message, DocumentoSchema, DocumentoPublic, DocumentoPaginated, MessageUpload
from contratrix_api.security import get_current_user 

router = APIRouter()

Session = Annotated[Session, Depends(get_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]

router = APIRouter(prefix='/documentos', tags=['Documentos'])


@router.post('/gerar', status_code=HTTPStatus.CREATED, response_model=DocumentoPublic)
def create_documento(
    documento: DocumentoSchema,
    session: Session,
    user: CurrentUser
):

    # user_id: e4cae1f4-b1c3-47f6-b511-05ffae243bb8
    # prestador: 7b149677-c6cc-44f0-8b00-177575cb2907
    # cliente: bb87ffef-486f-49a3-bbd0-81a59df7b3bc
    # template: 058cf410-a650-4daf-8f72-639b35c52d1d

    # Buscar o template
    template = session.query(Template).filter(Template.id == documento.template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template não encontrado")

    # Buscar cliente (somente se informado)
    cliente = None
    if documento.cliente_id:
        cliente = session.query(Cliente).filter(Cliente.id == documento.cliente_id).first()
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")

    # Buscar prestador
    perfil = session.query(Prestador).filter(Prestador.user_id == user.id).first()
    if not perfil:
        raise HTTPException(status_code=400, detail="Usuário sem perfil cadastrado")

    # Carregar o html bruto
    html_template = template.template
    data_dict = {}

    for campo in template.campos:
        valor = ""
        # prestador
        if hasattr(perfil, campo):
            valor = getattr(perfil, campo) or ""
        # cliente (se houver)
        elif cliente and hasattr(cliente, campo):
            valor = getattr(cliente, campo) or ""
        # payload extra
        elif documento.dados_contrato and campo in documento.dados_contrato:
            valor = documento.dados_contrato[campo] or ""

        data_dict[campo] = valor

    if documento.dados_contrato:
        for campo, valor in documento.dados_contrato.items():
            if campo not in data_dict:  # não sobrescreve se já veio do perfil/cliente
                data_dict[campo] = valor or ""

    # Substituir placeholders no HTML
    html_final = html_template
    for key, value in data_dict.items():
        html_final = html_final.replace(f"{{{{{key}}}}}", str(value))

    if not html_final:
        raise HTTPException(status_code=400, detail="Erro ao gerar HTML do documento")

    # Persistência
    db_documento = Documentos(
        nome_documento=documento.nome_documento,
        tipo=documento.tipo,
        modo=documento.modo,
        documento_text=html_final,
        pdf_url='',
        status='draft',
        user_id=user.id,
        cliente_id=documento.cliente_id,
        template_id=documento.template_id
    )

    session.add(db_documento)
    session.commit()
    session.refresh(db_documento)  # garante que retorna atualizado
    return db_documento


@router.post("/express", status_code=HTTPStatus.CREATED, response_model=DocumentoPublic)
def criar_documento_express(
    documento: DocumentoSchema,
    session: Session,
    user: CurrentUser
):  
    
    # Buscar o template
    template = session.query(Template).filter(Template.id == documento.template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template não encontrado")
    
    campos = template.campos  # lista de campos
    texto = template.template  # texto base com placeholders

    # 2. Fazer de/para
    data_dict = {}
    for campo in campos:
        chave = campo["name"]  # pega a string
        valor = documento.dados_contrato.get(chave, "")
        data_dict[chave] = valor

    # 3. Substituir placeholders no texto
    for campo, valor in data_dict.items():
        placeholder = f"{{{{{campo}}}}}"  # exemplo: {{nome_cliente}}
        texto = texto.replace(placeholder, valor)
    
    # Persistência
    db_documento = Documentos(
        nome_documento=documento.nome_documento,
        tipo=documento.tipo,
        modo=documento.modo,
        documento_text=texto,
        pdf_url='',
        status='draft',
        user_id=user.id,
        cliente_id=None,
        template_id=documento.template_id
    )

    session.add(db_documento)
    session.commit()
    session.refresh(db_documento)

    return db_documento


@router.get('/', status_code=HTTPStatus.OK, response_model=DocumentoPaginated)
def documentos(  # noqa
    session: Session,
    user: CurrentUser,
    nome: str = Query(None),
    tipo: str = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100)
):
    
    query = select(Documentos).where(Documentos.user_id == user.id)

    if nome:
        query = query.filter(Documentos.nome_documento.contains(nome))

    if tipo:
        query = query.filter(Documentos.tipo.contains(tipo))

    total = session.scalar(select(func.count()).select_from(query.subquery()))

    offset = (page - 1) * limit
    documentos = session.scalars(query.offset(offset).limit(limit)).all()

    pages = (total + limit - 1) // limit if total else 1

    return {
        'total': total,
        'page': page,
        'size': limit,
        'pages': pages,
        'documentos': documentos,
    }


@router.get('/{documento_id}', status_code=HTTPStatus.OK, response_model=DocumentoPublic)
def documento_details(  # noqa
    session: Session,
    documento_id: UUID,
    user: CurrentUser
):  

    db_documento = session.query(Documentos).where(Documentos.user_id == user.id).filter_by(id=documento_id).first()

    if not db_documento:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Documento não encontrado.'
        )


    return db_documento


@router.delete("/{documento_id}", status_code=HTTPStatus.OK, response_model=Message)
def delete_documento(
    documento_id: UUID, 
    session: Session,
    user: CurrentUser
):

    db_documento = session.query(Documentos).filter_by(id=documento_id).first()

    if not db_documento:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Documento não encontrado.'
        )

    if user.id != db_documento.user_id:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Usuário não autorizado para realizar esse tipo de operação.'
        )

    db_documento.status = 'deleted'

    session.commit()

    return {'message': 'Documento deletado.'}