from src.db import db
from src.infrastructure.database import Base
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship


class Country(Base):
    __tablename__ = 'country'
    id = Column(Integer, primary_key=True)
    name = Column(String(190), nullable=False)
    iso = Column(String(2), nullable=False)
    iso3 = Column(String(3), nullable=True)
