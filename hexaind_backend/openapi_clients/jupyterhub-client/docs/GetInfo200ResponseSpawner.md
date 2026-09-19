# GetInfo200ResponseSpawner


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**var_class** | **str** | The Python class currently active for spawning single-user notebook servers | [optional] 
**version** | **str** | The version of the currently active Spawner | [optional] 

## Example

```python
from jupyterhub_client.models.get_info200_response_spawner import GetInfo200ResponseSpawner

# TODO update the JSON string below
json = "{}"
# create an instance of GetInfo200ResponseSpawner from a JSON string
get_info200_response_spawner_instance = GetInfo200ResponseSpawner.from_json(json)
# print the JSON string representation of the object
print(GetInfo200ResponseSpawner.to_json())

# convert the object into a dict
get_info200_response_spawner_dict = get_info200_response_spawner_instance.to_dict()
# create an instance of GetInfo200ResponseSpawner from a dict
get_info200_response_spawner_from_dict = GetInfo200ResponseSpawner.from_dict(get_info200_response_spawner_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


