import dash
from dash import html, dcc, Input, Output, State, dash_table, callback_context
import dash_bootstrap_components as dbc
import requests
import pandas as pd
from datetime import datetime
import random

API_BASE_URL = "http://127.0.0.1:8000"

# Initialize Dash application with Darkly theme
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    title="Autonomous Logistics & Dispatch Engine"
)

# ---------------------------------------------------------
# STYLING CUSTOMIZATION
# ---------------------------------------------------------
CARD_STYLE = {
    "backgroundColor": "#161b22",
    "border": "1px solid #30363d",
    "borderRadius": "10px",
    "boxShadow": "0 4px 6px rgba(0, 0, 0, 0.3)"
}

# ---------------------------------------------------------
# NAVBAR / HEADER SETUP (Tabs & Trigger Button)
# ---------------------------------------------------------
navbar = dbc.Navbar(
    dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(html.H4("🚚 SmartLogistics Engine", className="text-white fw-bold mb-0")),
                    dbc.Col(html.Span("Multi-Model Routing & Inventory PoC", className="text-muted ms-3 fs-6"), className="d-none d-md-block")
                ],
                align="center",
                className="g-0",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Tabs(
                            [
                                dbc.Tab(label="📊 Overview & Live Feed", tab_id="tab-overview", className="text-white"),
                                dbc.Tab(label="📦 Store Inventory Matrix", tab_id="tab-inventory", className="text-white"),
                            ],
                            id="nav-tabs",
                            active_tab="tab-overview",
                            className="border-0"
                        ),
                        className="d-none d-lg-block"
                    ),
                    dbc.Col(
                        dbc.Button(
                            "⚡ Trigger Event", 
                            id="btn-trigger-simulation", 
                            color="danger", 
                            size="sm", 
                            className="fw-bold px-3 py-1 shadow-sm ms-3",
                            title="Manual Simulation Trigger"
                        ),
                        className="d-flex align-items-center"
                    )
                ],
                align="center",
                className="g-0 ms-auto"
            )
        ],
        fluid=True
    ),
    color="#0d1117",
    dark=True,
    className="border-bottom border-secondary py-2"
)

# ---------------------------------------------------------
# UI LAYOUT CONTAINER
# ---------------------------------------------------------
app.layout = html.Div(
    [
        navbar,
        dbc.Container(
            id="page-content",
            fluid=True,
            className="px-4 py-3"
        )
    ],
    style={"backgroundColor": "#0b0f19", "minHeight": "100vh", "color": "#c9d1d9"}
)

# ---------------------------------------------------------
# STATE & REAL-TIME INVENTORY DATABASE MOCK
# ---------------------------------------------------------
sim_state = {
    "stockout_events": 0,
    "successful_dispatches": 0,
    "rejections": 0,
    "total_cost_vnd": 0
}

orders_history = []

# Khởi tạo lượng tồn kho ban đầu cho Kho tổng và các cửa hàng
store_inventories = {
    "Central Hub (Kho Tổng)": {"SKU-BEER-01": 500, "SKU-WINE-05": 300, "SKU-SNACK-10": 1000, "SKU-MILK-02": 400},
    "STORE-01 (Quận 1)":      {"SKU-BEER-01": 15,  "SKU-WINE-05": 2,   "SKU-SNACK-10": 25,   "SKU-MILK-02": 8},
    "STORE-02 (Thủ Đức)":     {"SKU-BEER-01": 40,  "SKU-WINE-05": 18,  "SKU-SNACK-10": 5,    "SKU-MILK-02": 30},
    "STORE-03 (Tân Bình)":    {"SKU-BEER-01": 2,   "SKU-WINE-05": 10,  "SKU-SNACK-10": 35,   "SKU-MILK-02": 12}
}

