# QueuedEventCollection

A collection of Dataset Dag Run Queues.  *New in version 2.9.0* 

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**total_entries** | **int** | Count of total objects in the current result set before pagination parameters (limit, offset) are applied.  | [optional] 
**datasets** | [**List[QueuedEvent]**](QueuedEvent.md) |  | [optional] 

## Example

```python
from airflow_client.models.queued_event_collection import QueuedEventCollection

# TODO update the JSON string below
json = "{}"
# create an instance of QueuedEventCollection from a JSON string
queued_event_collection_instance = QueuedEventCollection.from_json(json)
# print the JSON string representation of the object
print(QueuedEventCollection.to_json())

# convert the object into a dict
queued_event_collection_dict = queued_event_collection_instance.to_dict()
# create an instance of QueuedEventCollection from a dict
queued_event_collection_from_dict = QueuedEventCollection.from_dict(queued_event_collection_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


