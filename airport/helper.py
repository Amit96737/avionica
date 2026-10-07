REQUIRED_AIRPORT_FIELDS = {
    "general_information": [
        "name",
        "type",
        # "url",
    ],
    "location": [
        "lat",
        "lon",
        "city",
        "state",
        "country",
    ],
    "time_information": [
        "tz",
        "utc",
    ],
    "codes": [
        "code",
        "icao",
    ],
    "runway_information": [
        "number_Runways",
        "runway_s_direction",
        "runway_s_length_m",
        "elevation_ft",
        "runway_surface_type",
        "number__terminals",
    ],
    "operational_statistics": [
        "annual_movements_approx",
        "annual_passenger_traffic_approx",
    ],
}