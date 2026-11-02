import dash
from dash import html, dcc, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import requests
import pandas as pd
from datetime import datetime
import random
import threading

API_BASE_URL = "http://127.0.0.1:8000"

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    title="Autonomous Logistics & Dispatch Engine",
    suppress_callback_exceptions=True
)

CARD_STYLE = {
    "backgroundColor": "#161b22",
    "border": "1px solid #30363d",
    "borderRadius": "10px",
    "boxShadow": "0 4px 6px rgba(0, 0, 0, 0.3)"
}

# ---------------- NAVBAR ----------------
navbar = dbc.Navbar(
    dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(html.H4("🚚 SmartLogistics Engine", className="text-white fw-bold mb-0")),
                    dbc.Col(html.Span("Autonomous Routing & Dispatch PoC", className="text-muted ms-3 fs-6"), className="d-none d-md-block")
                ],
                align="center",
                className="g-0",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Nav(
                            [
                                dbc.NavItem(dbc.NavLink("📊 Overview", href="#", active=True, className="text-white")),
                                dbc.NavItem(dbc.NavLink("📜 Logs", href="#", className="text-muted")),
                                dbc.NavItem(dbc.NavLink("🔴 Live Orders", href="#", className="text-danger fw-bold")),
                            ],
                            navbar=True,
                        ),
                        className="d-none d-lg-block"
                    ),
                    dbc.Col(
                        dbc.Button(
                            "⚡ Trigger Event",
                            id="btn-trigger-simulation",
                            color="danger",
                            size="sm",
                            className="fw-bold px-3 py-1 shadow-sm",
                            title="Manual Simulation Trigger"
                        ),
                        className="ms-3"
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

# ---------------- HEADER + METRICS ----------------
overview_header = html.Div(
    [
        html.H3("Logistics Operation Command Center", className="text-white fw-bold mt-3"),
        html.P("Real-time automated route optimization, shipping cost evaluation, and margin protection rules engine.", className="text-muted"),
        html.Div(id="simulation-trigger-output", className="mb-2"),
        html.Hr(className="border-secondary")
    ]
)

metrics_row = dbc.Row(
    [
        dbc.Col(dbc.Card(dbc.CardBody([html.Small("TOTAL STOCKOUT / REQUESTS", className="text-muted fw-bold"), html.H3(id="metric-stockout", children="0", className="text-info fw-bold mt-1")]), style=CARD_STYLE), md=3),
        dbc.Col(dbc.Card(dbc.CardBody([html.Small("SUCCESSFUL DISPATCHES", className="text-muted fw-bold"), html.H3(id="metric-success", children="0", className="text-success fw-bold mt-1")]), style=CARD_STYLE), md=3),
        dbc.Col(dbc.Card(dbc.CardBody([html.Small("3PL REJECTIONS", className="text-muted fw-bold"), html.H3(id="metric-rejections", children="0", className="text-danger fw-bold mt-1")]), style=CARD_STYLE), md=3),
        dbc.Col(dbc.Card(dbc.CardBody([html.Small("TOTAL SHIPPING COST", className="text-muted fw-bold"), html.H3(id="metric-cost", children="0 ₫", className="text-success fw-bold mt-1")]), style=CARD_STYLE), md=3),
    ],
    className="mb-4 g-3"
)

# ---------------- MAP ----------------
network_map_figure = go.Figure()
milk_run_stops = [
    ("Main Warehouse", 10.8231, 106.6297),
    ("Store - District 1", 10.7769, 106.7009),
    ("Store - Tan Binh", 10.8015, 106.6520),
    ("Store - Thu Duc", 10.8494, 106.7537),
    ("Main Warehouse", 10.8231, 106.6297),
]
network_map_figure.add_trace(go.Scattergeo(
    lat=[s[1] for s in milk_run_stops],
    lon=[s[2] for s in milk_run_stops],
    mode="lines",
    line={"width": 3, "color": "#58a6ff"},
    name="Milk Run Route",
    hoverinfo="skip"
))
network_map_figure.add_trace(go.Scattergeo(
    lat=[10.8231, 10.7769, 10.8015, 10.8494],
    lon=[106.6297, 106.7009, 106.6520, 106.7537],
    mode="markers+text",
    marker={"size": [18, 13, 13, 13], "color": ["#f85149", "#3fb950", "#3fb950", "#3fb950"]},
    text=["Main Warehouse", "Store · District 1", "Store · Tan Binh", "Store · Thu Duc"],
    textposition="top right",
    customdata=["Warehouse", "Store", "Store", "Store"],
    hovertemplate="%{text}<br>%{customdata}<extra></extra>",
    name="Warehouse & Stores"
))
network_map_figure.update_layout(
    geo={
        "scope": "asia",
        "projection": {"type": "mercator"},
        "center": {"lat": 10.815, "lon": 106.69},
        "zoom": 5.7,
        "showland": True,
        "landcolor": "#0d1117",
        "showlakes": True,
        "lakecolor": "#0d1117",
        "showocean": True,
        "oceancolor": "#0d1117",
        "showcoastlines": True,
        "coastlinecolor": "#30363d",
        "countrycolor": "#30363d",
        "countrywidth": 0.7,
        "subunitcolor": "#30363d"
    },
    margin={"l": 0, "r": 0, "t": 0, "b": 0},
    paper_bgcolor="#161b22",
    plot_bgcolor="#161b22",
    font={"color": "#c9d1d9"},
    legend={"orientation": "h", "y": 0, "x": 0.02}
)

network_map = dbc.Card(
    dbc.CardBody([
        html.H5("🗺️ Live Network Map", className="text-info fw-bold mb-1"),
        html.P("Main warehouse, retail stores across Ho Chi Minh City, and the Milk Run route.", className="text-muted small mb-2"),
        dcc.Graph(figure=network_map_figure, config={"displayModeBar": False, "responsive": True}, style={"height": "430px"})
    ]),
    style=CARD_STYLE,
    className="mb-3"
)

# ---------------- MAIN LAYOUT ----------------
simulation_and_ranking = dbc.Row(
    [
        dbc.Col(network_map, width=12),
        dbc.Col(
            [
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H5("🚨 Stockout & Replenishment Alerts", className="text-danger fw-bold mb-2"),
                            html.P("Inventory is consumed during the simulation. When a store runs out, supply evaluates a transfer from another store versus replenishment from the warehouse.", className="text-muted small mb-3"),
                            dcc.Interval(id="stockout-interval", interval=120000, n_intervals=0),
                            dash_table.DataTable(
                                id="stockout-alert-table",
                                data=[],
                                columns=[{"name": i, "id": i} for i in ["SKU", "Store", "Shortage", "Priority", "Supply Decision", "Supply Status"]],
                                style_header={'backgroundColor': '#21262d', 'color': 'white', 'fontWeight': 'bold', 'border': 'none'},
                                style_cell={'backgroundColor': '#161b22', 'color': 'white', 'textAlign': 'left', 'padding': '8px', 'fontSize': '12px', 'border': '1px solid #30363d', 'whiteSpace': 'normal', 'height': 'auto'},
                                style_table={'overflowX': 'auto'}
                            ),
                            html.Br(),
                            html.P("Transfers are preferred when stock is available and the route is cheaper; otherwise the warehouse supplies the store.", className="text-muted small mb-0")
                        ]
                    ),
                    style=CARD_STYLE
                )
            ],
            md=4
        ),
        dbc.Col(
            [
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.Div(
                                [
                                    html.H5("📋 Live OOS Replenishment Shipments", className="text-info fw-bold m-0"),
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
                                                html.H6("🔍 Replenishment Shipment Details", className="text-warning fw-bold mb-3 border-bottom border-secondary pb-2"),
                                                html.Div(
                                                    id="order-detail-panel",
                                                    children=html.P("Select a shipment supplying a store after a stockout to inspect its details.", className="text-muted small italic")
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
                )
            ],
            md=8
        )
    ],
    className="g-3 mb-5"
)