def generate_random_order():
    skus = ["SKU-BEER-01", "SKU-WINE-05", "SKU-SNACK-10", "SKU-MILK-02"]
    tiers = ["BRONZE", "SILVER", "GOLD", "PLATINUM"]
    delivery_types = ["1. Warehouse to Store", "2. Store to Store", "3. Store to Customer"]
    
    model_type = random.choice(delivery_types)
    sku = random.choice(skus)
    tier = random.choice(tiers)
    
    stores = ["STORE-01 (Quận 1)", "STORE-02 (Thủ Đức)", "STORE-03 (Tân Bình)"]
    
    if model_type == "1. Warehouse to Store":
        origin = "Central Hub (Kho Tổng)"
        destination = random.choice(stores)
        distance = round(random.uniform(10.0, 25.0), 1)
        shipping_cost = int(distance * 4000 + 50000)
    elif model_type == "2. Store to Store":
        origin = random.choice(stores)
        destination = random.choice([s for s in stores if s != origin])
        distance = round(random.uniform(3.0, 12.0), 1)
        shipping_cost = int(distance * 5000 + 20000)
    else: # Store to Customer
        origin = random.choice(stores)
        destination = random.choice([
            "Nguyễn Văn A (12 Nguyễn Huệ, Q.1)", 
            "Trần Thị B (45 Lê Văn Việt, Thủ Đức)", 
            "Lê Hoàng C (88 Trường Chinh, Tân Bình)"
        ])
        distance = round(random.uniform(1.0, 9.0), 1)
        shipping_cost = int(distance * 6000 + 15000)

    current_stock = store_inventories.get(origin, {}).get(sku, 10)
    
    is_success = True
    if origin != "Central Hub (Kho Tổng)" and current_stock <= 2:
        is_success = False  
    elif tier == "BRONZE" and shipping_cost > 60000:
        is_success = False

    decision = "EXPRESS_DISPATCH" if is_success else "REJECT_OUT_OF_STOCK_OR_HIGH_COST"
    if not is_success and tier == "PLATINUM":
        decision = "VIP_BYPASS_OVERRIDE"
        is_success = True

    qty_moved = random.randint(5, 15) if "Store" in model_type else random.randint(50, 100)
    if is_success:
        if origin in store_inventories and store_inventories[origin][sku] >= qty_moved:
            store_inventories[origin][sku] -= qty_moved
        if destination in store_inventories:
            store_inventories[destination][sku] += qty_moved

    ord_id = f"ORD-{random.randint(10000, 99999)}"
    timestamp = datetime.now().strftime("%H:%M:%S")

    return {
        "Time": timestamp,
        "Order ID": ord_id,
        "Model": model_type,
        "SKU": sku,
        "Origin": origin,
        "Destination": destination,
        "Tier": tier,
        "Distance": f"{distance} km",
        "Cost": f"{shipping_cost:,.0f} ₫",
        "Decision": decision
    }, is_success, shipping_cost

