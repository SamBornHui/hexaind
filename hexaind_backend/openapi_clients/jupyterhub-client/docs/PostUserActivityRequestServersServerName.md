# PostUserActivityRequestServersServerName

Activity for a single server. 

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**last_activity** | **datetime** | Timestamp of last-seen activity on this server.  | 

## Example

```python
from jupyterhub_client.models.post_user_activity_request_servers_server_name import PostUserActivityRequestServersServerName

# TODO update the JSON string below
json = "{}"
# create an instance of PostUserActivityRequestServersServerName from a JSON string
post_user_activity_request_servers_server_name_instance = PostUserActivityRequestServersServerName.from_json(json)
# print the JSON string representation of the object
print(PostUserActivityRequestServersServerName.to_json())

# convert the object into a dict
post_user_activity_request_servers_server_name_dict = post_user_activity_request_servers_server_name_instance.to_dict()
# create an instance of PostUserActivityRequestServersServerName from a dict
post_user_activity_request_servers_server_name_from_dict = PostUserActivityRequestServersServerName.from_dict(post_user_activity_request_servers_server_name_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


