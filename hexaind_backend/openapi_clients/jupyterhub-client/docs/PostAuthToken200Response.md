# PostAuthToken200Response


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**token** | **str** | The new API token. | [optional] 

## Example

```python
from jupyterhub_client.models.post_auth_token200_response import PostAuthToken200Response

# TODO update the JSON string below
json = "{}"
# create an instance of PostAuthToken200Response from a JSON string
post_auth_token200_response_instance = PostAuthToken200Response.from_json(json)
# print the JSON string representation of the object
print(PostAuthToken200Response.to_json())

# convert the object into a dict
post_auth_token200_response_dict = post_auth_token200_response_instance.to_dict()
# create an instance of PostAuthToken200Response from a dict
post_auth_token200_response_from_dict = PostAuthToken200Response.from_dict(post_auth_token200_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


