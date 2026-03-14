from flask import Blueprint, jsonify, request
from app.extensions import db
from app.utils.logger import logger
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, get_jwt
import string
import random

bp = Blueprint('auth', __name__, url_prefix='/api/auth')

def generate_tenant_code(length=7):
    """Generate a random alphanumeric string like 'GDJSJAJ' for tenant ID."""
    return ''.join(random.choices(string.ascii_uppercase, k=length))

@bp.route('/register', methods=['POST'])
def register():
    """Register a new user and initialize a tenant/company."""
    try:
        data = request.get_json()
        if not data or 'email' not in data or 'password' not in data:
            return jsonify({"status": "error", "message": "Email and password are required"}), 400
        
        email = data.get('email')
        password = data.get('password')
        company_name = data.get('companyName', f"{data.get('name', 'User')}'s Company")
        
        # Check if user already exists
        if db.users.find_one({"email": email}):
            return jsonify({"status": "error", "message": "User already exists"}), 409
            
        # 1. Create a new Tenant / Company record
        tenant_id = generate_tenant_code()
        while db.tenants.find_one({"_id": tenant_id}):
            tenant_id = generate_tenant_code()
            
        new_tenant = {
            "_id": tenant_id,
            "name": company_name,
            "createdAt": __import__('datetime').datetime.now().isoformat()
        }
        db.tenants.insert_one(new_tenant)
        
        # 2. Create the User linked to the Tenant
        hashed_password = generate_password_hash(password)
        new_user = {
            "email": email,
            "password": hashed_password,
            "name": data.get('name', ''),
            "role": data.get('role', 'admin'), # First user is usually admin
            "tenant_id": tenant_id # Core Multi-Tenancy Link
        }
        
        result = db.users.insert_one(new_user)
        
        return jsonify({
            "status": "success", 
            "message": "Company and User registered successfully",
            "data": {
                "id": str(result.inserted_id),
                "tenant_id": tenant_id
            }
        }), 201

    except Exception as e:
        logger.error(f"Error registering user: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500


@bp.route('/login', methods=['POST'])
def login():
    """Authenticate user and return access & refresh tokens containing the tenant_id."""
    data = request.get_json()
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({"status": "error", "message": "Email and password are required"}), 400
    
    email = data.get('email')
    password = data.get('password')
    
    user = db.users.find_one({"email": email})
    
    if not user or not check_password_hash(user['password'], password):
        return jsonify({"status": "error", "message": "Invalid email or password"}), 401
    
    # Generate tokens
    user_identity = str(user['_id'])
    tenant_id = user.get('tenant_id') 
    
    # If using legacy/seed data, assign a default dummy tenant_id if missed
    if not tenant_id: 
        tenant_id = "default_tenant_123"
    
    # Add extra info to the token
    additional_claims = {
        "role": user.get('role', 'user'),
        "email": user.get('email', ''),
        "tenant_id": tenant_id   # Inject Tenant ID into Token Claims securely
    }

    access_token = create_access_token(identity=user_identity, additional_claims=additional_claims)
    refresh_token = create_refresh_token(identity=user_identity, additional_claims=additional_claims)
    
    return jsonify({
        "status": "success",
        "message": "Login successful",
        "data": {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "id": str(user['_id']),
                "email": user.get('email', ''),
                "name": user.get('name', ''),
                "role": user.get('role', 'user'),
                "tenant_id": tenant_id
            }
        }
    }), 200
    
@bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Generate a new access token using a refresh token."""
    try:
        current_user = get_jwt_identity()
        claims = get_jwt()
        
        # Carry over claims to the new access token
        additional_claims = {
            "role": claims.get('role'),
            "email": claims.get('email'),
            "tenant_id": claims.get('tenant_id')
        }
        
        new_access_token = create_access_token(identity=current_user, additional_claims=additional_claims)
        
        return jsonify({
            "status": "success",
            "data": {
                "access_token": new_access_token
            }
        }), 200
    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        return jsonify({"status": "error", "message": "Failed to refresh token"}), 401
