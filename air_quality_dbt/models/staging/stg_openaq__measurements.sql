with source as (
    select * from {{ source('openaq', 'measurements') }}
),

cleaned as (
    select
        cast(location_id   as int64)       as location_id,
        cast(sensor_id     as int64)       as sensor_id,
        parameter,
        display_name,
        cast(value         as float64)     as value,
        unit,
        datetime(datetime_from)            as measured_from,
        datetime(datetime_to)              as measured_to,
        datetime(_ingested_at)             as ingested_at,

        -- dedup key
        {{ dbt_utils.generate_surrogate_key([
            'location_id', 'sensor_id', 'datetime_from'
        ]) }}                              as measurement_id

    from source
    where value is not null
      and value >= 0
)

select * from cleaned