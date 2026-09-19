# PostUserActivityRequestServers

Register activity for specific servers by name. The keys of this dict are the names of servers. The default server has an empty name (''). 

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**server_name** | [**PostUserActivityRequestServersServerName**](PostUserActivityRequestServersServerName.md) |  | [optional] 

## Example

```python
from jupyterhub_client.models.post_user_activity_request_servers import PostUserActivityRequestServers

# TODO update the JSON string below
json = "{}"
# create an instance of PostUserActivityRequestServers from a JSON string
post_user_activity_request_servers_instance = PostUserActivityRequestServers.from_json(json)
# print the JSON string representation of the object
print(PostUserActivityRequestServers.to_json())

# convert the object into a dict
post_user_activity_request_servers_dict = post_user_activity_request_servers_instance.to_dict()
# create an instance of PostUserActivityRequestServers from a dict
post_user_activity_request_servers_from_dict = PostUserActivityRequestServers.from_dict(post_user_activity_request_servers_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


