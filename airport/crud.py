from sqlalchemy.orm import Session
from airport.models import AirportData
import json
from database import SessionLocal
from fastapi import HTTPException

airport_import_jobs = {}


def process_airport_upload(files_data, task_id):

    db = SessionLocal()

    inserted_count = 0
    updated_count = 0
    failed_count = 0

    inserted_airports = []
    already_exists_files = []

    airport_import_jobs[task_id].update({
        "status": "processing",
        "message": "Airport upload is processing."
    })

    try:

        for file_data in files_data:

            file_name = file_data["file_name"]
            content = file_data["content"]

            try:

                data = json.loads(
                    content.decode("utf-8")
                )

                general_information = data.get(
                    "general_information", {}
                )

                location = data.get(
                    "location", {}
                )

                time_information = data.get(
                    "time_information", {}
                )

                codes = data.get(
                    "codes", {}
                )

                runway_information = data.get(
                    "runway_information", {}
                )

                operational_statistics = data.get(
                    "operational_statistics", {}
                )

                name = general_information.get("name")
                latitude = location.get("lat")
                longitude = location.get("lon")
                country = location.get("country")

                if not name:
                    raise ValueError(
                        "general_information.name is required"
                    )

                if latitude is None:
                    raise ValueError(
                        "location.lat is required"
                    )

                if longitude is None:
                    raise ValueError(
                        "location.lon is required"
                    )

                if not country:
                    raise ValueError(
                        "location.country is required"
                    )

                iata_code = codes.get("code")
                icao_code = codes.get("icao")

                existing_airport = None

                if iata_code and icao_code:

                    existing_airport = (
                        db.query(AirportData)
                        .filter(
                            AirportData.iata_code == iata_code,
                            AirportData.icao == icao_code
                        )
                        .first()
                    )

                if existing_airport:

                    already_exists_files.append(
                        file_name
                    )

                    print(
                        f"ALREADY EXISTS: {file_name}"
                    )

                    continue

                airport_data = {

                    "name": name,

                    "type": general_information.get(
                        "type"
                    ),

                    "website_url": general_information.get(
                        "url"
                    ),

                    "latitude_deg": latitude,
                    "longitude_deg": longitude,

                    "city": location.get(
                        "city"
                    ),

                    "state": location.get(
                        "state"
                    ),

                    "country": country,

                    "timezone": time_information.get(
                        "tz"
                    ),

                    "utc_offset": time_information.get(
                        "utc"
                    ),

                    "iata_code": iata_code,
                    "icao": icao_code,

                    "number_of_runways":
                        runway_information.get(
                            "number_Runways"
                        ),

                    "runway_direction":
                        runway_information.get(
                            "runway_s_direction"
                        ),

                    "runway_length":
                        runway_information.get(
                            "runway_s_length_m"
                        ),

                    "elev":
                        runway_information.get(
                            "elevation_ft"
                        ),

                    "runway_surface_type":
                        runway_information.get(
                            "runway_surface_type"
                        ),

                    "number_of_terminals":
                        runway_information.get(
                            "number__terminals"
                        ),

                    "annual_movements":
                        operational_statistics.get(
                            "annual_movements_approx"
                        ),

                    "annual_passenger_traffic":
                        operational_statistics.get(
                            "annual_passenger_traffic_approx"
                        ),

                    "airport_weather": None,
                }

                airport = AirportData(
                    **airport_data
                )

                db.add(airport)

                db.flush()

                inserted_airports.append({

                    "id": airport.id,

                    "name": airport.name,
                    "type": airport.type,
                    "website_url": airport.website_url,

                    "latitude_deg":
                        airport.latitude_deg,

                    "longitude_deg":
                        airport.longitude_deg,

                    "city": airport.city,
                    "state": airport.state,
                    "country": airport.country,

                    "timezone":
                        airport.timezone,

                    "utc_offset":
                        airport.utc_offset,

                    "iata_code":
                        airport.iata_code,

                    "icao":
                        airport.icao,

                    "number_of_runways":
                        airport.number_of_runways,

                    "runway_direction":
                        airport.runway_direction,

                    "runway_length":
                        airport.runway_length,

                    "elev":
                        airport.elev,

                    "runway_surface_type":
                        airport.runway_surface_type,

                    "number_of_terminals":
                        airport.number_of_terminals,

                    "annual_movements":
                        airport.annual_movements,

                    "annual_passenger_traffic":
                        airport.annual_passenger_traffic,

                    "airport_weather":
                        airport.airport_weather,

                    "is_approved":
                        airport.is_approved,
                })

                inserted_count += 1

                print(
                    f"INSERTED AIRPORT: {file_name}"
                )

                db.commit()

            except Exception as file_error:

                db.rollback()

                failed_count += 1

                print(
                    f"FAILED AIRPORT FILE: {file_name}"
                )

                print(
                    f"ERROR: {file_error}"
                )

        # print("=" * 60)
        # print("AIRPORT UPLOAD COMPLETED")
        # print(f"Inserted: {inserted_count}")
        # print(f"Updated: {updated_count}")
        # print(f"Already Exists: {len(already_exists_files)}")
        # print(f"Failed: {failed_count}")
        # print("=" * 60)

        airport_import_jobs[task_id].update({
            "status": "completed",
            "inserted_count": inserted_count,
            "updated_count": updated_count,
            "already_exists_count": len(already_exists_files),
            "failed_count": failed_count,
            "inserted_airports": inserted_airports,
            "already_exists_files": already_exists_files,
            "message":
                "Airport upload completed successfully."
        })

    except Exception as error:

        db.rollback()

        airport_import_jobs[task_id].update({
            "status": "failed",
            "inserted_count": inserted_count,
            "updated_count": updated_count,
            "already_exists_count": len(already_exists_files),
            "failed_count": failed_count,
            "inserted_airports": inserted_airports,
            "already_exists_files": already_exists_files,
            "message": str(error)
        })

        print(
            f"AIRPORT BACKGROUND UPLOAD ERROR: {error}"
        )

    finally:

        db.close()        
        
        
        
