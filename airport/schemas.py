from pydantic import BaseModel, ConfigDict, StrictFloat
from typing import Optional
from typing import Optional, List
# from airport.models import AirportCreditType


class AirportBase(BaseModel):
    iata_code: str
    name: str
    latitude_deg: float
    longitude_deg: float
    city: str
    state: str
    country: str
    timezone: str
    type: str
    runway_length: int
    elev: str
    icao: str


class AirportResponse(AirportBase):
    id: str

    model_config = ConfigDict(from_attributes=True)


class AirportShotDetails(BaseModel):
    id: str
    name: str
    city: str
    state: str
    country: str
    longitude_deg: Optional[float] = None
    latitude_deg : Optional[float] = None

    model_config = ConfigDict(from_attributes=True)




class GeneralInformation(BaseModel):
    name: str
    type: Optional[str]
    url: Optional[str]


class Location(BaseModel):
    lat: StrictFloat
    lon: StrictFloat
    city: Optional[str]
    state: Optional[str]
    country: str


class TimeInformation(BaseModel):
    tz: Optional[str]
    utc: Optional[str]


class Codes(BaseModel):
    code: Optional[str]   # IATA
    icao: Optional[str]


class RunwayInformation(BaseModel):
    number_Runways: Optional[str]
    runway_s_direction: Optional[str]
    runway_s_length_m: Optional[str]
    elevation_ft: Optional[str]
    runway_surface_type: Optional[str]
    number__terminals: Optional[str]


class OperationalStatistics(BaseModel):
    annual_movements_approx: Optional[str]
    annual_passenger_traffic_approx: Optional[str]



class AirportNestedRequest(BaseModel):
    general_information: GeneralInformation
    location: Location
    time_information: Optional[TimeInformation]
    codes: Codes
    runway_information: Optional[RunwayInformation]
    operational_statistics: Optional[OperationalStatistics]


class AirportDataResponse(BaseModel):
    id: str
    name: str
    type: Optional[str]
    website_url: Optional[str]

    latitude_deg: float
    longitude_deg: float
    city: Optional[str]
    state: Optional[str]
    country: str

    timezone: Optional[str]
    utc_offset: Optional[str]

    iata_code: Optional[str]
    icao: Optional[str]

    number_of_runways: Optional[str]
    runway_direction: Optional[str]
    runway_length: Optional[str]
    elev: Optional[str]
    runway_surface_type: Optional[str]
    number_of_terminals: Optional[str]

    annual_movements: Optional[str]
    annual_passenger_traffic: Optional[str]
    airport_weather: Optional[str] = ""

    model_config = ConfigDict(from_attributes=True)


# New Schemas

class DeleteAirportRequest(BaseModel):
    airport_id: str
    
    
class BulkDeleteAirportRequest(BaseModel):
    airport_ids: List[str]
    
    
class BulkApproveAirportRequest(BaseModel):
    airport_ids: List[str]
    

