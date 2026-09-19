# ShareGroup

the group being shared with (exactly one of 'user' or 'group' will be non-null, the other will be null)

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** |  | [optional] 

## Example

```python
from jupyterhub_client.models.share_group import ShareGroup

# TODO update the JSON string below
json = "{}"
# create an instance of ShareGroup from a JSON string
share_group_instance = ShareGroup.from_json(json)
# print the JSON string representation of the object
print(ShareGroup.to_json())

# convert the object into a dict
share_group_dict = share_group_instance.to_dict()
# create an instance of ShareGroup from a dict
share_group_from_dict = ShareGroup.from_dict(share_group_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


