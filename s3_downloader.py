import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError

def parse_s3_path(path_string):
    """
    Parses an S3 ARN or path string into bucket and prefix.
    Example: 'arn:aws:s3:::mys3/folder/' -> ('mys3', 'folder/')
    Example: 'mys3/folder/' -> ('mys3', 'folder/')
    Example: 'mys3' -> ('mys3', '')
    """
    path = path_string.strip()
    if path.startswith("arn:aws:s3:::"):
        path = path.replace("arn:aws:s3:::", "")
    
    if "/" in path:
        parts = path.split("/", 1)
        bucket = parts[0]
        prefix = parts[1]
        # Ensure prefix ends with / if it exists
        if prefix and not prefix.endswith("/"):
            prefix += "/"
        return bucket, prefix
    else:
        return path, ""

def get_s3_objects(s3_path, access_key, secret_key, region):
    """Lists all objects in the S3 bucket/prefix."""
    try:
        bucket, prefix = parse_s3_path(s3_path)
        
        s3 = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        
        response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
        
        if 'Contents' not in response:
            return [], None
            
        # Return only the object keys (full paths)
        return [obj['Key'] for obj in response['Contents']], None
            
    except Exception as e:
        return None, str(e)

def download_from_s3(s3_path, object_key, access_key, secret_key, region):
    """Downloads an object from S3."""
    try:
        bucket, _ = parse_s3_path(s3_path)
        
        s3 = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        
        response = s3.get_object(Bucket=bucket, Key=object_key)
        return response['Body'].read(), None
            
    except Exception as e:
        return None, str(e)
