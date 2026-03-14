from flask import Flask
from flask_cors import CORS
from app.config import Config
from app.extensions import init_redis, init_mongo, init_jwt

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Enable Cross-Origin Resource Sharing for all domains
    CORS(app)

    # Initialize Flask extensions
    init_redis(app)
    init_mongo(app)
    init_jwt(app)
    
    # Register blueprints
    from app.routes.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    from app.routes.products import bp as products_bp
    app.register_blueprint(products_bp)
    
    from app.routes.orders import bp as orders_bp
    app.register_blueprint(orders_bp)

    from app.routes.auth import bp as auth_bp
    app.register_blueprint(auth_bp)
    
    from app.routes.customers import bp as customers_bp
    app.register_blueprint(customers_bp)

    from app.routes.dashboard import bp as dashboard_bp
    app.register_blueprint(dashboard_bp)

    from app.routes.inventory import bp as inventory_bp
    app.register_blueprint(inventory_bp)

    from app.routes.settings import bp as settings_bp
    app.register_blueprint(settings_bp)

    from app.routes.credits import bp as credits_bp
    app.register_blueprint(credits_bp)

    from app.routes.payments import bp as payments_bp
    app.register_blueprint(payments_bp)

    return app
