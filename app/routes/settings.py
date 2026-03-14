from flask import Blueprint, request, jsonify
from app.extensions import db
from flask_jwt_extended import jwt_required, get_jwt
from app.utils.logger import logger

bp = Blueprint('settings', __name__, url_prefix='/api/settings')

@bp.route('/', methods=['GET'])
@jwt_required()
def get_settings():
    try:
        tenant_id = get_jwt().get('tenant_id')
        settings = db.settings.find_one({"tenant_id": tenant_id}, {'_id': False})
        if not settings:
            # Default settings
            default_settings = {
                "tenant_id": tenant_id,
                "store": {
                    "name": "BriFix Express",
                    "email": "admin@brifix.com",
                    "phone": "+1 (555) 100-2000",
                    "address": "100 Commerce Ave, New York, NY 10001",
                    "currency": "USD — US Dollar ($)",
                    "timezone": "America/New_York (EST)",
                    "parlour": False,
                    "tea_full_price": 15,
                    "tea_half_price": 10
                },
                "tax": {
                    "rate": 8.5,
                    "inclusive": True,
                    "showOnReceipt": True,
                    "taxExemptNonTaxable": True,
                    "gstNumber": ""
                },
                "payment": {
                    "cash": True,
                    "card": True,
                    "qr": True,
                    "split": True,
                    "loyalty": False,
                    "storeCredit": False,
                    "credit_system": False
                },
                "receipt": {
                    "header": "BriFix Express",
                    "footer": "Thank you for your purchase! Visit us again.",
                    "showLogo": True,
                    "showBarcode": True,
                    "showQr": False,
                    "autoPrint": False,
                    "emailReceipt": True,
                    "paperSize": "80mm (Standard Thermal)"
                },
                "notifications": {
                    "lowStock": True,
                    "outOfStock": True,
                    "dailySummary": True,
                    "newCustomer": False,
                    "largeTransactions": True,
                    "failedPayments": True,
                    "refunds": False
                }
            }
            return jsonify({"status": "success", "data": default_settings}), 200
        
        return jsonify({"status": "success", "data": settings}), 200
    except Exception as e:
        logger.error(f"Error fetching settings: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route('/', methods=['POST', 'PUT'])
@jwt_required()
def update_settings():
    try:
        tenant_id = get_jwt().get('tenant_id')
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
        
        # Ensure tenant_id is preserved/set
        if 'tenant_id' in data:
            del data['tenant_id']
            
        # Update or create settings for this tenant
        db.settings.update_one(
            {"tenant_id": tenant_id}, 
            {'$set': {**data, "tenant_id": tenant_id}}, 
            upsert=True
        )
        
        return jsonify({"status": "success", "message": "Settings updated successfully"}), 200
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
