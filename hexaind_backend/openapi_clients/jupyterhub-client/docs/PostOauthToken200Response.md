# PostOauthToken200Response


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**access_token** | **str** | The new API token for the user | [optional] 
**token_type** | **str** | Will always be &#39;Bearer&#39; | [optional] 

## Example

```python
from jupyterhub_client.models.post_oauth_token200_response import PostOauthToken200Response

# TODO update the JSON string below
json = "{}"
# create an instance of PostOauthToken200Response from a JSON string
post_oauth_token200_response_instance = PostOauthToken200Response.from_json(json)
# print the JSON string representation of the object
print(PostOauthToken200Response.to_json())

# convert the object into a dict
post_oauth_token200_response_dict = post_oauth_token200_response_instance.to_dict()
# create an instance of PostOauthToken200Response from a dict
post_oauth_token200_response_from_dict = PostOauthToken200Response.from_dict(post_oauth_token200_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


