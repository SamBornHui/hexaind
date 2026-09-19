# PatchSharesServerRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**group** | **str** | group to revoke permissions from. Exactly one of &#39;user&#39; and &#39;group&#39; must be specified.  | [optional] 
**user** | **str** | user to revoke permissions from. Exactly one of &#39;user&#39; and &#39;group&#39; must be specified.  | [optional] 
**scopes** | **List[str]** | scopes to revoke. If no scopes are specified, all permissions are revoked.  | [optional] 

## Example

```python
from jupyterhub_client.models.patch_shares_server_request import PatchSharesServerRequest

# TODO update the JSON string below
json = "{}"
# create an instance of PatchSharesServerRequest from a JSON string
patch_shares_server_request_instance = PatchSharesServerRequest.from_json(json)
# print the JSON string representation of the object
print(PatchSharesServerRequest.to_json())

# convert the object into a dict
patch_shares_server_request_dict = patch_shares_server_request_instance.to_dict()
# create an instance of PatchSharesServerRequest from a dict
patch_shares_server_request_from_dict = PatchSharesServerRequest.from_dict(patch_shares_server_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


