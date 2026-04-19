{{
    config(
        materialized='table',
        partition_by={
            'field': 'measured_date',
            'data_type': 'date',
            'granularity': 'day'
        },
        cluster_by=['aqi_category']
    )
}}


with sub as (
    select * from {{ ref('int_aqi_sub_indices') }}
),

hourly as (
    select
        location_id,
        date(measured_from)                                    as measured_date,
        time(measured_from)                                    as measured_hour,
        
        -- pivot pollutants into columns
        round(max(case when parameter = 'no2'  then sub_index end), 2)  as aqi_no2,
        round(max(case when parameter = 'o3'   then sub_index end), 2)  as aqi_o3,
        round(max(case when parameter = 'pm25' then sub_index end), 2)  as aqi_pm25,
        round(max(case when parameter = 'pm10' then sub_index end), 2)  as aqi_pm10,
        round(max(sub_index), 2)                               as aqi_score

    from sub
    group by 1, 2, 3
),

categorized as (
    select
        *,
        datetime(measured_date, measured_hour)  as measured_datetime,   -- ← derived here

        case
            when aqi_score <= 25  then 'Good'
            when aqi_score <= 50  then 'Fair'
            when aqi_score <= 75  then 'Poor'
            when aqi_score <= 100 then 'Very Poor'
            else                       'Extremely Poor'
        end as aqi_category

    from hourly
)

select * from categorized