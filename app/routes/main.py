from flask import Blueprint, jsonify
from app.extensions import redis_client
import redis

bp = Blueprint('main', __name__)

@bp.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint."""
    return jsonify({
        "status": "success",
        "message": "Application is healthy"
    }), 200

@bp.route('/health/redis', methods=['GET'])
def redis_check():
    """Endpoint to check Redis connection status."""
    try:
        # Ping the Redis server
        redis_ping = redis_client.ping()
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
