from flask import Blueprint, jsonify
from app.extensions import db
from app.utils.logger import logger
from flask_jwt_extended import jwt_required, get_jwt
import datetime

bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')

@bp.route('/stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    """Retrieve overview statistics for the POS dashboard."""
    try:
        tenant_id = get_jwt()['tenant_id']
        
        # For an MVP, we often generate quick aggregates or return seeded mock structures
        # In a full app, these would be complex aggregation pipelines over Orders & Products
        
        # Calculate base stats
        today = datetime.datetime.now()
        start_of_day = today.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        
        today_orders = list(db.orders.find({
            "createdAt": {"$gte": start_of_day},
            "tenant_id": tenant_id
        }))
        today_revenue = sum(order.get('total', 0) for order in today_orders)
        
        # We can simulate SALES_DATA, MONTHLY_REVENUE, TOP_PRODUCTS based on db or seed values.
        # Below is a structural return matching frontend expectations.
        return jsonify({
            "status": "success",
            "data": {
                "today_revenue": today_revenue,
                "today_orders": len(today_orders),
                "avg_order_value": (today_revenue / len(today_orders)) if today_orders else 0,
                
                # Frontend specific mock structures for charts
                "sales_data": [
                    {"date": (today - datetime.timedelta(days=i)).strftime('%Y-%m-%d'), "revenue": 1000 + (100 * i), "orders": 50 + i} 
                    for i in range(7, -1, -1)
                ],
                "monthly_revenue": [
                    {"month": "Jan", "revenue": 45000},
                    {"month": "Feb", "revenue": 52000},
                    {"month": "Mar", "revenue": 58000}
                ],
                "top_products": [
                    # If we had real aggregation: db.orders.aggregate([{$unwind: "$items"}, {$group: {_id: "$items.product.name", total: {$sum: "$items.quantity"}}}])
                    {"name": "Coffee", "revenue": 500, "units": 100},
                    {"name": "Tea", "revenue": 200, "units": 100}
                ]
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {e}")
        return jsonify({"status": "error", "message": "Failed to fetch dashboard statistics"}), 500
