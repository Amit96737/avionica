from sqlalchemy.orm import Session
from triviagia.models import AviationChronicle
from database import SessionLocal
from fastapi import HTTPException, UploadFile, BackgroundTasks
from datetime import datetime
import csv
import io
import uuid


aviation_chronicle_import_jobs = {}



def process_aviation_chronicle_csv(rows, task_id):
    db = SessionLocal()

    try:
        inserted_count = 0
        updated_count = 0
        uploaded_aviation_chronicle_ids = []

        for row in rows:

            if "Term" in row and "Definition" in row:
                title = row.get("Term")
                description = row.get("Definition")

            else:
                title = row.get("ABBREVIATION")
                description = row.get("DEFINITION")

            if title is not None:
                title = title.strip()

            if description is not None:
                description = description.strip()

            aviation_chronicle = AviationChronicle(
                title=title,
                description=description
            )

            db.add(aviation_chronicle)
            db.flush()

            inserted_count += 1
            uploaded_aviation_chronicle_ids.append(
                aviation_chronicle.id
            )

        db.commit()

        aviation_chronicle_import_jobs[task_id] = {
            "status": "completed",
            "inserted_records": inserted_count,
            "updated_records": updated_count,
            "uploaded_aviation_chronicle_ids": uploaded_aviation_chronicle_ids
        }

    except Exception as e:
        db.rollback()

        aviation_chronicle_import_jobs[task_id] = {
            "status": "failed",
            "inserted_records": 0,
            "updated_records": 0,
            "uploaded_aviation_chronicle_ids": [],
            "message": "Failed to import Aviation Chronicle data"
        }

        print(f"Failed to import Aviation Chronicle data: {e}")

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

    headers = {
        header.strip()
        for header in reader.fieldnames
        if header
    }

    format_1 = {"Term", "Definition"}
    format_2 = {"ABBREVIATION", "DEFINITION"}

    if not (
        format_1.issubset(headers)
        or format_2.issubset(headers)
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid CSV format. Required columns are either "
                "'Term, Definition' or 'ABBREVIATION, DEFINITION'."
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

        if format_1.issubset(headers):
            required_fields = ["Term", "Definition"]
        else:
            required_fields = ["ABBREVIATION", "DEFINITION"]

        for required_field in required_fields:

            value = row.get(required_field)

            if value is None or not str(value).strip():

                validation_errors.append(
                    f"Row {row_number}: '{required_field}' is required."
                )

    if validation_errors:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "CSV contains missing required fields.",
                "errors": validation_errors
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
    
        