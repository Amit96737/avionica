from sqlalchemy.orm import Session
from triviagia.models import AviationChronicle
import json
from database import SessionLocal
from fastapi import HTTPException, UploadFile, BackgroundTasks
from datetime import datetime
import csv
import io
import uuid
from triviagia.mapping import REQUIRED_AVIATION_CHRONICLE_CSV_COLUMNS


aviation_chronicle_import_jobs = {}


async def get_aviation_chronicle(db: Session, pagination):
    aviationChronicle = (
        db.query(AviationChronicle)
        .order_by(AviationChronicle.title.asc())
    )
    
    total_count = aviationChronicle.count()
    paginated_query = pagination.paginate_query(aviationChronicle)
    aviation = paginated_query.all()

    return pagination.get_paginated_response(
        aviation,
        total_count,
        detail="Aviation Chronicle fetched successfully.")
    


# def process_manufacturer_csv(rows, task_id):

#     db = SessionLocal()

#     try:

#         inserted_count = 0
#         updated_count = 0
#         uploaded_aviation_chronicle_ids = []

#         for row in rows:

#             aviation_chronicle_data = {}

#             for csv_column, model_column in REQUIRED_AVIATION_CHRONICLE_CSV_COLUMNS.items():

#                 value = row.get(csv_column)

#                 if value is not None:
#                     value = value.strip()

#                 aviation_chronicle_data[model_column] = value

#             title = manufacturer_data.get(
#                 "interesting_facts"
#             )

#             if interesting_facts:
#                 manufacturer_data["interesting_facts"] = [
#                     fact.strip()
#                     for fact in interesting_facts.split("\n\n")
#                     if fact.strip()
#                 ]

#             company_name = manufacturer_data.get("company_name")

#             if not company_name:
#                 continue

#             manufacturer = (
#                 db.query(Manufacturer)
#                 .filter(
#                     Manufacturer.company_name == company_name
#                 )
#                 .first()
#             )

#             if manufacturer:

#                 has_changes = False

#                 for field, new_value in manufacturer_data.items():

#                     if field == "company_name":
#                         continue

#                     if new_value is None or new_value == "":
#                         continue

#                     old_value = getattr(
#                         manufacturer,
#                         field,
#                         None
#                     )

#                     if old_value != new_value:

#                         setattr(
#                             manufacturer,
#                             field,
#                             new_value
#                         )

#                         has_changes = True

#                 if has_changes:
#                     updated_count += 1

#             else:

#                 manufacturer = Manufacturer(
#                     **manufacturer_data
#                 )

#                 db.add(manufacturer)
#                 db.flush()

#                 inserted_count += 1

#             if manufacturer.id not in uploaded_manufacturer_ids:
#                 uploaded_manufacturer_ids.append(
#                     manufacturer.id
#                 )

#             products_1 = row.get("products 1 ")

#             if products_1:

#                 airplane_data = [
#                     item.strip()
#                     for item in products_1.split(",")
#                     if item.strip()
#                 ]

#                 existing_product = (
#                     db.query(Product)
#                     .filter(
#                         Product.manufacturer_id == manufacturer.id,
#                         Product.series == "Airplane"
#                     )
#                     .first()
#                 )

#                 if existing_product:

#                     if existing_product.data != airplane_data:
#                         existing_product.data = airplane_data

#                 else:

#                     product = Product(
#                         series="Airplane",
#                         data=airplane_data,
#                         manufacturer_id=manufacturer.id
#                     )

#                     db.add(product)

#             products_2 = row.get("products 2")

#             if products_2:

#                 helicopter_data = [
#                     item.strip()
#                     for item in products_2.split(",")
#                     if item.strip()
#                 ]

#                 existing_product = (
#                     db.query(Product)
#                     .filter(
#                         Product.manufacturer_id == manufacturer.id,
#                         Product.series == "Helicopter"
#                     )
#                     .first()
#                 )

#                 if existing_product:

#                     if existing_product.data != helicopter_data:
#                         existing_product.data = helicopter_data

#                 else:

#                     product = Product(
#                         series="Helicopter",
#                         data=helicopter_data,
#                         manufacturer_id=manufacturer.id
#                     )

#                     db.add(product)

#         db.commit()

#         aviation_chronicle_import_jobs[task_id] = {
#             "status": "completed",
#             "inserted_records": inserted_count,
#             "updated_records": updated_count,
#             "manufacturer_ids": uploaded_manufacturer_ids
#         }

