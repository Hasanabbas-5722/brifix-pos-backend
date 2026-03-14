from flask import Blueprint, jsonify, request
from app.extensions import db
from app.utils.logger import logger
from flask_jwt_extended import jwt_required, get_jwt
from bson import ObjectId
import datetime

bp = Blueprint('payments', __name__, url_prefix='/api/payments')

@bp.route('/', methods=['POST'])
@jwt_required()
def create_payment():
    """Record a payment (can be for an order or a credit payoff)."""
    try:
        tenant_id = get_jwt()['tenant_id']
        data = request.get_json()
        
        amount = float(data.get('amount', 0))
        customer_id = data.get('customerId')
        order_id = data.get('orderId') # Optional: link to a specific order
        
        payment_record = {
            "tenant_id": tenant_id,
            "customerId": customer_id,
            "orderId": order_id,
            "amount": amount,
            "method": data.get('method', 'cash'),
            "type": data.get('type', 'sale'), # 'sale', 'credit_payoff', 'refund'
            "note": data.get('note', ''),
            "createdAt": datetime.datetime.now().isoformat()
        }
        
        # Insert payment record
        result = db.payments.insert_one(payment_record)
        payment_record['id'] = str(result.inserted_id)
        
        # If this is a credit payoff, we should update the related order(s) or just the summary
        # If order_id is provided, update that specific order's amountPaid/amountDue
        if order_id:
            db.orders.update_one(
                {"_id": ObjectId(order_id), "tenant_id": tenant_id},
                {
                    "$inc": {"amountPaid": amount, "amountDue": -amount},
                    "$set": {"lastUpdated": datetime.datetime.now().isoformat()}
                }
            )
            # Update payment status if now fully paid
            order = db.orders.find_one({"_id": ObjectId(order_id)})
            if order and order.get('amountDue', 0) <= 0:
                db.orders.update_one({"_id": ObjectId(order_id)}, {"$set": {"paymentStatus": "paid"}})

        # If it's a general customer credit payoff (no specific order), 
        # normally in advanced systems we'd apply it to the oldest bills first (FIFO)
        # For now, we'll let the user link to an order for clarity.

        if '_id' in payment_record: del payment_record['_id']
        
        return jsonify({
            "status": "success",
            "message": "Payment recorded successfully",
            "data": payment_record
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating payment: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route('/customer/<customer_id>', methods=['GET'])
@jwt_required()
def get_customer_payments(customer_id):
    """Get all payments made by a customer."""
    try:
        tenant_id = get_jwt()['tenant_id']
        payments = list(db.payments.find({
            "tenant_id": tenant_id,
            "customerId": customer_id
        }).sort("createdAt", -1))
        
        for p in payments:
            p['id'] = str(p.pop('_id'))
            
        return jsonify({
            "status": "success",
            "data": payments
        }), 200
    except Exception as e:
        logger.error(f"Error fetching customer payments: {e}")
        return jsonify({"status": "error", "message": "Failed to fetch payments"}), 500