# ---------------------------------------------------------
# CALLBACK: SWITCH TABS (Overview vs Inventory Matrix)
# ---------------------------------------------------------
@app.callback(
    Output("page-content", "children"),
    Input("nav-tabs", "active_tab")
)
def render_tab_content(active_tab):
    if active_tab == "tab-inventory":
        inv_data = []
        for loc, skus in store_inventories.items():
            row = {"Location / Store": loc}
            row.update(skus)
            inv_data.append(row)
        
        df_inv = pd.DataFrame(inv_data)
        
        return html.Div(
            [
                html.H3("📦 Real-time Store Inventory Matrix", className="text-white fw-bold mt-2"),
                html.P("Tracking real-time inventory levels of each SKU across Central Hub and retail branch stores.", className="text-muted"),
                html.Hr(className="border-secondary"),
                dbc.Card(
                    dbc.CardBody(
                        [
                            dash_table.DataTable(
                                data=df_inv.to_dict('records'),
                                columns=[{"name": col, "id": col} for col in df_inv.columns],
                                style_header={'backgroundColor': '#21262d', 'color': '#58a6ff', 'fontWeight': 'bold', 'border': 'none'},
                                style_cell={'backgroundColor': '#161b22', 'color': 'white', 'textAlign': 'center', 'padding': '12px', 'border': '1px solid #30363d'},
                                style_data_conditional=[
                                    {
                                        'if': {'filter_query': '{SKU-BEER-01} < 5', 'column_id': 'SKU-BEER-01'},
                                        'backgroundColor': '#482325', 'color': '#ff7b72'
                                    },
                                    {
                                        'if': {'filter_query': '{SKU-WINE-05} < 5', 'column_id': 'SKU-WINE-05'},
                                        'backgroundColor': '#482325', 'color': '#ff7b72'
                                    }
                                ],
                                style_table={'overflowX': 'auto'}
                            ),
                            html.Br(),
                            html.P("💡 Note: Red highlighted cells indicate low stock levels (< 5 items), prompting Store-to-Store or Warehouse-to-Store replenishment rules.", className="text-warning small mb-0")
                        ]
                    ),
                    style=CARD_STYLE
                )
            ]
        )
    
    return html.Div(
        [
            html.Div(
                [
                    html.H3("Logistics Operation Command Center", className="text-white fw-bold mt-2"),
                    html.P("Real-time multi-model routing engine (Warehouse-to-Store, Store-to-Store, Store-to-Customer).", className="text-muted"),
                    html.Div(id="simulation-trigger-output", className="mb-2"),
                    html.Hr(className="border-secondary")
                ]
            ),
            # Metrics Row
            dbc.Row(
                [
                    dbc.Col(dbc.Card(dbc.CardBody([html.Small("TOTAL REQUESTS", className="text-muted fw-bold"), html.H3(id="metric-stockout", children=str(sim_state["stockout_events"]), className="text-info fw-bold mt-1")]), style=CARD_STYLE), md=3),
                    dbc.Col(dbc.Card(dbc.CardBody([html.Small("SUCCESSFUL DISPATCHES", className="text-muted fw-bold"), html.H3(id="metric-success", children=str(sim_state["successful_dispatches"]), className="text-success fw-bold mt-1")]), style=CARD_STYLE), md=3),
                    dbc.Col(dbc.Card(dbc.CardBody([html.Small("3PL REJECTIONS", className="text-muted fw-bold"), html.H3(id="metric-rejections", children=str(sim_state["rejections"]), className="text-danger fw-bold mt-1")]), style=CARD_STYLE), md=3),
                    dbc.Col(dbc.Card(dbc.CardBody([html.Small("TOTAL SHIPPING COST", className="text-muted fw-bold"), html.H3(id="metric-cost", children=f"{sim_state['total_cost_vnd']:,.0f} ₫", className="text-success fw-bold mt-1")]), style=CARD_STYLE), md=3),
                ],
                className="mb-4 g-3"
            ),
            # Main Content Grid
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.H5("🏆 Store Performance Leaderboard", className="text-warning fw-bold mb-3"),
                                    dash_table.DataTable(
                                        data=[
                                            {"Store ID": "STORE-01", "Name": "District 1 Hub", "KPI Points": 180, "Status": "🥇 Top"},
                                            {"Store ID": "STORE-02", "Name": "Thu Duc Express", "KPI Points": 150, "Status": "🥈 On Target"},
                                            {"Store ID": "STORE-03", "Name": "Tan Binh Center", "KPI Points": 110, "Status": "🥉 On Target"}
                                        ],
                                        columns=[{"name": i, "id": i} for i in ["Store ID", "Name", "KPI Points", "Status"]],
                                        style_header={'backgroundColor': '#21262d', 'color': 'white', 'fontWeight': 'bold', 'border': 'none'},
                                        style_cell={'backgroundColor': '#161b22', 'color': 'white', 'textAlign': 'left', 'padding': '12px', 'border': '1px solid #30363d'},
                                        style_table={'overflowX': 'auto'}
                                    ),
                                    html.Br(),
                                    html.P("💡 Tip: Check the 'Store Inventory Matrix' tab above to monitor live stock updates.", className="text-muted small mb-0")
                                ]
                            ),
                            style=CARD_STYLE
                        ),
                        md=4
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div(
                                        [
                                            html.H5("📋 Live Multi-Model Delivery Feed", className="text-info fw-bold m-0"),
                                            dbc.Button("Clear Feed", id="btn-clear-feed", color="outline-danger", size="sm")
                                        ],
                                        className="d-flex justify-content-between align-items-center mb-3"
                                    ),
                                    dcc.Interval(id="live-stream-interval", interval=12000, n_intervals=0),
                                    dbc.Row(
                                        [
                                            dbc.Col(html.Div(id="live-orders-table-container"), md=7),
                                            dbc.Col(
                                                html.Div(
                                                    [
                                                        html.H6("🔍 Delivery Details Inspection", className="text-warning fw-bold mb-3 border-bottom border-secondary pb-2"),
                                                        html.Div(
                                                            id="order-detail-panel",
                                                            children=html.P("Click any order row to view origin, destination, customer & fulfillment type.", className="text-muted small italic")
                                                        )
                                                    ],
                                                    style={
                                                        "backgroundColor": "#0d1117", 
                                                        "padding": "15px", 
                                                        "border": "1px solid #30363d",
                                                        "borderRadius": "8px",
                                                        "height": "100%",
                                                        "minHeight": "250px"
                                                    }
                                                ),
                                                md=5
                                            )
                                        ],
                                        className="g-2"
                                    )
                                ]
                            ),
                            style=CARD_STYLE
                        ),
                        md=8
                    )
                ],
                className="g-3"
            )
        ]
    )

# ---------------------------------------------------------
# CALLBACK: MANUAL TRIGGER
# ---------------------------------------------------------
@app.callback(
    Output("simulation-trigger-output", "children"),
    Input("btn-trigger-simulation", "n_clicks"),
    prevent_initial_call=True
)
def manual_trigger(n_clicks):
    new_order, is_success, cost = generate_random_order()
    orders_history.insert(0, new_order)
    if len(orders_history) > 15:
        orders_history.pop()

    sim_state["stockout_events"] += 1
    if is_success:
        sim_state["successful_dispatches"] += 1
    else:
        sim_state["rejections"] += 1
    sim_state["total_cost_vnd"] += cost

    return dbc.Alert(
        [
            html.Strong(f"🚀 Triggered [{new_order['Model']}] - {new_order['Order ID']}! "),
            html.Span(f"Route: {new_order['Origin']} ➔ {new_order['Destination']}", className="text-light")
        ],
        color="success",
        dismissable=True,
        className="py-2 mb-0 small shadow-sm"
    )

