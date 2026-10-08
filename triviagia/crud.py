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
    


def process_aviation_chronicle_csv(rows, task_id):

    db = SessionLocal()

    try:

        inserted_count = 0
        updated_count = 0
        uploaded_aviation_chronicle_ids = []

        for row in rows:

            aviation_chronicle_data = {}

            for csv_column, model_column in REQUIRED_AVIATION_CHRONICLE_CSV_COLUMNS.items():

                value = row.get(csv_column)

                if value is not None:
                    value = value.strip()

                aviation_chronicle_data[model_column] = value

            title = aviation_chronicle_data.get(
                "title"
            )

            description = aviation_chronicle_data.get(
                "description"
            )

            existing_aviation_chronicle = (
                db.query(AviationChronicle)
                .filter(
                    AviationChronicle.title == title
                )
                .first()
            )

            if existing_aviation_chronicle:

                has_changes = False

                if existing_aviation_chronicle.description != description:

                    existing_aviation_chronicle.description = description

                    has_changes = True

                if has_changes:

                    updated_count += 1

                aviation_chronicle_id = (
                    existing_aviation_chronicle.id
                )

            else:

                aviation_chronicle = AviationChronicle(
                    **aviation_chronicle_data
                )

                db.add(aviation_chronicle)

                db.flush()

                inserted_count += 1

                aviation_chronicle_id = (
                    aviation_chronicle.id
                )

            if (
                aviation_chronicle_id
                not in uploaded_aviation_chronicle_ids
            ):

                uploaded_aviation_chronicle_ids.append(
                    aviation_chronicle_id
                )

        db.commit()

        aviation_chronicle_import_jobs[task_id] = {
            "status": "completed",
            "inserted_records": inserted_count,
            "updated_records": updated_count,
            "uploaded_aviation_chronicle_ids":
                uploaded_aviation_chronicle_ids
        }

        print(
            f"Aviation Chronicle import completed. "
            f"Inserted: {inserted_count}, "
            f"Updated: {updated_count}"
        )

    except Exception as e:

        db.rollback()

        aviation_chronicle_import_jobs[task_id] = {
            "status": "failed",
            "inserted_records": 0,
            "updated_records": 0,
            "uploaded_aviation_chronicle_ids": [],
            "message":
                "Failed to import Aviation Chronicle data"
        }

        print(
            f"Failed to import Aviation Chronicle data: {e}"
        )

    finally:
        db.close()



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

    background_tasks.add_task(
        process_aviation_chronicle_csv,
        rows,
        task_id
    )

    return {
        "success": True,
        "task_id": task_id,
        "message": "Aviation Chronicle import started in background."
    }



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
    
        