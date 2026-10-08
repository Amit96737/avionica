from common.models import CommonFields
from database import Base
from sqlalchemy import Column, String, Text, Boolean, DateTime


class AviationChronicle(CommonFields, Base):
    __tablename__ = "aviation_chronicle"

    title = Column(String, nullable=False)
    description = Column(Text)
    
    is_approved = Column(Boolean, default=False)
    is_approved_time = Column(DateTime, nullable=True)
