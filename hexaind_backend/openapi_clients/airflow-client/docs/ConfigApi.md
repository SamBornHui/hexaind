# airflow_client.ConfigApi

All URIs are relative to */api/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_config**](ConfigApi.md#get_config) | **GET** /config | Get current configuration
[**get_value**](ConfigApi.md#get_value) | **GET** /config/section/{section}/option/{option} | Get a option from configuration


# **get_config**
> Config get_config(section=section)

Get current configuration

### Example


```python
import airflow_client
from airflow_client.models.config import Config
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
    api_instance = airflow_client.ConfigApi(api_client)
    section = 'section_example' # str | If given, only return config of this section. (optional)

    try:
        # Get current configuration
        api_response = api_instance.get_config(section=section)
        print("The response of ConfigApi->get_config:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ConfigApi->get_config: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **section** | **str**| If given, only return config of this section. | [optional] 

### Return type

[**Config**](Config.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json, text/plain

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Success. |  -  |
**401** | Request not authenticated due to missing, invalid, authentication info. |  -  |
**403** | Client does not have sufficient permission. |  -  |
**404** | A specified resource is not found. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_value**
> Config get_value(section, option)

Get a option from configuration

### Example


```python
import airflow_client
from airflow_client.models.config import Config
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
    api_instance = airflow_client.ConfigApi(api_client)
    section = 'section_example' # str | 
    option = 'option_example' # str | 

    try:
        # Get a option from configuration
        api_response = api_instance.get_value(section, option)
        print("The response of ConfigApi->get_value:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ConfigApi->get_value: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **section** | **str**|  | 
 **option** | **str**|  | 

### Return type

[**Config**](Config.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json, text/plain

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Success. |  -  |
**401** | Request not authenticated due to missing, invalid, authentication info. |  -  |
**403** | Client does not have sufficient permission. |  -  |
**404** | A specified resource is not found. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

