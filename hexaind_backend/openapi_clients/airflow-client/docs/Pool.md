# Pool

The pool

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** | The name of pool. | [optional] 
**slots** | **int** | The maximum number of slots that can be assigned to tasks. One job may occupy one or more slots.  | [optional] 
**occupied_slots** | **int** | The number of slots used by running/queued tasks at the moment. May include deferred tasks if &#39;include_deferred&#39; is set to true. | [optional] [readonly] 
**running_slots** | **int** | The number of slots used by running tasks at the moment. | [optional] [readonly] 
**queued_slots** | **int** | The number of slots used by queued tasks at the moment. | [optional] [readonly] 
**open_slots** | **int** | The number of free slots at the moment. | [optional] [readonly] 
**scheduled_slots** | **int** | The number of slots used by scheduled tasks at the moment. | [optional] [readonly] 
**deferred_slots** | **int** | The number of slots used by deferred tasks at the moment. Relevant if &#39;include_deferred&#39; is set to true.  *New in version 2.7.0*  | [optional] [readonly] 
**description** | **str** | The description of the pool.  *New in version 2.3.0*  | [optional] 
**include_deferred** | **bool** | If set to true, deferred tasks are considered when calculating open pool slots.  *New in version 2.7.0*  | [optional] 

## Example

```python
from airflow_client.models.pool import Pool

# TODO update the JSON string below
json = "{}"
# create an instance of Pool from a JSON string
pool_instance = Pool.from_json(json)
# print the JSON string representation of the object
print(Pool.to_json())

# convert the object into a dict
pool_dict = pool_instance.to_dict()
# create an instance of Pool from a dict
pool_from_dict = Pool.from_dict(pool_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


