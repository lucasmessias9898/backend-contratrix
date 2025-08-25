from datetime import datetime
from typing import List, Optional, Dict, Union
from uuid import UUID 
from pydantic import BaseModel, EmailStr, HttpUrl, ConfigDict


class Message(BaseModel):
    message: str


class MessageUpload(BaseModel):
    message: str
    image: str


class MetricsPublic(BaseModel):
    total_users: int
    total_active_users: int
    total_active_clothes: int
    total_looks_generated: int
    total_users_premium: int
    total_premium: int

# Termos
class TermosSchema(BaseModel):
    aceito: bool
    data_aceite: datetime


class TermosPublic(BaseModel):
    aceito: bool
    data_aceite: datetime


# Endereco
class EnderecoSchema(BaseModel):
    cep: str | None = None
    rua: str | None = None
    numero: str | None = None
    complemento: str | None = None
    bairro: str | None = None
    cidade: str | None = None
    uf: str | None = None
    pais: str | None = None


# Dados usuario
class UserSchema(BaseModel):
    nome: str
    sobrenome: str
    email: EmailStr
    password: str
    termos: TermosSchema
    role: str
    inicio_plano: datetime | None
    fim_plano: datetime | None
    assinatura_id: str | None
    plano_id: str | None
    status: str | None = 'active'


class UserRecoverPassword(BaseModel):
    email: str


class UserPublic(BaseModel):
    id: UUID
    nome: str
    sobrenome: str
    email: EmailStr
    user_photo: str
    primeiro_acesso: bool
    termos: TermosPublic
    role: str
    inicio_plano: datetime | None
    fim_plano: datetime | None
    assinatura_id: str | None
    plano_id: str | None
    status: str
    created_at: datetime
    updated_at: datetime


class UserList(BaseModel):
    users: list[UserPublic]


class UserPaginated(BaseModel):
    total: int
    page: int
    size: int
    pages: int
    users: List[UserPublic]


class UserUpdate(BaseModel):
    nome: str | None = None
    sobrenome: str | None = None
    email: EmailStr | None = None
    user_photo: str | None = None
    is_first_access: bool | None = None
    plan: str | None = None
    status: str | None = None


class UserUpdateAdmin(BaseModel):
    nome: str | None = None
    sobrenome: str | None = None
    email: EmailStr | None = None
    user_photo: str | None = None
    is_first_access: bool | None = None
    plan: str | None = None
    status: str | None = None


class UserUpdatePassword(BaseModel):
   email: str
   code: str
   password: str


class UserDB(UserSchema):
    id: UUID


#Dados Prestador
class PrestadorSchema(BaseModel):
    tipo_prestador: str
    nome_prestador: str | None
    sobrenome_prestador: str | None
    cpf_prestador: str | None
    email_prestador: str | None
    telefone_prestador: str | None
    razao_social_prestador: str | None
    nome_fantasia_prestador: str | None
    cnpj_prestador: str | None
    endereco_prestador: EnderecoSchema | None = None
    logo_prestador: str | None
    status_prestador: str | None = 'active'


class PrestadorPublic(BaseModel):
    id: UUID
    tipo_prestador: str
    nome_prestador: str
    sobrenome_prestador: str
    cpf_prestador: str
    email_prestador: str
    telefone_prestador: str
    razao_social_prestador: str
    nome_fantasia_prestador: str
    cnpj_prestador: str
    endereco_prestador: EnderecoSchema
    status_prestador: str
    logo_prestador: str
    user_id: UUID
    created_at_prestador: datetime
    updated_at_prestador: datetime


class PrestadorUpdate(BaseModel):
    tipo_prestador: str | None = None
    nome_prestador: str | None = None
    sobrenome_prestador: str | None = None
    cpf_prestador: str | None = None
    email_prestador: str | None = None
    telefone_prestador: str | None = None
    razao_social_prestador: str | None = None
    nome_fantasia_prestador: str | None = None
    cnpj_prestador: str | None = None
    endereco_prestador: EnderecoSchema | None = None
    logo_prestador: str | None = None
    status_prestador: str | None = None


# Dados Cliente
class ClienteSchema(BaseModel):
    tipo_cliente: str
    nome_cliente: str | None
    sobrenome_cliente: str | None
    cpf_cliente: str | None
    email_cliente: str | None
    telefone_cliente: str | None
    razao_social_cliente: str | None
    nome_fantasia_cliente: str | None
    cnpj_cliente: str | None
    endereco_cliente: EnderecoSchema | None = None
    logo_cliente: str | None = None
    status_cliente: str | None = 'active'


class ClientePublic(BaseModel):
    id: UUID
    tipo_cliente: str
    nome_cliente: str
    sobrenome_cliente: str
    cpf_cliente: str
    email_cliente: str
    telefone_cliente: str
    razao_social_cliente: str
    nome_fantasia_cliente: str
    cnpj_cliente: str
    endereco_cliente: EnderecoSchema
    status_cliente: str
    logo_cliente: str
    user_id: UUID
    created_at_cliente: datetime
    updated_at_cliente: datetime


class ClienteList(BaseModel):
    clientes: list[ClientePublic]


