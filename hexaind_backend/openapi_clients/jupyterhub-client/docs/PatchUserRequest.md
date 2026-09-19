# PatchUserRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** | the new name (optional, if another key is updated i.e. admin) | [optional] 
**admin** | **bool** | update admin (optional, if another key is updated i.e. name) | [optional] 

## Example

```python
from jupyterhub_client.models.patch_user_request import PatchUserRequest

# TODO update the JSON string below
json = "{}"
# create an instance of PatchUserRequest from a JSON string
patch_user_request_instance = PatchUserRequest.from_json(json)
# print the JSON string representation of the object
print(PatchUserRequest.to_json())

# convert the object into a dict
patch_user_request_dict = patch_user_request_instance.to_dict()
# create an instance of PatchUserRequest from a dict
patch_user_request_from_dict = PatchUserRequest.from_dict(patch_user_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