# ---------------------------------------------------------
# CALLBACK: UPDATE TABLE & METRICS
# ---------------------------------------------------------
@app.callback(
    [
        Output("live-orders-table-container", "children"),
        Output("metric-stockout", "children"),
        Output("metric-success", "children"),
        Output("metric-rejections", "children"),
        Output("metric-cost", "children")
    ],
    [Input("live-stream-interval", "n_intervals"), Input("btn-clear-feed", "n_clicks")]
)
def update_dashboard(n, clear_clicks):
    ctx = callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else ""

    if triggered_id == "btn-clear-feed":
        orders_history.clear()
        sim_state["stockout_events"] = 0
        sim_state["successful_dispatches"] = 0
        sim_state["rejections"] = 0
        sim_state["total_cost_vnd"] = 0

    elif triggered_id == "live-stream-interval":
        new_order, is_success, cost = generate_random_order()
        orders_history.insert(0, new_order)
        if len(orders_history) > 15:
            orders_history.pop()

        sim_state["stockout_events"] += 1
        if is_success:
            sim_state["successful_dispatches"] += 1
        else:
            sim_state["rejections"] += 1
        sim_state["total_cost_vnd"] += cost

    if not orders_history:
        table_content = html.P("No delivery operations recorded yet.", className="text-muted text-center py-4 small")
    else:
        df = pd.DataFrame(orders_history)
        table_content = dash_table.DataTable(
            id='live-orders-table',
            data=df.to_dict('records'),
            columns=[
                {"name": "Time", "id": "Time"},
                {"name": "Order ID", "id": "Order ID"},
                {"name": "Type", "id": "Model"},
                {"name": "Status", "id": "Decision"}
            ],
            style_header={'backgroundColor': '#21262d', 'color': '#58a6ff', 'fontWeight': 'bold', 'border': 'none', 'fontSize': '11px'},
            style_cell={'backgroundColor': '#161b22', 'color': 'white', 'textAlign': 'left', 'padding': '6px', 'fontSize': '11px', 'border': '1px solid #30363d'},
            style_table={'overflowX': 'auto'},
            row_selectable='single',
            selected_rows=[]
        )

    cost_val = sim_state["total_cost_vnd"]
    cost_str = f"{cost_val / 1_000_000:.2f}M ₫" if cost_val >= 1_000_000 else f"{cost_val:,.0f} ₫"

    return (
        table_content,
        str(sim_state["stockout_events"]),
        str(sim_state["successful_dispatches"]),
        str(sim_state["rejections"]),
        cost_str
    )

# ---------------------------------------------------------
# CALLBACK: INSPECT ORDER DETAILS
# ---------------------------------------------------------
@app.callback(
    Output("order-detail-panel", "children"),
    [Input("live-orders-table", "selected_rows"), Input("live-orders-table", "data")]
)
def display_order_details(selected_rows, table_data):
    if not selected_rows or not table_data:
        return html.P("Click any order row from the table to inspect details here.", className="text-muted small italic")
    
    row_idx = selected_rows[0]
    if row_idx >= len(table_data):
        return html.P("Select a valid row.", className="text-muted small")
    
    order = table_data[row_idx]
    decision_color = "text-success" if "EXPRESS" in order['Decision'] or "BYPASS" in order['Decision'] else "text-danger"

    return html.Div(
        [
            html.Div([html.Strong("Order ID: "), html.Span(order['Order ID'], className="text-info fw-bold")]),
            html.Div([html.Strong("Timestamp: "), html.Span(order['Time'])]),
            html.Div([html.Strong("Model Type: "), html.Span(order['Model'], className="text-warning")]),
            html.Hr(className="border-secondary my-2"),
            html.Div([html.Strong("Product SKU: "), html.Span(order['SKU'])]),
            html.Div([html.Strong("Customer Tier: "), html.Span(order['Tier'])]),
            html.Div([html.Strong("Origin (Điểm đi): "), html.Span(order['Origin'], className="text-light")]),
            html.Div([html.Strong("Destination (Điểm đến): "), html.Span(order['Destination'], className="text-light")]),
            html.Div([html.Strong("Distance: "), html.Span(order['Distance'])]),
            html.Div([html.Strong("Shipping Cost: "), html.Span(order['Cost'], className="text-success")]),
            html.Hr(className="border-secondary my-2"),
            html.Div([html.Strong("Engine Decision: "), html.Div(order['Decision'], className=f"fw-bold {decision_color} mt-1")])
        ],
        style={"fontSize": "13px", "lineHeight": "1.6"}
    )


if __name__ == "__main__":
    app.run(debug=True, port=8050)