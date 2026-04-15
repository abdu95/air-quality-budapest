from openaq import OpenAQ
import pandas as pd

import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime, timezone


API_KEY = 'c72d8691436b5de3c36e9703deeb5ee8134bce3f2900c77d9562a85ae602237b'
client = OpenAQ(api_key= API_KEY)

response = client.locations.list(
    coordinates=(47.4979, 19.0402),  # Budapest center
    radius=25000,
    limit=20
)


response = client.locations.get(783927)  # Budapest Gergely utca
# response = client.locations.get(783939)
location = response.results[0]

records = []

for sensor in location.sensors:
    measurements = client.measurements.list(
        sensors_id=sensor.id,
        data="hours",
        datetime_from="2026-04-13T00:00:00+00:00",
        datetime_to="2026-04-13T23:59:59+00:00",
        limit=24
    )
    for m in measurements.results:
        records.append({
            "location_id":     location.id,
            "sensor_id":       sensor.id,
            "parameter":       sensor.parameter.name,        # "no2", "pm25", "pm10", "co"
            "display_name":    sensor.parameter.display_name,
            "value":           m.value,
            "unit":            sensor.parameter.units,
            "datetime_from":   m.period.datetime_from.utc,   # confirm this attr name
            "datetime_to":     m.period.datetime_to.utc,
        })

df = pd.DataFrame(records)

df["datetime_from"] = df["datetime_from"].astype("datetime64[us, UTC]")
df["datetime_to"]   = df["datetime_to"].astype("datetime64[us, UTC]")
df["_ingested_at"]  = datetime.now(timezone.utc)

df.to_csv("file.csv", index = False) 

# table = pa.Table.from_pandas(df)
# pq.write_table(table, "measurements.parquet")
# print(pq.read_table("measurements.parquet").schema)

client.close()