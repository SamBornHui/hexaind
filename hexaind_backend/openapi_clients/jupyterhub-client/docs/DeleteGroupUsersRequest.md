# DeleteGroupUsersRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**users** | **List[str]** | List of usernames to remove from the group | [optional] 

## Example

```python
from jupyterhub_client.models.delete_group_users_request import DeleteGroupUsersRequest

# TODO update the JSON string below
json = "{}"
# create an instance of DeleteGroupUsersRequest from a JSON string
delete_group_users_request_instance = DeleteGroupUsersRequest.from_json(json)
# print the JSON string representation of the object
print(DeleteGroupUsersRequest.to_json())

# convert the object into a dict
delete_group_users_request_dict = delete_group_users_request_instance.to_dict()
# create an instance of DeleteGroupUsersRequest from a dict
delete_group_users_request_from_dict = DeleteGroupUsersRequest.from_dict(delete_group_users_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


