from http import HTTPStatus
from typing import Annotated
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, Query, HTTPException, File, Form, UploadFile
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from contratrix_api.database import get_session
from contratrix_api.models import Template, User
from contratrix_api.schemas import Message, TemplatePublic, TemplateUpdate, TemplateSchema, TemplatePaginated, MessageUpload
from contratrix_api.security import get_current_user
from contratrix_api.settings import Settings
import boto3

router = APIRouter()

Session = Annotated[Session, Depends(get_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]

router = APIRouter(prefix='/templates', tags=['Templates'])


@router.post('/', status_code=HTTPStatus.CREATED, response_model=TemplatePublic)
def create_template(
    template: TemplateSchema,
    session: Session,
):
    
    campos_dict = [campo.dict() for campo in template.campos]
    
    db_template = Template(
        nome=template.nome, 
        tipo=template.tipo, 
        campos=campos_dict, 
        template=template.template, 
        status=template.status
    )

    session.add(db_template)
    session.commit()
    session.refresh(db_template)

    return db_template


@router.get('/', status_code=HTTPStatus.OK, response_model=TemplatePaginated)
def templates(  # noqa
    session: Session,
    user: CurrentUser,
    nome: str = Query(None),
    tipo: str = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100)
):
    
    query = select(Template).where(Template.status != 'deleted')

    if nome:
        query = query.filter(Template.nome.contains(nome))

    if tipo:
        query = query.filter(Template.tipo.contains(tipo))

    total = session.scalar(select(func.count()).select_from(query.subquery()))

    offset = (page - 1) * limit
    templates = session.scalars(query.offset(offset).limit(limit)).all()

    pages = (total + limit - 1) // limit if total else 1

    return {
        'total': total,
        'page': page,
        'size': limit,
        'pages': pages,
        'templates': templates,
    }


@router.get('/{template_id}', status_code=HTTPStatus.OK, response_model=TemplatePublic)
def template_details(  # noqa
    session: Session,
    template_id: UUID,
    user: CurrentUser
):  

    db_template = session.query(Template).where(Template.id == template_id).first()

    if not db_template:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Template não encontrado.'
        )


    return db_template


@router.patch('/{template_id}', status_code=HTTPStatus.OK, response_model=TemplatePublic)
def patch_template(
    template_id: UUID,
    template: TemplateUpdate,
    session: Session,
    user: CurrentUser
):  

    db_template = session.query(Template).where(Template.id == template_id).first()

    if not db_template:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Template não encontrado.'
        )

    for key, value in template.model_dump(exclude_unset=True).items():
        setattr(db_template, key, value)

    session.commit()
    session.refresh(db_template)

    return db_template


@router.post('/upload', status_code=HTTPStatus.OK, response_model=MessageUpload)
def post_upload(
    session: Session,
    userCurrent: CurrentUser,
    file: UploadFile = File,
    file_old: str = Form(None)
):

    s3_client = boto3.client(
        "s3",
        region_name='auto',
        endpoint_url=f"https://{Settings().CLOUDFLARE_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=f"{Settings().CLOUDFLARE_ACCESS_KEY_ID}",
        aws_secret_access_key=f"{Settings().CLOUDFLARE_SECRET_ACCESS_KEY}",
    )

    new_file_name = f"{uuid4()}-{file.filename.replace(' ', '-')}"

    s3_client.upload_fileobj(
        file.file,
        f"{Settings().BUCKET_NAME_TEMPLATES}",
        new_file_name
    )

    if file_old:
        s3_client.delete_object(
            Bucket=f"{Settings().BUCKET_NAME_TEMPLATES}",
            Key=file_old
        )

    return {'message': 'Upload', 'image': new_file_name}


@router.delete("/{template_id}", status_code=HTTPStatus.OK, response_model=Message)
def delete_template(
    template_id: UUID, 
    session: Session,
    user: CurrentUser
):

    db_template = session.query(Template).filter_by(id=template_id).first()

    if not db_template:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Template não encontrado.'
        )

    db_template.status = 'deleted'

    session.commit()

    return {'message': 'Template deletado.'}