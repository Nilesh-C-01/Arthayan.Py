from sqlalchemy import Column, Integer, String, Float, DateTime
from app.models.database import Base
import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(String)

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float)
    type = Column(String)
    category = Column(String)
    description = Column(String)
    date = Column(DateTime, default=datetime.datetime.utcnow)
    owner = Column(String)  