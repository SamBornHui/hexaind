# airflow_client.DagStatsApi

All URIs are relative to */api/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_dag_stats**](DagStatsApi.md#get_dag_stats) | **GET** /dagStats | List Dag statistics


# **get_dag_stats**
> DagStatsCollectionSchema get_dag_stats(dag_ids)

List Dag statistics

### Example


```python
import airflow_client
from airflow_client.models.dag_stats_collection_schema import DagStatsCollectionSchema
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
    api_instance = airflow_client.DagStatsApi(api_client)
    dag_ids = 'dag_ids_example' # str | One or more DAG IDs separated by commas to filter relevant Dags. 

    try:
        # List Dag statistics
        api_response = api_instance.get_dag_stats(dag_ids)
        print("The response of DagStatsApi->get_dag_stats:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DagStatsApi->get_dag_stats: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **dag_ids** | **str**| One or more DAG IDs separated by commas to filter relevant Dags.  | 

### Return type

[**DagStatsCollectionSchema**](DagStatsCollectionSchema.md)

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

