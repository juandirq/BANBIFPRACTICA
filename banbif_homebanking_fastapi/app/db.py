from sqlmodel import SQLModel, create_engine
from app.config import settings

if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
else:
    # Necesario para Supabase Transaction Pooler, puerto 6543
    connect_args = {"prepare_threshold": None}

engine = create_engine(
    settings.database_url,
    echo=False,
    connect_args=connect_args,
    pool_pre_ping=True
)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
