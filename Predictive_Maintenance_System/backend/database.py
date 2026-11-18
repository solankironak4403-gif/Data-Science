import os
import logging
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from backend.models_db import Base, PredictionRecord

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("database")

# Load environment variables from .env
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "predictive_maintenance")

db_status = {
    "type": "unknown",
    "connected": False,
    "database": DB_NAME,
    "host": DB_HOST,
    "port": DB_PORT,
    "message": ""
}

def create_mysql_database_if_not_exists():
    """
    Attempts to connect to MySQL server and create the database if it doesn't already exist.
    """
    import pymysql

    conn = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT,
        connect_timeout=3
    )
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        conn.commit()
    finally:
        conn.close()

def init_engine():
    global db_status
    # 1. Attempt MySQL connection
    try:
        logger.info(f"Connecting to MySQL database '{DB_NAME}' at {DB_HOST}:{DB_PORT}...")
        create_mysql_database_if_not_exists()

        encoded_pw = quote_plus(DB_PASSWORD) if DB_PASSWORD else ""
        mysql_url = f"mysql+pymysql://{DB_USER}:{encoded_pw}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

        engine = create_engine(
            mysql_url,
            pool_pre_ping=True,
            pool_recycle=3600
        )
        # Test connection
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        Base.metadata.create_all(bind=engine)
        logger.info(f"Successfully connected to MySQL database: {DB_NAME}")
        db_status = {
            "type": "MySQL",
            "connected": True,
            "database": DB_NAME,
            "host": DB_HOST,
            "port": DB_PORT,
            "message": "Connected to MySQL database."
        }
        return engine

    except Exception as mysql_err:
        logger.warning(
            f"MySQL connection failed ({mysql_err}). "
            f"Ensure MySQL is running (e.g. in XAMPP / MySQL Service) with credentials in backend/.env. "
            f"Falling back to local SQLite database so the application continues to run seamlessly."
        )
        # 2. Fallback to SQLite so server never crashes if MySQL service hasn't started yet
        sqlite_file = Path(__file__).resolve().parent / "predictive_maintenance.db"
        sqlite_url = f"sqlite:///{sqlite_file}"
        engine = create_engine(
            sqlite_url,
            connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(bind=engine)
        db_status = {
            "type": "SQLite (Fallback)",
            "connected": True,
            "database": str(sqlite_file.name),
            "host": "localhost",
            "port": None,
            "message": f"Using SQLite fallback. MySQL error: {str(mysql_err)}"
        }
        return engine

engine = init_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    FastAPI dependency yielding a database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_database_status():
    return db_status

