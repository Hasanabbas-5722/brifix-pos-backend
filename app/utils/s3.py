import os
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
import uuid
from werkzeug.utils import secure_filename
from app.utils.logger import logger

def get_s3_client():
    return boto3.client(
        's3',
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
        region_name=os.environ.get('AWS_REGION', 'ap-south-1')
    )

def upload_file_to_s3(file_obj, folder='products'):
    bucket_name = os.environ.get('AWS_S3_BUCKET_NAME')
    
    if not bucket_name:
        # Fallback if S3 is not fully configured, prevent app breaking
        logger.warning("AWS_S3_BUCKET_NAME not set. Using a mock URL.")
        # Optional: return a mock or local url
        return f"https://via.placeholder.com/150?text=S3+{folder}"
        
    s3_client = get_s3_client()
    
    original_filename = secure_filename(file_obj.filename)
    unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
    s3_key = f"{folder}/{unique_filename}"
    
    try:
        s3_client.upload_fileobj(
            file_obj,
            bucket_name,
            s3_key,
            ExtraArgs={
                "ContentType": file_obj.content_type,
            }
        )
        url = f"https://{bucket_name}.s3.{os.environ.get('AWS_REGION', 'ap-south-1')}.amazonaws.com/{s3_key}"
        return url
    except Exception as e:
        logger.error(f"Failed to upload to S3: {e}")
        return None
