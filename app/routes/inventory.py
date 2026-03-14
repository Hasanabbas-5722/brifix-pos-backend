from flask import Blueprint, jsonify, request
from app.extensions import db
from app.utils.logger import logger
from bson import ObjectId
from flask_jwt_extended import jwt_required, get_jwt
import datetime

bp = Blueprint('inventory', __name__, url_prefix='/api/inventory')

@bp.route('/', methods=['GET'])
@jwt_required()
def get_inventory():
    """Get inventory status for all products."""
    try:
        tenant_id = get_jwt()['tenant_id']
        products = list(db.products.find({"tenant_id": tenant_id}, {
            "name": 1, "sku": 1, "stock": 1, "minStock": 1, "unit": 1, "category": 1
        }))
        
        for p in products:
            p['id'] = str(p.pop('_id'))
            p['status'] = 'low' if p.get('stock', 0) <= p.get('minStock', 0) else 'in_stock'
            if p.get('stock', 0) == 0:
                p['status'] = 'out_of_stock'
                
        return jsonify({
            "status": "success",
            "data": products
        }), 200
    except Exception as e:
        logger.error(f"Error fetching inventory: {e}")
        return jsonify({"status": "error", "message": "Failed to fetch inventory"}), 500

@bp.route('/add', methods=['POST'])
@jwt_required()
def add_inventory():
    """Restock inventory for a specific product."""
    try:
        tenant_id = get_jwt()['tenant_id']
        data = request.get_json()
        
        product_id = data.get('productId')
        quantity = int(data.get('quantity', 0))
        reason = data.get('reason', 'Stock In')
        
        if not product_id or quantity <= 0:
            return jsonify({"status": "error", "message": "Product ID and positive quantity are required"}), 400
            
        product = db.products.find_one({"_id": ObjectId(product_id), "tenant_id": tenant_id})
        if not product:
            return jsonify({"status": "error", "message": "Product not found"}), 404
            
        # Update product stock
        db.products.update_one(
            {"_id": ObjectId(product_id)},
            {"$inc": {"stock": quantity}}
        )
        
        # Log inventory transaction
        transaction = {
            "productId": product_id,
            "productName": product['name'],
            "quantity": quantity,
            "type": "in",
            "reason": reason,
            "tenant_id": tenant_id,
            "createdAt": datetime.datetime.now().isoformat()
        }
        db.inventory_transactions.insert_one(transaction)
        
        return jsonify({
            "status": "success",
            "message": f"Successfully added {quantity} units to {product['name']}"
        }), 200
        
    except Exception as e:
        logger.error(f"Error adding inventory: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500

@bp.route('/transactions', methods=['GET'])
@jwt_required()
def get_transactions():
    """Get recent inventory transactions."""
    try:
        tenant_id = get_jwt()['tenant_id']
        transactions = list(db.inventory_transactions.find({"tenant_id": tenant_id}).sort("createdAt", -1).limit(50))
        
        for t in transactions:
            t['id'] = str(t.pop('_id'))
            
        return jsonify({
            "status": "success",
            "data": transactions
        }), 200
    except Exception as e:
        logger.error(f"Error fetching transactions: {e}")
        return jsonify({"status": "error", "message": "Failed to fetch transactions"}), 500