#         print(
#             f"Manufacturer import completed. "
#             f"Inserted: {inserted_count}, "
#             f"Updated: {updated_count}"
#         )

#     except Exception as e:

#         db.rollback()

#         aviation_chronicle_import_jobs[task_id] = {
#             "status": "failed",
#             "inserted_records": 0,
#             "updated_records": 0,
#             "manufacturer_ids": [],
#             "message": "Failed to import manufacturer data"
#         }

#         print(
#             f"Failed to import manufacturer data: {e}"
#         )

#     finally:
#         db.close()




async def upload_aviation_chronicle_csv(
    file: UploadFile,
    db: Session,
    background_tasks: BackgroundTasks
):

    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are allowed"
        )
    
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
        for column in REQUIRED_AVIATION_CHRONICLE_CSV_COLUMNS
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

        for required_field in REQUIRED_AVIATION_CHRONICLE_CSV_COLUMNS:

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
        
    task_id = str(uuid.uuid4())

    aviation_chronicle_import_jobs[task_id] = {
        "status": "processing",
        "inserted_records": 0,
        "updated_records": 0,
        "manufacturer_ids": []
    }

    # background_tasks.add_task(
    #     process_aviation_chronicle_csv,
    #     rows,
    #     task_id
    # )

    return {
        "success": True,
        "task_id": task_id,
        "message": "Aviation Chronicle import started in background."
    }




async def delete_aviation_chronicle(
    db: Session,
    aviation_chronicle_id: str
):
    aviation_chronicle = (
        db.query(AviationChronicle)
        .filter(AviationChronicle.id == aviation_chronicle_id)
        .first()
    )

    if not aviation_chronicle:
        raise HTTPException(
            status_code=404,
            detail="Aviation Chronicle not found"
        )

    db.delete(aviation_chronicle)
    db.commit()

    return {
        "message": "Aviation Chronicle deleted successfully",
        "id": aviation_chronicle_id
    } 
    
    
    
async def bulk_delete_aviation_chronicle(
    db: Session,
    aviation_chronicle_ids: list[str]
):
    aviation_chronicle = (
        db.query(AviationChronicle)
        .filter(AviationChronicle.id.in_(aviation_chronicle_ids))
        .all()
    )

    if not aviation_chronicle:
        raise HTTPException(
            status_code=404,
            detail="Aviation Chronicle not found"
        )

    deleted_ids = [chronicle.id for chronicle in aviation_chronicle]
    for chronicle in aviation_chronicle:
        db.delete(chronicle)

    db.commit()

    return {
        "message": "Aviation Chronicle deleted successfully",
        "deleted_count": len(deleted_ids),
        "deleted_ids": deleted_ids,
    }



async def bulk_approve_aviation_chronicle(
    db: Session,
    aviation_chronicle_ids: list[str]
):
    aviation_chronicle = (
        db.query(AviationChronicle)
        .filter(AviationChronicle.id.in_(aviation_chronicle_ids))
        .all()
    )

    if not aviation_chronicle:
        raise HTTPException(
            status_code=404,
            detail="Aviation Chronicle not found"
        )

    for chronicle in aviation_chronicle:
        chronicle.is_approved = True
        chronicle.is_approved_time = datetime.utcnow()

    db.commit()

    return {
        "message": "Aviation Chronicle Approved successfully",
        "updated_count": len(aviation_chronicle),
        "aviation_chronicle": [
            {
                "id": chronicle.id,
                "is_approved": chronicle.is_approved,
                "is_approved_time": chronicle.is_approved_time
            }
            for chronicle in aviation_chronicle
        ]
    }
    
    

async def bulk_disapprove_aviation_chronicle(
    db: Session,
    aviation_chronicle_ids: list[str]
):
    aviation_chronicle = (
        db.query(AviationChronicle)
        .filter(AviationChronicle.id.in_(aviation_chronicle_ids))
        .all()
    )

    if not aviation_chronicle:
        raise HTTPException(
            status_code=404,
            detail="Aviation Chronicle not found"
        )

    for chronicle in aviation_chronicle:
        chronicle.is_approved = False

    db.commit()

    return {
        "message": "Aviation Chronicle disapproved successfully",
        "updated_count": len(aviation_chronicle),
        "aviation_chronicle": [
            {
                "id": chronicle.id,
                "is_approved": chronicle.is_approved,
                "is_approved_time": chronicle.is_approved_time
            }
            for chronicle in aviation_chronicle
        ]
    }
    
        