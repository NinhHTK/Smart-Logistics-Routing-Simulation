from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

import database as db
import engine

# Initialize SQLite tables
db.init_db()

app = FastAPI(
    title="Autonomous Logistics Routing & Dispatch Engine",
    description="MVP API for Stockout Alert Handling, Margin Evaluation, VIP Bypass, and Automated 3PL Dispatch",
    version="1.0.0"
)

# Dependency to get DB session per request
def get_db():
    session = db.SessionLocal()
    try:
        yield session
    finally:
        session.close()

# Pydantic Schemas for Request & Response validation
class StockoutRequest(BaseModel):
    order_id: str
    item_sku: str
    requesting_store_id: str
    fulfilling_store_id: str
    order_value: float
    profit_margin: float
    items_count: int
    distance_km: float
    customer_tier: str = "BRONZE"
    is_service_recovery: bool = False

@app.get("/")
def root():
    return {"status": "online", "system": "Autonomous Logistics Dispatch Engine MVP"}

@app.post("/api/v1/routing/evaluate")
def evaluate_and_dispatch(payload: StockoutRequest, session: Session = Depends(get_db)):
    """
    Main Endpoint: Receives stockout order, executes 3-Threshold Rules Engine,
    logs decisions, updates Store KPI points, and triggers mock 3PL dispatch.
    """
    # 1. Run core logic engine
    eval_result = engine.evaluate_stockout_transfer(
        order_value=payload.order_value,
        profit_margin=payload.profit_margin,
        distance_km=payload.distance_km,
        items_count=payload.items_count,
        customer_tier=payload.customer_tier,
        is_service_recovery=payload.is_service_recovery
    )
    
    # 2. Record Stockout Alert in DB
    alert = db.StockoutAlert(
        order_id=payload.order_id,
        item_sku=payload.item_sku,
        requesting_store_id=payload.requesting_store_id,
        fulfilling_store_id=payload.fulfilling_store_id,
        order_value=payload.order_value,
        profit_margin=payload.profit_margin,
        customer_tier=payload.customer_tier,
        distance_km=payload.distance_km,
        status="RESOLVED" if eval_result["is_3pl_booked"] else "REJECTED"
    )
    session.add(alert)
    session.commit()
    session.refresh(alert)
    
    # 3. Log Transfer Decision
    transfer_log = db.TransferLog(
        alert_id=alert.id,
        decision=eval_result["decision"],
        shipping_cost=eval_result["shipping_cost"],
        net_profit=eval_result["net_profit"],
        is_3pl_booked=eval_result["is_3pl_booked"],
        tracking_code=eval_result["tracking_code"],
        kpi_points_awarded=eval_result["kpi_points_awarded"]
    )
    session.add(transfer_log)

    # 4. Update Store Manager KPI score
    store = session.query(db.Store).filter(db.Store.id == payload.requesting_store_id).first()
    if store:
        store.kpi_score += eval_result["kpi_points_awarded"]
    
    session.commit()
    
    return {
        "alert_id": alert.id,
        "evaluation": eval_result
    }

@app.get("/api/v1/logs")
def get_transfer_logs(session: Session = Depends(get_db)):
    """Retrieves all historical transfer decisions for dashboard analytics."""
    return session.query(db.TransferLog).all()
