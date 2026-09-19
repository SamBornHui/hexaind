# ShareCode

A single sharing code. There is at most one of these objects per (server, user) or (server, group) combination.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**server** | [**SharedServer**](SharedServer.md) | the server granting shared access | [optional] 
**scopes** | **List[str]** | the scopes granted by this Share | [optional] 
**id** | **str** | the share-code&#39;s id. Can be used to revoke share codes.  | [optional] 
**created_at** | **datetime** | when the share code was issued | [optional] 
**expires_at** | **datetime** | When the share code will expire, always in the future. &#x60;null&#x60; if the code does not expire.  | [optional] 

## Example

```python
from jupyterhub_client.models.share_code import ShareCode

# TODO update the JSON string below
json = "{}"
# create an instance of ShareCode from a JSON string
share_code_instance = ShareCode.from_json(json)
# print the JSON string representation of the object
print(ShareCode.to_json())

# convert the object into a dict
share_code_dict = share_code_instance.to_dict()
# create an instance of ShareCode from a dict
share_code_from_dict = ShareCode.from_dict(share_code_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


