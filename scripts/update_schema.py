from sqlalchemy import create_engine
from database import SQLALCHEMY_DATABASE_URL
from models import Base


def update_schema():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

    # This will create tables that don't exist, but won't modify existing tables
    Base.metadata.create_all(bind=engine)

    print("Database schema updated.")


if __name__ == "__main__":
    update_schema()
