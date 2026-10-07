from datetime import date
from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
from aircraft.models import Aircraft
from avionica.models import Manufacturer
from services.s3 import upload_image_to_s3
from urllib.parse import unquote
from database import SessionLocal
import json
from pydantic import ValidationError
from aircraft.schemas import AircraftData


aircraft_import_jobs = {}


def process_aircraft_upload(
    task_id: str,
    manufacturer_id: str,
    files_data: list
):
    db = SessionLocal()
    results = []

    aircraft_import_jobs[task_id] = {
        "status": "processing",
        "message": "Aircraft upload is in progress."
    }

    try:
        for file_data in files_data:
            file_name = file_data["file_name"]
            content = file_data["content"]

            result = {
                "file_name": file_name,
                "status": "failed",
                "message": None,
            }

            try:
                if not file_name.lower().endswith(".json"):
                    result["message"] = "Only JSON files are allowed"
                    results.append(result)
                    continue

                try:
                    data = json.loads(
                        content.decode("utf-8")
                    )
                except (
                    json.JSONDecodeError,
                    UnicodeDecodeError
                ):
                    result["message"] = "Invalid JSON file"
                    results.append(result)
                    continue

                if not isinstance(data, dict):
                    result["message"] = "Wrong JSON file"
                    results.append(result)
                    continue

                if "Identification_Classification" not in data:
                    result["message"] = "Invalid aircraft data: Identification_Classification is required"
                    results.append(result)
                    continue

                aircraft = create_aircraft_from_json(
                    db=db,
                    data=data,
                    manufacturer_id=manufacturer_id,
                )

                # for i in range(1, 101):
                #     aircraft = create_aircraft_from_json(
                #         db=db,
                #         data=data,
                #         manufacturer_id=manufacturer_id,
                #         model_suffix=i,
                #     )

                result["status"] = "success"
                result["message"] = "Aircraft uploaded successfully"
                result["aircraft_id"] = str(aircraft.id)

            except ValueError as e:
                db.rollback()
                result["message"] = str(e)

            except Exception as e:
                db.rollback()
                result["message"] = str(e)

            results.append(result)

        successful_files = [
            result
            for result in results
            if result["status"] == "success"
        ]

        failed_files = [
            result
            for result in results
            if result["status"] == "failed"
        ]

        if not successful_files:
            db.rollback()

            error_messages = [
                result["message"]
                for result in failed_files
                if result.get("message")
            ]

            aircraft_import_jobs[task_id] = {
                "status": "failed",
                "message": error_messages[0]
                if error_messages
                else "No aircraft were uploaded.",
                "successful_files": 0,
                "failed_files": len(failed_files),
            }

            print(
                error_messages[0]
                if error_messages
                else "No aircraft were uploaded."
            )

            return

        try:
            db.commit()

            aircraft_import_jobs[task_id] = {
                "status": "completed",
                "message": "Aircraft upload completed.",
                "successful_files": len(successful_files),
                "failed_files": len(failed_files),
            }

            print(
                f"Aircraft upload completed. "
                f"Successful files: {len(successful_files)}, "
                f"Failed files: {len(failed_files)}"
            )

        except Exception as e:
            db.rollback()

            aircraft_import_jobs[task_id] = {
                "status": "failed",
                "message": f"Database error: {str(e)}",
            }

            print(
                f"Database error during aircraft upload: {e}"
            )

    except Exception as e:
        db.rollback()

        aircraft_import_jobs[task_id] = {
            "status": "failed",
            "message": f"Aircraft background upload failed: {str(e)}",
        }

        print(
            f"Aircraft background upload failed: {e}"
        )

    finally:
        db.close()     



