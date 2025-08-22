from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from contratrix_api.settings import Settings

# Criação da engine com configuração de pool
engine = create_engine(
    Settings().DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=280       
)

# Criação do factory de sessões
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Função para ser usada com Depends no FastAPI
def get_session() -> Session:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
