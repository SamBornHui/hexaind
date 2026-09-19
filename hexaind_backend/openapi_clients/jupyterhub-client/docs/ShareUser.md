# ShareUser

the user being shared with (exactly one of 'user' or 'group' will be non-null, the other will be null)

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** |  | [optional] 

## Example

```python
from jupyterhub_client.models.share_user import ShareUser

# TODO update the JSON string below
json = "{}"
# create an instance of ShareUser from a JSON string
share_user_instance = ShareUser.from_json(json)
# print the JSON string representation of the object
print(ShareUser.to_json())

# convert the object into a dict
share_user_dict = share_user_instance.to_dict()
# create an instance of ShareUser from a dict
share_user_from_dict = ShareUser.from_dict(share_user_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


