# Share

A single sharing permission. There is at most one of these objects per (server, user) or (server, group) combination. 

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**server** | [**SharedServer**](SharedServer.md) | the server granting shared access | [optional] 
**scopes** | **List[str]** | the scopes granted by this Share | [optional] 
**group** | [**ShareGroup**](ShareGroup.md) |  | [optional] 
**user** | [**ShareUser**](ShareUser.md) |  | [optional] 
**created_at** | **datetime** | when the share was first granted | [optional] 

## Example

```python
from jupyterhub_client.models.share import Share

# TODO update the JSON string below
json = "{}"
# create an instance of Share from a JSON string
share_instance = Share.from_json(json)
# print the JSON string representation of the object
print(Share.to_json())

# convert the object into a dict
share_dict = share_instance.to_dict()
# create an instance of Share from a dict
share_from_dict = Share.from_dict(share_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


