# SharedServer

Subset of Server model present in Share responses

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** | the server name. &#39;&#39; for the default server. | [optional] 
**url** | **str** | the server&#39;s URL (path only when not using subdomains) | [optional] 
**full_url** | **str** | The full URL of the server (&#x60;https://hub.example.org/user/:name/:servername&#x60;). &#x60;null&#x60; unless JupyterHub.public_url or subdomains are configured.  | [optional] 
**ready** | **bool** | whether the server is ready | [optional] 
**user** | [**SharedServerUser**](SharedServerUser.md) |  | [optional] 

## Example

```python
from jupyterhub_client.models.shared_server import SharedServer

# TODO update the JSON string below
json = "{}"
# create an instance of SharedServer from a JSON string
shared_server_instance = SharedServer.from_json(json)
# print the JSON string representation of the object
print(SharedServer.to_json())

# convert the object into a dict
shared_server_dict = shared_server_instance.to_dict()
# create an instance of SharedServer from a dict
shared_server_from_dict = SharedServer.from_dict(shared_server_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


