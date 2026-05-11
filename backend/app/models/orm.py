from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.database import Base


class Business(Base):
    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    rut = Column(String, unique=True, nullable=True)
    city = Column(String, nullable=True)
    type = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SalesHistory(Base):
    __tablename__ = "sales_history"

    id = Column(Integer, primary_key=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), default=1, index=True)
    date = Column(Date, nullable=False, index=True)
    store_nbr = Column(Integer, nullable=False, index=True)
    family = Column(String, nullable=False, index=True)
    sales = Column(Float, nullable=False)
    onpromotion = Column(Integer, default=0)
    lag_7 = Column(Float)
    lag_14 = Column(Float)
    rolling_mean_7 = Column(Float)
    day_of_week = Column(Integer)
    month = Column(Integer)


class Store(Base):
    __tablename__ = "stores"

    store_nbr = Column(Integer, primary_key=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), default=1, index=True)
    city = Column(String)
    state = Column(String)
    type = Column(String)
    cluster = Column(Integer)


class OilPrice(Base):
    __tablename__ = "oil_prices"

    date = Column(Date, primary_key=True)
    dcoilwtico = Column(Float)


class Holiday(Base):
    __tablename__ = "holidays"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False)
    type = Column(String)
    locale = Column(String)
    locale_name = Column(String)
    description = Column(Text)
    transferred = Column(Boolean, default=False)