def create_aircraft_from_json(
    db: Session,
    data: dict,
    manufacturer_id: str,
    # model_suffix: int,
):
    try:
        validated_data = AircraftData.model_validate(data)
    except ValidationError as e:
        missing_fields = []

        for error in e.errors():
            field = ".".join(
                str(location)
                for location in error["loc"]
            )

            if error["type"] == "missing":
                missing_fields.append(
                    f"{field} is required"
                )
            else:
                missing_fields.append(
                    f"{field}: {error['msg']}"
                )

        raise ValueError(
            "Invalid aircraft data: "
            + ", ".join(missing_fields)
        )
        
        
    manufacturer = (
        db.query(Manufacturer)
        .filter(
            Manufacturer.id == manufacturer_id
        )
        .first()
    )

    if not manufacturer:
        raise ValueError(
            f"Manufacturer not found with id: {manufacturer_id}"
        )

    identification = data.get(
        "Identification_Classification",
        {}
    )

    powerplant = data.get(
        "Powerplant_Propulsion",
        {}
    )

    dimensions = data.get(
        "Dimensions",
        {}
    )

    weights = data.get(
        "Weights",
        {}
    )

    performance = data.get(
        "Performance",
        {}
    )

    operational = data.get(
        "Operational_Limitations",
        {}
    )

    landing_gear = data.get(
        "Landing_Gear_Configuration",
        {}
    )

    certification = data.get(
        "Certification_Environmental",
        {}
    )

    aircraft_model = identification.get(
        "Aircraft_Model"
    )

    if not aircraft_model:
        raise ValueError(
            "Aircraft_Model is required"
        )
    
    # aircraft_model = f"{aircraft_model}-{model_suffix}"

    existing_aircraft = (
        db.query(Aircraft)
        .filter(Aircraft.Aircraft_Model == aircraft_model)
        .first()
    )

    if existing_aircraft:
        raise ValueError(
            f"Aircraft model already exists: {aircraft_model}"
        )

    maiden_flight = identification.get(
        "Date_of_Maiden_Flight"
    )

    if maiden_flight:
        try:
            maiden_flight = date.fromisoformat(
                maiden_flight
            )
        except (ValueError, TypeError):
            raise ValueError(
                "Invalid Date_of_Maiden_Flight format"
            )

    number_of_engines = powerplant.get(
        "Number_of_Engines"
    )

    if number_of_engines is not None:
        try:
            number_of_engines = int(number_of_engines)
        except (ValueError, TypeError):
            raise ValueError(
                "Number_of_Engines must be a valid integer"
            )

    aircraft = Aircraft(

        # Foreign Key
        manufacturer_id=manufacturer_id,
        images=data.get("images"),

        # Identification
        ICAO_Type_Code=identification.get(
            "ICAO_Type_Code"
        ),

        Aircraft_Model=aircraft_model,

        Aircraft_Role=identification.get(
            "Aircraft_Role"
        ),

        Aircraft_Type=identification.get(
            "Aircraft_Type"
        ),

        Wake_Turbulence_Category=identification.get(
            "Wake_Turbulence_Category"
        ),

        Civilian_Military_or_Dual_Use=identification.get(
            "Civilian_Military_or_Dual_Use"
        ),

        Country_of_Origin=identification.get(
            "Country_of_Origin"
        ),

        Date_of_Maiden_Flight=maiden_flight,

        Year_of_Introduction=identification.get(
            "Year_of_Introduction"
        ),

        Production_Status=identification.get(
            "Production_Status"
        ),

        Avionics_System=identification.get(
            "Avionics_System"
        ),

        Number_of_Crew=identification.get(
            "Number_of_Crew"
        ),

        Number_of_Passengers=identification.get(
            "Number_of_Passengers"
        ),

        Number_of_Engines=number_of_engines,

        Engine=powerplant.get("Engine"),

        APU_Type=powerplant.get("APU_Type"),

        Fuel=powerplant.get("Fuel"),

        # Dimensions
        Wingspan_m=dimensions.get("Wingspan_m"),
        Wingspan_ft=dimensions.get("Wingspan_ft"),
        Length_m=dimensions.get("Length_m"),
        Length_ft=dimensions.get("Length_ft"),
        Height_m=dimensions.get("Height_m"),
        Height_ft=dimensions.get("Height_ft"),
        Wing_Area_m2=dimensions.get("Wing_Area_m2"),
        Cabin_Width_m=dimensions.get("Cabin_Width_m"),
        Door_Height_m=dimensions.get("Door_Height_m"),
        Wingtip_Configuration=dimensions.get(
            "Wingtip_Configuration"
        ),

        # Weights
        Operating_Empty_Weight_kg=weights.get(
            "Operating_Empty_Weight_kg"
        ),
        Maximum_Zero_Fuel_Weight_kg=weights.get(
            "Maximum_Zero_Fuel_Weight_kg"
        ),
        Maximum_Takeoff_Weight_kg=weights.get(
            "Maximum_Takeoff_Weight_kg"
        ),
        Maximum_Payload_kg=weights.get(
            "Maximum_Payload_kg"
        ),
        Maximum_Landing_Weight_kg=weights.get(
            "Maximum_Landing_Weight_kg"
        ),
        Baggage_or_Cargo_Volume=weights.get(
            "Baggage_or_Cargo_Volume"
        ),

        # Performance
        Takeoff_Speed_kts=performance.get(
            "Takeoff_Speed_kts"
        ),
        Takeoff_Distance_m=performance.get(
            "Takeoff_Distance_m"
        ),
        Initial_Climb_Rate_fpm=performance.get(
            "Initial_Climb_Rate_fpm"
        ),
        Average_Rate_of_Climb_fpm=performance.get(
            "Average_Rate_of_Climb_fpm"
        ),
        Maximum_Rate_of_Climb_fpm=performance.get(
            "Maximum_Rate_of_Climb_fpm"
        ),
        Service_Ceiling_ft=performance.get(
            "Service_Ceiling_ft"
        ),
        Max_Certified_Altitude_ft=performance.get(
            "Max_Certified_Altitude_ft"
        ),
        Cruise_Speed_kt=performance.get(
            "Cruise_Speed_kt"
        ),
        Cruise_Mach=performance.get(
            "Cruise_Mach"
        ),
        Maximum_Cruise_Speed_kts_or_Mach=performance.get(
            "Maximum_Cruise_Speed_kts_or_Mach"
        ),
        VMO_kts=performance.get("VMO_kts"),
        MMO_Mach=performance.get("MMO_Mach"),
        Range=performance.get("Range"),
        Initial_Rate_of_Descent_fpm=performance.get(
            "Initial_Rate_of_Descent_fpm"
        ),
        Average_Rate_of_Descent_fpm=performance.get(
            "Average_Rate_of_Descent_fpm"
        ),
        Minimum_Clean_Speed_kts=performance.get(
            "Minimum_Clean_Speed_kts"
        ),
        Approach_Speed_kts=performance.get(
            "Approach_Speed_kts"
        ),
        Approach_Category=performance.get(
            "Approach_Category"
        ),
        Landing_Speed_kts=performance.get(
            "Landing_Speed_kts"
        ),
        Landing_Distance_m=performance.get(
            "Landing_Distance_m"
        ),
        Runway_Length_Required_m=performance.get(
            "Runway_Length_Required_m"
        ),
        Stall_Speed_kts=performance.get(
            "Stall_Speed_kts"
        ),

        # Operational
        Runway_Slope_Limit_percent=operational.get(
            "Runway_Slope_Limit_percent"
        ),
        Max_Crosswind_Normal_Law_kts=operational.get(
            "Max_Crosswind_Normal_Law_kts"
        ),
        Max_Crosswind_Degraded_Law_kts=operational.get(
            "Max_Crosswind_Degraded_Law_kts"
        ),
        Max_Tailwind_Landing_kts=operational.get(
            "Max_Tailwind_Landing_kts"
        ),
        Max_Tailwind_Takeoff_kts=operational.get(
            "Max_Tailwind_Takeoff_kts"
        ),
        Field_Elevation_Limit_ft=operational.get(
            "Field_Elevation_Limit_ft"
        ),
        Max_Runway_Altitude_ft=operational.get(
            "Max_Runway_Altitude_ft"
        ),
        Autoland_Capability=operational.get(
            "Autoland_Capability"
        ),

        # Landing Gear
        Type=landing_gear.get("Type"),
        Number_of_Wheels=landing_gear.get(
            "Number_of_Wheels"
        ),
        Tyre_Size_inches=landing_gear.get(
            "Tyre_Size_inches"
        ),
        Tyre_Pressure_bar_psi=landing_gear.get(
            "Tyre_Pressure_bar_(psi)"
        ),

        # Certification
        Certification_Basis=certification.get(
            "Certification_Basis"
        ),
        EASA_TCDS_Number=certification.get(
            "EASA_TCDS_Number"
        ),
        FAA_TCDS_Number=certification.get(
            "FAA_TCDS_Number"
        ),
        Special_Conditions=certification.get(
            "Special_Conditions"
        ),
        Noise_Compliance=certification.get(
            "Noise_Compliance"
        ),
        Emissions_Category=certification.get(
            "Emissions_Category"
        ),
    )

    db.add(aircraft)
    db.flush()

    return aircraft



