import os
import sys

# Add backend directory to sys.path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app

def seed_database():
    print("Connecting to MongoDB to seed initial data...")
    from app.extensions import db
    from app.routes.auth import generate_tenant_code
    from werkzeug.security import generate_password_hash
    import datetime
    
    # 1. Spin up a brand new secure Tenant!
    tenant_id = generate_tenant_code()
    while db.tenants.find_one({"_id": tenant_id}):
        tenant_id = generate_tenant_code()
        
    print(f"----------------------------------------")
    print(f"🏙️  Creating Sandbox Company: {tenant_id}")
    print(f"----------------------------------------")
    
    db.tenants.insert_one({
        "_id": tenant_id,
        "name": f"Demo Store {tenant_id}",
        "createdAt": datetime.datetime.now().isoformat()
    })
    
    # 2. Create an exact admin user linked to this fresh tenant 
    demo_email = f"admin@{tenant_id.lower()}.com"
    demo_password = "admin123"
    db.users.insert_one({
        "email": demo_email,
        "password": generate_password_hash(demo_password),
        "name": "Demo Manager",
        "role": "admin",
        "tenant_id": tenant_id
    })
    
    print(f"👤 Created Admin Login -> Email: {demo_email} | Password: {demo_password}")
    
    # 3. PRODUCTS
    products_collection = db.products
    print(f"☕ Seeding Products into {tenant_id}...")
    products_collection.insert_many([
        {"tenant_id": tenant_id, "name": "Caramel Macchiato", "sku": "BEV-001", "barcode": "8901234567890", "category": "beverages", "price": 5.99, "cost": 1.2, "stock": 150, "minStock": 20, "unit": "cup", "image": "☕", "description": "Rich espresso with steamed milk and caramel drizzle", "isActive": True, "taxable": True, "createdAt": "2024-01-15"},
        {"tenant_id": tenant_id, "name": "Green Tea Latte", "sku": "BEV-002", "barcode": "8901234567891", "category": "beverages", "price": 4.99, "cost": 0.8, "stock": 120, "minStock": 20, "unit": "cup", "image": "🍵", "description": "Premium matcha with creamy steamed milk", "isActive": True, "taxable": True, "createdAt": "2024-01-15"},
        {"tenant_id": tenant_id, "name": "Iced Americano", "sku": "BEV-003", "barcode": "8901234567892", "category": "beverages", "price": 3.99, "cost": 0.7, "stock": 8, "minStock": 15, "unit": "cup", "image": "🧊", "description": "Double espresso over ice with cold water", "isActive": True, "taxable": True, "createdAt": "2024-01-15"},
        {"tenant_id": tenant_id, "name": "Chocolate Croissant", "sku": "FOOD-001", "barcode": "8901234567893", "category": "food", "price": 3.49, "cost": 0.9, "stock": 45, "minStock": 10, "unit": "piece", "image": "🥐", "description": "Buttery flaky pastry filled with dark chocolate", "isActive": True, "taxable": True, "createdAt": "2024-01-20"},
        {"tenant_id": tenant_id, "name": "Avocado Toast", "sku": "FOOD-002", "barcode": "8901234567894", "category": "food", "price": 8.99, "cost": 2.5, "stock": 30, "minStock": 5, "unit": "plate", "image": "🥑", "description": "Smashed avocado on sourdough with cherry tomatoes", "isActive": True, "taxable": True, "createdAt": "2024-01-20"},
        {"tenant_id": tenant_id, "name": "Blueberry Muffin", "sku": "FOOD-003", "barcode": "8901234567895", "category": "food", "price": 2.99, "cost": 0.6, "stock": 60, "minStock": 10, "unit": "piece", "image": "🫐", "description": "Fresh baked muffin studded with wild blueberries", "isActive": True, "taxable": True, "createdAt": "2024-01-20"},
        {"tenant_id": tenant_id, "name": "Wireless Earbuds", "sku": "ELEC-001", "barcode": "8901234567896", "category": "electronics", "price": 79.99, "cost": 35.0, "stock": 25, "minStock": 5, "unit": "pair", "image": "🎧", "description": "True wireless earbuds with ANC and 24hr battery", "isActive": True, "taxable": True, "createdAt": "2024-02-01"},
        {"tenant_id": tenant_id, "name": "Cotton T-Shirt", "sku": "CLO-001", "barcode": "8901234567898", "category": "clothing", "price": 19.99, "cost": 6.0, "stock": 3, "minStock": 10, "unit": "piece", "image": "👕", "description": "Premium 100% organic cotton t-shirt", "isActive": True, "taxable": True, "createdAt": "2024-02-10"},
    ])

    # 4. CUSTOMERS
    customers_collection = db.customers
    print(f"👥 Seeding Customers into {tenant_id}...")
    customers_collection.insert_many([
        {"tenant_id": tenant_id, "name": "Sarah Johnson", "email": "sarah.johnson@email.com", "phone": "+1 (555) 234-5678", "address": "123 Maple Street", "loyaltyPoints": 1250, "totalSpent": 845.5, "totalOrders": 42, "createdAt": "2024-01-10", "lastVisit": "2024-03-05", "avatar": "SJ"},
        {"tenant_id": tenant_id, "name": "Michael Chen", "email": "m.chen@techcorp.com", "phone": "+1 (555) 876-5432", "address": "456 Oak Avenue", "loyaltyPoints": 3200, "totalSpent": 2340.0, "totalOrders": 89, "createdAt": "2023-11-20", "lastVisit": "2024-03-06", "avatar": "MC"},
        {"tenant_id": tenant_id, "name": "Emma Rodriguez", "email": "emma.r@gmail.com", "phone": "+1 (555) 345-6789", "address": "789 Pine Road", "loyaltyPoints": 580, "totalSpent": 320.75, "totalOrders": 18, "createdAt": "2024-02-01", "lastVisit": "2024-03-04", "avatar": "ER"}
    ])

    print(f"\n✅ SUCCESS! Spawned sandbox environment for {tenant_id}!")

if __name__ == '__main__':
    # Initialize app context so extensions connect
    app = create_app()
    with app.app_context():
        seed_database()
