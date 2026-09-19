# DagProcessorStatus

The status and the latest dag processor heartbeat.  *New in version 2.6.3* 

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | [**HealthStatus**](HealthStatus.md) |  | [optional] 
**latest_dag_processor_heartbeat** | **str** | The time the dag processor last did a heartbeat. | [optional] [readonly] 

## Example

```python
from airflow_client.models.dag_processor_status import DagProcessorStatus

# TODO update the JSON string below
json = "{}"
# create an instance of DagProcessorStatus from a JSON string
dag_processor_status_instance = DagProcessorStatus.from_json(json)
# print the JSON string representation of the object
print(DagProcessorStatus.to_json())

# convert the object into a dict
dag_processor_status_dict = dag_processor_status_instance.to_dict()
# create an instance of DagProcessorStatus from a dict
dag_processor_status_from_dict = DagProcessorStatus.from_dict(dag_processor_status_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


