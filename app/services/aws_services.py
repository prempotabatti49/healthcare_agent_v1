import boto3
import json

def get_secret(secret_name: str, region_name: str = "us-east-1"):
    client = boto3.client("secretsmanager", region_name=region_name)

    response = client.get_secret_value(SecretId=secret_name)

    # Secret stored as JSON string
    if "SecretString" in response:
        secret = response["SecretString"]
        return json.loads(secret)
    else:
        # binary (rare)
        return response["SecretBinary"]


def upload_file_to_s3(file_path: str, bucket_name: str, object_name: str, region_name: str = "us-east-1") -> str:
    s3_client = boto3.client("s3", region_name=region_name)
    s3_client.upload_file(file_path, bucket_name, object_name)
    url = f"https://{bucket_name}.s3.{region_name}.amazonaws.com/{object_name}"
    return url


def inject_secrets_to_secret_manager(secret_name: str, secrets_dict: dict, region_name: str = "us-east-1"):
    client = boto3.client("secretsmanager", region_name=region_name)
    secret_string = json.dumps(secrets_dict)
    try:
        client.create_secret(Name=secret_name, SecretString=secret_string)
        print(f"Secret '{secret_name}' created successfully.")
    except client.exceptions.ResourceExistsException:
        client.update_secret(SecretId=secret_name, SecretString=secret_string)
        print(f"Secret '{secret_name}' updated successfully.")