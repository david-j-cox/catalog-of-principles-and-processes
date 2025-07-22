from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment (Railway will provide this)
DATABASE_URL = os.getenv("DATABASE_URL")

# For local development, fallback to SQLite if DATABASE_URL is not set
if not DATABASE_URL or DATABASE_URL.startswith("postgresql://username"):
    DATABASE_URL = "sqlite:///./jeab_database.db"

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    # For PostgreSQL, we need to handle the connection properly
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 