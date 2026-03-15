from flask import Blueprint, jsonify
from app import extensions
import redis

bp = Blueprint('main', __name__)

@bp.route('/health', methods=['GET'])
def health_check():
    """Comprehensive health check endpoint."""
    health_status = {
        "status": "success",
        "message": "Application is healthy",
        "services": {
            "redis": "unknown",
            "mongodb": "unknown"
        }
    }
    
    # Check Redis
    try:
        redis_ping = extensions.redis_client.ping()
        health_status["services"]["redis"] = "connected" if redis_ping else "disconnected"
    except Exception:
        health_status["services"]["redis"] = "error"
        health_status["status"] = "degraded"
        health_status["message"] = "Some services are degraded"

    # Check MongoDB
    try:
        if extensions.mongo_client:
            extensions.mongo_client.admin.command('ping')
            health_status["services"]["mongodb"] = "connected"
        else:
            health_status["services"]["mongodb"] = "disconnected"
    except Exception:
        health_status["services"]["mongodb"] = "error"
        health_status["status"] = "degraded"
        health_status["message"] = "Some services are degraded"

    status_code = 200 if health_status["status"] == "success" else 503
    return jsonify(health_status), status_code

@bp.route('/health/redis', methods=['GET'])
def redis_check():
    """Endpoint to check Redis connection status."""
    try:
        # Ping the Redis server
        redis_ping = extensions.redis_client.ping()
        if redis_ping:
            return jsonify({
                "status": "success",
                "message": "Successfully connected to Redis"
            }), 200
    except redis.ConnectionError as e:
        return jsonify({
            "status": "error",
            "message": "Failed to connect to Redis",
            "error_details": str(e)
        }), 503
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "An unexpected error occurred while connecting to Redis",
            "error_details": str(e)
        }), 500
