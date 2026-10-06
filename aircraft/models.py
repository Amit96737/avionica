from common.models import CommonFields
from sqlalchemy import Column, Integer, String, Date, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship, validates
from database import Base
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.dialects.postgresql import JSONB


class Aircraft(CommonFields, Base):
    __tablename__ = "aircrafts"

    images = Column(JSON)

    #  Identification & classification
    manufacturer_id = Column(String, ForeignKey("manufacturers.id", ondelete="CASCADE"), nullable=False, index=True)
    manufacturer = relationship("Manufacturer", back_populates="aircrafts")
    ICAO_Type_Code = Column(String)
    Aircraft_Model = Column(String, unique=True)
    # model_normalized = Column(String, nullable=False, unique=True)

    Aircraft_Role = Column(String)
    Aircraft_Type = Column(String)
    Wake_Turbulence_Category = Column(String)
    Civilian_Military_or_Dual_Use = Column(String)
    Country_of_Origin = Column(String)
    Date_of_Maiden_Flight = Column(Date)
    Year_of_Introduction = Column(String)
    Production_Status = Column(String)
    Avionics_System = Column(String)
    Number_of_Crew = Column(String)
    Number_of_Passengers = Column(JSONB)

    # Powerplant & Propulsion
    Number_of_Engines = Column(Integer)
    Engine = Column(JSONB)
    APU_Type = Column(String, nullable=True)
    Fuel = Column(JSONB)

    # Dimensions
    Wingspan_m = Column(String)
    Wingspan_ft = Column(String)
    Length_m = Column(String)
    Length_ft = Column(String)
    Height_m = Column(String)
    Height_ft = Column(String)
    Wing_Area_m2 = Column(String)
    Cabin_Width_m = Column(String)
    Door_Height_m = Column(String)
    Wingtip_Configuration = Column(String)

    # Weights
    Operating_Empty_Weight_kg = Column(String)
    Maximum_Zero_Fuel_Weight_kg = Column(String)
    Maximum_Takeoff_Weight_kg = Column(String)
    Maximum_Payload_kg = Column(String)
    Maximum_Landing_Weight_kg = Column(String)
    Baggage_or_Cargo_Volume = Column(JSONB)

    # Performance
    Takeoff_Speed_kts = Column(String)
    Takeoff_Distance_m = Column(String)
    Initial_Climb_Rate_fpm = Column(String)
    Average_Rate_of_Climb_fpm = Column(String)
    Maximum_Rate_of_Climb_fpm = Column(String)
    Service_Ceiling_ft = Column(String)
    Max_Certified_Altitude_ft = Column(String)
    Cruise_Speed_kt = Column(String)
    Cruise_Mach = Column(String)
    Maximum_Cruise_Speed_kts_or_Mach = Column(String)
    VMO_kts = Column(String)
    MMO_Mach = Column(String)
    Range = Column(JSONB)
    Initial_Rate_of_Descent_fpm = Column(String)
    Average_Rate_of_Descent_fpm = Column(String)
    Minimum_Clean_Speed_kts = Column(String)
    Approach_Speed_kts = Column(String)
    Approach_Category = Column(String)
    Landing_Speed_kts = Column(String)
    Landing_Distance_m = Column(String)
    Runway_Length_Required_m = Column(String)
    Stall_Speed_kts = Column(String)

    # Operational limitations
    Runway_Slope_Limit_percent = Column(String)
    Max_Crosswind_Normal_Law_kts = Column(String)
    Max_Crosswind_Degraded_Law_kts = Column(String)
    Max_Tailwind_Landing_kts = Column(String)
    Max_Tailwind_Takeoff_kts = Column(String)
    Field_Elevation_Limit_ft = Column(String)  # ft in default
    Max_Runway_Altitude_ft = Column(String)  # ft in default
    Autoland_Capability = Column(JSONB)

    # Landing Gear
    Type = Column(String)
    Number_of_Wheels = Column(String)
    Tyre_Size_inches = Column(String)
    Tyre_Pressure_bar_psi = Column(String)

    # Certification & Environmental
    Certification_Basis = Column(String)
    EASA_TCDS_Number = Column(String)
    FAA_TCDS_Number = Column(String)
    Special_Conditions = Column(String)
    Noise_Compliance = Column(String)
    Emissions_Category = Column(String)
    
    is_approved = Column(Boolean, default=False)
    is_approved_time = Column(DateTime, nullable=True)

    @validates("model")
    def normalize_model(self, key, value: str):
        self.model_normalized = value.lower()
        return value
