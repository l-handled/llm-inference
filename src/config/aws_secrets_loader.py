import os
import sys
import json
from typing import Dict, Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

def fetch_secret(secret_name: str, region_name: str = "us-east-1") -> Dict[str, Any]:
    """
    Fetch a secret from AWS Secrets Manager.
    If the secret is a JSON string, parse and return as dict.
    If the secret is a plain string, return as {secret_name: value}.
    """
    client = boto3.client("secretsmanager", region_name=region_name)
    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except (BotoCoreError, ClientError) as e:
        print(f"Error fetching secret '{secret_name}': {e}", file=sys.stderr)
        sys.exit(1)

    secret = get_secret_value_response.get("SecretString")
    if not secret:
        print(f"No SecretString found for secret '{secret_name}'", file=sys.stderr)
        sys.exit(1)

    try:
        # Try to parse as JSON
        secret_dict = json.loads(secret)
        if isinstance(secret_dict, dict):
            return secret_dict
        else:
            # If it's not a dict, treat as string
            return {secret_name: secret}
    except json.JSONDecodeError:
        # Not JSON, treat as string
        return {secret_name: secret}

def export_env_vars(secret_dict: Dict[str, Any]) -> None:
    """
    Export each key-value pair in the secret dict as an environment variable.
    """
    for key, value in secret_dict.items():
        os.environ[key] = str(value)
        print(f"Exported {key}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Fetch secrets from AWS Secrets Manager and export as env vars.")
    parser.add_argument("--secret-name", required=True, help="Name of the secret in AWS Secrets Manager.")
    parser.add_argument("--region", default="us-east-1", help="AWS region (default: us-east-1)")
    parser.add_argument("--print-export", action="store_true", help="Print 'export KEY=VALUE' lines for shell usage.")
    args = parser.parse_args()

    secret_dict = fetch_secret(args.secret_name, args.region)
    export_env_vars(secret_dict)

    if args.print_export:
        for key, value in secret_dict.items():
            print(f"export {key}='{value}'")

if __name__ == "__main__":
    main() 