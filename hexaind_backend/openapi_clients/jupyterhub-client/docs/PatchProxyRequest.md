# PatchProxyRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**ip** | **str** | IP address of the new proxy | [optional] 
**port** | **str** | Port of the new proxy | [optional] 
**protocol** | **str** | Protocol of new proxy, if changed | [optional] 
**auth_token** | **str** | CONFIGPROXY_AUTH_TOKEN for the new proxy | [optional] 

## Example

```python
from jupyterhub_client.models.patch_proxy_request import PatchProxyRequest

# TODO update the JSON string below
json = "{}"
# create an instance of PatchProxyRequest from a JSON string
patch_proxy_request_instance = PatchProxyRequest.from_json(json)
# print the JSON string representation of the object
print(PatchProxyRequest.to_json())

# convert the object into a dict
patch_proxy_request_dict = patch_proxy_request_instance.to_dict()
# create an instance of PatchProxyRequest from a dict
patch_proxy_request_from_dict = PatchProxyRequest.from_dict(patch_proxy_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


