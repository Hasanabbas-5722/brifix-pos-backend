from flask import Blueprint, jsonify, request
from app.extensions import db
from app.utils.logger import logger
from bson import ObjectId
from flask_jwt_extended import jwt_required, get_jwt
import datetime

bp = Blueprint('customers', __name__, url_prefix='/api/customers')

@bp.route('/', methods=['GET'])
@jwt_required()
def get_customers():
    """Get all customers."""
    try:
        tenant_id = get_jwt()['tenant_id']
        customers = list(db.customers.find({"tenant_id": tenant_id}))
        for customer in customers:
            customer['id'] = str(customer.pop('_id'))
            
        return jsonify({
            "status": "success",
            "data": customers
        }), 200
    except Exception as e:
        logger.error(f"Error fetching customers: {e}")
        return jsonify({"status": "error", "message": "Failed to fetch customers"}), 500

@bp.route('/<customer_id>', methods=['GET'])
@jwt_required()
def get_customer(customer_id):
    """Get a single customer."""
    try:
        tenant_id = get_jwt()['tenant_id']
        customer = db.customers.find_one({"_id": ObjectId(customer_id), "tenant_id": tenant_id})
        if not customer:
            return jsonify({"status": "error", "message": "Customer not found"}), 404
            
        customer['id'] = str(customer.pop('_id'))
        
        return jsonify({
            "status": "success",
            "data": customer
        }), 200
    except Exception as e:
        logger.error(f"Error fetching customer: {e}")
        return jsonify({"status": "error", "message": "Failed to fetch customer"}), 500

@bp.route('/', methods=['POST'])
@jwt_required()
def add_customer():
    """Add a new customer."""
    try:
        tenant_id = get_jwt()['tenant_id']
        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({"status": "error", "message": "Customer name is required"}), 400
        
        new_customer = {
            "name": data.get('name'),
            "email": data.get('email', ''),
            "phone": data.get('phone', ''),
            "address": data.get('address', ''),
            "loyaltyPoints": int(data.get('loyaltyPoints', 0)),
            "totalSpent": float(data.get('totalSpent', 0)),
            "totalOrders": int(data.get('totalOrders', 0)),
            "createdAt": data.get('createdAt', datetime.datetime.now().isoformat()),
            "lastVisit": data.get('lastVisit', datetime.datetime.now().isoformat()),
            "avatar": data.get('avatar', data.get('name', 'C')[0].upper() if data.get('name') else 'C'),
            "tenant_id": tenant_id
        }
        
        result = db.customers.insert_one(new_customer)
        new_customer['id'] = str(result.inserted_id)
        
        if '_id' in new_customer:
            del new_customer['_id']
            
        return jsonify({
            "status": "success",
            "message": "Customer added successfully",
            "data": new_customer
        }), 201
        
    except Exception as e:
        logger.error(f"Error adding customer: {e}")
        return jsonify({"status": "error", "message": "Failed to add customer"}), 500

@bp.route('/<customer_id>', methods=['PUT'])
@jwt_required()
def update_customer(customer_id):
    """Update a customer."""
    try:
        tenant_id = get_jwt()['tenant_id']
        data = request.get_json()
        # In case frontend passes the generated ID, exclude from update payload
        if 'id' in data:
            del data['id']
            
        result = db.customers.update_one(
            {"_id": ObjectId(customer_id), "tenant_id": tenant_id},
            {"$set": data}
        )
        
        if result.matched_count == 0:
            return jsonify({"status": "error", "message": "Customer not found"}), 404
            
        return jsonify({
            "status": "success",
            "message": "Customer updated successfully"
        }), 200
    except Exception as e:
        logger.error(f"Error updating customer: {e}")
        return jsonify({"status": "error", "message": "Failed to update customer"}), 500

@bp.route('/<customer_id>', methods=['DELETE'])
@jwt_required()
def delete_customer(customer_id):
    """Delete a customer."""
    try:
        tenant_id = get_jwt()['tenant_id']
        result = db.customers.delete_one({"_id": ObjectId(customer_id), "tenant_id": tenant_id})
        
        if result.deleted_count == 0:
            return jsonify({"status": "error", "message": "Customer not found"}), 404
            
        return jsonify({
            "status": "success",
            "message": "Customer deleted successfully"
        }), 200
    except Exception as e:
        logger.error(f"Error deleting customer: {e}")
        return jsonify({"status": "error", "message": "Failed to delete customer"}), 500
