import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sqlalchemy import create_engine, inspect
from database import SQLALCHEMY_DATABASE_URL
from models import Base


def reset_database():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    inspector = inspect(engine)

    # Get list of all table names
    table_names = inspector.get_table_names()

    # Drop all tables
    Base.metadata.drop_all(bind=engine)
    print(f"Dropped tables: {', '.join(table_names)}")

    # Recreate all tables
    Base.metadata.create_all(bind=engine)
    print("Recreated all tables.")


if __name__ == "__main__":
    reset_database()