class ClientePaginated(BaseModel):
    total: int
    page: int
    size: int
    pages: int
    clientes: List[ClientePublic]


class ClienteUpdate(BaseModel):
    tipo_cliente: str | None = None
    nome_cliente: str | None = None
    sobrenome_cliente: str | None = None
    cpf_cliente: str | None = None
    email_cliente: str | None = None
    telefone_cliente: str | None = None
    razao_social_cliente: str | None = None
    nome_fantasia_cliente: str | None = None
    cnpj_cliente: str | None = None
    endereco_cliente: EnderecoSchema | None = None
    logo_cliente: str | None = None
    status_cliente: str | None = None


# Dados Template
class CampoTemplate(BaseModel):
    name: str
    label: str | None = None


class TemplateSchema(BaseModel):
    nome: str
    tipo: str 
    campos: List[CampoTemplate]
    template: str
    status: str


class TemplatePublic(BaseModel):
    id: UUID
    nome: str
    tipo: str 
    campos: List[CampoTemplate]
    template: str
    status: str
    created_at: datetime
    updated_at: datetime


class TemplatePaginated(BaseModel):
    total: int
    page: int
    size: int
    pages: int
    templates: List[TemplatePublic]


class TemplateUpdate(BaseModel):
    nome: str | None = None
    tipo: str | None = None
    campos: List[CampoTemplate] | None = None
    template: str | None = None
    status: str | None = None
    status: str | None = None


# Dados Gerar Documento
class DocumentoSchema(BaseModel):
    nome_documento: Optional[str] = None
    tipo: str
    modo: str
    template_id: UUID
    cliente_id: Optional[UUID] = None
    dados_contrato: Dict[str, Optional[str]]


class DocumentoPublic(BaseModel):
    id: UUID
    nome_documento: str
    tipo: str
    modo: str
    documento_text: str
    pdf_url: str
    status: str
    user_id: UUID
    cliente_id: Optional[UUID] = None
    template_id: UUID
    created_at: datetime
    updated_at: datetime


class DocumentoPaginated(BaseModel):
    total: int
    page: int
    size: int
    pages: int
    documentos: List[DocumentoPublic]


class DocumentoUpdate(BaseModel):
    nome: str | None = None
    tipo: str | None = None
    campos: List[str] | None = None
    template: str | None = None
    status: str | None = None
    status: str | None = None


# Dados token
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str | None = None


# Planos
class PlanoSchema(BaseModel):
    nome: str
    descricao: str
    preco_cents: int
    ciclo_faturamento: str
    pagarme_planoId: str
    status: str | None = 'active'


class PlanoPublic(BaseModel):
    id: UUID
    nome: str
    descricao: str
    preco_cents: int
    ciclo_faturamento: str
    pagarme_planoId: str
    status: str
    created_at: datetime
    updated_at: datetime


class PlanoPaginated(BaseModel):
    total: int
    page: int
    size: int
    pages: int
    planos: List[PlanoPublic]


class PlanoUpdate(BaseModel):
    nome: str | None = None
    descricao: str | None = None
    preco_cents: int | None = None
    ciclo_faturamento: str | None = None
    pagarme_planoId: str | None = None
    status: str | None = None


# Dados Transação
class TransacaoSchema(BaseModel):
    tipo_transacao: str
    valor_cents: int
    pagarme_transacao_id: str
    pagarme_planoId: str | None = None
    status: str
    user_id: UUID
    documento_id: UUID | None = None


class TransacaoPublic(BaseModel):
    id: UUID
    tipo_transacao: str
    valor_cents: int
    pagarme_transacao_id: str
    pagarme_planoId: str | None = None
    status: str
    user_id: UUID
    documento_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


class TransacaoPaginated(BaseModel):
    total: int
    page: int
    size: int
    pages: int
    transacoes: List[TransacaoPublic]


class TransacaoUpdate(BaseModel):
    tipo_transacao: str | None = None
    valor_cents: int | None = None
    pagarme_transacao_id: str | None = None
    pagarme_planoId: str | None = None
    status: str | None = None
    documento_id: UUID | None = None


# Dados Cupom
class CupomSchema(BaseModel):
    code: str
    tipo_desconto: str
    valor_desconto: int
    aplicavel: str
    quantidade_total: int
    limit_uso_usuario: int
    inicio: datetime
    termino: datetime
    observacao: str | None = None
    status: str | None = 'active'


class CupomPublic(BaseModel):
    id: UUID
    code: str
    tipo_desconto: str
    valor_desconto: int
    aplicavel: str
    quantidade_total: int
    limit_uso_usuario: int
    inicio: datetime
    termino: datetime
    observacao: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime


class CupomPaginated(BaseModel):
    total: int
    page: int
    size: int
    pages: int
    cupons: List[CupomPublic]


class CupomUpdate(BaseModel):
    code: str | None = None
    tipo_desconto: str | None = None
    valor_desconto: int | None = None
    aplicavel: str | None = None
    quantidade_total: int | None = None
    limit_uso_usuario: int | None = None
    inicio: datetime | None = None
    termino: datetime | None = None
    observacao: str | None = None
    status: str | None = None