from flask import Blueprint, jsonify, request
from app.utils.logger import logger
from app.utils.s3 import upload_file_to_s3
from flask_jwt_extended import jwt_required

bp = Blueprint('upload', __name__, url_prefix='/api/upload')

@bp.route('/image', methods=['POST'])
@jwt_required()
def upload_image():
    """Upload an image to S3 and return the URL."""
    try:
        if 'file' not in request.files:
            return jsonify({"status": "error", "message": "No file part in the request"}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({"status": "error", "message": "No selected file"}), 400
            
        folder = request.form.get('folder', 'products')
        
        url = upload_file_to_s3(file, folder=folder)
        
        if not url:
            return jsonify({"status": "error", "message": "Failed to upload file to S3"}), 500
            
        return jsonify({
            "status": "success",
            "message": "File uploaded successfully",
            "data": {
                "url": url
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        return jsonify({"status": "error", "message": "Internal server error during file upload"}), 500
