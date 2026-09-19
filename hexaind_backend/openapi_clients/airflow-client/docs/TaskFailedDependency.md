# TaskFailedDependency


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** |  | [optional] 
**reason** | **str** |  | [optional] 

## Example

```python
from airflow_client.models.task_failed_dependency import TaskFailedDependency

# TODO update the JSON string below
json = "{}"
# create an instance of TaskFailedDependency from a JSON string
task_failed_dependency_instance = TaskFailedDependency.from_json(json)
# print the JSON string representation of the object
print(TaskFailedDependency.to_json())

# convert the object into a dict
task_failed_dependency_dict = task_failed_dependency_instance.to_dict()
# create an instance of TaskFailedDependency from a dict
task_failed_dependency_from_dict = TaskFailedDependency.from_dict(task_failed_dependency_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