app.layout = html.Div(
    [
        navbar,
        dbc.Container(
            [overview_header, metrics_row, simulation_and_ranking],
            fluid=True,
            className="px-4 py-2"
        )
    ],
    style={"backgroundColor": "#0b0f19", "minHeight": "100vh", "color": "#c9d1d9"}
)

# ---------------- STATE & SIMULATION ----------------
sim_state = {
    "stockout_events": 0,
    "successful_dispatches": 0,
    "rejections": 0,
    "total_cost_vnd": 0
}

orders_history = []

inventory_stores = ["District 1 Hub", "Thu Duc Express", "Tan Binh Center"]
inventory_skus = ["SKU-LAPTOP-02", "SKU-PHONE-10", "SKU-EARBUDS-01"]
inventory = {
    (sku, store): random.randint(4, 8)
    for sku in inventory_skus for store in inventory_stores
}
warehouse_inventory = {sku: 30 for sku in inventory_skus}
stockout_alerts = []
pending_replenishments = []
stockout_state_lock = threading.Lock()


def advance_stockout_simulation():
    for pending in pending_replenishments[:]:
        sku, store, shortage = pending["sku"], pending["store"], pending["shortage"]
        choices = [
            (random.randint(15000, 22000), source)
            for source in inventory_stores
            if source != store and inventory[(sku, source)] >= shortage
        ]
        store_option = min(choices) if choices else None
        warehouse_option = (25000, "warehouse") if warehouse_inventory[sku] >= shortage else None

        if store_option and (not warehouse_option or store_option[0] <= warehouse_option[0]):
            cost, source = store_option
            inventory[(sku, source)] -= shortage
            decision = f"Transfer from {source} ({cost:,} ₫)"
            status = "Store transfer dispatched"
        elif warehouse_option:
            cost, source = warehouse_option
            warehouse_inventory[sku] -= shortage
            decision = f"Replenish from warehouse ({cost:,} ₫)"
            status = "Warehouse shipment dispatched"
        else:
            pending["row"].update({"Source": "Unavailable", "Supply Decision": "No source available", "Supply Status": "Awaiting stock"})
            continue

        inventory[(sku, store)] += shortage
        pending["row"].update({"Source": source if source != "warehouse" else "Warehouse", "Supply Decision": decision, "Supply Status": status})
        pending_replenishments.remove(pending)

    sku = random.choice(inventory_skus)
    store = random.choice(inventory_stores)
    key = (sku, store)
    inventory[key] = max(0, inventory[key] - random.randint(2, 5))
    already_pending = any(p["sku"] == sku and p["store"] == store for p in pending_replenishments)
    if inventory[key] == 0 and not already_pending:
        shortage = random.randint(5, 10)
        row = {
            "Time": datetime.now().strftime("%H:%M:%S"),
            "Shipment ID": f"REP-{random.randint(10000, 99999)}",
            "SKU": sku, "Store": store, "Shortage": f"{shortage} units",
            "Source": "Evaluating",
            "Priority": "🔴 Critical", "Supply Decision": "Evaluating sources",
            "Supply Status": "Stockout detected"
        }
        stockout_alerts.insert(0, row)
        pending_replenishments.append({"sku": sku, "store": store, "shortage": shortage, "row": row})
        if len(stockout_alerts) > 20:
            removed = stockout_alerts.pop()
            pending_replenishments[:] = [p for p in pending_replenishments if p["row"] is not removed]


