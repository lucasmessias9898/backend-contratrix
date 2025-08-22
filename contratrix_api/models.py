from datetime import datetime
from enum import Enum
from typing import List, TypedDict

from sqlalchemy import ForeignKey, String, func, Column, ARRAY, String, ForeignKey, Column
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, TEXT
from sqlalchemy.orm import Mapped, mapped_column, registry, relationship
import uuid
from sqlalchemy.dialects.postgresql import UUID


table_registry = registry()


@table_registry.mapped_as_dataclass
class User:
    __tablename__ = 'users'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        init=False
    )
    nome: Mapped[str]
    sobrenome: Mapped[str]
    password: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
    user_photo: Mapped[str] = mapped_column(nullable=True)
    primeiro_acesso: Mapped[bool]
    termos: Mapped[List[str]] = mapped_column(JSONB, nullable=False)
    plano: Mapped[str]
    role: Mapped[str]
    inicio_plano: Mapped[datetime]
    fim_plano: Mapped[datetime]
    assinatura_id: Mapped[str]
    status: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now(), onupdate=func.now()
    )

    plano_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('planos.id'))
    reset_tokens = relationship('PasswordResetToken', init=False, back_populates='user', cascade="all, delete-orphan")
    clientes = relationship('Cliente', backref='user', cascade="all, delete-orphan")



@table_registry.mapped_as_dataclass
class Prestador:
    __tablename__ = 'prestador'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        init=False
    )
    tipo_prestador: Mapped[str]
    nome_prestador: Mapped[str] = mapped_column(nullable=True)
    sobrenome_prestador: Mapped[str] = mapped_column(nullable=True)
    cpf_prestador: Mapped[str] = mapped_column(nullable=True)
    telefone_prestador: Mapped[str]
    email_prestador: Mapped[str]
    razao_social_prestador: Mapped[str] = mapped_column(nullable=True)
    nome_fantasia_prestador: Mapped[str] = mapped_column(nullable=True)
    cnpj_prestador: Mapped[str] = mapped_column(nullable=True)
    endereco_prestador: Mapped[List[str]] = mapped_column(JSONB, nullable=False)
    status_prestador: Mapped[str] = mapped_column()
    logo_prestador: Mapped[str] = mapped_column(nullable=True)
    created_at_prestador: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now()
    )
    updated_at_prestador: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now(), onupdate=func.now()
    )

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id'))


@table_registry.mapped_as_dataclass
class Cliente:
    __tablename__ = 'clientes'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        init=False
    )
    tipo_cliente: Mapped[str]
    nome_cliente: Mapped[str] = mapped_column(nullable=True)
    sobrenome_cliente: Mapped[str] = mapped_column(nullable=True)
    cpf_cliente: Mapped[str] = mapped_column(nullable=True)
    telefone_cliente: Mapped[str]
    email_cliente: Mapped[str]
    razao_social_cliente: Mapped[str] = mapped_column(nullable=True)
    nome_fantasia_cliente: Mapped[str] = mapped_column(nullable=True)
    cnpj_cliente: Mapped[str] = mapped_column(nullable=True)
    endereco_cliente: Mapped[List[str]] = mapped_column(JSONB, nullable=False)
    status_cliente: Mapped[str] = mapped_column()
    logo_cliente: Mapped[str] = mapped_column(nullable=True)
    created_at_cliente: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now()
    )
    updated_at_cliente: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now(), onupdate=func.now()
    )

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id'))


@table_registry.mapped_as_dataclass
class Template:
    __tablename__ = 'templates'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        init=False
    )
    nome: Mapped[str]
    tipo: Mapped[str]
    campos: Mapped[List[str]] = mapped_column(JSONB, nullable=False)
    template: Mapped[str]
    status: Mapped[str] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now(), onupdate=func.now()
    )


@table_registry.mapped_as_dataclass
class Documentos:
    __tablename__ = 'documentos'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        init=False
    )
    nome_documento: Mapped[str] = mapped_column(nullable=True)
    tipo: Mapped[str] = mapped_column(nullable=False)
    modo: Mapped[str] = mapped_column(nullable=False)
    documento_text: Mapped[str] = mapped_column(TEXT, nullable=True)
    pdf_url: Mapped[str] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now(), onupdate=func.now()
    )

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id'))
    cliente_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('clientes.id'), nullable=True)
    template_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('templates.id'))


@table_registry.mapped_as_dataclass
class Planos:
    __tablename__ = 'planos'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        init=False
    )
    nome: Mapped[str]
    descricao: Mapped[str]
    preco_cents: Mapped[int]
    ciclo_faturamento: Mapped[str]
    pagarme_planoId: Mapped[str]
    status: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now(), onupdate=func.now()
    )


@table_registry.mapped_as_dataclass
class Transacoes:
    __tablename__ = 'transacoes'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        init=False
    )
    tipo_transacao: Mapped[str]
    valor_cents: Mapped[int]
    pagarme_transacao_id: Mapped[str]
    pagarme_planoId: Mapped[str]
    status: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now(), onupdate=func.now()
    )

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id'))
    documento_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('documentos.id'), nullable=True)


@table_registry.mapped_as_dataclass
class Cupom:
    __tablename__ = 'cupons'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        init=False
    )
    code: Mapped[str]
    tipo_desconto: Mapped[str]
    valor_desconto: Mapped[int]
    aplicavel: Mapped[str]
    quantidade_total: Mapped[int]
    limit_uso_usuario: Mapped[int]
    inicio: Mapped[datetime]
    termino: Mapped[datetime]
    observacao: Mapped[str]
    status: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now(), onupdate=func.now()
    )


@table_registry.mapped_as_dataclass
class CupomUsage:
    __tablename__ = 'cupom_usado'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        init=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    cupom_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("cupons.id", ondelete="CASCADE"), 
        nullable=False
    )
    quantidade_usado: Mapped[int]
    ultima_vez_usado: Mapped[datetime] = mapped_column(
        init=False,
        server_default=func.now()
    )


@table_registry.mapped_as_dataclass
class PasswordResetToken:
    __tablename__ = 'password_reset_tokens'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        init=False
    )
    code: Mapped[str]
    expires_at: Mapped[datetime]
    used: Mapped[bool] 
    created_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now(), onupdate=func.now()
    )

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id'))
    user = relationship('User', back_populates='reset_tokens')