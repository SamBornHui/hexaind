# TaskInstanceHistoryCollection

Collection of task instances .  *Changed in version 2.1.0*&#58; 'total_entries' field is added. 

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**total_entries** | **int** | Count of total objects in the current result set before pagination parameters (limit, offset) are applied.  | [optional] 
**task_instances_history** | [**List[TaskInstanceHistory]**](TaskInstanceHistory.md) |  | [optional] 

## Example

```python
from airflow_client.models.task_instance_history_collection import TaskInstanceHistoryCollection

# TODO update the JSON string below
json = "{}"
# create an instance of TaskInstanceHistoryCollection from a JSON string
task_instance_history_collection_instance = TaskInstanceHistoryCollection.from_json(json)
# print the JSON string representation of the object
print(TaskInstanceHistoryCollection.to_json())

# convert the object into a dict
task_instance_history_collection_dict = task_instance_history_collection_instance.to_dict()
# create an instance of TaskInstanceHistoryCollection from a dict
task_instance_history_collection_from_dict = TaskInstanceHistoryCollection.from_dict(task_instance_history_collection_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


