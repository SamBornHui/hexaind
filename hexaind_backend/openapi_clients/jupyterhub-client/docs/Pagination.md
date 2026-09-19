# Pagination

page info for paginated endpoints

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**total** | **float** | total number of results for the query | [optional] 
**limit** | **float** | the maximum number of results | [optional] 
**offset** | **float** | the starting point for this | [optional] 
**next** | [**PaginationNext**](PaginationNext.md) |  | [optional] 

## Example

```python
from jupyterhub_client.models.pagination import Pagination

# TODO update the JSON string below
json = "{}"
# create an instance of Pagination from a JSON string
pagination_instance = Pagination.from_json(json)
# print the JSON string representation of the object
print(Pagination.to_json())

# convert the object into a dict
pagination_dict = pagination_instance.to_dict()
# create an instance of Pagination from a dict
pagination_from_dict = Pagination.from_dict(pagination_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


