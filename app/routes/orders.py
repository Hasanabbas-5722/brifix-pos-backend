from flask import Blueprint, jsonify, request
from app.extensions import db
from app.utils.logger import logger
from bson import ObjectId
from flask_jwt_extended import jwt_required, get_jwt
import datetime

bp = Blueprint('orders', __name__, url_prefix='/api/orders')

@bp.route('/', methods=['GET'])
@jwt_required()
def get_orders():
    """Get all orders."""
    try:
        tenant_id = get_jwt()['tenant_id']
        orders = list(db.orders.find({"tenant_id": tenant_id}).sort("createdAt", -1))
        for order in orders:
            order['id'] = str(order.pop('_id'))
            
            # Sub-documents (like customer object inside order) might also have ObjectId _id
            if 'customer' in order and order['customer'] and '_id' in order['customer']:
                order['customer']['id'] = str(order['customer'].pop('_id'))
                
        return jsonify({
            "status": "success",
            "data": orders
        }), 200
    except Exception as e:
        logger.error(f"Error fetching orders: {e}")
        return jsonify({"status": "error", "message": "Failed to fetch orders"}), 500

@bp.route('/<order_id>', methods=['GET'])
@jwt_required()
def get_order(order_id):
    """Get a single order."""
    try:
        tenant_id = get_jwt()['tenant_id']
        order = db.orders.find_one({"_id": ObjectId(order_id), "tenant_id": tenant_id})
        if not order:
            return jsonify({"status": "error", "message": "Order not found"}), 404
            
        order['id'] = str(order.pop('_id'))
        
        return jsonify({
            "status": "success",
            "data": order
        }), 200
    except Exception as e:
        logger.error(f"Error fetching order: {e}")
        return jsonify({"status": "error", "message": "Failed to fetch order"}), 500

@bp.route('/summary', methods=['GET'])
@jwt_required()
def get_orders_summary():
    """Get summary of orders including total credit/due."""
    try:
        tenant_id = get_jwt()['tenant_id']
        pipeline = [
            {"$match": {"tenant_id": tenant_id}},
            {"$group": {
                "_id": None,
                "totalSales": {"$sum": "$total"},
                "totalPaid": {"$sum": "$amountPaid"},
                "totalDue": {"$sum": "$amountDue"},
                "orderCount": {"$sum": 1}
            }}
        ]
        result = list(db.orders.aggregate(pipeline))
        summary = result[0] if result else {
            "totalSales": 0,
            "totalPaid": 0,
            "totalDue": 0,
            "orderCount": 0
        }
        if "_id" in summary: del summary["_id"]
        
        return jsonify({
            "status": "success",
            "data": summary
        }), 200
    except Exception as e:
        logger.error(f"Error fetching orders summary: {e}")
        return jsonify({"status": "error", "message": "Failed to fetch summary"}), 500

