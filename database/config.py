from dotenv import load_dotenv
import os
from sqlalchemy import create_engine

# Load environment
load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

# Singleton engine - created once, reused everywhere
_engine = None

def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    return _engine

# For convenience, export the engine
engine = get_engine()