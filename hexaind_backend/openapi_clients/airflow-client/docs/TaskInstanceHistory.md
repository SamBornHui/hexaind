# TaskInstanceHistory


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**task_id** | **str** |  | [optional] 
**task_display_name** | **str** | Human centric display text for the task.  *New in version 2.9.0*  | [optional] 
**dag_id** | **str** |  | [optional] 
**dag_run_id** | **str** | The DagRun ID for this task instance  *New in version 2.3.0*  | [optional] 
**start_date** | **str** |  | [optional] 
**end_date** | **str** |  | [optional] 
**duration** | **float** |  | [optional] 
**state** | [**TaskState**](TaskState.md) |  | [optional] 
**try_number** | **int** |  | [optional] 
**map_index** | **int** |  | [optional] 
**max_tries** | **int** |  | [optional] 
**hostname** | **str** |  | [optional] 
**unixname** | **str** |  | [optional] 
**pool** | **str** |  | [optional] 
**pool_slots** | **int** |  | [optional] 
**queue** | **str** |  | [optional] 
**priority_weight** | **int** |  | [optional] 
**operator** | **str** | *Changed in version 2.1.1*&amp;#58; Field becomes nullable.  | [optional] 
**queued_when** | **str** | The datetime that the task enter the state QUEUE, also known as queue_at  | [optional] 
**pid** | **int** |  | [optional] 
**executor** | **str** | Executor the task is configured to run on or None (which indicates the default executor)  *New in version 2.10.0*  | [optional] 
**executor_config** | **str** |  | [optional] 

## Example

```python
from airflow_client.models.task_instance_history import TaskInstanceHistory

# TODO update the JSON string below
json = "{}"
# create an instance of TaskInstanceHistory from a JSON string
task_instance_history_instance = TaskInstanceHistory.from_json(json)
# print the JSON string representation of the object
print(TaskInstanceHistory.to_json())

# convert the object into a dict
task_instance_history_dict = task_instance_history_instance.to_dict()
# create an instance of TaskInstanceHistory from a dict
task_instance_history_from_dict = TaskInstanceHistory.from_dict(task_instance_history_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


