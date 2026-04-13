import requests

TOKEN = "7494731f1f3ed160d720cbb7315115c4781ee09e"

# Tashkent by city name
# resp = requests.get(f"https://api.waqi.info/feed/tashkent/?token={TOKEN}")
# data = resp.json()



resp = requests.get(
    f"https://api.waqi.info/search/?token={TOKEN}&keyword=budapest"
)

data = resp.json()
# print(f"Total stations found: {len(data['data'])}")
# for station in data["data"]:
#     print(f"  ID: @{station['uid']} | Name: {station['station']['name']} | AQI: {station['aqi']} | Time: {station['time']['stime']}")


active_stations = [uid for uid in [3367, 3371, 3375, 3368, 3373, 3876, 3372, 8044]]

for uid in active_stations:
    resp = requests.get(f"https://api.waqi.info/feed/@{uid}/?token={TOKEN}")
    data = resp.json()["data"]
    
    print(f"\n📍 {data['city']['name']}")
    print(f"  AQI: {data['aqi']} | Time: {data['time']['s']}")
    for pollutant in ["pm25", "pm10", "o3", "no2", "co", "so2"]:
        val = data["iaqi"].get(pollutant, {}).get("v", "N/A")
        print(f"  {pollutant.upper()}: {val}")