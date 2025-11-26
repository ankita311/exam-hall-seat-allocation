from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

#sqlalchemy url format
#'postgresql://<username>:<password>@<ip-address/hostname>/<databasename>

# SQLALCHEMY_DATABASE_URL = f'postgresql://{settings.database_username}:{settings.database_password}@{settings.database_hostname}/{settings.database_name}'

# SQLALCHEMY_DATABASE_URL = "postgresql://postgres:5rW0ggJwQsJ2aPm1@db.nsecnrqmylajmvvdbtbk.supabase.co:5432/postgres"
SQLALCHEMY_DATABASE_URL = "postgresql://postgres.nsecnrqmylajmvvdbtbk:5rW0ggJwQsJ2aPm1@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
print("connecting to", SQLALCHEMY_DATABASE_URL)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()