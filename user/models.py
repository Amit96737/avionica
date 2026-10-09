from common.models import CommonFields
from database import Base
from sqlalchemy import Column, String, Text, Boolean, DateTime


class Glossary(CommonFields, Base):
    __tablename__ = "glossary"

    title = Column(String)
    description = Column(Text)
    
    is_approved = Column(Boolean, default=False)
    is_approved_time = Column(DateTime, nullable=True)
