import requests
import json


API_KEY = "424406784657e8ab26db6f4df574144f8cc45a76e3332615601809a1cda724d2"
BASE_URL = "https://api.openaq.org/v3"
headers = {"X-API-Key": API_KEY}


# Step 1: Find Tashkent locations
locations_resp = requests.get(
    f"{BASE_URL}/locations",
    headers=headers,
    params={
        "coordinates": "41.2995,69.2401",  # lat,lon for Tashkent
        "radius": 25000,
        "limit": 20
    }
)

locations = locations_resp.json()
print(f"Total found: {locations['meta']['found']}")

# used to obtain Location ID: 8881, 4902926
# for loc in locations["results"]:
#     print(f"ID: {loc['id']} | Name: {loc['name']} | Country: {loc['country']['name']} | Coords: {loc['coordinates']}")


# Step 1: Get location details (includes sensor IDs)
loc_resp = requests.get(f"{BASE_URL}/locations/4902926", headers=headers)
loc_data = loc_resp.json()["results"][0]


print(f"First reading: {loc_data['datetimeFirst']['local']}")
print(f"Last reading:  {loc_data['datetimeLast']['local']}")

# print("Sensors at US Embassy Tashkent:")
# for s in loc_data["sensors"]:
#     print(f"  Sensor ID: {s['id']} | Parameter: {s['parameter']['displayName']}")

# Step 2: Get measurements for each sensor
# for s in loc_data["sensors"]:
#     sensor_id = s["id"]
#     param = s["parameter"]

#     resp = requests.get(
#         f"{BASE_URL}/sensors/{sensor_id}/measurements",
#         headers=headers,
#         params={"limit": 5, "order_by": "datetime", "sort_order": "desc"}
#     )
    # data = resp.json()

    # print(f"\n🔍 {param['displayName']} (sensor {sensor_id})")
    # for m in data.get("results", []):
    #     print(f"  {m['value']} {param['units']} at {m['datetime']['local']}")



    # print(f"\nSensor {sensor_id}:")
    # print(json.dumps(resp.json(), indent=2))
    # break  # just check first sensor for now