# SharedServerUser

the server's owner

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** |  | [optional] 

## Example

```python
from jupyterhub_client.models.shared_server_user import SharedServerUser

# TODO update the JSON string below
json = "{}"
# create an instance of SharedServerUser from a JSON string
shared_server_user_instance = SharedServerUser.from_json(json)
# print the JSON string representation of the object
print(SharedServerUser.to_json())

# convert the object into a dict
shared_server_user_dict = shared_server_user_instance.to_dict()
# create an instance of SharedServerUser from a dict
shared_server_user_from_dict = SharedServerUser.from_dict(shared_server_user_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


