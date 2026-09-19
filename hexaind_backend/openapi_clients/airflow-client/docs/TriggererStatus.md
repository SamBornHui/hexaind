# TriggererStatus

The status and the latest triggerer heartbeat.  *New in version 2.6.2* 

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | [**HealthStatus**](HealthStatus.md) |  | [optional] 
**latest_triggerer_heartbeat** | **str** | The time the triggerer last did a heartbeat. | [optional] [readonly] 

## Example

```python
from airflow_client.models.triggerer_status import TriggererStatus

# TODO update the JSON string below
json = "{}"
# create an instance of TriggererStatus from a JSON string
triggerer_status_instance = TriggererStatus.from_json(json)
# print the JSON string representation of the object
print(TriggererStatus.to_json())

# convert the object into a dict
triggerer_status_dict = triggerer_status_instance.to_dict()
# create an instance of TriggererStatus from a dict
triggerer_status_from_dict = TriggererStatus.from_dict(triggerer_status_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


