# PostShutdownRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**proxy** | **bool** | Whether the proxy should be shutdown as well (default from Hub config) | [optional] 
**servers** | **bool** | Whether users&#39; notebook servers should be shutdown as well (default from Hub config) | [optional] 

## Example

```python
from jupyterhub_client.models.post_shutdown_request import PostShutdownRequest

# TODO update the JSON string below
json = "{}"
# create an instance of PostShutdownRequest from a JSON string
post_shutdown_request_instance = PostShutdownRequest.from_json(json)
# print the JSON string representation of the object
print(PostShutdownRequest.to_json())

# convert the object into a dict
post_shutdown_request_dict = post_shutdown_request_instance.to_dict()
# create an instance of PostShutdownRequest from a dict
post_shutdown_request_from_dict = PostShutdownRequest.from_dict(post_shutdown_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