def get_aircraft(db: Session):
    aircraft_data = (
        db.query(Aircraft)
        .options(joinedload(Aircraft.manufacturer))
        .order_by(Aircraft.id.desc())
        .all()
    )

    return [
        {
            "id": aircraft.id,
            "images": aircraft.images,
            "Aircraft_Model": aircraft.Aircraft_Model,
            "ICAO_Type_Code": aircraft.ICAO_Type_Code,
            "manufacturer_id": aircraft.manufacturer_id,
            "manufacturer": {
                "id": aircraft.manufacturer.id,
                "company_name": aircraft.manufacturer.company_name,
            } if aircraft.manufacturer else None,
            "Production_Status": aircraft.Production_Status,
            "is_approved": aircraft.is_approved,
            "is_approved_time": aircraft.is_approved_time,
        }
        for aircraft in aircraft_data
    ]



async def delete_aircraft(
    db: Session,
    aircraft_id: str
):
    aircraft_data = (
        db.query(Aircraft)
        .filter(Aircraft.id == aircraft_id)
        .first()
    )

    if not aircraft_data:
        raise HTTPException(
            status_code=404,
            detail="Aircraft not found"
        )

    db.delete(aircraft_data)
    db.commit()

    return {
        "message": "Aircraft deleted successfully",
        "id": aircraft_id
    } 
    
    

