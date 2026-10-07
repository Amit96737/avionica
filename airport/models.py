from sqlalchemy import Column, Integer, String, Float, UniqueConstraint, Boolean, DateTime
from database import Base
from common.models import CommonFields
import enum


# class Airport(CommonFields, Base):
#     __tablename__ = "airports"

#     iata_code = Column(String(255), nullable=False, unique=True)  # code
#     name = Column(String(255), nullable=True)
#     latitude_deg = Column(Float, nullable=True)
#     longitude_deg = Column(Float, nullable=True)
#     city = Column(String(255))
#     state = Column(String(255))
#     country = Column(String(255))
#     timezone = Column(String(50))
#     type = Column(String(50))
#     runway_length = Column(Integer)
#     elev = Column(String)
#     icao = Column(String)  # unique=True


class AirportData(CommonFields, Base):
    __tablename__ = "airports_data"

    name = Column(String(255), nullable=False)
    type = Column(String(100))
    website_url = Column(String(500))

    latitude_deg = Column(Float, nullable=False)
    longitude_deg = Column(Float, nullable=False)
    city = Column(String(100))
    state = Column(String(100))
    country = Column(String(100), nullable=False)

    timezone = Column(String(100))
    utc_offset = Column(String(50))

    iata_code = Column(String(50), index=True)
    icao = Column(String(50), index=True)

    number_of_runways = Column(String)
    runway_direction = Column(String(50))
    runway_length = Column(String)  # meters
    elev = Column(String)
    runway_surface_type = Column(String(100))
    number_of_terminals = Column(String(50))

    annual_movements = Column(String(50))
    annual_passenger_traffic = Column(String(50))
    airport_weather = Column(String(50))
    
    is_approved = Column(Boolean, default=False)
    is_approved_time = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("iata_code", "icao", name="uq_airport_codes"),
    )


# class AirportCreditType(enum.IntEnum):
#     SUMMARY = 1
#     TRACK_FLIGHT = 2
#     EMPTY_REQUEST = 3
#     TRACK_FLIGHT_WILCO = 4


# class FlightRadarCredit(CommonFields, Base):
#     __tablename__ = "flight_radar_credits"

#     type = Column(Integer, nullable=False)
#     credit = Column(Float, nullable=False)
#     user_id = Column(String(36), nullable=False)
#     subscription_id = Column(String(length=36), nullable=True)
