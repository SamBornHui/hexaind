# PostShareCodeRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**expires_in** | **float** | expiration in seconds. If unspecified, expires in one day (86400)  | [optional] 
**scopes** | **List[str]** | scopes to grant | [optional] 

## Example

```python
from jupyterhub_client.models.post_share_code_request import PostShareCodeRequest

# TODO update the JSON string below
json = "{}"
# create an instance of PostShareCodeRequest from a JSON string
post_share_code_request_instance = PostShareCodeRequest.from_json(json)
# print the JSON string representation of the object
print(PostShareCodeRequest.to_json())

# convert the object into a dict
post_share_code_request_dict = post_share_code_request_instance.to_dict()
# create an instance of PostShareCodeRequest from a dict
post_share_code_request_from_dict = PostShareCodeRequest.from_dict(post_share_code_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


