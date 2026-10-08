def validate_airport_json_types(data):

    errors = []

    if not isinstance(data, dict):
        return ["JSON root must be an object/dictionary."]

    general_information = data.get("general_information")

    if not isinstance(general_information, dict):
        errors.append(
            "general_information must be an object/dictionary."
        )
    else:
        if "name" in general_information and not isinstance(
            general_information["name"], str
        ):
            errors.append(
                "general_information.name must be a string."
            )

        if "type" in general_information:
            value = general_information["type"]
            if value is not None and not isinstance(value, str):
                errors.append(
                    "general_information.type must be a string."
                )

        if "url" in general_information:
            value = general_information["url"]
            if value is not None and not isinstance(value, str):
                errors.append(
                    "general_information.url must be a string."
                )

    location = data.get("location")

    if not isinstance(location, dict):
        errors.append(
            "location must be an object/dictionary."
        )
    else:
        if "lat" in location:
            value = location["lat"]

            if (
                not isinstance(value, (int, float))
                or isinstance(value, bool)
            ):
                errors.append(
                    "location.lat must be a number."
                )

        if "lon" in location:
            value = location["lon"]

            if (
                not isinstance(value, (int, float))
                or isinstance(value, bool)
            ):
                errors.append(
                    "location.lon must be a number."
                )

        if "city" in location:
            value = location["city"]

            if value is not None and not isinstance(value, str):
                errors.append(
                    "location.city must be a string."
                )

        if "state" in location:
            value = location["state"]

            if value is not None and not isinstance(value, str):
                errors.append(
                    "location.state must be a string."
                )

        if "country" in location:
            value = location["country"]

            if not isinstance(value, str):
                errors.append(
                    "location.country must be a string."
                )

    time_information = data.get("time_information")

    if time_information is not None:

        if not isinstance(time_information, dict):
            errors.append(
                "time_information must be an object/dictionary."
            )
        else:
            for field in ["tz", "utc"]:

                if field in time_information:
                    value = time_information[field]

                    if value is not None and not isinstance(
                        value, str
                    ):
                        errors.append(
                            f"time_information.{field} "
                            f"must be a string."
                        )

    codes = data.get("codes")

    if not isinstance(codes, dict):
        errors.append(
            "codes must be an object/dictionary."
        )
    else:
        for field in ["code", "icao"]:

            if field in codes:
                value = codes[field]

                if value is not None and not isinstance(
                    value, str
                ):
                    errors.append(
                        f"codes.{field} must be a string."
                    )

    runway_information = data.get("runway_information")

    if runway_information is not None:

        if not isinstance(runway_information, dict):
            errors.append(
                "runway_information must be an object/dictionary."
            )
        else:
            fields = [
                "number_Runways",
                "runway_s_direction",
                "runway_s_length_m",
                "elevation_ft",
                "runway_surface_type",
                "number__terminals",
            ]

            for field in fields:

                if field in runway_information:
                    value = runway_information[field]

                    if value is not None and not isinstance(
                        value, str
                    ):
                        errors.append(
                            f"runway_information.{field} "
                            f"must be a string."
                        )

    operational_statistics = data.get(
        "operational_statistics"
    )

    if operational_statistics is not None:

        if not isinstance(operational_statistics, dict):
            errors.append(
                "operational_statistics must be an object/dictionary."
            )
        else:
            fields = [
                "annual_movements_approx",
                "annual_passenger_traffic_approx",
            ]

            for field in fields:

                if field in operational_statistics:
                    value = operational_statistics[field]

                    if value is not None and not isinstance(
                        value, str
                    ):
                        errors.append(
                            f"operational_statistics.{field} "
                            f"must be a string."
                        )

    return errors