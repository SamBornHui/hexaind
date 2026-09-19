# TaskInstanceDependencyCollection


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**dependencies** | [**List[TaskFailedDependency]**](TaskFailedDependency.md) |  | [optional] 

## Example

```python
from airflow_client.models.task_instance_dependency_collection import TaskInstanceDependencyCollection

# TODO update the JSON string below
json = "{}"
# create an instance of TaskInstanceDependencyCollection from a JSON string
task_instance_dependency_collection_instance = TaskInstanceDependencyCollection.from_json(json)
# print the JSON string representation of the object
print(TaskInstanceDependencyCollection.to_json())

# convert the object into a dict
task_instance_dependency_collection_dict = task_instance_dependency_collection_instance.to_dict()
# create an instance of TaskInstanceDependencyCollection from a dict
task_instance_dependency_collection_from_dict = TaskInstanceDependencyCollection.from_dict(task_instance_dependency_collection_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


