from flask import Blueprint, jsonify, request
from app.extensions import db
from app.utils.logger import logger
from bson import ObjectId
from flask_jwt_extended import jwt_required, get_jwt

bp = Blueprint('products', __name__, url_prefix='/api/products')

@bp.route('/', methods=['GET'])
@jwt_required()
def get_products():
    """Get all products."""
    try:
        tenant_id = get_jwt()['tenant_id']
        products = list(db.products.find({"tenant_id": tenant_id}))
        # Convert ObjectId to string for JSON serialization, map _id to id
        for product in products:
            product['id'] = str(product.pop('_id'))
            
        return jsonify({
            "status": "success",
            "data": products
        }), 200
    except Exception as e:
        logger.error(f"Error fetching products: {e}")
        return jsonify({"status": "error", "message": "Failed to fetch products"}), 500

@bp.route('/<product_id>', methods=['GET'])
@jwt_required()
def get_product(product_id):
    """Get a single product."""
    try:
        tenant_id = get_jwt()['tenant_id']
        product = db.products.find_one({"_id": ObjectId(product_id), "tenant_id": tenant_id})
        if not product:
            return jsonify({"status": "error", "message": "Product not found"}), 404
            
        product['id'] = str(product.pop('_id'))
        
        return jsonify({
            "status": "success",
            "data": product
        }), 200
    except Exception as e:
        logger.error(f"Error fetching product: {e}")
        return jsonify({"status": "error", "message": "Failed to fetch product"}), 500

@bp.route('/', methods=['POST'])
@jwt_required()
def add_product():
    """Add a new product."""
    try:
        tenant_id = get_jwt()['tenant_id']
        data = request.get_json()
        if not data or 'name' not in data or 'price' not in data:
            return jsonify({"status": "error", "message": "Invalid data, name and price are required"}), 400
        
        new_product = {
            "name": data.get('name'),
            "barcode": data.get('barcode', ''),
            "category": data.get('category', 'all'),
            "price": float(data.get('price')),
            "cost": float(data.get('cost', 0)),
            "stock": int(data.get('stock', 0)),
            "minStock": int(data.get('minStock', 0)),
            "unit": data.get('unit', 'piece'),
            "image": data.get('image', ''),
            "description": data.get('description', ''),
            "isActive": data.get('isActive', True),
            "taxable": data.get('taxable', True),
            "createdAt": data.get('createdAt', ''),
            "tenant_id": tenant_id
        }
        
        result = db.products.insert_one(new_product)
        new_product['id'] = str(result.inserted_id)
        
        # Don't return ObjectId in response
        if '_id' in new_product:
            del new_product['_id']
            
        return jsonify({
            "status": "success",
            "message": "Product added successfully",
            "data": new_product
        }), 201
        
    except Exception as e:
        logger.error(f"Error adding product: {e}")
        return jsonify({"status": "error", "message": "Failed to add product"}), 500

@bp.route('/<product_id>', methods=['PUT'])
@jwt_required()
def update_product(product_id):
    """Update a product."""
    try:
        tenant_id = get_jwt()['tenant_id']
        data = request.get_json()
        result = db.products.update_one(
            {"_id": ObjectId(product_id), "tenant_id": tenant_id},
            {"$set": data}
        )
        
        if result.matched_count == 0:
            return jsonify({"status": "error", "message": "Product not found"}), 404
            
        return jsonify({
            "status": "success",
            "message": "Product updated successfully"
        }), 200
    except Exception as e:
        logger.error(f"Error updating product: {e}")
        return jsonify({"status": "error", "message": "Failed to update product"}), 500

@bp.route('/<product_id>', methods=['DELETE'])
@jwt_required()
def delete_product(product_id):
    """Delete a product."""
    try:
        tenant_id = get_jwt()['tenant_id']
        result = db.products.delete_one({"_id": ObjectId(product_id), "tenant_id": tenant_id})
        
        if result.deleted_count == 0:
            return jsonify({"status": "error", "message": "Product not found"}), 404
            
        return jsonify({
            "status": "success",
            "message": "Product deleted successfully"
        }), 200
    except Exception as e:
        logger.error(f"Error deleting product: {e}")
        return jsonify({"status": "error", "message": "Failed to delete product"}), 500