async def bulk_delete_aircraft(
    db: Session,
    aircraft_ids: list[str]
):
    aircraft_data = (
        db.query(Aircraft)
        .filter(Aircraft.id.in_(aircraft_ids))
        .all()
    )

    if not aircraft_data:
        raise HTTPException(
            status_code=404,
            detail="No aircraft found"
        )

    deleted_ids = [aircraft.id for aircraft in aircraft_data]

    for aircraft in aircraft_data:
        db.delete(aircraft)

    db.commit()

    return {
        "message": "Aircraft deleted successfully",
        "deleted_count": len(deleted_ids),
        "deleted_ids": deleted_ids,
    }
    


async def update_aircraft(
    db: Session,
    aircraft_id: str
):
    aircraft_data = (
        db.query(Aircraft)
        .filter(Aircraft.id == aircraft_id)
        .first()
    )

    if not aircraft_data:
        raise HTTPException(
            status_code=404,
            detail="Aircraft with this id not found"
        )

    aircraft_data.is_approved = not aircraft_data.is_approved

    if aircraft_data.is_approved:
        aircraft_data.is_approved_time = datetime.utcnow()

    else:
        aircraft_data.is_approved_time = None

    db.commit()
    db.refresh(aircraft_data)

    return {
        "message": "Manufacturer status updated successfully",
        "id": aircraft_data.id,
        "is_approved": aircraft_data.is_approved,
        "is_approved_time": aircraft_data.is_approved_time
    }



def upload_aircraft_images_background(
    aircraft_ids: list[str]
):
    db = SessionLocal()

    try:
        aircraft_data = (
            db.query(Aircraft)
            .filter(Aircraft.id.in_(aircraft_ids))
            .all()
        )

        if not aircraft_data:
            print("No aircraft found for image upload")
            return

        for aircraft in aircraft_data:

            if not aircraft.images:
                continue

            updated_images = []

            for image in aircraft.images:

                image_url = image.get("url")

                if not image_url:
                    updated_images.append(image)
                    continue

                image_url = (
                    unquote(image_url)
                    .strip()
                    .rstrip('"')
                )

                try:
                    s3_image_url = upload_image_to_s3(
                        image_url,
                        folder="test_folder"
                    )

                    if s3_image_url:
                        image["url"] = s3_image_url

                except Exception as e:
                    print(
                        f"Failed to upload aircraft image: "
                        f"{image_url}"
                    )
                    print("Error:", str(e))

                updated_images.append(image)

            aircraft.images = updated_images

        db.commit()

        print(
            f"Aircraft image background task completed: "
            f"{len(aircraft_data)} aircraft"
        )

    except Exception as e:
        db.rollback()
        print(
            "Aircraft image background error:",
            str(e)
        )

    finally:
        db.close()       



async def bulk_disapprove_aircraft(
    db: Session,
    aircraft_ids: list[str]
):
    aircraft_data = (
        db.query(Aircraft)
        .filter(Aircraft.id.in_(aircraft_ids))
        .all()
    )

    if not aircraft_data:
        raise HTTPException(
            status_code=404,
            detail="No aircraft found"
        )

    for aircraft in aircraft_data:
        aircraft.is_approved = False
        aircraft.is_approved_time = None

    db.commit()

    return {
        "message": "Aircraft disapproved successfully",
        "updated_count": len(aircraft_data),
        "aircraft": [
            {
                "id": aircraft.id,
                "is_approved": aircraft.is_approved,
                "is_approved_time": aircraft.is_approved_time
            }
            for aircraft in aircraft_data
        ]
    }
    