def generate_random_order():
    skus = ["SKU-LAPTOP-01", "SKU-PHONE-05", "SKU-EARBUDS-10", "SKU-TABLET-02"]
    tiers = ["BRONZE", "SILVER", "GOLD", "PLATINUM"]
    stores = [("STORE-01 (District 1)", "STORE-02 (Thu Duc)"), ("STORE-02 (Thu Duc)", "STORE-03 (Tan Binh)"), ("STORE-03 (Tan Binh)", "STORE-01 (District 1)")]

    sku = random.choice(skus)
    tier = random.choice(tiers)
    req_s, ful_s = random.choice(stores)
    distance = round(random.uniform(2.5, 8.5), 1)
    shipping_cost = int(distance * 6000 + random.randint(15000, 35000))

    is_success = True if (tier in ["GOLD", "PLATINUM"] or shipping_cost < 50000) else random.choice([True, False])
    decision = "DROP_SHIP_EXPRESS" if is_success else "REJECT_UNPROFITABLE"
    if not is_success and tier == "PLATINUM":
        decision = "VIP_BYPASS_OVERRIDE"
        is_success = True

    ord_id = f"ORD-{random.randint(10000, 99999)}"
    timestamp = datetime.now().strftime("%H:%M:%S")

    return {
        "Time": timestamp,
        "Order ID": ord_id,
        "SKU Product": sku,
        "Tier": tier,
        "Route": f"{req_s} ➔ {ful_s}",
        "Distance": f"{distance} km",
        "Shipping Cost": f"{shipping_cost:,.0f} ₫",
        "Decision": decision
    }, is_success, shipping_cost

