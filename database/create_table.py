from config import engine
from models import Base
from sqlalchemy import inspect

# Create tables based on the models defined in models.py
Base.metadata.create_all(engine)

# Verify tables were created
inspector = inspect(engine)
tables = inspector.get_table_names()
print(f"Tables in database: {tables}")