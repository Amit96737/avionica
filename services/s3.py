import os
import time
import requests
import boto3
from uuid import uuid4
from urllib.parse import unquote

ALLOWED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".svg"
}


def upload_image_to_s3(
    image_url: str,
    folder="test_folder"
):
    if not image_url:
        raise Exception("Image URL not found")
    
    image_url = unquote(
        image_url
    ).strip().rstrip('"')

    extension = os.path.splitext(
        image_url.split("?")[0]
    )[1].lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise Exception(
            f"Unsupported image extension: {extension}"
        )

    response = requests.get(
        image_url,
        headers={
            "User-Agent": "Mozilla/5.0"
        },
        timeout=30
    )

    if response.status_code != 200:
        raise Exception(
            f"Failed to download manufacturer image. "
            f"Status: {response.status_code}, "
            f"URL: {image_url}"
        )

    s3 = boto3.client(
        "s3",
        aws_access_key_id=os.getenv(
            "AWS_ACCESS_KEY_ID"
        ),
        aws_secret_access_key=os.getenv(
            "AWS_SECRET_ACCESS_KEY"
        ),
        region_name=os.getenv("AWS_REGION"),
    )

    bucket_name = os.getenv(
        "AWS_S3_BUCKET_NAME"
    )

    file_name = f"{folder}/{uuid4()}{extension}"

    s3.put_object(
        Bucket=bucket_name,
        Key=file_name,
        Body=response.content,
        ContentType=response.headers.get(
            "Content-Type",
            "application/octet-stream"
        ),
    )

    cloudfront_url = os.getenv("CLOUDFRONT_URL")

    file_url = (
        f"{cloudfront_url.rstrip('/')}/"
        f"{file_name}"
    )
    print("file_url", file_url)

    return file_url