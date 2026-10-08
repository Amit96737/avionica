from fastapi import UploadFile, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
import csv
import io
from avionica.manufacture_csv_mapping import MANUFACTURER_CSV_MAPPING, REQUIRED_MANUFACTURER_CSV_COLUMNS, REQUIRED_MANUFACTURER_CSV_COLUMNS_DATA
from avionica.models import Manufacturer
from constants import DEFAULT_MANUFACTURER_LOGO
from datetime import datetime
from avionica.models import Product
from services.s3 import upload_image_to_s3
from database import SessionLocal
import uuid
from pydantic import ValidationError

manufacturer_import_jobs = {}


def process_manufacturer_csv(rows, task_id):

    db = SessionLocal()

    try:

        inserted_count = 0
        updated_count = 0
        uploaded_manufacturer_ids = []

        for row in rows:

            manufacturer_data = {}

            for csv_column, model_column in MANUFACTURER_CSV_MAPPING.items():

                value = row.get(csv_column)

                if value is not None:
                    value = value.strip()

                manufacturer_data[model_column] = value

            if not manufacturer_data.get("logo"):
                manufacturer_data["logo"] = DEFAULT_MANUFACTURER_LOGO

            cover_photo_url = manufacturer_data.get("cover_photo")

            if cover_photo_url:
                manufacturer_data["cover_photo"] = {
                    "url": cover_photo_url,
                    "license": row.get("licence_type"),
                    "author": row.get("author_name"),
                    "wiki": row.get("wiki_link"),
                }

            interesting_facts = manufacturer_data.get(
                "interesting_facts"
            )

            if interesting_facts:
                manufacturer_data["interesting_facts"] = [
                    fact.strip()
                    for fact in interesting_facts.split("\n\n")
                    if fact.strip()
                ]

            company_name = manufacturer_data.get("company_name")

            if not company_name:
                continue

            manufacturer = (
                db.query(Manufacturer)
                .filter(
                    Manufacturer.company_name == company_name
                )
                .first()
            )

            if manufacturer:

                has_changes = False

                for field, new_value in manufacturer_data.items():

                    if field == "company_name":
                        continue

                    if new_value is None or new_value == "":
                        continue

                    old_value = getattr(
                        manufacturer,
                        field,
                        None
                    )

                    if old_value != new_value:

                        setattr(
                            manufacturer,
                            field,
                            new_value
                        )

                        has_changes = True

                if has_changes:
                    updated_count += 1

            else:

                manufacturer = Manufacturer(
                    **manufacturer_data
                )

                db.add(manufacturer)
                db.flush()

                inserted_count += 1

            if manufacturer.id not in uploaded_manufacturer_ids:
                uploaded_manufacturer_ids.append(
                    manufacturer.id
                )

            products_1 = row.get("products 1 ")

            if products_1:

                airplane_data = [
                    item.strip()
                    for item in products_1.split(",")
                    if item.strip()
                ]

                existing_product = (
                    db.query(Product)
                    .filter(
                        Product.manufacturer_id == manufacturer.id,
                        Product.series == "Airplane"
                    )
                    .first()
                )

                if existing_product:

                    if existing_product.data != airplane_data:
                        existing_product.data = airplane_data

                else:

                    product = Product(
                        series="Airplane",
                        data=airplane_data,
                        manufacturer_id=manufacturer.id
                    )

                    db.add(product)

            products_2 = row.get("products 2")

            if products_2:

                helicopter_data = [
                    item.strip()
                    for item in products_2.split(",")
                    if item.strip()
                ]

                existing_product = (
                    db.query(Product)
                    .filter(
                        Product.manufacturer_id == manufacturer.id,
                        Product.series == "Helicopter"
                    )
                    .first()
                )

                if existing_product:

                    if existing_product.data != helicopter_data:
                        existing_product.data = helicopter_data

                else:

                    product = Product(
                        series="Helicopter",
                        data=helicopter_data,
                        manufacturer_id=manufacturer.id
                    )

                    db.add(product)

        db.commit()

        manufacturer_import_jobs[task_id] = {
            "status": "completed",
            "inserted_records": inserted_count,
            "updated_records": updated_count,
            "manufacturer_ids": uploaded_manufacturer_ids
        }

        print(
            f"Manufacturer import completed. "
            f"Inserted: {inserted_count}, "
            f"Updated: {updated_count}"
        )

    except Exception as e:

        db.rollback()

        manufacturer_import_jobs[task_id] = {
            "status": "failed",
            "inserted_records": 0,
            "updated_records": 0,
            "manufacturer_ids": [],
            "message": "Failed to import manufacturer data"
        }

        print(
            f"Failed to import manufacturer data: {e}"
        )

    finally:
        db.close()



