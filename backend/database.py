from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# 1. Database Connection URL for local XAMPP MySQL
# Format: mysql+pymysql://<user>:<password>@<host>:<port>/<database_name>
DATABASE_URL = "mysql+pymysql://root:@localhost:3306/annas_kokken"

# 2. Create the SQLAlchemy Engine
# pool_pre_ping=True checks connection liveness before executing queries
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

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