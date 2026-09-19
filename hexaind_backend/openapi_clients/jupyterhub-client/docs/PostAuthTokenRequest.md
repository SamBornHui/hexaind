# PostAuthTokenRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**username** | **str** |  | [optional] 
**password** | **str** |  | [optional] 

## Example

```python
from jupyterhub_client.models.post_auth_token_request import PostAuthTokenRequest

# TODO update the JSON string below
json = "{}"
# create an instance of PostAuthTokenRequest from a JSON string
post_auth_token_request_instance = PostAuthTokenRequest.from_json(json)
# print the JSON string representation of the object
print(PostAuthTokenRequest.to_json())

# convert the object into a dict
post_auth_token_request_dict = post_auth_token_request_instance.to_dict()
# create an instance of PostAuthTokenRequest from a dict
post_auth_token_request_from_dict = PostAuthTokenRequest.from_dict(post_auth_token_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


