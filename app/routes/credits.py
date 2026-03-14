from flask import Blueprint, jsonify, request
from app.extensions import db
from app.utils.logger import logger
from flask_jwt_extended import jwt_required, get_jwt
from bson import ObjectId

bp = Blueprint('credits', __name__, url_prefix='/api/credits')

@bp.route('/customer-summary', methods=['GET'])
@jwt_required()
def get_customer_credit_summary():
    """Get total credit and paid summary per customer."""
    try:
        tenant_id = get_jwt()['tenant_id']
        
        # Aggregate orders by customer to get total paid and total due
        pipeline = [
            {"$match": {"tenant_id": tenant_id, "customer": {"$ne": None}}},
            {"$group": {
                "_id": "$customer.id",
                "customerName": {"$first": "$customer.name"},
                "customerEmail": {"$first": "$customer.email"},
                "totalAmount": {"$sum": "$total"},
                "totalPaid": {"$sum": "$amountPaid"},
                "totalDue": {"$sum": "$amountDue"},
                "orderCount": {"$sum": 1}
            }},
            {"$match": {"totalDue": {"$gt": 0}}}, # Only show customers with pending credit
            {"$sort": {"totalDue": -1}}
        ]
        
        results = list(db.orders.aggregate(pipeline))
        
        # Clean up output
        for res in results:
            res['customerId'] = res.pop('_id')
            
        return jsonify({
            "status": "success",
            "data": results
        }), 200
    except Exception as e:
        logger.error(f"Error fetching customer credit summary: {e}")
        return jsonify({"status": "error", "message": "Failed to fetch summary"}), 500

@bp.route('/customer/<customer_id>/bills', methods=['GET'])
@jwt_required()
def get_customer_bills(customer_id):
    """Get bill-wise credit details for a specific customer."""
    try:
        tenant_id = get_jwt()['tenant_id']
        
        # Fetch all orders for this customer that have amountDue > 0
        orders = list(db.orders.find({
            "tenant_id": tenant_id,
            "customer.id": customer_id,
            "amountDue": {"$gt": 0}
        }).sort("createdAt", -1))
        
        for order in orders:
            order['id'] = str(order.pop('_id'))
            
        return jsonify({
            "status": "success",
            "data": orders
        }), 200
    except Exception as e:
        logger.error(f"Error fetching customer bills: {e}")
        return jsonify({"status": "error", "message": "Failed to fetch bills"}), 500

@bp.route('/customer/<customer_id>', methods=['GET'])
@jwt_required()
def get_customer_credit(customer_id):
    """Get credit summary for a single customer."""
    try:
        tenant_id = get_jwt()['tenant_id']
        
        pipeline = [
            {"$match": {"tenant_id": tenant_id, "customer.id": customer_id}},
            {"$group": {
                "_id": "$customer.id",
                "totalBilled": {"$sum": "$total"},
                "totalPaid": {"$sum": "$amountPaid"},
                "totalDue": {"$sum": "$amountDue"}
            }}
        ]
        
        result = list(db.orders.aggregate(pipeline))
        summary = result[0] if result else {
            "totalBilled": 0,
            "totalPaid": 0,
            "totalDue": 0
        }
        
        return jsonify({
            "status": "success",
            "data": summary
        }), 200
    except Exception as e:
        logger.error(f"Error fetching customer credit: {e}")
        return jsonify({"status": "error", "message": "Failed to fetch customer credit"}), 500

@bp.route('/summary', methods=['GET'])
@jwt_required()
def get_global_credit_summary():
    """Get global credit summary for the tenant."""
    try:
        tenant_id = get_jwt()['tenant_id']
        
        pipeline = [
            {"$match": {"tenant_id": tenant_id}},
            {"$group": {
                "_id": None,
                "totalCredit": {"$sum": "$amountDue"},
                "totalPaid": {"$sum": "$amountPaid"},
                "totalOrders": {"$sum": 1}
            }}
        ]
        
        result = list(db.orders.aggregate(pipeline))
        summary = result[0] if result else {
            "totalCredit": 0,
            "totalPaid": 0,
            "totalOrders": 0
        }
        if "_id" in summary: del summary["_id"]
        
        return jsonify({
            "status": "success",
            "data": summary
        }), 200
    except Exception as e:
        logger.error(f"Error fetching global credit summary: {e}")
        return jsonify({"status": "error", "message": "Failed to fetch summary"}), 500
