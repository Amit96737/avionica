from pydantic import BaseModel, Field, validator, ConfigDict, field_validator
from typing import Optional, List
from datetime import datetime, date


class Passengers(BaseModel):
    Typical: str
    Maximum: str


class IdentificationClassification(BaseModel):
    ICAO_Type_Code: str
    Manufacturer: Optional[str] = ""
    manufacturer_id: Optional[str]
    Aircraft_Model: str
    Aircraft_Role: str
    Aircraft_Type: str
    Wake_Turbulence_Category: str
    Civilian_Military_or_Dual_Use: str
    Country_of_Origin: str
    Date_of_Maiden_Flight: date  # could also be datetime.date
    Year_of_Introduction: str
    Production_Status: str
    Avionics_System: str
    Number_of_Crew: str
    Number_of_Passengers: Passengers

    model_config = ConfigDict(from_attributes=True)

    # @validator("Date_of_Maiden_Flight", pre=True)
    # def parse_maiden_flight_date(cls, value):
    #     if isinstance(value, date):
    #         return value
    #     try:
    #         return datetime.strptime(value, "%d %B %Y").date()
    #     except ValueError:
    #         raise ValueError("Date_of_Maiden_Flight must be in format 'DD Month YYYY' (e.g., '17 September 1997')")


class Engine(BaseModel):
    Manufacturer: str
    Model: str
    Engine_Type: str
    Thrust_Per_Engine_kN_or_kW: str
    Physical_Engine_Code: str


class FuelSchema(BaseModel):
    Fuel_Type: str
    Fuel_Additives: str
    Capacity_L_or_kg: str
    Fuel_Burn_Cruise_kg_per_hr: str


class PowerplantPropulsion(BaseModel):
    Number_of_Engines: int
    Engine: Engine
    APU_Type: Optional[str] = None
    Fuel: FuelSchema

    model_config = ConfigDict(from_attributes=True)


class Dimensions(BaseModel):
    Wingspan_m: str
    Wingspan_ft: str
    Length_m: str
    Length_ft: str
    Height_m: str
    Height_ft: str
    Wing_Area_m2: str
    Cabin_Width_m: str
    Door_Height_m: str
    Wingtip_Configuration: str

    model_config = ConfigDict(from_attributes=True)


class BaggageCargoVolume(BaseModel):
    Minimum_m3: str
    Maximum_m3: str

    @field_validator('Minimum_m3', 'Maximum_m3', mode='before')
    def convert_float_to_str(cls, v):
        return str(v)


class Weights(BaseModel):
    Operating_Empty_Weight_kg: str
    Maximum_Zero_Fuel_Weight_kg: str
    Maximum_Takeoff_Weight_kg: str
    Maximum_Payload_kg: str
    Maximum_Landing_Weight_kg: str
    Baggage_or_Cargo_Volume: BaggageCargoVolume
    model_config = ConfigDict(from_attributes=True)


class RangeSchema(BaseModel):
    Normal_Range_NM: str
    Normal_Range_km: str
    Ferry_Range_NM: str


class Performance(BaseModel):
    Takeoff_Speed_kts: str
    Takeoff_Distance_m: str
    Initial_Climb_Rate_fpm: str
    Average_Rate_of_Climb_fpm: str
    Maximum_Rate_of_Climb_fpm: str
    Service_Ceiling_ft: str
    Max_Certified_Altitude_ft: str
    Cruise_Speed_kt: str
    Cruise_Mach: Optional[str] = "N/A"
    Maximum_Cruise_Speed_kts_or_Mach: str
    VMO_kts: str
    MMO_Mach: Optional[str] = "N/A"
    Range: RangeSchema
    Initial_Rate_of_Descent_fpm: str
    Average_Rate_of_Descent_fpm: str
    Minimum_Clean_Speed_kts: str
    Approach_Speed_kts: str
    Approach_Category: str
    Landing_Speed_kts: str
    Landing_Distance_m: str
    Runway_Length_Required_m: str
    Stall_Speed_kts: str
    model_config = ConfigDict(from_attributes=True)

    @field_validator('Landing_Distance_m', mode='before')
    def convert_int_to_str(cls, v):
        return str(v)


class AutolandCapabilitySchema(BaseModel):
    Supported_Categories: Optional[str] = None
    Certified_Autoland_Level: str


class OperationalLimitations(BaseModel):
    Runway_Slope_Limit_percent: str
    Max_Crosswind_Normal_Law_kts: str
    Max_Crosswind_Degraded_Law_kts: str
    Max_Tailwind_Landing_kts: str
    Max_Tailwind_Takeoff_kts: str
    Field_Elevation_Limit_ft: str
    Max_Runway_Altitude_ft: str
    Autoland_Capability: AutolandCapabilitySchema
    model_config = ConfigDict(from_attributes=True)


class LandingGear(BaseModel):
    Type: str
    Number_of_Wheels: str
    Tyre_Size_inches: str
    Tyre_Pressure_bar_psi: str
    model_config = ConfigDict(from_attributes=True)


class CertificationEnvironmental(BaseModel):
    Certification_Basis: str
    EASA_TCDS_Number: Optional[str] = "N/A"
    FAA_TCDS_Number: Optional[str] = "N/A"
    Special_Conditions: Optional[str] = None
    Noise_Compliance: str
    Emissions_Category: str

    model_config = ConfigDict(from_attributes=True)


class AircraftImg(BaseModel):
    url: str = Field(..., min_length=1)
    cc: Optional[str] = ""
    is_default: Optional[bool] = False


class AircraftData(BaseModel):
    Identification_Classification: IdentificationClassification
    Powerplant_Propulsion: PowerplantPropulsion
    Dimensions: Dimensions
    Weights: Weights
    Performance: Performance
    Operational_Limitations: OperationalLimitations
    Landing_Gear_Configuration: LandingGear
    Certification_Environmental: CertificationEnvironmental
    images: list[dict]
    # images: List[AircraftImg]

class DeleteAircraftRequest(BaseModel):
    aircraft_id: str
    
    
class BulkDeleteAircraftRequest(BaseModel):
    aircraft_ids: List[str]
    
    
class BulkApproveAircraftRequest(BaseModel):
    aircraft_ids: List[str]
    
    
class UpdateAircraftRequest(BaseModel):
    aircraft_id: str
