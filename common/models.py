from sqlalchemy import Column, String, DateTime, Boolean
from datetime import datetime
import uuid


class CommonFields(object):
    id = Column(String(length=36), unique=True, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
