# PostUserActivityRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**last_activity** | **datetime** | Timestamp of last-seen activity for this user. Only needed if this is not activity associated with using a given server.  | [optional] 
**servers** | [**PostUserActivityRequestServers**](PostUserActivityRequestServers.md) |  | [optional] 

## Example

```python
from jupyterhub_client.models.post_user_activity_request import PostUserActivityRequest

# TODO update the JSON string below
json = "{}"
# create an instance of PostUserActivityRequest from a JSON string
post_user_activity_request_instance = PostUserActivityRequest.from_json(json)
# print the JSON string representation of the object
print(PostUserActivityRequest.to_json())

# convert the object into a dict
post_user_activity_request_dict = post_user_activity_request_instance.to_dict()
# create an instance of PostUserActivityRequest from a dict
post_user_activity_request_from_dict = PostUserActivityRequest.from_dict(post_user_activity_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


