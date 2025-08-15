# models.py
from typing import List, Optional, Any
from sqlmodel import Field, SQLModel, JSON, Column
from datetime import datetime, timezone
from database import engine 

class ExtractionJob(SQLModel, table=True):
    id: str = Field(primary_key=True, index=True)
    filename: Optional[str] = None
    status: str = Field(default="completed")

    processed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    
    medications: List[Any] = Field(sa_column=Column(JSON)) # list of dictionaries using JSON column type
    
    total_medications: Optional[int] = None
    validated_count: Optional[int] = None

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)