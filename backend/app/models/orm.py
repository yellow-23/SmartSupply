from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, JSON, Numeric, String, Text
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    supabase_uid = Column(String, unique=True, nullable=True, index=True)
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
    onboarding_completed = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SalesHistory(Base):
    __tablename__ = "sales_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), default=1, index=True)
    date = Column(Date, nullable=False, index=True)
    store_nbr = Column(Integer, nullable=False, index=True)
    family = Column(String, nullable=False, index=True)
    sales = Column(Float, nullable=False)
    revenue = Column(Float, nullable=True)
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


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    store_nbr = Column(Integer, nullable=False, index=True)
    family = Column(String(50), nullable=False, index=True)
    unit_cost = Column(Numeric(12, 2), nullable=True)
    order_cost = Column(Numeric(12, 2), default=5000)
    holding_rate = Column(Numeric(5, 4), default=0.25)
    lead_time_days = Column(Integer, default=7)
    moq = Column(Numeric(10, 2), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class StockLevel(Base):
    __tablename__ = "stock_levels"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    store_nbr = Column(Integer, nullable=False, index=True)
    family = Column(String(50), nullable=False, index=True)
    quantity = Column(Numeric(12, 2), default=0)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    store_nbr = Column(Integer, nullable=False, index=True)
    family = Column(String(50), nullable=False, index=True)
    quantity = Column(Numeric(12, 2), nullable=False)
    trigger_stock = Column(Numeric(12, 2), nullable=True)
    reorder_point_s = Column(Numeric(12, 2), nullable=True)
    order_up_to_S = Column("order_up_to_s", Numeric(12, 2), nullable=True)
    policy_used = Column(String(10), default="s_s")
    status = Column(String(20), default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expected_delivery = Column(Date, nullable=True)
    received_at = Column(DateTime(timezone=True), nullable=True)


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


class UserBusiness(Base):
    __tablename__ = "user_businesses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False, default="member")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


