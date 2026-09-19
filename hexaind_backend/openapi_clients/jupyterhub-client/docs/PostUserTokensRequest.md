# PostUserTokensRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**expires_in** | **float** | lifetime (in seconds) after which the requested token will expire. Omit, or specify null or 0 for no expiration. | [optional] 
**note** | **str** | A note attached to the token for future bookkeeping | [optional] 
**roles** | **List[str]** | A list of role names from which to derive scopes. This is a shortcut for assigning collections of scopes; Tokens do not retain role assignment. (Changed in 3.0: roles are immediately resolved to scopes instead of stored on roles.)  | [optional] 
**scopes** | **List[str]** | A list of scopes that the token should have. (new in JupyterHub 3.0).  | [optional] 

## Example

```python
from jupyterhub_client.models.post_user_tokens_request import PostUserTokensRequest

# TODO update the JSON string below
json = "{}"
# create an instance of PostUserTokensRequest from a JSON string
post_user_tokens_request_instance = PostUserTokensRequest.from_json(json)
# print the JSON string representation of the object
print(PostUserTokensRequest.to_json())

# convert the object into a dict
post_user_tokens_request_dict = post_user_tokens_request_instance.to_dict()
# create an instance of PostUserTokensRequest from a dict
post_user_tokens_request_from_dict = PostUserTokensRequest.from_dict(post_user_tokens_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


