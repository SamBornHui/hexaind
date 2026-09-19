# PostUsersRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**usernames** | **List[str]** | list of usernames to create on the Hub | [optional] 
**admin** | **bool** | whether the created users should be admins | [optional] 

## Example

```python
from jupyterhub_client.models.post_users_request import PostUsersRequest

# TODO update the JSON string below
json = "{}"
# create an instance of PostUsersRequest from a JSON string
post_users_request_instance = PostUsersRequest.from_json(json)
# print the JSON string representation of the object
print(PostUsersRequest.to_json())

# convert the object into a dict
post_users_request_dict = post_users_request_instance.to_dict()
# create an instance of PostUsersRequest from a dict
post_users_request_from_dict = PostUsersRequest.from_dict(post_users_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


