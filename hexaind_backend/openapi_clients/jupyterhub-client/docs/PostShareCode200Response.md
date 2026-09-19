# PostShareCode200Response


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**server** | [**SharedServer**](SharedServer.md) | the server granting shared access | [optional] 
**scopes** | **List[str]** | the scopes granted by this Share | [optional] 
**id** | **str** | the share-code&#39;s id. Can be used to revoke share codes.  | [optional] 
**created_at** | **datetime** | when the share code was issued | [optional] 
**expires_at** | **datetime** | When the share code will expire, always in the future. &#x60;null&#x60; if the code does not expire.  | [optional] 
**code** | **str** | The share code itself | [optional] 
**accept_url** | **str** | The URL path for accepting the code | [optional] 
**full_accept_url** | **str** | The full URL for accepting the code, if JupyterHub.public_url configuration is defined.  | [optional] 

## Example

```python
from jupyterhub_client.models.post_share_code200_response import PostShareCode200Response

# TODO update the JSON string below
json = "{}"
# create an instance of PostShareCode200Response from a JSON string
post_share_code200_response_instance = PostShareCode200Response.from_json(json)
# print the JSON string representation of the object
print(PostShareCode200Response.to_json())

# convert the object into a dict
post_share_code200_response_dict = post_share_code200_response_instance.to_dict()
# create an instance of PostShareCode200Response from a dict
post_share_code200_response_from_dict = PostShareCode200Response.from_dict(post_share_code200_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


