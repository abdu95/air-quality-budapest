with stg as (
    select * from {{ ref('stg_openaq__measurements') }}
),

sub_indices as (
    select
        location_id,
        measured_from,
        parameter,
        value,

        case parameter
            -- EU breakpoints (µg/m³), linear interpolation per band
            when 'no2' then
                case
                    when value <= 40   then value / 40 * 25
                    when value <= 90   then 25 + (value - 40)  / 50  * 25
                    when value <= 120  then 50 + (value - 90)  / 30  * 25
                    when value <= 230  then 75 + (value - 120) / 110 * 25
                    when value <= 340  then 100 + (value - 230)/ 110 * 25
                    else 125
                end

            when 'o3' then
                case
                    when value <= 50   then value / 50 * 25
                    when value <= 100  then 25 + (value - 50)  / 50  * 25
                    when value <= 130  then 50 + (value - 100) / 30  * 25
                    when value <= 240  then 75 + (value - 130) / 110 * 25
                    when value <= 380  then 100 + (value - 240)/ 140 * 25
                    else 125
                end

            when 'pm25' then
                case
                    when value <= 10   then value / 10 * 25
                    when value <= 20   then 25 + (value - 10)  / 10  * 25
                    when value <= 25   then 50 + (value - 20)  / 5   * 25
                    when value <= 50   then 75 + (value - 25)  / 25  * 25
                    when value <= 75   then 100 + (value - 50) / 25  * 25
                    else 125
                end

            when 'pm10' then
                case
                    when value <= 20   then value / 20 * 25
                    when value <= 40   then 25 + (value - 20)  / 20  * 25
                    when value <= 50   then 50 + (value - 40)  / 10  * 25
                    when value <= 100  then 75 + (value - 50)  / 50  * 25
                    when value <= 150  then 100 + (value - 100)/ 50  * 25
                    else 125
                end

            else null
        end as sub_index

    from stg
    where parameter in ('no2', 'o3', 'pm25', 'pm10')
)

select * from sub_indices
where sub_index is not null