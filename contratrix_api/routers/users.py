from http import HTTPStatus
from typing import Annotated
import random
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile, Form
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from contratrix_api.database import get_session
from contratrix_api.models import User, Prestador, PasswordResetToken
from contratrix_api.schemas import Message, UserPublic, UserSchema, UserUpdate, UserUpdateAdmin, UserPaginated, UserRecoverPassword, UserUpdatePassword
from contratrix_api.security import (
    get_current_user,
    get_password_hash,
)
from contratrix_api.settings import Settings
from contratrix_api.utils.email import send_email

import boto3

router = APIRouter(prefix='/users', tags=['Users'])
Session = Annotated[Session, Depends(get_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post('/', status_code=HTTPStatus.CREATED, response_model=UserPublic)
def create_user(user: UserSchema, session: Session):

    db_user = session.scalar(select(User).where(User.email == user.email))

    if db_user:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='E-mail em uso. Tente recuperar a senha ou usar outro e-mail',
        )

    hashed_password = get_password_hash(user.password)

    termos = {'aceito': user.termos.aceito, 'data_aceite': user.termos.data_aceite.isoformat()}

    db_user = User(
        nome=user.nome,
        sobrenome=user.sobrenome,
        email=user.email,
        password=hashed_password,
        user_photo='',
        primeiro_acesso=True,
        termos=termos,
        role='user',
        inicio_plano=None,
        fim_plano=None,
        assinatura_id=None,
        plano_id=None,
        status='active',
    )

    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    db_prestador = Prestador(
        tipo_prestador=None,
        nome_prestador=None, 
        sobrenome_prestador=None, 
        cpf_prestador=None, 
        email_prestador=None, 
        telefone_prestador=None, 
        razao_social_prestador=None, 
        nome_fantasia_prestador=None, 
        cnpj_prestador=None, 
        endereco_prestador=None,
        logo_prestador=None, 
        status_prestador='active',
        user_id=db_user.id
    )

    session.add(db_prestador)
    session.commit()
    session.refresh(db_prestador)

    #send_email(user.name, user.email, 13, { 'name': user.name })

    return db_user


@router.get('/me', status_code=HTTPStatus.OK, response_model=UserPublic)
def user_details(  # noqa
    session: Session,
    user: CurrentUser
):
    db_user = session.query(User).filter_by(id=user.id).first()

    if not db_user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Usuário não encontrado.'
        )

    if db_user.user_photo and db_user.user_photo.strip().lower() not in ['null', 'none', '']:
        db_user.user_photo = Settings().CLOUDFLARE_AVATAR + db_user.user_photo

    return db_user


@router.get('/', status_code=HTTPStatus.OK, response_model=UserPaginated)
def Users(  # noqa
    session: Session,
    user: CurrentUser,
    nome: str = Query(None),
    status: str = Query(None),
    role: str = Query(None),
    plano: str = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100)
):  

    if user.role != 'admin':
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail='Usuário não autorizado.'
        )

    query = select(User).where(User.status != 'deleted').order_by(User.nome)

    if nome:
        query = query.filter(User.nome.contains(nome))

    if status:
        query = query.filter(User.status == status)

    if role:
        query = query.filter(User.role == role)

    if plano:
        query = query.filter(User.plano == plano)

    total = session.scalar(select(func.count()).select_from(query.subquery()))

    offset = (page - 1) * limit
    users = session.scalars(query.offset(offset).limit(limit)).all()

    for user in users:
        if user.user_photo and user.user_photo.strip().lower() not in ['null', 'none', '']:
            user.user_photo = ''

    pages = (total + limit - 1) // limit if total else 1

    return {
        'total': total,
        'page': page,
        'size': limit,
        'pages': pages,
        'users': users
    }


@router.get('/{user_id}', status_code=HTTPStatus.OK, response_model=UserPublic)
def user_details(  # noqa
    session: Session,
    user_id: UUID,
    user: CurrentUser
):
    db_user = session.query(User).filter_by(id=user_id).first()

    if not db_user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Usuário não encontrado.'
        )

    if user.role != 'admin' and user_id != db_user.id:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Usuário não autorizado.'
        )

    if db_user.user_photo and db_user.user_photo.strip().lower() not in ['null', 'none', '']:
        if user.role == 'user' and user_id == db_user.id:
            db_user.user_photo = Settings().CLOUDFLARE_AVATAR + db_user.user_photo
        else:
            db_user.user_photo = ''

    return db_user


