# QueuedEvent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**uri** | **str** | The datata uri. | [optional] 
**dag_id** | **str** | The DAG ID. | [optional] 
**created_at** | **datetime** | The creation time of QueuedEvent | [optional] 

## Example

```python
from airflow_client.models.queued_event import QueuedEvent

# TODO update the JSON string below
json = "{}"
# create an instance of QueuedEvent from a JSON string
queued_event_instance = QueuedEvent.from_json(json)
# print the JSON string representation of the object
print(QueuedEvent.to_json())

# convert the object into a dict
queued_event_dict = queued_event_instance.to_dict()
# create an instance of QueuedEvent from a dict
queued_event_from_dict = QueuedEvent.from_dict(queued_event_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


