# GetUserTokens200Response


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**api_tokens** | [**List[Token]**](Token.md) |  | [optional] 

## Example

```python
from jupyterhub_client.models.get_user_tokens200_response import GetUserTokens200Response

# TODO update the JSON string below
json = "{}"
# create an instance of GetUserTokens200Response from a JSON string
get_user_tokens200_response_instance = GetUserTokens200Response.from_json(json)
# print the JSON string representation of the object
print(GetUserTokens200Response.to_json())

# convert the object into a dict
get_user_tokens200_response_dict = get_user_tokens200_response_instance.to_dict()
# create an instance of GetUserTokens200Response from a dict
get_user_tokens200_response_from_dict = GetUserTokens200Response.from_dict(get_user_tokens200_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


