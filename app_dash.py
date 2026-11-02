import dash
from dash import html, dcc, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import requests
import pandas as pd

API_BASE_URL = "http://127.0.0.1:8000"

# Initialize Dash application with Bootstrap Dark/Slate theme
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    title="Autonomous Logistics Engine MVP"
)

# ---------------------------------------------------------
# UI COMPONENTS SETUP
# ---------------------------------------------------------

# Header Component
header = dbc.Row(
    dbc.Col(
        [
            html.H2("🚚 Autonomous Logistics Routing & Dispatch Engine", className="text-white fw-bold mt-3"),
            html.P("Proof of Concept (PoC) — Margin Evaluation, VIP Bypass & Automated 3PL Dispatch", className="text-muted"),
            html.Hr(className="my-3")
        ]
    )
)

# Tab 1: Stockout Simulation Form
tab1_content = dbc.Card(
    dbc.CardBody(
        [
            html.H5("Simulate New Stockout Alert", className="card-title text-primary fw-bold mb-4"),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Label("Order ID"),
                            dbc.Input(id="input-order-id", type="text", value="ORD-10088"),
                            html.Br(),
                            dbc.Label("Out-of-Stock Item SKU"),
                            dbc.Select(
                                id="input-item-sku",
                                options=[
                                    {"label": "SKU-BEER-01", "value": "SKU-BEER-01"},
                                    {"label": "SKU-WINE-05", "value": "SKU-WINE-05"},
                                    {"label": "SKU-SNACK-10", "value": "SKU-SNACK-10"},
                                ],
                                value="SKU-BEER-01"
                            ),
                            html.Br(),
                            dbc.Label("Requesting Store (Out of Stock)"),
                            dbc.Select(
                                id="input-req-store",
                                options=[
                                    {"label": "STORE-01 (District 1)", "value": "STORE-01"},
                                    {"label": "STORE-02 (Thu Duc)", "value": "STORE-02"},
                                    {"label": "STORE-03 (Tan Binh)", "value": "STORE-03"},
                                ],
                                value="STORE-01"
                            ),
                            html.Br(),
                            dbc.Label("Fulfilling Store (Surplus Stock)"),
                            dbc.Select(
                                id="input-ful-store",
                                options=[
                                    {"label": "STORE-01 (District 1)", "value": "STORE-01"},
                                    {"label": "STORE-02 (Thu Duc)", "value": "STORE-02"},
                                    {"label": "STORE-03 (Tan Binh)", "value": "STORE-03"},
                                ],
                                value="STORE-02"
                            ),
                            html.Br(),
                            dbc.Label("Order Value (VND)"),
                            dbc.Input(id="input-order-value", type="number", value=500000, step=50000),
                        ],
                        md=6
                    ),
                    dbc.Col(
                        [
                            dbc.Label("Item Profit Margin (VND)"),
                            dbc.Input(id="input-profit-margin", type="number", value=35000, step=5000),
                            html.Br(),
                            dbc.Label("Quantity (Items Count)"),
                            dbc.Input(id="input-items-count", type="number", value=1, min=1),
                            html.Br(),
                            dbc.Label("Distance Between Stores (km)"),
                            dbc.Input(id="input-distance", type="number", value=5.5, step=0.5),
                            html.Br(),
                            dbc.Label("Customer Loyalty Tier"),
                            dbc.Select(
                                id="input-customer-tier",
                                options=[
                                    {"label": "BRONZE Tier", "value": "BRONZE"},
                                    {"label": "SILVER Tier", "value": "SILVER"},
                                    {"label": "GOLD Tier", "value": "GOLD"},
                                    {"label": "PLATINUM Tier", "value": "PLATINUM"},
                                ],
                                value="BRONZE"
                            ),
                            html.Br(),
                            dbc.Checkbox(
                                id="input-service-recovery",
                                label="Service Recovery Order (VIP Bypass Override)",
                                value=False,
                                className="text-warning mt-2"
                            ),
                        ],
                        md=6
                    )
                ]
            ),
            html.Br(),
            dbc.Button("Run Autonomous Dispatch Engine", id="btn-submit-stockout", color="primary", className="w-100 fw-bold py-2"),
            html.Br(), html.Br(),
            html.Div(id="evaluation-output-container")
        ]
    ),
    className="mt-3 border-secondary"
)

# Tab 2: Decision Logs Table
tab2_content = dbc.Card(
    dbc.CardBody(
        [
            dbc.Row(
                [
                    dbc.Col(html.H5("Historical Routing & Transfer Decisions", className="card-title text-info fw-bold"), md=9),
                    dbc.Col(dbc.Button("Refresh Logs", id="btn-refresh-logs", color="outline-info", size="sm", className="float-end"), md=3)
                ]
            ),
            html.Br(),
            html.Div(id="logs-table-container")
        ]
    ),
    className="mt-3 border-secondary"
)

# Tab 3: KPI Leaderboard
tab3_content = dbc.Card(
    dbc.CardBody(
        [
            html.H5("Gamified Store KPI Ranking", className="card-title text-warning fw-bold mb-3"),
            html.P("Stores earn points for successfully solving stockout events without margin loss.", className="text-muted"),
            dash_table.DataTable(
                data=[
                    {"Store ID": "STORE-01", "Store Name": "District 1 Flagship Hub", "KPI Points": 180, "Tier Status": "🥇 Top Performer"},
                    {"Store ID": "STORE-02", "Store Name": "Thu Duc Express Store", "KPI Points": 150, "Tier Status": "🥈 On Target"},
                    {"Store ID": "STORE-03", "Store Name": "Tan Binh Retail Center", "KPI Points": 110, "Tier Status": "🥉 On Target"}
                ],
                columns=[{"name": i, "id": i} for i in ["Store ID", "Store Name", "KPI Points", "Tier Status"]],
                style_header={'backgroundColor': '#2c3e50', 'color': 'white', 'fontWeight': 'bold'},
                style_cell={'backgroundColor': '#1a252f', 'color': 'white', 'textAlign': 'left', 'padding': '12px'},
                style_table={'overflowX': 'auto'}
            )
        ]
    ),
    className="mt-3 border-secondary"
)

