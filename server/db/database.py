import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set!")

# Create the async engine
engine = create_async_engine(DATABASE_URL, echo=True) # Set echo=False in production

# Create a session factory to use in your FastAPI dependencies
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)