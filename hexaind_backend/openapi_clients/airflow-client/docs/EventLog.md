# EventLog

Log of user operations via CLI or Web UI.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**event_log_id** | **int** | The event log ID | [optional] [readonly] 
**when** | **datetime** | The time when these events happened. | [optional] [readonly] 
**dag_id** | **str** | The DAG ID | [optional] [readonly] 
**task_id** | **str** | The Task ID | [optional] [readonly] 
**run_id** | **str** | The DAG Run ID | [optional] [readonly] 
**map_index** | **int** | The Map Index | [optional] [readonly] 
**try_number** | **int** | The Try Number | [optional] [readonly] 
**event** | **str** | A key describing the type of event. | [optional] [readonly] 
**execution_date** | **datetime** | When the event was dispatched for an object having execution_date, the value of this field.  | [optional] [readonly] 
**owner** | **str** | Name of the user who triggered these events a. | [optional] [readonly] 
**extra** | **str** | Other information that was not included in the other fields, e.g. the complete CLI command.  | [optional] [readonly] 

## Example

```python
from airflow_client.models.event_log import EventLog

# TODO update the JSON string below
json = "{}"
# create an instance of EventLog from a JSON string
event_log_instance = EventLog.from_json(json)
# print the JSON string representation of the object
print(EventLog.to_json())

# convert the object into a dict
event_log_dict = event_log_instance.to_dict()
# create an instance of EventLog from a dict
event_log_from_dict = EventLog.from_dict(event_log_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


