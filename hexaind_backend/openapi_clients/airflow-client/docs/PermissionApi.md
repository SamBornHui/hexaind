# airflow_client.PermissionApi

All URIs are relative to */api/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_permissions**](PermissionApi.md#get_permissions) | **GET** /permissions | List permissions


# **get_permissions**
> ActionCollection get_permissions(limit=limit, offset=offset)

List permissions

Get a list of permissions.  *This API endpoint is deprecated, please use the endpoint `/auth/fab/v1` for this operation instead.* 

### Example


```python
import airflow_client
from airflow_client.models.action_collection import ActionCollection
from airflow_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /api/v1
# See configuration.py for a list of all supported configuration parameters.
configuration = airflow_client.Configuration(
    host = "/api/v1"
)


# Enter a context with an instance of the API client
with airflow_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = airflow_client.PermissionApi(api_client)
    limit = 100 # int | The numbers of items to return. (optional) (default to 100)
    offset = 56 # int | The number of items to skip before starting to collect the result set. (optional)

    try:
        # List permissions
        api_response = api_instance.get_permissions(limit=limit, offset=offset)
        print("The response of PermissionApi->get_permissions:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling PermissionApi->get_permissions: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **limit** | **int**| The numbers of items to return. | [optional] [default to 100]
 **offset** | **int**| The number of items to skip before starting to collect the result set. | [optional] 

### Return type

[**ActionCollection**](ActionCollection.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Success. |  -  |
**401** | Request not authenticated due to missing, invalid, authentication info. |  -  |
**403** | Client does not have sufficient permission. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

