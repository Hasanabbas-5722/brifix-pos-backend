import os

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    
    # Redis Configuration
    REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
    REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', None)

    # MongoDB Configuration
    MONGO_URI = os.environ.get('MONGO_URI', 'mongodb+srv://hasanabbasc_db_user:8yPxcVUOmfA9miqn@cluster0.vc5lpsh.mongodb.net/?appName=Cluster0')

    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'default-jwt-secret-key')
    
    # JWT Expiration settings
    JWT_ACCESS_TOKEN_EXPIRES = 60 * 60 * 7 # 7 hours
    JWT_REFRESH_TOKEN_EXPIRES = 60 * 60 * 24 * 30 # 30 days



# mongo-username : hasanabbasc_db_user
# mongo-password : 8yPxcVUOmfA9miqn