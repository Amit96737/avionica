from sqlalchemy.orm import Session
from user.models import Glossary
from database import SessionLocal
from fastapi import HTTPException, UploadFile, BackgroundTasks
from datetime import datetime
import csv
import io
import uuid



glossary_import_jobs = {}
    



def process_glossary_csv(rows, task_id):
    db = SessionLocal()

    try:
        inserted_count = 0
        updated_count = 0
        uploaded_glossary_ids = []

        for row in rows:

            if "Title" in row and "Storyline" in row:
                title = row.get("Title")
                storyline = row.get("Storyline")


            if title is not None:
                title = title.strip()

            if storyline is not None:
                storyline = storyline.strip()

            user_glossary = Glossary(
                title=title,
                description=storyline
            )

            db.add(user_glossary)
            db.flush()

            inserted_count += 1
            
            uploaded_glossary_ids.append(
                user_glossary.id
            )

        db.commit()

        glossary_import_jobs[task_id] = {
            "status": "completed",
            "inserted_records": inserted_count,
            "updated_records": updated_count,
            "uploaded_glossary_ids": uploaded_glossary_ids
        }

    except Exception as e:
        db.rollback()

        glossary_import_jobs[task_id] = {
            "status": "failed",
            "inserted_records": 0,
            "updated_records": 0,
            "uploaded_glossary_ids": [],
            "message": "Failed to import glossary data"
        }

        print(f"Failed to import glossary data: {e}")

    finally:
        db.close()




async def upload_glossary_csv(
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

    format_1 = {"Title", "Storyline"}

    if not (
        format_1.issubset(headers)
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid CSV format. Required columns are either "
                "'Title, Storyline'."
            )
        )

    rows = list(reader)

    if not rows:
        raise HTTPException(
            status_code=400,
            detail="CSV file glossary no data."
        )

    validation_errors = []

    for row_number, row in enumerate(rows, start=2):

        if format_1.issubset(headers):
            required_fields = ["Title", "Storyline"]

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

    glossary_import_jobs[task_id] = {
        "status": "processing",
        "inserted_records": 0,
        "updated_records": 0,
        "glossary_ids": []
    }

    background_tasks.add_task(
        process_glossary_csv,
        rows,
        task_id
    )

    return {
        "success": True,
        "task_id": task_id,
        "message": "Glossary import started in background."
    }




async def get_glossary_details(db: Session, pagination):
    user_glossary = (
        db.query(Glossary)
        .order_by(Glossary.title.asc())
    )
    
    total_count = user_glossary.count()
    paginated_query = pagination.paginate_query(user_glossary)
    glossary = paginated_query.all()

    return pagination.get_paginated_response(
        glossary,
        total_count,
        detail="Glossary fetched successfully.")
    
    


async def delete_glossary(
    db: Session,
    glossary_id: str
):
    user_glossary = (
        db.query(Glossary)
        .filter(Glossary.id == glossary_id)
        .first()
    )

    if not user_glossary:
        raise HTTPException(
            status_code=404,
            detail="Glossary not found"
        )

    db.delete(user_glossary)
    db.commit()

    return {
        "message": "Glossary deleted successfully",
        "id": glossary_id
    } 
    
    
    
    
async def bulk_delete_glossary(
    db: Session,
    glossary_ids: list[str]
):
    user_glossary = (
        db.query(Glossary)
        .filter(Glossary.id.in_(glossary_ids))
        .all()
    )

    if not user_glossary:
        raise HTTPException(
            status_code=404,
            detail="Glossary not found"
        )

    deleted_ids = [glossary.id for glossary in user_glossary]
    for glossary in user_glossary:
        db.delete(glossary)

    db.commit()

    return {
        "message": "Glossary  deleted successfully",
        "deleted_count": len(deleted_ids),
        "deleted_ids": deleted_ids,
    }




async def bulk_approve_glossary(
    db: Session,
    glossary_ids: list[str]
):
    user_glossary = (
        db.query(Glossary)
        .filter(Glossary.id.in_(glossary_ids))
        .all()
    )

    if not user_glossary:
        raise HTTPException(
            status_code=404,
            detail="Glossary not found"
        )

    for glossary in user_glossary:
        glossary.is_approved = True
        glossary.is_approved_time = datetime.utcnow()

    db.commit()

    return {
        "message": "Glossary Approved successfully",
        "updated_count": len(user_glossary),
        "glossary": [
            {
                "id": glossary.id,
                "is_approved": glossary.is_approved,
                "is_approved_time": glossary.is_approved_time
            }
            for glossary in user_glossary
        ]
    }
    
    
    

async def bulk_disapprove_glossary(
    db: Session,
    glossary_ids: list[str]
):
    user_glossary = (
        db.query(Glossary)
        .filter(Glossary.id.in_(glossary_ids))
        .all()
    )

    if not user_glossary:
        raise HTTPException(
            status_code=404,
            detail="Glossary not found"
        )

    for glossary in user_glossary:
        glossary.is_approved = False

    db.commit()

    return {
        "message": "Glossary disapproved successfully",
        "updated_count": len(user_glossary),
        "glossary": [
            {
                "id": glossary.id,
                "is_approved": glossary.is_approved,
                "is_approved_time": glossary.is_approved_time
            }
            for glossary in user_glossary
        ]
    }
    
        