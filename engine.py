import json
import random

# Load configuration from config.json
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

def evaluate_stockout_transfer(order_value, profit_margin, distance_km, items_count, customer_tier, is_service_recovery=False):
    """
    Core Rules Engine: Evaluates stockout transfer routing, net profit, 
    customer tier bypass rules, and triggers automated 3PL dispatch.
    """
    costs = config["logistics_costs"]
    bypass_rules = config["tier_bypass_rules"]
    
    truck_cost_per_km = costs["truck_cost_per_km"]
    express_base_cost = costs["express_3pl_base_cost"]
    min_bulk_items = costs["min_bulk_items_threshold"]
    
    # Rule 1: Check if volume is large enough for Bulk (Milk Run) truck delivery
    if items_count >= min_bulk_items:
        shipping_cost = distance_km * (truck_cost_per_km / 2) # Shared truck cost
        decision = "BULK_MILK_RUN"
        net_profit = profit_margin - shipping_cost
        kpi_points = 50
        is_booked = False
        tracking_code = None
        reason = "Sufficient volume for shared truck delivery (Milk Run)."
        
    else:
        # Rule 2: Evaluate Express / Drop-and-Ship scenario using 3PL (e.g., AhaMove)
        shipping_cost = express_base_cost + (distance_km * 5000)
        net_profit = profit_margin - shipping_cost
        
        # Get customer tier policy
        tier_rule = bypass_rules.get(customer_tier, {"allow_margin_loss": False})
        allow_loss = tier_rule.get("allow_margin_loss", False)
        max_loss = tier_rule.get("max_allowed_loss", 0)
        
        if net_profit >= 0:
            # Standard positive profit case
            decision = "DROP_SHIP_EXPRESS"
            kpi_points = 30
            is_booked = True
            tracking_code = f"AHM-EXPRESS-{random.randint(10000, 99999)}"
            reason = "Positive net profit. Automatic 3PL express dispatch triggered."
            
        elif is_service_recovery or (allow_loss and abs(net_profit) <= max_loss):
            # VIP Tier or Service Recovery Bypass case
            decision = "VIP_BYPASS_EXPRESS"
            kpi_points = 10  # Reduced points due to margin subsidy
            is_booked = True
            tracking_code = f"AHM-VIP-{random.randint(10000, 99999)}"
            reason = f"Margin loss accepted due to {customer_tier} tier / Service Recovery bypass policy."
            
        else:
            # Negative profit exceeds tolerance -> Lock express shipping
            decision = "SAVE_THE_SALE_OR_REJECT"
            shipping_cost = 0.0
            net_profit = profit_margin
            kpi_points = 0
            is_booked = False
            tracking_code = None
            reason = "Negative net profit exceeds tier tolerance. Express shipping locked."

    return {
        "decision": decision,
        "shipping_cost": round(shipping_cost, 2),
        "net_profit": round(net_profit, 2),
        "is_3pl_booked": is_booked,
        "tracking_code": tracking_code,
        "kpi_points_awarded": kpi_points,
        "reason": reason
    }

# Quick test if run directly
if __name__ == "__main__":
    test_result = evaluate_stockout_transfer(
        order_value=500000, 
        profit_margin=40000, 
        distance_km=5.0, 
        items_count=1, 
        customer_tier="PLATINUM"
    )
    print("Test Evaluation Result:", json.dumps(test_result, indent=4, ensure_ascii=False))
