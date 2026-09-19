# airflow_client.DatasetApi

All URIs are relative to */api/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**create_dataset_event**](DatasetApi.md#create_dataset_event) | **POST** /datasets/events | Create dataset event
[**delete_dag_dataset_queued_event**](DatasetApi.md#delete_dag_dataset_queued_event) | **DELETE** /dags/{dag_id}/datasets/queuedEvent/{uri} | Delete a queued Dataset event for a DAG.
[**delete_dag_dataset_queued_events**](DatasetApi.md#delete_dag_dataset_queued_events) | **DELETE** /dags/{dag_id}/datasets/queuedEvent | Delete queued Dataset events for a DAG.
[**delete_dataset_queued_events**](DatasetApi.md#delete_dataset_queued_events) | **DELETE** /datasets/queuedEvent/{uri} | Delete queued Dataset events for a Dataset.
[**get_dag_dataset_queued_event**](DatasetApi.md#get_dag_dataset_queued_event) | **GET** /dags/{dag_id}/datasets/queuedEvent/{uri} | Get a queued Dataset event for a DAG
[**get_dag_dataset_queued_events**](DatasetApi.md#get_dag_dataset_queued_events) | **GET** /dags/{dag_id}/datasets/queuedEvent | Get queued Dataset events for a DAG.
[**get_dataset**](DatasetApi.md#get_dataset) | **GET** /datasets/{uri} | Get a dataset
[**get_dataset_events**](DatasetApi.md#get_dataset_events) | **GET** /datasets/events | Get dataset events
[**get_dataset_queued_events**](DatasetApi.md#get_dataset_queued_events) | **GET** /datasets/queuedEvent/{uri} | Get queued Dataset events for a Dataset.
[**get_datasets**](DatasetApi.md#get_datasets) | **GET** /datasets | List datasets
[**get_upstream_dataset_events**](DatasetApi.md#get_upstream_dataset_events) | **GET** /dags/{dag_id}/dagRuns/{dag_run_id}/upstreamDatasetEvents | Get dataset events for a DAG run


# **create_dataset_event**
> DatasetEvent create_dataset_event(create_dataset_event)

Create dataset event

Create dataset event

### Example


```python
import airflow_client
from airflow_client.models.create_dataset_event import CreateDatasetEvent
from airflow_client.models.dataset_event import DatasetEvent
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
    api_instance = airflow_client.DatasetApi(api_client)
    create_dataset_event = airflow_client.CreateDatasetEvent() # CreateDatasetEvent | 

    try:
        # Create dataset event
        api_response = api_instance.create_dataset_event(create_dataset_event)
        print("The response of DatasetApi->create_dataset_event:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DatasetApi->create_dataset_event: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **create_dataset_event** | [**CreateDatasetEvent**](CreateDatasetEvent.md)|  | 

### Return type

[**DatasetEvent**](DatasetEvent.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Success. |  -  |
**400** | Client specified an invalid argument. |  -  |
**401** | Request not authenticated due to missing, invalid, authentication info. |  -  |
**403** | Client does not have sufficient permission. |  -  |
**404** | A specified resource is not found. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_dag_dataset_queued_event**
> delete_dag_dataset_queued_event(dag_id, uri, before=before)

Delete a queued Dataset event for a DAG.

Delete a queued Dataset event for a DAG.  *New in version 2.9.0* 

### Example


```python
import airflow_client
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
    api_instance = airflow_client.DatasetApi(api_client)
    dag_id = 'dag_id_example' # str | The DAG ID.
    uri = 'uri_example' # str | The encoded Dataset URI
    before = '2013-10-20T19:20:30+01:00' # datetime | Timestamp to select event logs occurring before. (optional)

    try:
        # Delete a queued Dataset event for a DAG.
        api_instance.delete_dag_dataset_queued_event(dag_id, uri, before=before)
    except Exception as e:
        print("Exception when calling DatasetApi->delete_dag_dataset_queued_event: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **dag_id** | **str**| The DAG ID. | 
 **uri** | **str**| The encoded Dataset URI | 
 **before** | **datetime**| Timestamp to select event logs occurring before. | [optional] 

### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**204** | Success. |  -  |
**400** | Client specified an invalid argument. |  -  |
**401** | Request not authenticated due to missing, invalid, authentication info. |  -  |
**403** | Client does not have sufficient permission. |  -  |
**404** | A specified resource is not found. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_dag_dataset_queued_events**
> delete_dag_dataset_queued_events(dag_id, before=before)

Delete queued Dataset events for a DAG.

Delete queued Dataset events for a DAG.  *New in version 2.9.0* 

### Example


```python
import airflow_client
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
    api_instance = airflow_client.DatasetApi(api_client)
    dag_id = 'dag_id_example' # str | The DAG ID.
    before = '2013-10-20T19:20:30+01:00' # datetime | Timestamp to select event logs occurring before. (optional)

    try:
        # Delete queued Dataset events for a DAG.
        api_instance.delete_dag_dataset_queued_events(dag_id, before=before)
    except Exception as e:
        print("Exception when calling DatasetApi->delete_dag_dataset_queued_events: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **dag_id** | **str**| The DAG ID. | 
 **before** | **datetime**| Timestamp to select event logs occurring before. | [optional] 

### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**204** | Success. |  -  |
**400** | Client specified an invalid argument. |  -  |
**401** | Request not authenticated due to missing, invalid, authentication info. |  -  |
**403** | Client does not have sufficient permission. |  -  |
**404** | A specified resource is not found. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_dataset_queued_events**
> delete_dataset_queued_events(uri, before=before)

Delete queued Dataset events for a Dataset.

Delete queued Dataset events for a Dataset.  *New in version 2.9.0* 

### Example


```python
import airflow_client
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
    api_instance = airflow_client.DatasetApi(api_client)
    uri = 'uri_example' # str | The encoded Dataset URI
    before = '2013-10-20T19:20:30+01:00' # datetime | Timestamp to select event logs occurring before. (optional)

    try:
        # Delete queued Dataset events for a Dataset.
        api_instance.delete_dataset_queued_events(uri, before=before)
    except Exception as e:
        print("Exception when calling DatasetApi->delete_dataset_queued_events: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **uri** | **str**| The encoded Dataset URI | 
 **before** | **datetime**| Timestamp to select event logs occurring before. | [optional] 

### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**204** | Success. |  -  |
**400** | Client specified an invalid argument. |  -  |
**401** | Request not authenticated due to missing, invalid, authentication info. |  -  |
**403** | Client does not have sufficient permission. |  -  |
**404** | A specified resource is not found. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_dag_dataset_queued_event**
> QueuedEvent get_dag_dataset_queued_event(dag_id, uri, before=before)

Get a queued Dataset event for a DAG

Get a queued Dataset event for a DAG.  *New in version 2.9.0* 

### Example


```python
import airflow_client
from airflow_client.models.queued_event import QueuedEvent
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
    api_instance = airflow_client.DatasetApi(api_client)
    dag_id = 'dag_id_example' # str | The DAG ID.
    uri = 'uri_example' # str | The encoded Dataset URI
    before = '2013-10-20T19:20:30+01:00' # datetime | Timestamp to select event logs occurring before. (optional)

    try:
        # Get a queued Dataset event for a DAG
        api_response = api_instance.get_dag_dataset_queued_event(dag_id, uri, before=before)
        print("The response of DatasetApi->get_dag_dataset_queued_event:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DatasetApi->get_dag_dataset_queued_event: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **dag_id** | **str**| The DAG ID. | 
 **uri** | **str**| The encoded Dataset URI | 
 **before** | **datetime**| Timestamp to select event logs occurring before. | [optional] 

### Return type

[**QueuedEvent**](QueuedEvent.md)

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
**404** | A specified resource is not found. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_dag_dataset_queued_events**
> QueuedEventCollection get_dag_dataset_queued_events(dag_id, before=before)

Get queued Dataset events for a DAG.

Get queued Dataset events for a DAG.  *New in version 2.9.0* 

### Example


```python
import airflow_client
from airflow_client.models.queued_event_collection import QueuedEventCollection
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
    api_instance = airflow_client.DatasetApi(api_client)
    dag_id = 'dag_id_example' # str | The DAG ID.
    before = '2013-10-20T19:20:30+01:00' # datetime | Timestamp to select event logs occurring before. (optional)

    try:
        # Get queued Dataset events for a DAG.
        api_response = api_instance.get_dag_dataset_queued_events(dag_id, before=before)
        print("The response of DatasetApi->get_dag_dataset_queued_events:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DatasetApi->get_dag_dataset_queued_events: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **dag_id** | **str**| The DAG ID. | 
 **before** | **datetime**| Timestamp to select event logs occurring before. | [optional] 

### Return type

[**QueuedEventCollection**](QueuedEventCollection.md)

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
**404** | A specified resource is not found. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_dataset**
> Dataset get_dataset(uri)

Get a dataset

Get a dataset by uri.

### Example


```python
import airflow_client
from airflow_client.models.dataset import Dataset
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
    api_instance = airflow_client.DatasetApi(api_client)
    uri = 'uri_example' # str | The encoded Dataset URI

    try:
        # Get a dataset
        api_response = api_instance.get_dataset(uri)
        print("The response of DatasetApi->get_dataset:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DatasetApi->get_dataset: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **uri** | **str**| The encoded Dataset URI | 

### Return type

[**Dataset**](Dataset.md)

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
**404** | A specified resource is not found. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_dataset_events**
> DatasetEventCollection get_dataset_events(limit=limit, offset=offset, order_by=order_by, dataset_id=dataset_id, source_dag_id=source_dag_id, source_task_id=source_task_id, source_run_id=source_run_id, source_map_index=source_map_index)

Get dataset events

Get dataset events

### Example


```python
import airflow_client
from airflow_client.models.dataset_event_collection import DatasetEventCollection
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
    api_instance = airflow_client.DatasetApi(api_client)
    limit = 100 # int | The numbers of items to return. (optional) (default to 100)
    offset = 56 # int | The number of items to skip before starting to collect the result set. (optional)
    order_by = 'order_by_example' # str | The name of the field to order the results by. Prefix a field name with `-` to reverse the sort order.  *New in version 2.1.0*  (optional)
    dataset_id = 56 # int | The Dataset ID that updated the dataset. (optional)
    source_dag_id = 'source_dag_id_example' # str | The DAG ID that updated the dataset. (optional)
    source_task_id = 'source_task_id_example' # str | The task ID that updated the dataset. (optional)
    source_run_id = 'source_run_id_example' # str | The DAG run ID that updated the dataset. (optional)
    source_map_index = 56 # int | The map index that updated the dataset. (optional)

    try:
        # Get dataset events
        api_response = api_instance.get_dataset_events(limit=limit, offset=offset, order_by=order_by, dataset_id=dataset_id, source_dag_id=source_dag_id, source_task_id=source_task_id, source_run_id=source_run_id, source_map_index=source_map_index)
        print("The response of DatasetApi->get_dataset_events:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DatasetApi->get_dataset_events: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **limit** | **int**| The numbers of items to return. | [optional] [default to 100]
 **offset** | **int**| The number of items to skip before starting to collect the result set. | [optional] 
 **order_by** | **str**| The name of the field to order the results by. Prefix a field name with &#x60;-&#x60; to reverse the sort order.  *New in version 2.1.0*  | [optional] 
 **dataset_id** | **int**| The Dataset ID that updated the dataset. | [optional] 
 **source_dag_id** | **str**| The DAG ID that updated the dataset. | [optional] 
 **source_task_id** | **str**| The task ID that updated the dataset. | [optional] 
 **source_run_id** | **str**| The DAG run ID that updated the dataset. | [optional] 
 **source_map_index** | **int**| The map index that updated the dataset. | [optional] 

### Return type

[**DatasetEventCollection**](DatasetEventCollection.md)

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
**404** | A specified resource is not found. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_dataset_queued_events**
> QueuedEventCollection get_dataset_queued_events(uri, before=before)

Get queued Dataset events for a Dataset.

Get queued Dataset events for a Dataset  *New in version 2.9.0* 

### Example


```python
import airflow_client
from airflow_client.models.queued_event_collection import QueuedEventCollection
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
    api_instance = airflow_client.DatasetApi(api_client)
    uri = 'uri_example' # str | The encoded Dataset URI
    before = '2013-10-20T19:20:30+01:00' # datetime | Timestamp to select event logs occurring before. (optional)

    try:
        # Get queued Dataset events for a Dataset.
        api_response = api_instance.get_dataset_queued_events(uri, before=before)
        print("The response of DatasetApi->get_dataset_queued_events:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DatasetApi->get_dataset_queued_events: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **uri** | **str**| The encoded Dataset URI | 
 **before** | **datetime**| Timestamp to select event logs occurring before. | [optional] 

### Return type

[**QueuedEventCollection**](QueuedEventCollection.md)

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
**404** | A specified resource is not found. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_datasets**
> DatasetCollection get_datasets(limit=limit, offset=offset, order_by=order_by, uri_pattern=uri_pattern, dag_ids=dag_ids)

List datasets

### Example


```python
import airflow_client
from airflow_client.models.dataset_collection import DatasetCollection
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
    api_instance = airflow_client.DatasetApi(api_client)
    limit = 100 # int | The numbers of items to return. (optional) (default to 100)
    offset = 56 # int | The number of items to skip before starting to collect the result set. (optional)
    order_by = 'order_by_example' # str | The name of the field to order the results by. Prefix a field name with `-` to reverse the sort order.  *New in version 2.1.0*  (optional)
    uri_pattern = 'uri_pattern_example' # str | If set, only return datasets with uris matching this pattern.  (optional)
    dag_ids = 'dag_ids_example' # str | One or more DAG IDs separated by commas to filter datasets by associated DAGs either consuming or producing.  *New in version 2.9.0*  (optional)

    try:
        # List datasets
        api_response = api_instance.get_datasets(limit=limit, offset=offset, order_by=order_by, uri_pattern=uri_pattern, dag_ids=dag_ids)
        print("The response of DatasetApi->get_datasets:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DatasetApi->get_datasets: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **limit** | **int**| The numbers of items to return. | [optional] [default to 100]
 **offset** | **int**| The number of items to skip before starting to collect the result set. | [optional] 
 **order_by** | **str**| The name of the field to order the results by. Prefix a field name with &#x60;-&#x60; to reverse the sort order.  *New in version 2.1.0*  | [optional] 
 **uri_pattern** | **str**| If set, only return datasets with uris matching this pattern.  | [optional] 
 **dag_ids** | **str**| One or more DAG IDs separated by commas to filter datasets by associated DAGs either consuming or producing.  *New in version 2.9.0*  | [optional] 

### Return type

[**DatasetCollection**](DatasetCollection.md)

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

# **get_upstream_dataset_events**
> DatasetEventCollection get_upstream_dataset_events(dag_id, dag_run_id)

Get dataset events for a DAG run

Get datasets for a dag run.  *New in version 2.4.0* 

### Example


```python
import airflow_client
from airflow_client.models.dataset_event_collection import DatasetEventCollection
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
    api_instance = airflow_client.DatasetApi(api_client)
    dag_id = 'dag_id_example' # str | The DAG ID.
    dag_run_id = 'dag_run_id_example' # str | The DAG run ID.

    try:
        # Get dataset events for a DAG run
        api_response = api_instance.get_upstream_dataset_events(dag_id, dag_run_id)
        print("The response of DatasetApi->get_upstream_dataset_events:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DatasetApi->get_upstream_dataset_events: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **dag_id** | **str**| The DAG ID. | 
 **dag_run_id** | **str**| The DAG run ID. | 

### Return type

[**DatasetEventCollection**](DatasetEventCollection.md)

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
**404** | A specified resource is not found. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