@router.patch('/{user_id}', status_code=HTTPStatus.OK, response_model=UserPublic)
def patch_user(
    user_id: UUID,
    user: UserUpdate,
    session: Session,
    userCurrent: CurrentUser
):
    db_user = session.query(User).filter_by(id=user_id).first()

    if not db_user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Usuário não encontrado.'
        )

    if userCurrent.role != 'admin' and userCurrent.id != db_user.id:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Usuário não autorizado.'
        )

    for key, value in user.model_dump(exclude_unset=True).items():
        setattr(db_user, key, value)

    session.commit()
    session.refresh(db_user)

    if db_user.user_photo and db_user.user_photo.strip().lower() not in ['null', 'none', '']:
        db_user.user_photo = Settings().CLOUDFLARE_AVATAR + db_user.user_photo

    return db_user


@router.patch('/web/{user_id}', status_code=HTTPStatus.OK, response_model=UserPublic)
def patch_user_admin(
    user_id: UUID,
    user: UserUpdateAdmin,
    session: Session,
    userCurrent: CurrentUser
):
    
    if userCurrent.role != 'admin':
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Usuário não autorizado.'
        )
    
    db_user = session.query(User).filter_by(id=user_id).first()

    if not db_user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Usuário não encontrado.'
        )

    for key, value in user.model_dump(exclude_unset=True).items():
        setattr(db_user, key, value)

    session.commit()
    session.refresh(db_user)

    if db_user.user_photo and db_user.user_photo.strip().lower() not in ['null', 'none', '']:
        db_user.user_photo = Settings().CLOUDFLARE_AVATAR + db_user.user_photo

    return db_user    


@router.put('/{user_id}/upload', status_code=HTTPStatus.OK, response_model=Message)
def put_user_upload(
    user_id: UUID,
    session: Session,
    userCurrent: CurrentUser,
    file: UploadFile = File,
    file_old: str = Form(None)
):

    db_user = session.query(User).filter_by(id=user_id).first()

    if not db_user:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Usuário não encontrado.')

    if userCurrent.role != 'admin' and userCurrent.id != db_user.id:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Usuário não encontrado.'
        )

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
        f"{Settings().BUCKET_NAME_AVATAR}",
        new_file_name
    )

    if file_old:
        s3_client.delete_object(
            Bucket=f"{Settings().BUCKET_NAME_AVATAR}",
            Key=file_old
        )

    db_user.user_photo = new_file_name
    session.commit()
    session.refresh(db_user)

    return {'message': 'Upload'}


@router.delete('/{user_id}', response_model=Message)
def delete_user(
    user_id: UUID,
    session: Session,
    user: CurrentUser
):
    db_user = session.query(User).filter_by(id=user_id).first()

    if not db_user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Usuário não encontrado.'
        )

    if user.role != 'admin' and user.id != db_user.id:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Usuário não autorizado.'
        )

    db_user.status = 'deleted'
    db_user.nome = None
    db_user.email = None
    db_user.telefone = None
    db_user.aceite = None

    session.commit()

    return {'message': 'User deleted'}


@router.post('/recover-password', status_code=HTTPStatus.CREATED, response_model=Message)
def recover_password_user(user: UserRecoverPassword, session: Session):
    reset_code = str(random.randint(100000, 999999))
    expires_at = datetime.utcnow() + timedelta(minutes=10)

    db_user = session.query(User).filter_by(email=user.email).first()

    if not db_user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Usuário não encontrado.'
        )

    session.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == db_user.id,
        PasswordResetToken.used == False
    ).update({ "used": True })

    token = PasswordResetToken(
        code=reset_code,
        expires_at=expires_at,
        used=False,
        user_id=db_user.id
    )
    session.add(token)
    session.commit()

    #send_email(db_user.name, user.email, 11, { 'name': db_user.name, 'code': reset_code })

    return {'message': 'Código de recuperação enviado por email'}


@router.post('/reset-password', status_code=HTTPStatus.OK, response_model=Message)
def reset_password_user(user: UserUpdatePassword, session: Session):
    db_user = session.query(User).filter_by(email=user.email).first()

    if not db_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    db_token = (
        session.query(PasswordResetToken)
        .filter_by(user_id=db_user.id, code=user.code, used=False)
        .filter(PasswordResetToken.expires_at > datetime.utcnow())
        .order_by(PasswordResetToken.created_at.desc())
        .first()
    )

    if not db_token:
        raise HTTPException(status_code=400, detail="Código inválido ou expirado.")

    db_user.password = get_password_hash(user.password)
    session.commit()

    session.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == db_user.id,
        PasswordResetToken.used == False
    ).update({ "used": True })
    session.commit()

    #send_email(db_user.name, user.email, 15, { 'name': db_user.name })

    return {"message": "Senha atualizada com sucesso."}