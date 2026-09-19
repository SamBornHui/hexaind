# GetApi200Response


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**version** | **str** | The version of JupyterHub itself | [optional] 

## Example

```python
from jupyterhub_client.models.get_api200_response import GetApi200Response

# TODO update the JSON string below
json = "{}"
# create an instance of GetApi200Response from a JSON string
get_api200_response_instance = GetApi200Response.from_json(json)
# print the JSON string representation of the object
print(GetApi200Response.to_json())

# convert the object into a dict
get_api200_response_dict = get_api200_response_instance.to_dict()
# create an instance of GetApi200Response from a dict
get_api200_response_from_dict = GetApi200Response.from_dict(get_api200_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


