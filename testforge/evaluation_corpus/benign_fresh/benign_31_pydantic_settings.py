from pydantic import BaseModel, Field
from typing import Optional

class DatabaseConfig(BaseModel):
    host: str = Field(default='127.0.0.1')
    port: int = Field(default=5432, ge=1, le=65535)
    database_name: str = 'production_db'
    timeout_seconds: float = 30.0
