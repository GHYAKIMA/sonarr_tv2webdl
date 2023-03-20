#!/usr/bin/env python3
import os
import requests
import config


def api(method: str, endpoint: str, json: dict = None) -> requests.Response:
    url = config.URL.rstrip("/") + endpoint
    auth_data = {"x-api-key": config.KEY}

    response = requests.api.request(method, url, headers=auth_data, json=json)
    return response


def get_web_quality(resolution: int):
    quality_definitions = api("GET", "/qualitydefinition").json()

    data = [
        x["quality"]["id"]
        for x in quality_definitions
        if x["quality"]["source"] == "web" and x["quality"]["resolution"] == resolution
    ]

    return data[0]


def main():
    if os.environ.get("sonarr_eventtype") == "Download":
        series_id = os.environ.get("sonarr_series_id")
        file_id = os.environ.get("sonarr_episodefile_id")
        file_sourcepath = os.environ.get("sonarr_episodefile_sourcepath")

        if all((x not in file_sourcepath) for x in ["SDTV", "HDTV"]):
            file_data = api("GET", f"/episodefile/{file_id}").json()
            file_quality = file_data["quality"]["quality"]

            if file_quality["source"] == "television":
                web_id = get_web_quality(file_quality["resolution"])

                # Update episode file data
                quality_data = {"id": file_id, "quality": {"quality": {"id": web_id}}}
                api("PUT", f"/episodefile/{file_id}", json=quality_data)

                # Rename episode file
                command_data = {"name": "RenameFiles", "seriesId": series_id, "files": [file_id]}
                api("POST", "/command", json=command_data)


if __name__ == "__main__":
    main()
