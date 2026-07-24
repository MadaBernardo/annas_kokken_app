import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# 1. Database Connection URL
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "mysql+pymysql://root:@localhost:3306/annas_kokken"
)

# PyMySQL does not recognize 'ssl_mode' in the URL string.
# We clean it up and handle SSL via connect_args if connecting to the cloud.
connect_args = {}
if "ssl_mode=" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("ssl_mode=REQUIRED", "").replace("?&", "?").rstrip("?")

if "localhost" not in DATABASE_URL and "127.0.0.1" not in DATABASE_URL:
    # Enable SSL connection for cloud databases using PyMySQL
    connect_args["ssl"] = {}

# 2. Create the SQLAlchemy Engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)

# 3. Create a Session Factory (SessionLocal)
# Each API request will get its own short-lived session to ensure data isolation
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Base class for ORM Models mapping
Base = declarative_base()

# 5. Database Dependency Utility Function
def get_db():
    """
    Opens a database connection session for a single request lifecycle,
    and guarantees it closes immediately after the execution finishes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()