from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False, default="analyst")  # 'admin' | 'analyst'
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Business(Base):
    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    rut = Column(String, unique=True, nullable=True)
    city = Column(String, nullable=True)
    type = Column(String, nullable=True)
    owner_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SalesHistory(Base):
    __tablename__ = "sales_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), default=1, index=True)
    date = Column(Date, nullable=False, index=True)
    store_nbr = Column(Integer, nullable=False, index=True)
    family = Column(String, nullable=False, index=True)
    sales = Column(Float, nullable=False)
    onpromotion = Column(Integer, default=0)
    sales_unit = Column(String(10), nullable=False, default="units")  # 'units' | 'CLP'
    ingest_id = Column(Integer, ForeignKey("ingest_log.id"), nullable=True, index=True)
    lag_7 = Column(Float)
    lag_14 = Column(Float)
    rolling_mean_7 = Column(Float)
    day_of_week = Column(Integer)
    month = Column(Integer)


class Store(Base):
    __tablename__ = "stores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    store_nbr = Column(Integer, nullable=False)  # número local dentro del negocio
    name = Column(String)
    city = Column(String)
    state = Column(String)
    type = Column(String)
    cluster = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


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


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, default=1, index=True)
    sku_id = Column(String, nullable=False, index=True)  # único por (business_id, store_nbr)
    name = Column(String, nullable=False)
    family = Column(String, nullable=False, index=True)
    store_nbr = Column(Integer, nullable=False, default=1, index=True)
    unit_cost = Column(Float, nullable=False, default=0.0)
    lead_time_days = Column(Integer, nullable=False, default=3)
    order_cost = Column(Float, nullable=False, default=0.0)
    holding_cost_pct = Column(Float, nullable=False, default=0.20)
    min_order_qty = Column(Integer, nullable=False, default=1)
    pack_size = Column(Integer, nullable=False, default=1)
    supplier_name = Column(String, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class IngestLog(Base):
    __tablename__ = "ingest_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    store_nbr = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # image | excel | pdf | historic
    records_loaded = Column(Integer, nullable=False, default=0)
    sales_unit = Column(String(10), nullable=False, default="units")
    date_range_start = Column(Date)
    date_range_end = Column(Date)
    families = Column(JSON)
    status = Column(String(10), nullable=False, default="active")  # active | reverted
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token = Column(String, unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