# ---------------- CALLBACKS ----------------
@app.callback(
    Output("stockout-alert-table", "data"),
    Input("stockout-interval", "n_intervals")
)
def update_stockout_alerts(_n):
    with stockout_state_lock:
        advance_stockout_simulation()
        return [dict(alert) for alert in stockout_alerts]


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
            html.Strong(f"🚀 Triggered Manual Order {new_order['Order ID']}! "),
            html.Span(f"Product: {new_order['SKU Product']} | Decision: {new_order['Decision']}", className="text-light")
        ],
        color="success",
        dismissable=True,
        className="py-2 mb-0 small shadow-sm"
    )


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
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else ""

    if triggered_id == "btn-clear-feed":
        with stockout_state_lock:
            stockout_alerts.clear()
            pending_replenishments.clear()
            sim_state["stockout_events"] = 0
            sim_state["successful_dispatches"] = 0
            sim_state["rejections"] = 0
            sim_state["total_cost_vnd"] = 0

    with stockout_state_lock:
        alerts_snapshot = [dict(alert) for alert in stockout_alerts]

    if not alerts_snapshot:
        table_content = html.P("No store replenishment shipments recorded yet.", className="text-muted text-center py-4 small")
    else:
        df = pd.DataFrame(alerts_snapshot)
        table_content = dash_table.DataTable(
            id='live-orders-table',
            data=df.to_dict('records'),
            columns=[
                {"name": "Time", "id": "Time"},
                {"name": "Shipment ID", "id": "Shipment ID"},
                {"name": "SKU", "id": "SKU"},
                {"name": "Destination Store", "id": "Store"},
                {"name": "Shortage", "id": "Shortage"},
                {"name": "Source", "id": "Source"},
                {"name": "Supply Status", "id": "Supply Status"}
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


@app.callback(
    Output("order-detail-panel", "children"),
    [Input("live-orders-table", "selected_rows"), Input("live-orders-table", "data")]
)
def display_order_details(selected_rows, table_data):
    if not selected_rows or not table_data:
        return html.P("Select a shipment supplying a store after a stockout to inspect its details.", className="text-muted small italic")

    row_idx = selected_rows[0]
    if row_idx >= len(table_data):
        return html.P("Select a valid order row.", className="text-muted small")

    order = table_data[row_idx]
    status_color = "text-success" if "dispatched" in order["Supply Status"].lower() else "text-warning"

    return html.Div(
        [
            html.Div([html.Strong("Shipment ID: "), html.Span(order['Shipment ID'], className="text-info fw-bold")]),
            html.Div([html.Strong("Timestamp: "), html.Span(order['Time'])]),
            html.Hr(className="border-secondary my-2"),
            html.Div([html.Strong("SKU: "), html.Span(order['SKU'], className="text-warning")]),
            html.Div([html.Strong("Destination Store: "), html.Span(order['Store'])]),
            html.Div([html.Strong("Shortage: "), html.Span(order['Shortage'])]),
            html.Div([html.Strong("Supply Source: "), html.Span(order['Source'])]),
            html.Hr(className="border-secondary my-2"),
            html.Div([html.Strong("Supply Decision: "), html.Div(order['Supply Decision'], className=f"fw-bold {status_color} mt-1")]),
            html.Div([html.Strong("Shipment Status: "), html.Span(order['Supply Status'], className=status_color)])
        ],
        style={"fontSize": "13px", "lineHeight": "1.6"}
    )

# ---------------- RUN ----------------
app.run(debug=False, port=8050, jupyter_mode="inline", jupyter_height=1000)