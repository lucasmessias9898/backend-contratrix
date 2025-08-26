from http import HTTPStatus

from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from contratrix_api.routers import (
    auth,
    prestador,
    users,
    clientes,
    templates,
    contratos,
    planos,
    cupons,
    transacoes
)
from contratrix_api.schemas import Message

app = FastAPI()

origins = [
    "*"
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(prestador.router)
app.include_router(clientes.router)
app.include_router(templates.router)
app.include_router(contratos.router)
app.include_router(planos.router)
app.include_router(cupons.router)
app.include_router(transacoes.router)


@app.get('/', status_code=HTTPStatus.OK, response_model=Message)
def read_root():
    return {'message': 'Olá Contratrix!'}


@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        content={"message": str(exc.detail)},
        status_code=exc.status_code
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        content={"message": "Erro na validação das informações. Tente novamente mais tarde."},
        status_code=422
    )

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"message": "Erro interno no servidor. Tente novamente mais tarde."}
    )