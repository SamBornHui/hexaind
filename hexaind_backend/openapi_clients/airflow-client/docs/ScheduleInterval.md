# ScheduleInterval

Schedule interval. Defines how often DAG runs, this object gets added to your latest task instance's execution_date to figure out the next schedule. 

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**type** | **str** |  | 
**days** | **int** |  | 
**seconds** | **int** |  | 
**microseconds** | **int** |  | 
**years** | **int** |  | 
**months** | **int** |  | 
**leapdays** | **int** |  | 
**hours** | **int** |  | 
**minutes** | **int** |  | 
**year** | **int** |  | 
**month** | **int** |  | 
**day** | **int** |  | 
**hour** | **int** |  | 
**minute** | **int** |  | 
**second** | **int** |  | 
**microsecond** | **int** |  | 
**value** | **str** |  | 

## Example

```python
from airflow_client.models.schedule_interval import ScheduleInterval

# TODO update the JSON string below
json = "{}"
# create an instance of ScheduleInterval from a JSON string
schedule_interval_instance = ScheduleInterval.from_json(json)
# print the JSON string representation of the object
print(ScheduleInterval.to_json())

# convert the object into a dict
schedule_interval_dict = schedule_interval_instance.to_dict()
# create an instance of ScheduleInterval from a dict
schedule_interval_from_dict = ScheduleInterval.from_dict(schedule_interval_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


