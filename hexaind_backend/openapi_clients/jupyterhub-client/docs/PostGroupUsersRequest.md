# PostGroupUsersRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**users** | **List[str]** | List of usernames to add to the group | [optional] 

## Example

```python
from jupyterhub_client.models.post_group_users_request import PostGroupUsersRequest

# TODO update the JSON string below
json = "{}"
# create an instance of PostGroupUsersRequest from a JSON string
post_group_users_request_instance = PostGroupUsersRequest.from_json(json)
# print the JSON string representation of the object
print(PostGroupUsersRequest.to_json())

# convert the object into a dict
post_group_users_request_dict = post_group_users_request_instance.to_dict()
# create an instance of PostGroupUsersRequest from a dict
post_group_users_request_from_dict = PostGroupUsersRequest.from_dict(post_group_users_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


