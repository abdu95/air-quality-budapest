from openaq import OpenAQ

API_KEY = '424406784657e8ab26db6f4df574144f8cc45a76e3332615601809a1cda724d2'
client = OpenAQ(api_key= API_KEY)

response = client.locations.list(
    coordinates=(47.4979, 19.0402),  # Budapest center
    radius=25000,
    limit=20
)


# response = client.locations.get(783927)  # Budapest Gergely utca
response = client.locations.get(783939)
location = response.results[0]

for sensor in location.sensors:
    measurements = client.measurements.list(
        sensors_id=sensor.id,
        data="hours",
        datetime_from="2026-04-13T00:00:00+00:00",
        datetime_to="2026-04-13T23:59:59+00:00",
        limit=24
    )
    print(f"\n🔍 {sensor.parameter.display_name}")
    for m in measurements.results:
        print(f"  {m.value} {sensor.parameter.units} at {m.period.datetime_from.local}")


client.close()