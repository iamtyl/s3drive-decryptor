import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

def get_s3_objects(bucket, access_key, secret_key, region):
    """Lists all objects in the S3 bucket."""
    try:
        s3 = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        response = s3.list_objects_v2(Bucket=bucket)
        if 'Contents' in response:
            return [obj['Key'] for obj in response['Contents']], None
        return [], None
    except Exception as e:
        return None, str(e)

def download_from_s3(bucket, object_name, access_key, secret_key, region):
    """Downloads a file from S3 as bytes."""
    try:
        s3 = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        response = s3.get_object(Bucket=bucket, Key=object_name)
        return response['Body'].read(), None
    except Exception as e:
        return None, str(e)
