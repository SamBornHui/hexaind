# PaginationNext

fields for the next page, if any. Null if this is the last page. 

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**offset** | **float** | the offset for the next page | [optional] 
**limit** | **float** | the same as the above limit, for consistency | [optional] 
**url** | **str** | the assembled url for the next page, with query parameters already included.  | [optional] 

## Example

```python
from jupyterhub_client.models.pagination_next import PaginationNext

# TODO update the JSON string below
json = "{}"
# create an instance of PaginationNext from a JSON string
pagination_next_instance = PaginationNext.from_json(json)
# print the JSON string representation of the object
print(PaginationNext.to_json())

# convert the object into a dict
pagination_next_dict = pagination_next_instance.to_dict()
# create an instance of PaginationNext from a dict
pagination_next_from_dict = PaginationNext.from_dict(pagination_next_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