@bp.route('/', methods=['POST'])
@jwt_required()
def create_order():
    """Create a new order."""
    try:
        tenant_id = get_jwt()['tenant_id']
        data = request.get_json()
        if not data or 'items' not in data:
            return jsonify({"status": "error", "message": "Invalid data, items are required"}), 400
            
        # Generate an Order Number e.g. ORD-YYYYMMDD-XXXX (scoped by tenant)
        order_count = db.orders.count_documents({"tenant_id": tenant_id}) + 1
        date_str = datetime.datetime.now().strftime("%Y%m%d")
        order_num = f"ORD-{date_str}-{order_count:04d}"
        
        total = float(data.get('total', 0))
        amount_paid = float(data.get('amountPaid', total))
        amount_due = max(0, total - amount_paid)
        
        payment_status = "paid"
        if amount_due > 0:
            payment_status = "partial"
        if amount_paid == 0:
            payment_status = "unpaid"

        new_order = {
            "orderNumber": order_num,
            "customer": data.get('customer', None),
            "items": data.get('items', []),
            "subtotal": float(data.get('subtotal', 0)),
            "discount": float(data.get('discount', 0)),
            "tax": float(data.get('tax', 0)),
            "total": total,
            "paymentMethod": data.get('paymentMethod', 'cash'),
            "amountPaid": amount_paid,
            "amountDue": amount_due,
            "paymentStatus": payment_status,
            "status": data.get('status', 'completed'),
            "cashier": data.get('cashier', 'System'),
            "createdAt": data.get('createdAt', datetime.datetime.now().isoformat()),
            "note": data.get('note', ''),
            "tenant_id": tenant_id
        }
        
        result = db.orders.insert_one(new_order)
        new_order['id'] = str(result.inserted_id)
        
        # --- Database Sync & Consistency ---
        
        # 1. Update Product Stocks & Log Transactions
        for item in data.get('items', []):
            product_id = item.get('product', {}).get('id')
            qty = int(item.get('quantity', 0))
            if product_id and qty > 0:
                # Deduct Stock (Only if it's a valid ObjectId - skips virtual items like 'tea-half')
                if ObjectId.is_valid(product_id):
                    db.products.update_one(
                        {"_id": ObjectId(product_id), "tenant_id": tenant_id},
                        {"$inc": {"stock": -qty}}
                    )
                
                # Log "Stock Out" Transaction (Optional: keep even for virtual items for records)
                db.inventory_transactions.insert_one({
                    "productId": product_id,
                    "productName": item.get('product', {}).get('name', 'Product'),
                    "quantity": qty,
                    "type": "out",
                    "reason": f"Order {order_num}",
                    "tenant_id": tenant_id,
                    "createdAt": datetime.datetime.now().isoformat()
                })

        # 2. Update Customer Stats
        if data.get('customer') and data.get('customer').get('id'):
            cust_id = data.get('customer').get('id')
            try:
                db.customers.update_one(
                    {"_id": ObjectId(cust_id), "tenant_id": tenant_id},
                    {
                        "$inc": {
                            "totalSpent": total,
                            "totalOrders": 1
                        },
                        "$set": {
                            "lastVisit": datetime.datetime.now().isoformat()
                        }
                    }
                )
            except Exception as e:
                logger.error(f"Failed to update customer stats: {e}")

        # 3. Log Initial Payment receipt
        if amount_paid > 0:
            db.payments.insert_one({
                "tenant_id": tenant_id,
                "customerId": data.get('customer', {}).get('id') if data.get('customer') else None,
                "orderId": str(result.inserted_id),
                "orderNumber": order_num,
                "amount": amount_paid,
                "method": data.get('paymentMethod', 'cash'),
                "type": "sale",
                "createdAt": datetime.datetime.now().isoformat()
            })

        if '_id' in new_order:
            del new_order['_id']
            
        return jsonify({
            "status": "success",
            "message": "Order created successfully",
            "data": new_order
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating order: {e}")
        return jsonify({"status": "error", "message": f"Failed to create order: {str(e)}"}), 500

@bp.route('/<order_id>', methods=['PUT'])
@jwt_required()
def update_order(order_id):
    """Update order details (status, note, etc)."""
    try:
        tenant_id = get_jwt()['tenant_id']
        data = request.get_json()
        
        # Prevent overriding critical fields like full items/total directly unless specifically needed
        # In a real app we might only allow updating `status` and `paymentStatus`
        
        result = db.orders.update_one(
            {"_id": ObjectId(order_id), "tenant_id": tenant_id},
            {"$set": data}
        )
        
        if result.matched_count == 0:
            return jsonify({"status": "error", "message": "Order not found"}), 404
            
        return jsonify({
            "status": "success",
            "message": "Order updated successfully"
        }), 200
    except Exception as e:
        logger.error(f"Error updating order: {e}")
        return jsonify({"status": "error", "message": "Failed to update order"}), 500