async def upload_manufacturer_csv(
    file: UploadFile,
    db: Session,
    background_tasks: BackgroundTasks
):

    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are allowed"
        )

    # content = await file.read()

    # csv_file = io.StringIO(
    #     content.decode("utf-8-sig")
    # )
    
    content = await file.read()

    try:
        decoded_content = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            decoded_content = content.decode("cp1252")
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=400,
                detail="Invalid CSV encoding. Please upload a UTF-8 CSV file."
            )

    csv_file = io.StringIO(decoded_content)

    reader = csv.DictReader(csv_file)

    if not reader.fieldnames:
        raise HTTPException(
            status_code=400,
            detail="Invalid CSV format. CSV header is missing."
        )

    csv_headers = {
        header.strip()
        for header in reader.fieldnames
        if header
    }

    missing_columns = [
        column
        for column in REQUIRED_MANUFACTURER_CSV_COLUMNS
        if column not in csv_headers
    ]

    if missing_columns:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid CSV format missing column(s): "
                + ", ".join(missing_columns)
            )
        )

    rows = list(reader)

    if not rows:
        raise HTTPException(
            status_code=400,
            detail="CSV file contains no data."
        )

    validation_errors = []

    for row_number, row in enumerate(rows, start=2):

        for required_field in REQUIRED_MANUFACTURER_CSV_COLUMNS_DATA:

            value = row.get(required_field)

            if value is None or not str(value).strip():

                if required_field not in validation_errors:
                    validation_errors.append(required_field)

    if validation_errors:

        error_messages = [
            f"'{field}' is required."
            for field in validation_errors
        ]

        raise HTTPException(
            status_code=400,
            detail={
                "message": "CSV contains missing required fields.",
                "errors": error_messages
            }
        )
        
        
    founding_year_errors = []

    for row_number, row in enumerate(rows, start=2):
        founding_year = row.get("founding_year")

        if founding_year is not None:
            founding_year = str(founding_year).strip()

        if founding_year:
            try:
                int(founding_year)
            except ValueError:
                founding_year_errors.append(
                    f"Row {row_number}: founding_year: Input should be a valid integer"
                )

    if founding_year_errors:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "CSV contains invalid field values.",
                "errors": founding_year_errors
            }
        )
    
        
    task_id = str(uuid.uuid4())

    manufacturer_import_jobs[task_id] = {
        "status": "processing",
        "inserted_records": 0,
        "updated_records": 0,
        "manufacturer_ids": []
    }

    background_tasks.add_task(
        process_manufacturer_csv,
        rows,
        task_id
    )

    return {
        "success": True,
        "task_id": task_id,
        "message": "Manufacturers import started in background."
    }


    
async def get_manufacture(db: Session):
    manufacturers = (
        db.query(Manufacturer)
        .order_by(Manufacturer.company_name.asc())
        .all()
    )

    return manufacturers

# async def get_manufacture(db: Session, pagination):
#     manufacturers = (
#         db.query(Manufacturer)
#         .order_by(Manufacturer.company_name.asc())
#     )
#     total_count = manufacturers.count()
     
#     paginated_query = pagination.paginate_query(manufacturers)
    
#     manufacturer = paginated_query.all()

