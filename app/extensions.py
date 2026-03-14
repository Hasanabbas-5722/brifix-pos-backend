import redis
from pymongo import MongoClient
from pymongo.errors import ConfigurationError
from flask_jwt_extended import JWTManager
from app.utils.logger import logger

# We'll initialize extensions lazily in the app factory
redis_client = redis.Redis()
mongo_client = None
db = None
jwt = JWTManager()

def init_redis(app):
    """Initialize Redis with app context."""
    global redis_client
    redis_client = redis.Redis(
        host=app.config.get('REDIS_HOST', 'localhost'),
        port=app.config.get('REDIS_PORT', 6379),
        password=app.config.get('REDIS_PASSWORD', None),
        decode_responses=True
    )

def init_mongo(app):
    """Initialize MongoDB with app context."""
    global mongo_client, db
    try:
        mongo_uri = app.config.get('MONGO_URI')
        # Add a timeout so app initialization won't hang infinitely if DB is down
        mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        
        # Ping the database server to verify the connection is active
        mongo_client.admin.command('ping')
        logger.info("Successfully connected to MongoDB!")

        # Assign the target database
        try:
            logger.info(f"Successfully connected to MongoDB! {mongo_client}")
            db = mongo_client['brifix_pos']
            logger.info(f"Successfully connected to MongoDB! {db}")
        except ConfigurationError:
            # Fallback if the connection URI doesn't include a default DB
            db = mongo_client['brifix_pos']
            
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB. Error: {e}")

def init_jwt(app):
    """Initialize JWT with app context."""
    jwt.init_app(app)
