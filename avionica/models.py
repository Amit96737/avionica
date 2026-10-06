from database import Base
from sqlalchemy import String, Text, Column, ForeignKey, Boolean, JSON, DateTime
from common.models import CommonFields 
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSON
import enum as PyEnum
from aircraft.models import Aircraft

class ProductSeries(PyEnum.Enum):
    CIVILIAN = "Civilian"
    MILITARY = "Military"


class Manufacturer(CommonFields, Base):
    __tablename__ = "manufacturers"

    logo = Column(String)
    company_name = Column(String, unique=True, index=True)
    headquarter = Column(String)
    founding_date = Column(String)
    cover_photo = Column(JSON)

    # about company
    company_description = Column(Text)
    company_history = Column(Text)
    
    # gallery = Column(JSON)
    interesting_facts = Column(JSON)
    
    is_approved = Column(Boolean, default=False)
    is_approved_time = Column(DateTime, nullable=True)

    product = relationship("Product", back_populates="manufacturer", cascade="all, delete-orphan")
    aircrafts = relationship("Aircraft", back_populates="manufacturer", cascade="all, delete-orphan", passive_deletes=True,)


class Product(CommonFields, Base):
    __tablename__ = "products"

    series = Column(String(length=255))
    # description = Column(Text)
    data = Column(JSON, default=list)
    manufacturer_id = Column(ForeignKey("manufacturers.id"), nullable=False)

    manufacturer = relationship("Manufacturer", back_populates="product")
