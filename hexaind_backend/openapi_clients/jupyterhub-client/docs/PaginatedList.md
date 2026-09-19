# PaginatedList


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**items** | **List[object]** |  | [optional] 
**pagination** | [**Pagination**](Pagination.md) |  | [optional] 

## Example

```python
from jupyterhub_client.models.paginated_list import PaginatedList

# TODO update the JSON string below
json = "{}"
# create an instance of PaginatedList from a JSON string
paginated_list_instance = PaginatedList.from_json(json)
# print the JSON string representation of the object
print(PaginatedList.to_json())

# convert the object into a dict
paginated_list_dict = paginated_list_instance.to_dict()
# create an instance of PaginatedList from a dict
paginated_list_from_dict = PaginatedList.from_dict(paginated_list_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


