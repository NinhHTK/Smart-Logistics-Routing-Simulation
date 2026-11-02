import database as db

def seed_database():
    db.init_db()
    session = db.SessionLocal()
    
    # Clear existing mock data to prevent duplicates
    session.query(db.TransferLog).delete()
    session.query(db.StockoutAlert).delete()
    session.query(db.Store).delete()
    session.commit()
    
    # 1. Create Default Stores
    stores = [
        db.Store(id="STORE-01", name="District 1 Flagship Hub", address="Nguyen Hue, D1, HCMC", kpi_score=100),
        db.Store(id="STORE-02", name="Thu Duc Express Store", address="Vo Van Ngan, Thu Duc, HCMC", kpi_score=100),
        db.Store(id="STORE-03", name="Tan Binh Retail Center", address="Truong Chinh, Tan Binh, HCMC", kpi_score=100)
    ]
    session.add_all(stores)
    session.commit()
    
    # 2. Create Sample Stockout Alerts & Logs
    sample_alerts = [
        {
            "order_id": "ORD-9001",
            "item_sku": "SKU-BEER-01",
            "requesting_store_id": "STORE-01",
            "fulfilling_store_id": "STORE-02",
            "order_value": 450000.0,
            "profit_margin": 35000.0,
            "items_count": 1,
            "distance_km": 4.5,
            "customer_tier": "BRONZE",
            "is_service_recovery": False
        },
        {
            "order_id": "ORD-9002",
            "item_sku": "SKU-WINE-05",
            "requesting_store_id": "STORE-02",
            "fulfilling_store_id": "STORE-03",
            "order_value": 2500000.0,
            "profit_margin": 40000.0,
            "items_count": 1,
            "distance_km": 6.0,
            "customer_tier": "PLATINUM",
            "is_service_recovery": False
        },
        {
            "order_id": "ORD-9003",
            "item_sku": "SKU-SNACK-10",
            "requesting_store_id": "STORE-03",
            "fulfilling_store_id": "STORE-01",
            "order_value": 1200000.0,
            "profit_margin": 150000.0,
            "items_count": 8,
            "distance_km": 8.5,
            "customer_tier": "SILVER",
            "is_service_recovery": False
        }
    ]
    
    for data in sample_alerts:
        alert = db.StockoutAlert(
            order_id=data["order_id"],
            item_sku=data["item_sku"],
            requesting_store_id=data["requesting_store_id"],
            fulfilling_store_id=data["fulfilling_store_id"],
            order_value=data["order_value"],
            profit_margin=data["profit_margin"],
            customer_tier=data["customer_tier"],
            distance_km=data["distance_km"],
            status="PENDING"
        )
        session.add(alert)
    
    session.commit()
    session.close()
    print("✅ Successfully seeded mock stores and initial records into SQLite!")

if __name__ == "__main__":
    seed_database()
