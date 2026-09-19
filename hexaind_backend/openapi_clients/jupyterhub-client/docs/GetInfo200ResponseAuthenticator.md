# GetInfo200ResponseAuthenticator


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**var_class** | **str** | The Python class currently active for JupyterHub Authentication | [optional] 
**version** | **str** | The version of the currently active Authenticator | [optional] 

## Example

```python
from jupyterhub_client.models.get_info200_response_authenticator import GetInfo200ResponseAuthenticator

# TODO update the JSON string below
json = "{}"
# create an instance of GetInfo200ResponseAuthenticator from a JSON string
get_info200_response_authenticator_instance = GetInfo200ResponseAuthenticator.from_json(json)
# print the JSON string representation of the object
print(GetInfo200ResponseAuthenticator.to_json())

# convert the object into a dict
get_info200_response_authenticator_dict = get_info200_response_authenticator_instance.to_dict()
# create an instance of GetInfo200ResponseAuthenticator from a dict
get_info200_response_authenticator_from_dict = GetInfo200ResponseAuthenticator.from_dict(get_info200_response_authenticator_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


