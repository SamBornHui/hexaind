# PostSharesServerRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**group** | **str** | group to grant permissions to. Exactly one of &#39;user&#39; and &#39;group&#39; can be specified.  | [optional] 
**user** | **str** | user to grant permissions to. Exactly one of &#39;user&#39; and &#39;group&#39; can be specified.  | [optional] 
**scopes** | **List[str]** | scopes to grant | [optional] 

## Example

```python
from jupyterhub_client.models.post_shares_server_request import PostSharesServerRequest

# TODO update the JSON string below
json = "{}"
# create an instance of PostSharesServerRequest from a JSON string
post_shares_server_request_instance = PostSharesServerRequest.from_json(json)
# print the JSON string representation of the object
print(PostSharesServerRequest.to_json())

# convert the object into a dict
post_shares_server_request_dict = post_shares_server_request_instance.to_dict()
# create an instance of PostSharesServerRequest from a dict
post_shares_server_request_from_dict = PostSharesServerRequest.from_dict(post_shares_server_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


