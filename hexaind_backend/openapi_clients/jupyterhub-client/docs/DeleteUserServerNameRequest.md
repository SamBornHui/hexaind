# DeleteUserServerNameRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**remove** | **bool** | Whether to fully remove the server, rather than just stop it. Removing a server deletes things like the state of the stopped server. Default: false.  | [optional] 

## Example

```python
from jupyterhub_client.models.delete_user_server_name_request import DeleteUserServerNameRequest

# TODO update the JSON string below
json = "{}"
# create an instance of DeleteUserServerNameRequest from a JSON string
delete_user_server_name_request_instance = DeleteUserServerNameRequest.from_json(json)
# print the JSON string representation of the object
print(DeleteUserServerNameRequest.to_json())

# convert the object into a dict
delete_user_server_name_request_dict = delete_user_server_name_request_instance.to_dict()
# create an instance of DeleteUserServerNameRequest from a dict
delete_user_server_name_request_from_dict = DeleteUserServerNameRequest.from_dict(delete_user_server_name_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


