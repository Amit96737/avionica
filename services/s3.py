import os
import time
import requests
import boto3
from uuid import uuid4
from urllib.parse import unquote, urlparse
import re

ALLOWED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".svg"
}


def clean_image_name(url):
    filename = os.path.basename(
        unquote(urlparse(url).path))
    
    filename = re.sub(r"[^a-zA-Z0-9._-]", "_", filename)
    filename = re.sub(r"_+", "_", filename)
    filename = re.sub(r"_+\.", ".", filename)
    
    return filename



def upload_image_to_s3(image_url: str, folder="test_folder", image_type=""):
    if not image_url:
        raise Exception("Image URL not found")

    image_url = unquote(image_url).strip().rstrip('"')

    extension = os.path.splitext(
        urlparse(image_url).path
    )[1].lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise Exception(
            f"Unsupported image extension: {extension}"
        )

    headers = {
        "User-Agent": "AircraftBot/1.0",
        "Referer": "https://commons.wikimedia.org/",
    }

    response = None

    with requests.Session() as session:
        for attempt in range(5):
            try:
                response = session.get(
                    image_url,
                    headers=headers,
                    timeout=30,
                    stream=True,
                    allow_redirects=True,
                )

                if response.status_code == 429:
                    retry_after = response.headers.get(
                        "Retry-After", "300"
                    )

                    try:
                        wait_seconds = max(
                            300, int(retry_after)
                        )
                    except (ValueError, TypeError):
                        wait_seconds = 300

                    response.close()
                    response = None

                    print(
                        f"Wikimedia rate limit hit. "
                        f"Waiting {wait_seconds} seconds "
                        f"before retry {attempt + 1}/5..."
                    )
                    time.sleep(wait_seconds)
                    continue

                response.raise_for_status()

                image_content = response.content
                content_type = response.headers.get(
                    "Content-Type", "application/octet-stream"
                )

                print(
                    f"Image downloaded successfully: {image_url}"
                )
                break

            except requests.RequestException as e:
                if response is not None:
                    response.close()
                    response = None

                if attempt == 4:
                    raise Exception(
                        f"Image download failed after 5 attempts: "
                        f"{image_url}. Error: {e}"
                    ) from e

                wait_seconds = 5
                print(
                    f"Download failed: {e}. "
                    f"Retrying in {wait_seconds} seconds..."
                )
                time.sleep(wait_seconds)

            finally:
                if response is not None:
                    response.close()
                    response = None
        else:
            raise Exception(
                f"Image download failed after 5 attempts: {image_url}"
            )

    s3 = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION"),
    )

    bucket_name = os.getenv("AWS_S3_BUCKET_NAME")

    # file_name = (
    #     f"{folder}/{uuid4()}{extension}"
    # )
    
    file_name = f"{folder}/{image_type}{uuid4()}{extension}"

    s3.put_object(
        Bucket=bucket_name,
        Key=file_name,
        Body=image_content,
        ContentType=content_type,
    )

    cloudfront_url = os.getenv("CLOUDFRONT_URL")
    file_url = f"{cloudfront_url.rstrip('/')}/{file_name}"

    print("S3 upload successful:", file_url)

    return file_url

