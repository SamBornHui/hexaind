# RelativeDelta

Relative delta

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**type** | **str** |  | 
**years** | **int** |  | 
**months** | **int** |  | 
**days** | **int** |  | 
**leapdays** | **int** |  | 
**hours** | **int** |  | 
**minutes** | **int** |  | 
**seconds** | **int** |  | 
**microseconds** | **int** |  | 
**year** | **int** |  | 
**month** | **int** |  | 
**day** | **int** |  | 
**hour** | **int** |  | 
**minute** | **int** |  | 
**second** | **int** |  | 
**microsecond** | **int** |  | 

## Example

```python
from airflow_client.models.relative_delta import RelativeDelta

# TODO update the JSON string below
json = "{}"
# create an instance of RelativeDelta from a JSON string
relative_delta_instance = RelativeDelta.from_json(json)
# print the JSON string representation of the object
print(RelativeDelta.to_json())

# convert the object into a dict
relative_delta_dict = relative_delta_instance.to_dict()
# create an instance of RelativeDelta from a dict
relative_delta_from_dict = RelativeDelta.from_dict(relative_delta_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