#     return pagination.get_paginated_response(
#         manufacturer,
#         total_count,
#         detail="Manufacturers fetched successfully.")



async def update_manufacturer(
    db: Session,
    manufacturer_id: str
):
    manufacturer = (
        db.query(Manufacturer)
        .filter(Manufacturer.id == manufacturer_id)
        .first()
    )

    if not manufacturer:
        raise HTTPException(
            status_code=404,
            detail="Manufacturer with this id not found"
        )

    manufacturer.is_approved = not manufacturer.is_approved

    if manufacturer.is_approved:
        manufacturer.is_approved_time = datetime.utcnow()

    else:
        manufacturer.is_approved_time = None

    db.commit()
    db.refresh(manufacturer)

    return {
        "message": "Manufacturer status updated successfully",
        "id": manufacturer.id,
        "is_approved": manufacturer.is_approved,
        "is_approved_time": manufacturer.is_approved_time
    }
    
    
    
async def delete_manufacturer(
    db: Session,
    manufacturer_id: str
):
    manufacturer = (
        db.query(Manufacturer)
        .filter(Manufacturer.id == manufacturer_id)
        .first()
    )

    if not manufacturer:
        raise HTTPException(
            status_code=404,
            detail="Manufacturer not found"
        )

    db.delete(manufacturer)
    db.commit()

    return {
        "message": "Manufacturer deleted successfully",
        "id": manufacturer_id
    }
    

    
def upload_manufacturer_logos_background(
    manufacturer_ids: list[str]
):
    db = SessionLocal()

    try:
        manufacturers = (
            db.query(Manufacturer)
            .filter(
                Manufacturer.id.in_(manufacturer_ids)
            )
            .all()
        )

        if not manufacturers:
            print("No manufacturers found for logo upload")
            return

        for manufacturer in manufacturers:

            if (
                not manufacturer.logo
                or manufacturer.logo == DEFAULT_MANUFACTURER_LOGO
            ):
                continue

            try:
                s3_image_url = upload_image_to_s3(
                    manufacturer.logo,
                    folder="test_folder"
                )

                if s3_image_url:
                    manufacturer.logo = s3_image_url

                    print(
                        f"Manufacturer logo uploaded: "
                        f"{manufacturer.company_name}"
                    )

            except Exception as e:
                print(
                    f"Failed to upload manufacturer logo: "
                    f"{manufacturer.company_name}"
                )
                print("Error:", str(e))

        db.commit()

        print(
            f"Manufacturer logo background task completed: "
            f"{len(manufacturers)} manufacturers"
        )

    except Exception as e:
        db.rollback()
        print(
            "Manufacturer logo background error:",
            str(e)
        )

    finally:
        db.close()       



async def bulk_disapprove_manufacturer(
    db: Session,
    manufacturer_ids: list[str]
):

    manufacturers = (
        db.query(Manufacturer)
        .filter(
            Manufacturer.id.in_(manufacturer_ids)
        )
        .all()
    )

    if not manufacturers:
        raise HTTPException(
            status_code=404,
            detail="No manufacturers found"
        )

    for manufacturer in manufacturers:
        manufacturer.is_approved = False
        # manufacturer.is_approved_time = None

    db.commit()

    return {
        "message": "Manufacturers disapproved successfully",
        "updated_records": len(manufacturers)
    }



async def bulk_delete_manufacturer(
    db: Session,
    manufacturer_ids: list[str]
):
    manufacturers = (
        db.query(Manufacturer)
        .filter(Manufacturer.id.in_(manufacturer_ids))
        .all()
    )

    if not manufacturers:
        raise HTTPException(
            status_code=404,
            detail="No manufacturers found"
        )

    deleted_ids = [manufacturer.id for manufacturer in manufacturers]

    for manufacturer in manufacturers:
        db.delete(manufacturer)

    db.commit()

    return {
        "message": "Manufacturers deleted successfully",
        "deleted_count": len(deleted_ids),
        "deleted_ids": deleted_ids,
    }
    
    