def get_airport(db: Session, pagination):
    airport_data = (
        db.query(AirportData)
        .order_by(AirportData.name.asc())
    )
    
    total_count = airport_data.count()
    
    paginated_query = pagination.paginate_query(airport_data)
    
    airport = paginated_query.all()

    return pagination.get_paginated_response(
        airport,
        total_count,
        detail="Airport fetched successfully.")
        


async def delete_airport(
    db: Session,
    airport_id: str
):
    airport_data = (
        db.query(AirportData)
        .filter(AirportData.id == airport_id)
        .first()
    )

    if not airport_data:
        raise HTTPException(
            status_code=404,
            detail="Airport not found"
        )

    db.delete(airport_data)
    db.commit()

    return {
        "message": "Airport deleted successfully",
        "id": airport_id
    } 
    
    
    
async def bulk_delete_airport(
    db: Session,
    airport_ids: list[str]
):
    airport_data = (
        db.query(AirportData)
        .filter(AirportData.id.in_(airport_ids))
        .all()
    )

    if not airport_data:
        raise HTTPException(
            status_code=404,
            detail="Airport not found"
        )

    deleted_ids = [airport.id for airport in airport_data]

    for airport in airport_data:
        db.delete(airport)

    db.commit()

    return {
        "message": "Airport deleted successfully",
        "deleted_count": len(deleted_ids),
        "deleted_ids": deleted_ids,
    }



async def bulk_disapprove_airport(
    db: Session,
    airport_ids: list[str]
):
    airport_data = (
        db.query(AirportData)
        .filter(AirportData.id.in_(airport_ids))
        .all()
    )

    if not airport_data:
        raise HTTPException(
            status_code=404,
            detail="Aircraft not found"
        )

    for airport in airport_data:
        airport.is_approved = False

    db.commit()

    return {
        "message": "Airport disapproved successfully",
        "updated_count": len(airport_data),
        "airport": [
            {
                "id": airport.id,
                "is_approved": airport.is_approved,
                "is_approved_time": airport.is_approved_time
            }
            for airport in airport_data
        ]
    }