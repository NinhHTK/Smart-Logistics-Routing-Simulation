import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DB_URL = "sqlite:///./smart_logistics.db"
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Store(Base):
    """Table storing Store details"""
    __tablename__ = "stores"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    address = Column(String)
    kpi_score = Column(Integer, default=100)  # Store Manager cumulative KPI score

class StockoutAlert(Base):
    """Table recording Stockout Event alerts"""
    __tablename__ = "stockout_alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String, index=True)
    item_sku = Column(String, nullable=False)
    requesting_store_id = Column(String, nullable=False)  # Store requesting stock
    fulfilling_store_id = Column(String, nullable=True)   # Store fulfilling stock transfer
    order_value = Column(Float, nullable=False)
    profit_margin = Column(Float, nullable=False)
    customer_tier = Column(String, default="BRONZE")      # BRONZE, SILVER, GOLD, PLATINUM
    distance_km = Column(Float, default=0.0)
    status = Column(String, default="PENDING")             # PENDING, RESOLVED, REJECTED
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class TransferLog(Base):
    """Table logging Routing Decisions & Automated 3PL Booking status"""
    __tablename__ = "transfer_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_id = Column(Integer, index=True)
    decision = Column(String, nullable=False)             # BULK, DROP_SHIP_EXPRESS, SAVE_THE_SALE
    shipping_cost = Column(Float, nullable=False)
    net_profit = Column(Float, nullable=False)
    is_3pl_booked = Column(Boolean, default=False)
    tracking_code = Column(String, nullable=True)          # Mock tracking code (AhaMove/Grab)
    kpi_points_awarded = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

def init_db():
    """Initializes Database tables"""
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
    print("✅ SQLite database (smart_logistics.db) initialized successfully!")