# Layout Setup
app.layout = dbc.Container(
    [
        header,
        dbc.Tabs(
            [
                dbc.Tab(tab1_content, label="🚀 Trigger Stockout Event", tab_id="tab-1"),
                dbc.Tab(tab2_content, label="📜 Transfer Decision Logs", tab_id="tab-2"),
                dbc.Tab(tab3_content, label="🏆 Store KPI Leaderboard", tab_id="tab-3"),
            ],
            id="main-tabs",
            active_tab="tab-1"
        )
    ],
    fluid=True,
    className="px-4"
)

# ---------------------------------------------------------
# CALLBACK LOGIC (Event-Driven State Handling)
# ---------------------------------------------------------

# Callback 1: Handle Stockout Form Submission
@app.callback(
    Output("evaluation-output-container", "children"),
    Input("btn-submit-stockout", "n_clicks"),
    State("input-order-id", "value"),
    State("input-item-sku", "value"),
    State("input-req-store", "value"),
    State("input-ful-store", "value"),
    State("input-order-value", "value"),
    State("input-profit-margin", "value"),
    State("input-items-count", "value"),
    State("input-distance", "value"),
    State("input-customer-tier", "value"),
    State("input-service-recovery", "value"),
    prevent_initial_call=True
)
def process_stockout_evaluation(n_clicks, order_id, item_sku, req_store, ful_store, order_val, profit_margin, items_cnt, distance, tier, service_recovery):
    payload = {
        "order_id": order_id,
        "item_sku": item_sku,
        "requesting_store_id": req_store,
        "fulfilling_store_id": ful_store,
        "order_value": float(order_val),
        "profit_margin": float(profit_margin),
        "items_count": int(items_cnt),
        "distance_km": float(distance),
        "customer_tier": tier,
        "is_service_recovery": bool(service_recovery)
    }

    try:
        res = requests.post(f"{API_BASE_URL}/api/v1/routing/evaluate", json=payload)
        if res.status_code == 200:
            data = res.json()
            eval_data = data["evaluation"]

            status_color = "success" if eval_data["is_3pl_booked"] else "danger"
            
            return dbc.Alert(
                [
                    html.H5(f"✅ Evaluation Complete | Alert ID: #{data['alert_id']}", className="alert-heading text-white fw-bold"),
                    html.Hr(),
                    dbc.Row(
                        [
                            dbc.Col(html.Div([html.Small("Decision"), html.H4(eval_data["decision"], className="text-info fw-bold")]), md=3),
                            dbc.Col(html.Div([html.Small("Net Profit"), html.H4(f"{eval_data['net_profit']:,.0f} VND")]), md=3),
                            dbc.Col(html.Div([html.Small("Shipping Cost"), html.H4(f"{eval_data['shipping_cost']:,.0f} VND")]), md=3),
                            dbc.Col(html.Div([html.Small("3PL Dispatch"), html.H4("BOOKED" if eval_data["is_3pl_booked"] else "REJECTED", className=f"text-{status_color} fw-bold")]), md=3),
                        ]
                    ),
                    html.Br(),
                    html.P([html.Strong("Tracking Code: "), html.Code(eval_data["tracking_code"] or "N/A", className="fs-5 text-warning")]),
                    html.P([html.Strong("Engine Reason: "), eval_data["reason"]])
                ],
                color="dark",
                className="border border-secondary p-3 mt-3"
            )
        else:
            return dbc.Alert("Backend engine error occurred.", color="danger")
    except Exception as e:
        return dbc.Alert(f"Connection Error: Could not connect to FastAPI at {API_BASE_URL}. Details: {e}", color="danger")


# Callback 2: Load Transfer Logs Table
@app.callback(
    Output("logs-table-container", "children"),
    [Input("btn-refresh-logs", "n_clicks"), Input("main-tabs", "active_tab")]
)
def update_logs_table(n_clicks, active_tab):
    if active_tab != "tab-2":
        return dash.no_update

    try:
        res = requests.get(f"{API_BASE_URL}/api/v1/logs")
        if res.status_code == 200:
            logs = res.json()
            if not logs:
                return dbc.Alert("No transfer decisions logged yet.", color="info")

            df = pd.DataFrame(logs)
            return dash_table.DataTable(
                data=df.to_dict('records'),
                columns=[{"name": col, "id": col} for col in df.columns],
                style_header={'backgroundColor': '#2c3e50', 'color': 'white', 'fontWeight': 'bold'},
                style_cell={'backgroundColor': '#1a252f', 'color': 'white', 'textAlign': 'left', 'padding': '10px'},
                style_table={'overflowX': 'auto'},
                page_size=10
            )
        return dbc.Alert("Failed to retrieve logs from server.", color="warning")
    except Exception as e:
        return dbc.Alert(f"Connection Error: {e}", color="danger")


# ---------------------------------------------------------
# ENTRYPOINT
# ---------------------------------------------------------
if __name__ == "__main__":
    app.run_server(debug=True, port=8050)
