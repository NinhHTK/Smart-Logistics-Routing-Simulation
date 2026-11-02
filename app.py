import streamlit as st
import requests
import pandas as pd
import json

# Dashboard Setup
st.set_page_config(
    page_title="Autonomous Logistics Dispatch Engine",
    page_icon="🚚",
    layout="wide"
)

API_BASE_URL = "http://127.0.0.1:8000"

st.title("🚚 Autonomous Logistics Routing & Dispatch Engine")
st.caption("Proof of Concept (PoC) — Real-time Stockout Management & Automated 3PL Dispatch")

# Sidebar - System Controls
st.sidebar.header("⚙️ System Control Panel")
st.sidebar.info("Simulating stockout events with Margin Evaluation, VIP Bypass Policy, and Automated AhaMove Dispatch.")

# Main Tabs
tab1, tab2, tab3 = st.tabs(["🚀 Trigger Stockout Event", "📜 Transfer Decision Logs", "🏆 Store KPI Leaderboard"])

# ---------------------------------------------------------
# TAB 1: Trigger Stockout Simulation Form
# ---------------------------------------------------------
with tab1:
    st.subheader("Simulate New Stockout Alert")
    
    with st.form("stockout_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            order_id = st.text_input("Order ID", "ORD-10088")
            item_sku = st.selectbox("Out-of-Stock Item SKU", ["SKU-BEER-01", "SKU-WINE-05", "SKU-SNACK-10"])
            requesting_store_id = st.selectbox("Requesting Store (Out of Stock)", ["STORE-01", "STORE-02", "STORE-03"])
            fulfilling_store_id = st.selectbox("Fulfilling Store (Has Surplus Stock)", ["STORE-02", "STORE-03", "STORE-01"])
            order_value = st.number_input("Order Value (VND)", value=500000.0, step=50000.0)
            
        with col2:
            profit_margin = st.number_input("Item Profit Margin (VND)", value=35000.0, step=5000.0)
            items_count = st.number_input("Items Quantity", value=1, min_value=1)
            distance_km = st.number_input("Distance Between Stores (km)", value=5.5, step=0.5)
            customer_tier = st.selectbox("Customer Loyalty Tier", ["BRONZE", "SILVER", "GOLD", "PLATINUM"])
            is_service_recovery = st.checkbox("Service Recovery Order (VIP Bypass Override)")

        submit_btn = st.form_submit_button("Run Autonomous Dispatch Engine")

    if submit_btn:
        payload = {
            "order_id": order_id,
            "item_sku": item_sku,
            "requesting_store_id": requesting_store_id,
            "fulfilling_store_id": fulfilling_store_id,
            "order_value": order_value,
            "profit_margin": profit_margin,
            "items_count": items_count,
            "distance_km": distance_km,
            "customer_tier": customer_tier,
            "is_service_recovery": is_service_recovery
        }
        
        try:
            res = requests.post(f"{API_BASE_URL}/api/v1/routing/evaluate", json=payload)
            if res.status_code == 200:
                data = res.json()
                eval_data = data["evaluation"]
                
                st.success(f"Evaluation Complete! Alert ID: #{data['alert_id']}")
                
                res_col1, res_col2, res_col3, res_col4 = st.columns(4)
                res_col1.metric("Routing Decision", eval_data["decision"])
                res_col2.metric("Estimated Net Profit", f"{eval_data['net_profit']:,.0f} VND")
                res_col3.metric("Shipping Cost", f"{eval_data['shipping_cost']:,.0f} VND")
                res_col4.metric("3PL Dispatch Status", "BOOKED" if eval_data["is_3pl_booked"] else "LOCKED/REJECTED")
                
                if eval_data["tracking_code"]:
                    st.info(f"🚚 **Automated 3PL Booking Confirmed!** Tracking Code: `{eval_data['tracking_code']}`")
                st.write(f"**Engine Reason:** {eval_data['reason']}")
            else:
                st.error("Failed to connect to backend engine.")
        except Exception as e:
            st.error(f"Error executing request: {e}")

# ---------------------------------------------------------
# TAB 2: Transfer Logs & Decision History
# ---------------------------------------------------------
with tab2:
    st.subheader("Historical Routing & Dispatch Log")
    if st.button("Refresh Logs"):
        try:
            res = requests.get(f"{API_BASE_URL}/api/v1/logs")
            if res.status_code == 200:
                logs = res.json()
                if logs:
                    df = pd.DataFrame(logs)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No dispatch logs recorded yet.")
        except Exception as e:
            st.error(f"Could not load logs: {e}")

# ---------------------------------------------------------
# TAB 3: Store Manager KPI Leaderboard
# ---------------------------------------------------------
with tab3:
    st.subheader("Gamified Store KPI Ranking")
    st.write("Stores accumulate points for successful inventory routing and stockout resolutions.")
    # Static view for PoC demo
    kpi_data = pd.DataFrame([
        {"Store ID": "STORE-01", "Store Name": "District 1 Flagship Hub", "KPI Points": 180, "Tier Status": "🥇 Top Performer"},
        {"Store ID": "STORE-02", "Store Name": "Thu Duc Express Store", "KPI Points": 150, "Tier Status": "🥈 On Target"},
        {"Store ID": "STORE-03", "Store Name": "Tan Binh Retail Center", "KPI Points": 110, "Tier Status": "🥉 On Target"}
    ])
    st.table(kpi_data)
