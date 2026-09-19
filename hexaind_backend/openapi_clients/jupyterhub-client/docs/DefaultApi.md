# jupyterhub_client.DefaultApi

All URIs are relative to _/hub/api_

| Method                                                                     | HTTP request                                                | Description                                    |
| -------------------------------------------------------------------------- | ----------------------------------------------------------- | ---------------------------------------------- |
| [**delete_group**](DefaultApi.md#delete_group)                             | **DELETE** /groups/{name}                                   | Delete a group                                 |
| [**delete_group_shared_server**](DefaultApi.md#delete_group_shared_server) | **DELETE** /groups/{name}/shared/{owner}/{server_name}      | Leave a share (group)                          |
| [**delete_group_users**](DefaultApi.md#delete_group_users)                 | **DELETE** /groups/{name}/users                             | Remove users from a group                      |
| [**delete_share_code**](DefaultApi.md#delete_share_code)                   | **DELETE** /share-codes/{owner}/{server_name}               | Revoke share code                              |
| [**delete_shares_server**](DefaultApi.md#delete_shares_server)             | **DELETE** /shares/{owner}/{server_name}                    | Revoke all shared access                       |
| [**delete_user**](DefaultApi.md#delete_user)                               | **DELETE** /users/{name}                                    | Delete a user                                  |
| [**delete_user_server**](DefaultApi.md#delete_user_server)                 | **DELETE** /users/{name}/server                             | Stop a user&#39;s server                       |
| [**delete_user_server_name**](DefaultApi.md#delete_user_server_name)       | **DELETE** /users/{name}/servers/{server_name}              | Stop a user&#39;s named server                 |
| [**delete_user_shared_server**](DefaultApi.md#delete_user_shared_server)   | **DELETE** /users/{name}/shared/{owner}/{server_name}       | Leave a shared server                          |
| [**delete_user_token**](DefaultApi.md#delete_user_token)                   | **DELETE** /users/{name}/tokens/{token_id}                  | Delete (revoke) a token by id                  |
| [**get_api**](DefaultApi.md#get_api)                                       | **GET** /                                                   | Get JupyterHub version                         |
| [**get_auth_cookie**](DefaultApi.md#get_auth_cookie)                       | **GET** /authorizations/cookie/{cookie_name}/{cookie_value} | Identify a user from a cookie                  |
| [**get_auth_token**](DefaultApi.md#get_auth_token)                         | **GET** /authorizations/token/{token}                       | Identify a user or service from an API token   |
| [**get_current_user**](DefaultApi.md#get_current_user)                     | **GET** /user                                               | Get current user                               |
| [**get_group**](DefaultApi.md#get_group)                                   | **GET** /groups/{name}                                      | Get a group by name                            |
| [**get_group_shared**](DefaultApi.md#get_group_shared)                     | **GET** /groups/{name}/shared                               | List servers shared with group                 |
| [**get_group_shared_server**](DefaultApi.md#get_group_shared_server)       | **GET** /groups/{name}/shared/{owner}/{server_name}         | Get group&#39;s shared access                  |
| [**get_groups**](DefaultApi.md#get_groups)                                 | **GET** /groups                                             | List groups                                    |
| [**get_info**](DefaultApi.md#get_info)                                     | **GET** /info                                               | Get detailed info about JupyterHub             |
| [**get_oauth_authorize**](DefaultApi.md#get_oauth_authorize)               | **GET** /oauth2/authorize                                   | OAuth 2.0 authorize endpoint                   |
| [**get_proxy**](DefaultApi.md#get_proxy)                                   | **GET** /proxy                                              | Get the proxy&#39;s routing table              |
| [**get_service**](DefaultApi.md#get_service)                               | **GET** /services/{name}                                    | Get a service by name                          |
| [**get_services**](DefaultApi.md#get_services)                             | **GET** /services                                           | List services                                  |
| [**get_share_codes_owner**](DefaultApi.md#get_share_codes_owner)           | **GET** /share-codes/{owner}                                | List share codes by owner                      |
| [**get_share_codes_server**](DefaultApi.md#get_share_codes_server)         | **GET** /share-codes/{owner}/{server_name}                  | List share codes                               |
| [**get_shares_owner**](DefaultApi.md#get_shares_owner)                     | **GET** /shares/{owner}                                     | List shares by owner                           |
| [**get_shares_server**](DefaultApi.md#get_shares_server)                   | **GET** /shares/{owner}/{server_name}                       | List server shares                             |
| [**get_user**](DefaultApi.md#get_user)                                     | **GET** /users/{name}                                       | Get a user by name                             |
| [**get_user_shared**](DefaultApi.md#get_user_shared)                       | **GET** /users/{name}/shared                                | List servers shared with user                  |
| [**get_user_shared_server**](DefaultApi.md#get_user_shared_server)         | **GET** /users/{name}/shared/{owner}/{server_name}          | Get user&#39;s shared access to server         |
| [**get_user_token**](DefaultApi.md#get_user_token)                         | **GET** /users/{name}/tokens/{token_id}                     | Get one token                                  |
| [**get_user_tokens**](DefaultApi.md#get_user_tokens)                       | **GET** /users/{name}/tokens                                | List tokens for the user                       |
| [**get_users**](DefaultApi.md#get_users)                                   | **GET** /users                                              | List users                                     |
| [**patch_proxy**](DefaultApi.md#patch_proxy)                               | **PATCH** /proxy                                            | Notify the Hub about a new proxy               |
| [**patch_shares_server**](DefaultApi.md#patch_shares_server)               | **PATCH** /shares/{owner}/{server_name}                     | Revoke shared access                           |
| [**patch_user**](DefaultApi.md#patch_user)                                 | **PATCH** /users/{name}                                     | Modify a user                                  |
| [**post_auth_token**](DefaultApi.md#post_auth_token)                       | **POST** /authorizations/token                              | Request a new API token                        |
| [**post_group**](DefaultApi.md#post_group)                                 | **POST** /groups/{name}                                     | Create a group                                 |
| [**post_group_users**](DefaultApi.md#post_group_users)                     | **POST** /groups/{name}/users                               | Add users to a group                           |
| [**post_oauth_token**](DefaultApi.md#post_oauth_token)                     | **POST** /oauth2/token                                      | Request an OAuth2 token                        |
| [**post_proxy**](DefaultApi.md#post_proxy)                                 | **POST** /proxy                                             | Force the Hub to sync with the proxy           |
| [**post_share_code**](DefaultApi.md#post_share_code)                       | **POST** /share-codes/{owner}/{server_name}                 | Issue share code                               |
| [**post_shares_server**](DefaultApi.md#post_shares_server)                 | **POST** /shares/{owner}/{server_name}                      | Grant shared access                            |
| [**post_shutdown**](DefaultApi.md#post_shutdown)                           | **POST** /shutdown                                          | Shutdown the Hub                               |
| [**post_user**](DefaultApi.md#post_user)                                   | **POST** /users/{name}                                      | Create a single user                           |
| [**post_user_activity**](DefaultApi.md#post_user_activity)                 | **POST** /users/{name}/activity                             | Notify Hub of activity for a given user        |
| [**post_user_server**](DefaultApi.md#post_user_server)                     | **POST** /users/{name}/server                               | Start a user&#39;s single-user notebook server |
| [**post_user_server_name**](DefaultApi.md#post_user_server_name)           | **POST** /users/{name}/servers/{server_name}                | Start a user&#39;s named server                |
| [**post_user_tokens**](DefaultApi.md#post_user_tokens)                     | **POST** /users/{name}/tokens                               | Create a new token for the user                |
| [**post_users**](DefaultApi.md#post_users)                                 | **POST** /users                                             | Create multiple users                          |
| [**put_group_properties**](DefaultApi.md#put_group_properties)             | **PUT** /groups/{name}/properties                           | Set group properties                           |

# **delete_group**

> delete_group(name)

Delete a group

### Example

- OAuth Authentication (oauth2):

```python
import jupyterhub_client
from jupyterhub_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /hub/api
# See configuration.py for a list of all supported configuration parameters.
configuration = jupyterhub_client.Configuration(
    host = "/hub/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with jupyterhub_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = jupyterhub_client.DefaultApi(api_client)
    name = 'name_example' # str | group name

    try:
        # Delete a group
        api_instance.delete_group(name)
    except Exception as e:
        print("Exception when calling DefaultApi->delete_group: %s\n" % e)
```

### Parameters

| Name     | Type    | Description | Notes |
| -------- | ------- | ----------- | ----- |
| **name** | **str** | group name  |

### Return type

void (empty response body)

### Authorization

[oauth2](../README.md#oauth2)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: Not defined

### HTTP response details

| Status code | Description                | Response headers |
| ----------- | -------------------------- | ---------------- |
| **204**     | The group has been deleted | -                |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_group_shared_server**

> delete_group_shared_server(name, owner, server_name)

Leave a share (group)

Leave a share by revoking a group's permissions on a single server (new in 5.0)

### Example

- OAuth Authentication (oauth2):

```python
import jupyterhub_client
from jupyterhub_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /hub/api
# See configuration.py for a list of all supported configuration parameters.
configuration = jupyterhub_client.Configuration(
    host = "/hub/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with jupyterhub_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = jupyterhub_client.DefaultApi(api_client)
    name = 'name_example' # str | group name
    owner = 'owner_example' # str | name of the user who owns the shared server
    server_name = 'server_name_example' # str | name of the shared server (empty string for default server, which means the URL ends with a trailing '/', e.g. `/username/`).

    try:
        # Leave a share (group)
        api_instance.delete_group_shared_server(name, owner, server_name)
    except Exception as e:
        print("Exception when calling DefaultApi->delete_group_shared_server: %s\n" % e)
```

### Parameters

| Name            | Type    | Description                                                                                                                                     | Notes |
| --------------- | ------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | ----- |
| **name**        | **str** | group name                                                                                                                                      |
| **owner**       | **str** | name of the user who owns the shared server                                                                                                     |
| **server_name** | **str** | name of the shared server (empty string for default server, which means the URL ends with a trailing &#39;/&#39;, e.g. &#x60;/username/&#x60;). |

### Return type

void (empty response body)

### Authorization

[oauth2](../README.md#oauth2)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: Not defined

### HTTP response details

| Status code | Description                                                                         | Response headers |
| ----------- | ----------------------------------------------------------------------------------- | ---------------- |
| **204**     | Permission has been revoked, the group members no longer have access to the server. | -                |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_group_users**

> delete_group_users(name, delete_group_users_request)

Remove users from a group

Body should be a JSON dictionary where `users` is a list of usernames to remove from the groups. `json {   \"users\": [\"name1\", \"name2\"] } `

### Example

- OAuth Authentication (oauth2):

```python
import jupyterhub_client
from jupyterhub_client.models.delete_group_users_request import DeleteGroupUsersRequest
from jupyterhub_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /hub/api
# See configuration.py for a list of all supported configuration parameters.
configuration = jupyterhub_client.Configuration(
    host = "/hub/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with jupyterhub_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = jupyterhub_client.DefaultApi(api_client)
    name = 'name_example' # str | group name
    delete_group_users_request = jupyterhub_client.DeleteGroupUsersRequest() # DeleteGroupUsersRequest | The users to remove from the group

    try:
        # Remove users from a group
        api_instance.delete_group_users(name, delete_group_users_request)
    except Exception as e:
        print("Exception when calling DefaultApi->delete_group_users: %s\n" % e)
```

### Parameters

| Name                           | Type                                                      | Description                        | Notes |
| ------------------------------ | --------------------------------------------------------- | ---------------------------------- | ----- |
| **name**                       | **str**                                                   | group name                         |
| **delete_group_users_request** | [**DeleteGroupUsersRequest**](DeleteGroupUsersRequest.md) | The users to remove from the group |

### Return type

void (empty response body)

### Authorization

[oauth2](../README.md#oauth2)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: Not defined

### HTTP response details

| Status code | Description                                | Response headers |
| ----------- | ------------------------------------------ | ---------------- |
| **200**     | The users have been removed from the group | -                |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_share_code**

> delete_share_code(owner, server_name, code=code, id=id)

Revoke share code

Revoke a share code by id or code. Exactly one of `id` or `code` must be specified. (new in 5.0)

### Example

- OAuth Authentication (oauth2):

```python
import jupyterhub_client
from jupyterhub_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /hub/api
# See configuration.py for a list of all supported configuration parameters.
configuration = jupyterhub_client.Configuration(
    host = "/hub/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with jupyterhub_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = jupyterhub_client.DefaultApi(api_client)
    owner = 'owner_example' # str | name of the user who owns the shared server
    server_name = 'server_name_example' # str | name of the shared server (empty string for default server, which means the URL ends with a trailing '/', e.g. `/username/`).
    code = 'code_example' # str | the share code to revoke (optional)
    id = 'id_example' # str | the id of the share code to revoke (optional)

    try:
        # Revoke share code
        api_instance.delete_share_code(owner, server_name, code=code, id=id)
    except Exception as e:
        print("Exception when calling DefaultApi->delete_share_code: %s\n" % e)
```

### Parameters

| Name            | Type    | Description                                                                                                                                     | Notes      |
| --------------- | ------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| **owner**       | **str** | name of the user who owns the shared server                                                                                                     |
| **server_name** | **str** | name of the shared server (empty string for default server, which means the URL ends with a trailing &#39;/&#39;, e.g. &#x60;/username/&#x60;). |
| **code**        | **str** | the share code to revoke                                                                                                                        | [optional] |
| **id**          | **str** | the id of the share code to revoke                                                                                                              | [optional] |

### Return type

void (empty response body)

### Authorization

[oauth2](../README.md#oauth2)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: Not defined

### HTTP response details

| Status code | Description                      | Response headers |
| ----------- | -------------------------------- | ---------------- |
| **204**     | The share code has been revoked. | -                |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_shares_server**

> delete_shares_server(owner, server_name)

Revoke all shared access

Revoke all shared access to a given server (new in 5.0)

### Example

- OAuth Authentication (oauth2):

```python
import jupyterhub_client
from jupyterhub_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /hub/api
# See configuration.py for a list of all supported configuration parameters.
configuration = jupyterhub_client.Configuration(
    host = "/hub/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with jupyterhub_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = jupyterhub_client.DefaultApi(api_client)
    owner = 'owner_example' # str | name of the user who owns the shared server
    server_name = 'server_name_example' # str | name of the shared server (empty string for default server, which means the URL ends with a trailing '/', e.g. `/username/`).

    try:
        # Revoke all shared access
        api_instance.delete_shares_server(owner, server_name)
    except Exception as e:
        print("Exception when calling DefaultApi->delete_shares_server: %s\n" % e)
```

### Parameters

| Name            | Type    | Description                                                                                                                                     | Notes |
| --------------- | ------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | ----- |
| **owner**       | **str** | name of the user who owns the shared server                                                                                                     |
| **server_name** | **str** | name of the shared server (empty string for default server, which means the URL ends with a trailing &#39;/&#39;, e.g. &#x60;/username/&#x60;). |

### Return type

void (empty response body)

### Authorization

[oauth2](../README.md#oauth2)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: Not defined

### HTTP response details

| Status code | Description                                 | Response headers |
| ----------- | ------------------------------------------- | ---------------- |
| **204**     | All shares for the server have been deleted | -                |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_user**

> delete_user(name)

Delete a user

### Example

- OAuth Authentication (oauth2):

```python
import jupyterhub_client
from jupyterhub_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /hub/api
# See configuration.py for a list of all supported configuration parameters.
configuration = jupyterhub_client.Configuration(
    host = "/hub/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with jupyterhub_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = jupyterhub_client.DefaultApi(api_client)
    name = 'name_example' # str | username

    try:
        # Delete a user
        api_instance.delete_user(name)
    except Exception as e:
        print("Exception when calling DefaultApi->delete_user: %s\n" % e)
```

### Parameters

| Name     | Type    | Description | Notes |
| -------- | ------- | ----------- | ----- |
| **name** | **str** | username    |

### Return type

void (empty response body)

### Authorization

[oauth2](../README.md#oauth2)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: Not defined

### HTTP response details

| Status code | Description               | Response headers |
| ----------- | ------------------------- | ---------------- |
| **204**     | The user has been deleted | -                |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_user_server**

> delete_user_server(name)

Stop a user's server

### Example

- OAuth Authentication (oauth2):

```python
import jupyterhub_client
from jupyterhub_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /hub/api
# See configuration.py for a list of all supported configuration parameters.
configuration = jupyterhub_client.Configuration(
    host = "/hub/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with jupyterhub_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = jupyterhub_client.DefaultApi(api_client)
    name = 'name_example' # str | username

    try:
        # Stop a user's server
        api_instance.delete_user_server(name)
    except Exception as e:
        print("Exception when calling DefaultApi->delete_user_server: %s\n" % e)
```

### Parameters

| Name     | Type    | Description | Notes |
| -------- | ------- | ----------- | ----- |
| **name** | **str** | username    |

### Return type

void (empty response body)

### Authorization

[oauth2](../README.md#oauth2)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: Not defined

### HTTP response details

| Status code | Description                                                                        | Response headers |
| ----------- | ---------------------------------------------------------------------------------- | ---------------- |
| **202**     | The user&#39;s notebook server has not yet stopped as it is taking a while to stop | -                |
| **204**     | The user&#39;s notebook server has stopped                                         | -                |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_user_server_name**

> delete_user_server_name(name, server_name, delete_user_server_name_request=delete_user_server_name_request)

Stop a user's named server

To remove the named server in addition to deleting it, the body may be a JSON dictionary with a boolean `remove` field: `json {\"remove\": true} `

### Example

- OAuth Authentication (oauth2):

```python
import jupyterhub_client
from jupyterhub_client.models.delete_user_server_name_request import DeleteUserServerNameRequest
from jupyterhub_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /hub/api
# See configuration.py for a list of all supported configuration parameters.
configuration = jupyterhub_client.Configuration(
    host = "/hub/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with jupyterhub_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = jupyterhub_client.DefaultApi(api_client)
    name = 'name_example' # str | username
    server_name = 'server_name_example' # str | name given to a named-server (empty string for default server).  Note that depending on your JupyterHub infrastructure there are limitations to `server_name`. Default spawner with K8s pod will not allow Jupyter Notebooks to be spawned with a name that contains more than 253 characters (keep in hexaind that the pod will be spawned with extra characters to identify the user and hub).
    delete_user_server_name_request = jupyterhub_client.DeleteUserServerNameRequest() # DeleteUserServerNameRequest |  (optional)

    try:
        # Stop a user's named server
        api_instance.delete_user_server_name(name, server_name, delete_user_server_name_request=delete_user_server_name_request)
    except Exception as e:
        print("Exception when calling DefaultApi->delete_user_server_name: %s\n" % e)
```

### Parameters

| Name                                | Type                                                              | Description                                                                                                                                                                                                                                                                                                                                                                                               | Notes      |
| ----------------------------------- | ----------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| **name**                            | **str**                                                           | username                                                                                                                                                                                                                                                                                                                                                                                                  |
| **server_name**                     | **str**                                                           | name given to a named-server (empty string for default server). Note that depending on your JupyterHub infrastructure there are limitations to &#x60;server_name&#x60;. Default spawner with K8s pod will not allow Jupyter Notebooks to be spawned with a name that contains more than 253 characters (keep in hexaind that the pod will be spawned with extra characters to identify the user and hub). |
| **delete_user_server_name_request** | [**DeleteUserServerNameRequest**](DeleteUserServerNameRequest.md) |                                                                                                                                                                                                                                                                                                                                                                                                           | [optional] |

### Return type

void (empty response body)

### Authorization

[oauth2](../README.md#oauth2)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: Not defined

### HTTP response details

| Status code | Description                                                                              | Response headers |
| ----------- | ---------------------------------------------------------------------------------------- | ---------------- |
| **202**     | The user&#39;s notebook named-server has not yet stopped as it is taking a while to stop | -                |
| **204**     | The user&#39;s notebook named-server has stopped                                         | -                |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_user_shared_server**

> delete_user_shared_server(name, owner, server_name)

Leave a shared server

Revokes a user's access to a shared server by deleting. Users generally have access to this endpoint for themselves. (new in 5.0)

### Example

- OAuth Authentication (oauth2):

```python
import jupyterhub_client
from jupyterhub_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /hub/api
# See configuration.py for a list of all supported configuration parameters.
configuration = jupyterhub_client.Configuration(
    host = "/hub/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with jupyterhub_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = jupyterhub_client.DefaultApi(api_client)
    name = 'name_example' # str | username
    owner = 'owner_example' # str | name of the user who owns the shared server
    server_name = 'server_name_example' # str | name of the shared server (empty string for default server, which means the URL ends with a trailing '/', e.g. `/username/`).

    try:
        # Leave a shared server
        api_instance.delete_user_shared_server(name, owner, server_name)
    except Exception as e:
        print("Exception when calling DefaultApi->delete_user_shared_server: %s\n" % e)
```

### Parameters

| Name            | Type    | Description                                                                                                                                     | Notes |
| --------------- | ------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | ----- |
| **name**        | **str** | username                                                                                                                                        |
| **owner**       | **str** | name of the user who owns the shared server                                                                                                     |
| **server_name** | **str** | name of the shared server (empty string for default server, which means the URL ends with a trailing &#39;/&#39;, e.g. &#x60;/username/&#x60;). |

### Return type

void (empty response body)

### Authorization

[oauth2](../README.md#oauth2)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: Not defined

### HTTP response details

| Status code | Description                                                               | Response headers |
| ----------- | ------------------------------------------------------------------------- | ---------------- |
| **204**     | Permission has been revoked, the user no longer has access to the server. | -                |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_user_token**

> delete_user_token(name, token_id)

Delete (revoke) a token by id

### Example

- OAuth Authentication (oauth2):

```python
import jupyterhub_client
from jupyterhub_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /hub/api
# See configuration.py for a list of all supported configuration parameters.
configuration = jupyterhub_client.Configuration(
    host = "/hub/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with jupyterhub_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = jupyterhub_client.DefaultApi(api_client)
    name = 'name_example' # str | username
    token_id = 'token_id_example' # str |

    try:
        # Delete (revoke) a token by id
        api_instance.delete_user_token(name, token_id)
    except Exception as e:
        print("Exception when calling DefaultApi->delete_user_token: %s\n" % e)
```

### Parameters

| Name         | Type    | Description | Notes |
| ------------ | ------- | ----------- | ----- |
| **name**     | **str** | username    |
| **token_id** | **str** |             |

### Return type

void (empty response body)

### Authorization

[oauth2](../README.md#oauth2)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: Not defined

### HTTP response details

| Status code | Description                | Response headers |
| ----------- | -------------------------- | ---------------- |
| **204**     | The token has been deleted | -                |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_api**

> GetApi200Response get_api()

Get JupyterHub version

This endpoint is not authenticated for the purpose of clients and user to identify the JupyterHub version before setting up authentication.

### Example

- OAuth Authentication (oauth2):
- Bearer Authentication (token):

```python
import jupyterhub_client
from jupyterhub_client.models.get_api200_response import GetApi200Response
from jupyterhub_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /hub/api
# See configuration.py for a list of all supported configuration parameters.
configuration = jupyterhub_client.Configuration(
    host = "/hub/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Configure Bearer authorization: token
configuration = jupyterhub_client.Configuration(
    access_token = os.environ["BEARER_TOKEN"]
)

# Enter a context with an instance of the API client
with jupyterhub_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = jupyterhub_client.DefaultApi(api_client)

    try:
        # Get JupyterHub version
        api_response = api_instance.get_api()
        print("The response of DefaultApi->get_api:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->get_api: %s\n" % e)
```

### Parameters

This endpoint does not need any parameter.

### Return type

[**GetApi200Response**](GetApi200Response.md)

### Authorization

[oauth2](../README.md#oauth2), [token](../README.md#token)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details

| Status code | Description            | Response headers |
| ----------- | ---------------------- | ---------------- |
| **200**     | The JupyterHub version | -                |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_auth_cookie**

> User get_auth_cookie(cookie_name, cookie_value)

Identify a user from a cookie

Used by single-user notebook servers to hand off cookie authentication to the Hub

### Example

- OAuth Authentication (oauth2):
- Bearer Authentication (token):

```python
import jupyterhub_client
from jupyterhub_client.models.user import User
from jupyterhub_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /hub/api
# See configuration.py for a list of all supported configuration parameters.
configuration = jupyterhub_client.Configuration(
    host = "/hub/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Configure Bearer authorization: token
configuration = jupyterhub_client.Configuration(
    access_token = os.environ["BEARER_TOKEN"]
)

# Enter a context with an instance of the API client
with jupyterhub_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = jupyterhub_client.DefaultApi(api_client)
    cookie_name = 'cookie_name_example' # str |
    cookie_value = 'cookie_value_example' # str |

    try:
        # Identify a user from a cookie
        api_response = api_instance.get_auth_cookie(cookie_name, cookie_value)
        print("The response of DefaultApi->get_auth_cookie:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->get_auth_cookie: %s\n" % e)
```

### Parameters

| Name             | Type    | Description | Notes |
| ---------------- | ------- | ----------- | ----- |
| **cookie_name**  | **str** |             |
| **cookie_value** | **str** |             |

### Return type

[**User**](User.md)

### Authorization

[oauth2](../README.md#oauth2), [token](../README.md#token)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details

| Status code | Description                       | Response headers |
| ----------- | --------------------------------- | ---------------- |
| **200**     | The user identified by the cookie | -                |
| **404**     | A user is not found.              | -                |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_auth_token**

> get_auth_token(token)

Identify a user or service from an API token

### Example

- OAuth Authentication (oauth2):

```python
import jupyterhub_client
from jupyterhub_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /hub/api
# See configuration.py for a list of all supported configuration parameters.
configuration = jupyterhub_client.Configuration(
    host = "/hub/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with jupyterhub_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = jupyterhub_client.DefaultApi(api_client)
    token = 'token_example' # str |

    try:
        # Identify a user or service from an API token
        api_instance.get_auth_token(token)
    except Exception as e:
        print("Exception when calling DefaultApi->get_auth_token: %s\n" % e)
```

### Parameters

| Name      | Type    | Description | Notes |
| --------- | ------- | ----------- | ----- |
| **token** | **str** |             |

### Return type

void (empty response body)

### Authorization

[oauth2](../README.md#oauth2)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: Not defined

### HTTP response details

| Status code | Description                                     | Response headers |
| ----------- | ----------------------------------------------- | ---------------- |
| **200**     | The user or service identified by the API token | -                |
| **404**     | A user or service is not found.                 | -                |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_current_user**

> RequestIdentity get_current_user()

Get current user

Returns the User model for the owner of the authenticating token. Includes information about the requesting token itself, such as the currently authorized scopes.

### Example

- OAuth Authentication (oauth2):

```python
import jupyterhub_client
from jupyterhub_client.models.request_identity import RequestIdentity
from jupyterhub_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /hub/api
# See configuration.py for a list of all supported configuration parameters.
configuration = jupyterhub_client.Configuration(
    host = "/hub/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with jupyterhub_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = jupyterhub_client.DefaultApi(api_client)

    try:
        # Get current user
        api_response = api_instance.get_current_user()
        print("The response of DefaultApi->get_current_user:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->get_current_user: %s\n" % e)
```

### Parameters

This endpoint does not need any parameter.

### Return type

[**RequestIdentity**](RequestIdentity.md)

### Authorization

[oauth2](../README.md#oauth2)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details

| Status code | Description                                                                                                                                    | Response headers |
| ----------- | ---------------------------------------------------------------------------------------------------------------------------------------------- | ---------------- |
| **200**     | The authenticated user or service&#39;s model is returned with additional information about the permissions associated with the request token. | -                |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_group**

> Group get_group(name)

Get a group by name

### Example

- OAuth Authentication (oauth2):

```python
import jupyterhub_client
from jupyterhub_client.models.group import Group
from jupyterhub_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /hub/api
# See configuration.py for a list of all supported configuration parameters.
configuration = jupyterhub_client.Configuration(
    host = "/hub/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with jupyterhub_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = jupyterhub_client.DefaultApi(api_client)
    name = 'name_example' # str | group name

    try:
        # Get a group by name
        api_response = api_instance.get_group(name)
        print("The response of DefaultApi->get_group:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->get_group: %s\n" % e)
```

### Parameters

| Name     | Type    | Description | Notes |
| -------- | ------- | ----------- | ----- |
| **name** | **str** | group name  |

### Return type

[**Group**](Group.md)

### Authorization

[oauth2](../README.md#oauth2)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details

| Status code | Description     | Response headers |
| ----------- | --------------- | ---------------- |
| **200**     | The group model | -                |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_group_shared**

> GetGroupShared200Response get_group_shared(name)

List servers shared with group

Lists shares granting `group` access to shared servers (new in 5.0)

### Example

- OAuth Authentication (oauth2):

```python
import jupyterhub_client
from jupyterhub_client.models.get_group_shared200_response import GetGroupShared200Response
from jupyterhub_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /hub/api
# See configuration.py for a list of all supported configuration parameters.
configuration = jupyterhub_client.Configuration(
    host = "/hub/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with jupyterhub_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = jupyterhub_client.DefaultApi(api_client)
    name = 'name_example' # str | group name

    try:
        # List servers shared with group
        api_response = api_instance.get_group_shared(name)
        print("The response of DefaultApi->get_group_shared:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->get_group_shared: %s\n" % e)
```

### Parameters

| Name     | Type    | Description | Notes |
| -------- | ------- | ----------- | ----- |
| **name** | **str** | group name  |

### Return type

[**GetGroupShared200Response**](GetGroupShared200Response.md)

### Authorization

[oauth2](../README.md#oauth2)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details

| Status code | Description                        | Response headers |
| ----------- | ---------------------------------- | ---------------- |
| **200**     | Shared access granted to the group | -                |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_group_shared_server**

> Share get_group_shared_server(name, owner, server_name)

Get group's shared access

Get the Share representing a single group's access to a single server (new in 5.0)

### Example

- OAuth Authentication (oauth2):

```python
import jupyterhub_client
from jupyterhub_client.models.share import Share
from jupyterhub_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /hub/api
# See configuration.py for a list of all supported configuration parameters.
configuration = jupyterhub_client.Configuration(
    host = "/hub/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with jupyterhub_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = jupyterhub_client.DefaultApi(api_client)
    name = 'name_example' # str | group name
    owner = 'owner_example' # str | name of the user who owns the shared server
    server_name = 'server_name_example' # str | name of the shared server (empty string for default server, which means the URL ends with a trailing '/', e.g. `/username/`).

    try:
        # Get group's shared access
        api_response = api_instance.get_group_shared_server(name, owner, server_name)
        print("The response of DefaultApi->get_group_shared_server:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->get_group_shared_server: %s\n" % e)
```

### Parameters

| Name            | Type    | Description                                                                                                                                     | Notes |
| --------------- | ------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | ----- |
| **name**        | **str** | group name                                                                                                                                      |
| **owner**       | **str** | name of the user who owns the shared server                                                                                                     |
| **server_name** | **str** | name of the shared server (empty string for default server, which means the URL ends with a trailing &#39;/&#39;, e.g. &#x60;/username/&#x60;). |

### Return type

[**Share**](Share.md)

### Authorization

[oauth2](../README.md#oauth2)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details

| Status code | Description                                                                         | Response headers |
| ----------- | ----------------------------------------------------------------------------------- | ---------------- |
| **200**     | The permissions granted to members of &#x60;group&#x60; on &#x60;owner/server&#x60; | -                |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_groups**

> List[Group] get_groups(offset=offset, limit=limit)

List groups

### Example

- OAuth Authentication (oauth2):

```python
import jupyterhub_client
from jupyterhub_client.models.group import Group
from jupyterhub_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /hub/api
# See configuration.py for a list of all supported configuration parameters.
configuration = jupyterhub_client.Configuration(
    host = "/hub/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with jupyterhub_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = jupyterhub_client.DefaultApi(api_client)
    offset = 3.4 # float | Return a number of results, starting at the specified offset. Can be used with limit to paginate. If unspecified, return all items.  (optional)
    limit = 3.4 # float | Return a finite number of results. Can be used with offset to paginate. If unspecified, use api_page_default_limit.  (optional)

    try:
        # List groups
        api_response = api_instance.get_groups(offset=offset, limit=limit)
        print("The response of DefaultApi->get_groups:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->get_groups: %s\n" % e)
```

### Parameters

| Name       | Type      | Description                                                                                                                         | Notes      |
| ---------- | --------- | ----------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| **offset** | **float** | Return a number of results, starting at the specified offset. Can be used with limit to paginate. If unspecified, return all items. | [optional] |
| **limit**  | **float** | Return a finite number of results. Can be used with offset to paginate. If unspecified, use api_page_default_limit.                 | [optional] |

### Return type

[**List[Group]**](Group.md)

### Authorization

[oauth2](../README.md#oauth2)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details

| Status code | Description        | Response headers |
| ----------- | ------------------ | ---------------- |
| **200**     | The list of groups | -                |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_info**

> GetInfo200Response get_info()

Get detailed info about JupyterHub

Detailed JupyterHub information, including Python version, JupyterHub's version and executable path, and which Authenticator and Spawner are active.

### Example

- OAuth Authentication (oauth2):

```python
import jupyterhub_client
from jupyterhub_client.models.get_info200_response import GetInfo200Response
from jupyterhub_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /hub/api
# See configuration.py for a list of all supported configuration parameters.
configuration = jupyterhub_client.Configuration(
    host = "/hub/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with jupyterhub_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = jupyterhub_client.DefaultApi(api_client)

    try:
        # Get detailed info about JupyterHub
        api_response = api_instance.get_info()
        print("The response of DefaultApi->get_info:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->get_info: %s\n" % e)
```

### Parameters

This endpoint does not need any parameter.

### Return type

[**GetInfo200Response**](GetInfo200Response.md)

### Authorization

[oauth2](../README.md#oauth2)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details

| Status code | Description              | Response headers |
| ----------- | ------------------------ | ---------------- |
| **200**     | Detailed JupyterHub info | -                |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_oauth_authorize**

> get_oauth_authorize(client_id, response_type, redirect_uri, state=state)

OAuth 2.0 authorize endpoint

Redirect users to this URL to begin the OAuth process. It is not an API endpoint.

### Example

- OAuth Authentication (oauth2):
- Bearer Authentication (token):

```python
import jupyterhub_client
from jupyterhub_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /hub/api
# See configuration.py for a list of all supported configuration parameters.
configuration = jupyterhub_client.Configuration(
    host = "/hub/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Configure Bearer authorization: token
configuration = jupyterhub_client.Configuration(
    access_token = os.environ["BEARER_TOKEN"]
)

# Enter a context with an instance of the API client
with jupyterhub_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = jupyterhub_client.DefaultApi(api_client)
    client_id = 'client_id_example' # str | The client id
    response_type = 'response_type_example' # str | The response type (always 'code')
    redirect_uri = 'redirect_uri_example' # str | The redirect url
    state = 'state_example' # str | A state string (optional)

    try:
        # OAuth 2.0 authorize endpoint
        api_instance.get_oauth_authorize(client_id, response_type, redirect_uri, state=state)
    except Exception as e:
        print("Exception when calling DefaultApi->get_oauth_authorize: %s\n" % e)
```

### Parameters

| Name              | Type    | Description                               | Notes      |
| ----------------- | ------- | ----------------------------------------- | ---------- |
| **client_id**     | **str** | The client id                             |
| **response_type** | **str** | The response type (always &#39;code&#39;) |
| **redirect_uri**  | **str** | The redirect url                          |
| **state**         | **str** | A state string                            | [optional] |

### Return type

void (empty response body)

### Authorization

[oauth2](../README.md#oauth2), [token](../README.md#token)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: Not defined

### HTTP response details

| Status code | Description | Response headers |
| ----------- | ----------- | ---------------- |
| **200**     | Success     | -                |
| **400**     | OAuth2Error | -                |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_proxy**

> object get_proxy(offset=offset, limit=limit)

Get the proxy's routing table

A convenience alias for getting the routing table directly from the proxy

### Example

- OAuth Authentication (oauth2):

```python
import jupyterhub_client
from jupyterhub_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /hub/api
# See configuration.py for a list of all supported configuration parameters.
configuration = jupyterhub_client.Configuration(
    host = "/hub/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with jupyterhub_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = jupyterhub_client.DefaultApi(api_client)
    offset = 3.4 # float | Return a number of results, starting at the specified offset. Can be used with limit to paginate. If unspecified, return all items.  (optional)
    limit = 3.4 # float | Return a finite number of results. Can be used with offset to paginate. If unspecified, use api_page_default_limit.  (optional)

    try:
        # Get the proxy's routing table
        api_response = api_instance.get_proxy(offset=offset, limit=limit)
        print("The response of DefaultApi->get_proxy:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->get_proxy: %s\n" % e)
```

### Parameters

| Name       | Type      | Description                                                                                                                         | Notes      |
| ---------- | --------- | ----------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| **offset** | **float** | Return a number of results, starting at the specified offset. Can be used with limit to paginate. If unspecified, return all items. | [optional] |
| **limit**  | **float** | Return a finite number of results. Can be used with offset to paginate. If unspecified, use api_page_default_limit.                 | [optional] |

### Return type

**object**

### Authorization

[oauth2](../README.md#oauth2)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details

| Status code | Description   | Response headers |
| ----------- | ------------- | ---------------- |
| **200**     | Routing table | -                |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_service**

> Service get_service(name)

Get a service by name

### Example

- OAuth Authentication (oauth2):

```python
import jupyterhub_client
from jupyterhub_client.models.service import Service
from jupyterhub_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /hub/api
# See configuration.py for a list of all supported configuration parameters.
configuration = jupyterhub_client.Configuration(
    host = "/hub/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with jupyterhub_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = jupyterhub_client.DefaultApi(api_client)
    name = 'name_example' # str | service name

    try:
        # Get a service by name
        api_response = api_instance.get_service(name)
        print("The response of DefaultApi->get_service:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->get_service: %s\n" % e)
```

### Parameters

| Name     | Type    | Description  | Notes |
| -------- | ------- | ------------ | ----- |
| **name** | **str** | service name |

### Return type

[**Service**](Service.md)

### Authorization

[oauth2](../README.md#oauth2)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details

| Status code | Description       | Response headers |
| ----------- | ----------------- | ---------------- |
| **200**     | The Service model | -                |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_services**

> List[Service] get_services(offset=offset, limit=limit)

List services

### Example

- OAuth Authentication (oauth2):

```python
import jupyterhub_client
from jupyterhub_client.models.service import Service
from jupyterhub_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /hub/api
# See configuration.py for a list of all supported configuration parameters.
configuration = jupyterhub_client.Configuration(
    host = "/hub/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with jupyterhub_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = jupyterhub_client.DefaultApi(api_client)
    offset = 3.4 # float | Return a number of results, starting at the specified offset. Can be used with limit to paginate. If unspecified, return all items.  (optional)
    limit = 3.4 # float | Return a finite number of results. Can be used with offset to paginate. If unspecified, use api_page_default_limit.  (optional)

    try:
        # List services
        api_response = api_instance.get_services(offset=offset, limit=limit)
        print("The response of DefaultApi->get_services:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->get_services: %s\n" % e)
```

### Parameters

| Name       | Type      | Description                                                                                                                         | Notes      |
| ---------- | --------- | ----------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| **offset** | **float** | Return a number of results, starting at the specified offset. Can be used with limit to paginate. If unspecified, return all items. | [optional] |
| **limit**  | **float** | Return a finite number of results. Can be used with offset to paginate. If unspecified, use api_page_default_limit.                 | [optional] |

### Return type

[**List[Service]**](Service.md)

### Authorization

[oauth2](../README.md#oauth2)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details

| Status code | Description      | Response headers |
| ----------- | ---------------- | ---------------- |
| **200**     | The service list | -                |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_share_codes_owner**

> GetUserShared200Response get_share_codes_owner(owner, offset=offset, limit=limit)

List share codes by owner

List share codes granting access to a user's servers (new in 5.0)

### Example

- OAuth Authentication (oauth2):

```python
import jupyterhub_client
from jupyterhub_client.models.get_user_shared200_response import GetUserShared200Response
from jupyterhub_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /hub/api
# See configuration.py for a list of all supported configuration parameters.
configuration = jupyterhub_client.Configuration(
    host = "/hub/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with jupyterhub_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = jupyterhub_client.DefaultApi(api_client)
    owner = 'owner_example' # str | name of the user who owns the shared server
    offset = 3.4 # float | Return a number of results, starting at the specified offset. Can be used with limit to paginate. If unspecified, return all items.  (optional)
    limit = 3.4 # float | Return a finite number of results. Can be used with offset to paginate. If unspecified, use api_page_default_limit.  (optional)

    try:
        # List share codes by owner
        api_response = api_instance.get_share_codes_owner(owner, offset=offset, limit=limit)
        print("The response of DefaultApi->get_share_codes_owner:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->get_share_codes_owner: %s\n" % e)
```

### Parameters

| Name       | Type      | Description                                                                                                                         | Notes      |
| ---------- | --------- | ----------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| **owner**  | **str**   | name of the user who owns the shared server                                                                                         |
| **offset** | **float** | Return a number of results, starting at the specified offset. Can be used with limit to paginate. If unspecified, return all items. | [optional] |
| **limit**  | **float** | Return a finite number of results. Can be used with offset to paginate. If unspecified, use api_page_default_limit.                 | [optional] |

### Return type

[**GetUserShared200Response**](GetUserShared200Response.md)

### Authorization

[oauth2](../README.md#oauth2)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details

| Status code | Description             | Response headers |
| ----------- | ----------------------- | ---------------- |
| **200**     | The list of share codes | -                |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_share_codes_server**

> GetUserShared200Response get_share_codes_server(owner, server_name, offset=offset, limit=limit)

List share codes

List share codes which can be exchanged for access to a single server (new in 5.0)

### Example

- OAuth Authentication (oauth2):

```python
import jupyterhub_client
from jupyterhub_client.models.get_user_shared200_response import GetUserShared200Response
from jupyterhub_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /hub/api
# See configuration.py for a list of all supported configuration parameters.
configuration = jupyterhub_client.Configuration(
    host = "/hub/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with jupyterhub_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = jupyterhub_client.DefaultApi(api_client)
    owner = 'owner_example' # str | name of the user who owns the shared server
    server_name = 'server_name_example' # str | name of the shared server (empty string for default server, which means the URL ends with a trailing '/', e.g. `/username/`).
    offset = 3.4 # float | Return a number of results, starting at the specified offset. Can be used with limit to paginate. If unspecified, return all items.  (optional)
    limit = 3.4 # float | Return a finite number of results. Can be used with offset to paginate. If unspecified, use api_page_default_limit.  (optional)

    try:
        # List share codes
        api_response = api_instance.get_share_codes_server(owner, server_name, offset=offset, limit=limit)
        print("The response of DefaultApi->get_share_codes_server:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->get_share_codes_server: %s\n" % e)
```

### Parameters

| Name            | Type      | Description                                                                                                                                     | Notes      |
| --------------- | --------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| **owner**       | **str**   | name of the user who owns the shared server                                                                                                     |
| **server_name** | **str**   | name of the shared server (empty string for default server, which means the URL ends with a trailing &#39;/&#39;, e.g. &#x60;/username/&#x60;). |
| **offset**      | **float** | Return a number of results, starting at the specified offset. Can be used with limit to paginate. If unspecified, return all items.             | [optional] |
| **limit**       | **float** | Return a finite number of results. Can be used with offset to paginate. If unspecified, use api_page_default_limit.                             | [optional] |

### Return type

[**GetUserShared200Response**](GetUserShared200Response.md)

### Authorization

[oauth2](../README.md#oauth2)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details

| Status code | Description             | Response headers |
| ----------- | ----------------------- | ---------------- |
| **200**     | The list of share codes | -                |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_shares_owner**

> GetGroupShared200Response get_shares_owner(owner, offset=offset, limit=limit)

List shares by owner

List shares granting access to any of owner's servers (new in 5.0)

### Example

- OAuth Authentication (oauth2):

```python
import jupyterhub_client
from jupyterhub_client.models.get_group_shared200_response import GetGroupShared200Response
from jupyterhub_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /hub/api
# See configuration.py for a list of all supported configuration parameters.
configuration = jupyterhub_client.Configuration(
    host = "/hub/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with jupyterhub_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = jupyterhub_client.DefaultApi(api_client)
    owner = 'owner_example' # str | name of the user who owns the shared server
    offset = 3.4 # float | Return a number of results, starting at the specified offset. Can be used with limit to paginate. If unspecified, return all items.  (optional)
    limit = 3.4 # float | Return a finite number of results. Can be used with offset to paginate. If unspecified, use api_page_default_limit.  (optional)

    try:
        # List shares by owner
        api_response = api_instance.get_shares_owner(owner, offset=offset, limit=limit)
        print("The response of DefaultApi->get_shares_owner:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->get_shares_owner: %s\n" % e)
```

### Parameters

| Name       | Type      | Description                                                                                                                         | Notes      |
| ---------- | --------- | ----------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| **owner**  | **str**   | name of the user who owns the shared server                                                                                         |
| **offset** | **float** | Return a number of results, starting at the specified offset. Can be used with limit to paginate. If unspecified, return all items. | [optional] |
| **limit**  | **float** | Return a finite number of results. Can be used with offset to paginate. If unspecified, use api_page_default_limit.                 | [optional] |

### Return type

[**GetGroupShared200Response**](GetGroupShared200Response.md)

### Authorization

[oauth2](../README.md#oauth2)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details

| Status code | Description                                          | Response headers |
| ----------- | ---------------------------------------------------- | ---------------- |
| **200**     | The list of shares for any of the user&#39;s servers | -                |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_shares_server**

> GetGroupShared200Response get_shares_server(owner, server_name, offset=offset, limit=limit)

List server shares

List shares granting access to a single server (new in 5.0)

### Example

- OAuth Authentication (oauth2):

```python
import jupyterhub_client
from jupyterhub_client.models.get_group_shared200_response import GetGroupShared200Response
from jupyterhub_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /hub/api
# See configuration.py for a list of all supported configuration parameters.
configuration = jupyterhub_client.Configuration(
    host = "/hub/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with jupyterhub_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = jupyterhub_client.DefaultApi(api_client)
    owner = 'owner_example' # str | name of the user who owns the shared server
    server_name = 'server_name_example' # str | name of the shared server (empty string for default server, which means the URL ends with a trailing '/', e.g. `/username/`).
    offset = 3.4 # float | Return a number of results, starting at the specified offset. Can be used with limit to paginate. If unspecified, return all items.  (optional)
    limit = 3.4 # float | Return a finite number of results. Can be used with offset to paginate. If unspecified, use api_page_default_limit.  (optional)

    try:
        # List server shares
        api_response = api_instance.get_shares_server(owner, server_name, offset=offset, limit=limit)
        print("The response of DefaultApi->get_shares_server:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->get_shares_server: %s\n" % e)
```

### Parameters

| Name            | Type      | Description                                                                                                                                     | Notes      |
| --------------- | --------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| **owner**       | **str**   | name of the user who owns the shared server                                                                                                     |
| **server_name** | **str**   | name of the shared server (empty string for default server, which means the URL ends with a trailing &#39;/&#39;, e.g. &#x60;/username/&#x60;). |
| **offset**      | **float** | Return a number of results, starting at the specified offset. Can be used with limit to paginate. If unspecified, return all items.             | [optional] |
| **limit**       | **float** | Return a finite number of results. Can be used with offset to paginate. If unspecified, use api_page_default_limit.                             | [optional] |

### Return type

[**GetGroupShared200Response**](GetGroupShared200Response.md)

### Authorization

[oauth2](../README.md#oauth2)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details

| Status code | Description                                            | Response headers |
| ----------- | ------------------------------------------------------ | ---------------- |
| **200**     | The list of shares granting access to the given server | -                |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_user**

> User get_user(name, include_stopped_servers=include_stopped_servers)

Get a user by name

### Example

- OAuth Authentication (oauth2):

```python
import jupyterhub_client
from jupyterhub_client.models.user import User
from jupyterhub_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /hub/api
# See configuration.py for a list of all supported configuration parameters.
configuration = jupyterhub_client.Configuration(
    host = "/hub/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with jupyterhub_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = jupyterhub_client.DefaultApi(api_client)
    name = 'name_example' # str | username
    include_stopped_servers = True # bool | Include stopped servers in user model(s). (optional)

    try:
        # Get a user by name
        api_response = api_instance.get_user(name, include_stopped_servers=include_stopped_servers)
        print("The response of DefaultApi->get_user:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->get_user: %s\n" % e)
```

### Parameters

| Name                        | Type     | Description                               | Notes      |
| --------------------------- | -------- | ----------------------------------------- | ---------- |
| **name**                    | **str**  | username                                  |
| **include_stopped_servers** | **bool** | Include stopped servers in user model(s). | [optional] |

### Return type

[**User**](User.md)

### Authorization

[oauth2](../README.md#oauth2)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details

| Status code | Description    | Response headers |
| ----------- | -------------- | ---------------- |
| **200**     | The User model | -                |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_user_shared**

> GetUserShared200Response get_user_shared(name)

List servers shared with user

Returns list of Shares granting the user access to servers owned by others (new in 5.0)

### Example

- OAuth Authentication (oauth2):

```python
import jupyterhub_client
from jupyterhub_client.models.get_user_shared200_response import GetUserShared200Response
from jupyterhub_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /hub/api
# See configuration.py for a list of all supported configuration parameters.
configuration = jupyterhub_client.Configuration(
    host = "/hub/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with jupyterhub_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = jupyterhub_client.DefaultApi(api_client)
    name = 'name_example' # str | username

    try:
        # List servers shared with user
        api_response = api_instance.get_user_shared(name)
        print("The response of DefaultApi->get_user_shared:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->get_user_shared: %s\n" % e)
```

### Parameters

| Name     | Type    | Description | Notes |
| -------- | ------- | ----------- | ----- |
| **name** | **str** | username    |

### Return type

[**GetUserShared200Response**](GetUserShared200Response.md)

### Authorization

[oauth2](../README.md#oauth2)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details

| Status code | Description                       | Response headers |
| ----------- | --------------------------------- | ---------------- |
| **200**     | Shared access granted to the user | -                |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_user_shared_server**

> Share get_user_shared_server(name, owner, server_name)

Get user's shared access to server

Gets the Share representing a single user's access to a single server. Users generally have access to this endpoint for themselves. (new in 5.0)

### Example

- OAuth Authentication (oauth2):

```python
import jupyterhub_client
from jupyterhub_client.models.share import Share
from jupyterhub_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /hub/api
# See configuration.py for a list of all supported configuration parameters.
configuration = jupyterhub_client.Configuration(
    host = "/hub/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with jupyterhub_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = jupyterhub_client.DefaultApi(api_client)
    name = 'name_example' # str | username
    owner = 'owner_example' # str | name of the user who owns the shared server
    server_name = 'server_name_example' # str | name of the shared server (empty string for default server, which means the URL ends with a trailing '/', e.g. `/username/`).

    try:
        # Get user's shared access to server
        api_response = api_instance.get_user_shared_server(name, owner, server_name)
        print("The response of DefaultApi->get_user_shared_server:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->get_user_shared_server: %s\n" % e)
```

### Parameters

| Name            | Type    | Description                                                                                                                                     | Notes |
| --------------- | ------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | ----- |
| **name**        | **str** | username                                                                                                                                        |
| **owner**       | **str** | name of the user who owns the shared server                                                                                                     |
| **server_name** | **str** | name of the shared server (empty string for default server, which means the URL ends with a trailing &#39;/&#39;, e.g. &#x60;/username/&#x60;). |

### Return type

[**Share**](Share.md)

### Authorization

[oauth2](../README.md#oauth2)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details

| Status code | Description                                                              | Response headers |
| ----------- | ------------------------------------------------------------------------ | ---------------- |
| **200**     | The permissions granted to &#x60;user&#x60; on &#x60;owner/server&#x60;. | -                |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_user_token**

> Token get_user_token(name, token_id)

Get one token

Get the details for one token by id

### Example

- OAuth Authentication (oauth2):

```python
import jupyterhub_client
from jupyterhub_client.models.token import Token
from jupyterhub_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /hub/api
# See configuration.py for a list of all supported configuration parameters.
configuration = jupyterhub_client.Configuration(
    host = "/hub/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with jupyterhub_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = jupyterhub_client.DefaultApi(api_client)
    name = 'name_example' # str | username
    token_id = 'token_id_example' # str |

    try:
        # Get one token
        api_response = api_instance.get_user_token(name, token_id)
        print("The response of DefaultApi->get_user_token:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->get_user_token: %s\n" % e)
```

### Parameters

| Name         | Type    | Description | Notes |
| ------------ | ------- | ----------- | ----- |
| **name**     | **str** | username    |
| **token_id** | **str** |             |

### Return type

[**Token**](Token.md)

### Authorization

[oauth2](../README.md#oauth2)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details

| Status code | Description            | Response headers |
| ----------- | ---------------------- | ---------------- |
| **200**     | The info for the token | -                |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_user_tokens**

> GetUserTokens200Response get_user_tokens(name)

List tokens for the user

### Example

- OAuth Authentication (oauth2):

```python
import jupyterhub_client
from jupyterhub_client.models.get_user_tokens200_response import GetUserTokens200Response
from jupyterhub_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /hub/api
# See configuration.py for a list of all supported configuration parameters.
configuration = jupyterhub_client.Configuration(
    host = "/hub/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with jupyterhub_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = jupyterhub_client.DefaultApi(api_client)
    name = 'name_example' # str | username

    try:
        # List tokens for the user
        api_response = api_instance.get_user_tokens(name)
        print("The response of DefaultApi->get_user_tokens:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->get_user_tokens: %s\n" % e)
```

### Parameters

| Name     | Type    | Description | Notes |
| -------- | ------- | ----------- | ----- |
| **name** | **str** | username    |

### Return type

[**GetUserTokens200Response**](GetUserTokens200Response.md)

### Authorization

[oauth2](../README.md#oauth2)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details

| Status code | Description                        | Response headers |
| ----------- | ---------------------------------- | ---------------- |
| **200**     | The list of tokens                 | -                |
| **401**     | Authentication/Authorization error | -                |
| **404**     | No such user                       | -                |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_users**

> List[User] get_users(state=state, offset=offset, limit=limit, include_stopped_servers=include_stopped_servers, sort=sort)

List users

### Example

- OAuth Authentication (oauth2):

```python
import jupyterhub_client
from jupyterhub_client.models.user import User
from jupyterhub_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /hub/api
# See configuration.py for a list of all supported configuration parameters.
configuration = jupyterhub_client.Configuration(
    host = "/hub/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with jupyterhub_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = jupyterhub_client.DefaultApi(api_client)
    state = 'state_example' # str | Return only users who have servers in the given state. If unspecified, return all users.  active: all users with any active servers (ready OR pending) ready: all users who have any ready servers (running, not pending) inactive: all users who have *no* active servers (complement of active)  Added in JupyterHub 1.3  (optional)
    offset = 3.4 # float | Return a number of results, starting at the specified offset. Can be used with limit to paginate. If unspecified, return all items.  (optional)
    limit = 3.4 # float | Return a finite number of results. Can be used with offset to paginate. If unspecified, use api_page_default_limit.  (optional)
    include_stopped_servers = True # bool | Include stopped servers in user model(s). Added in JupyterHub 3.0. Allows retrieval of information about stopped servers, such as activity and state fields.  (optional)
    sort = 'id' # str | Sort users by this key (new in JupyterHub 5.0). Default: `id` (opaque but stable internal order). Supported fields: `id`, `name`, `last_activity`. Results will be in ascending order. Descending order can be requested with a `-` prefix, e.g. `sort=-last_activity` for most recently active users first.  (optional)

    try:
        # List users
        api_response = api_instance.get_users(state=state, offset=offset, limit=limit, include_stopped_servers=include_stopped_servers, sort=sort)
        print("The response of DefaultApi->get_users:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->get_users: %s\n" % e)
```

### Parameters

| Name                        | Type      | Description                                                                                                                                                                                                                                                                                                                                                                   | Notes      |
| --------------------------- | --------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| **state**                   | **str**   | Return only users who have servers in the given state. If unspecified, return all users. active: all users with any active servers (ready OR pending) ready: all users who have any ready servers (running, not pending) inactive: all users who have _no_ active servers (complement of active) Added in JupyterHub 1.3                                                      | [optional] |
| **offset**                  | **float** | Return a number of results, starting at the specified offset. Can be used with limit to paginate. If unspecified, return all items.                                                                                                                                                                                                                                           | [optional] |
| **limit**                   | **float** | Return a finite number of results. Can be used with offset to paginate. If unspecified, use api_page_default_limit.                                                                                                                                                                                                                                                           | [optional] |
| **include_stopped_servers** | **bool**  | Include stopped servers in user model(s). Added in JupyterHub 3.0. Allows retrieval of information about stopped servers, such as activity and state fields.                                                                                                                                                                                                                  | [optional] |
| **sort**                    | **str**   | Sort users by this key (new in JupyterHub 5.0). Default: &#x60;id&#x60; (opaque but stable internal order). Supported fields: &#x60;id&#x60;, &#x60;name&#x60;, &#x60;last_activity&#x60;. Results will be in ascending order. Descending order can be requested with a &#x60;-&#x60; prefix, e.g. &#x60;sort&#x3D;-last_activity&#x60; for most recently active users first. | [optional] |

### Return type

[**List[User]**](User.md)

### Authorization

[oauth2](../README.md#oauth2)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details

| Status code | Description             | Response headers |
| ----------- | ----------------------- | ---------------- |
| **200**     | The Hub&#39;s user list | -                |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **patch_proxy**

> patch_proxy(patch_proxy_request)

Notify the Hub about a new proxy

Notifies the Hub of a new proxy to use.

### Example

- OAuth Authentication (oauth2):

```python
import jupyterhub_client
from jupyterhub_client.models.patch_proxy_request import PatchProxyRequest
from jupyterhub_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /hub/api
# See configuration.py for a list of all supported configuration parameters.
configuration = jupyterhub_client.Configuration(
    host = "/hub/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with jupyterhub_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = jupyterhub_client.DefaultApi(api_client)
    patch_proxy_request = jupyterhub_client.PatchProxyRequest() # PatchProxyRequest | Any values that have changed for the new proxy. All keys are optional.

    try:
        # Notify the Hub about a new proxy
        api_instance.patch_proxy(patch_proxy_request)
    except Exception as e:
        print("Exception when calling DefaultApi->patch_proxy: %s\n" % e)
```

### Parameters

| Name                    | Type                                          | Description                                                            | Notes |
| ----------------------- | --------------------------------------------- | ---------------------------------------------------------------------- | ----- |
| **patch_proxy_request** | [**PatchProxyRequest**](PatchProxyRequest.md) | Any values that have changed for the new proxy. All keys are optional. |

### Return type

void (empty response body)

### Authorization

[oauth2](../README.md#oauth2)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: Not defined

### HTTP response details

| Status code | Description | Response headers |
| ----------- | ----------- | ---------------- |
| **200**     | Success     | -                |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **patch_shares_server**

> Share patch_shares_server(owner, server_name, patch_shares_server_request)

Revoke shared access

Revoke shared access to a single server for a single user or group. If scopes are specified, only the specified scopes are revoked, allowing the target user or group to retain partial access. Revocation is idempotent - revoking a scope not held does not result in an error. The resulting Share model is returned if any scopes remain. (new in 5.0)

### Example

- OAuth Authentication (oauth2):

```python
import jupyterhub_client
from jupyterhub_client.models.patch_shares_server_request import PatchSharesServerRequest
from jupyterhub_client.models.share import Share
from jupyterhub_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /hub/api
# See configuration.py for a list of all supported configuration parameters.
configuration = jupyterhub_client.Configuration(
    host = "/hub/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with jupyterhub_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = jupyterhub_client.DefaultApi(api_client)
    owner = 'owner_example' # str | name of the user who owns the shared server
    server_name = 'server_name_example' # str | name of the shared server (empty string for default server, which means the URL ends with a trailing '/', e.g. `/username/`).
    patch_shares_server_request = jupyterhub_client.PatchSharesServerRequest() # PatchSharesServerRequest | The share modifications to be made, as a JSON dict.

    try:
        # Revoke shared access
        api_response = api_instance.patch_shares_server(owner, server_name, patch_shares_server_request)
        print("The response of DefaultApi->patch_shares_server:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->patch_shares_server: %s\n" % e)
```

### Parameters

| Name                            | Type                                                        | Description                                                                                                                                     | Notes |
| ------------------------------- | ----------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | ----- |
| **owner**                       | **str**                                                     | name of the user who owns the shared server                                                                                                     |
| **server_name**                 | **str**                                                     | name of the shared server (empty string for default server, which means the URL ends with a trailing &#39;/&#39;, e.g. &#x60;/username/&#x60;). |
| **patch_shares_server_request** | [**PatchSharesServerRequest**](PatchSharesServerRequest.md) | The share modifications to be made, as a JSON dict.                                                                                             |

### Return type

[**Share**](Share.md)

### Authorization

[oauth2](../README.md#oauth2)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details

| Status code | Description                                                            | Response headers |
| ----------- | ---------------------------------------------------------------------- | ---------------- |
| **200**     | The updated Share permissions. An empty dict if no permissions remain. | -                |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **patch_user**

> User patch_user(name, patch_user_request)

Modify a user

Change a user's name or admin status

### Example

- OAuth Authentication (oauth2):

```python
import jupyterhub_client
from jupyterhub_client.models.patch_user_request import PatchUserRequest
from jupyterhub_client.models.user import User
from jupyterhub_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /hub/api
# See configuration.py for a list of all supported configuration parameters.
configuration = jupyterhub_client.Configuration(
    host = "/hub/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with jupyterhub_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = jupyterhub_client.DefaultApi(api_client)
    name = 'name_example' # str | username
    patch_user_request = jupyterhub_client.PatchUserRequest() # PatchUserRequest | Updated user info. At least one key to be updated (name or admin) is required.

    try:
        # Modify a user
        api_response = api_instance.patch_user(name, patch_user_request)
        print("The response of DefaultApi->patch_user:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->patch_user: %s\n" % e)
```

### Parameters

| Name                   | Type                                        | Description                                                                    | Notes |
| ---------------------- | ------------------------------------------- | ------------------------------------------------------------------------------ | ----- |
| **name**               | **str**                                     | username                                                                       |
| **patch_user_request** | [**PatchUserRequest**](PatchUserRequest.md) | Updated user info. At least one key to be updated (name or admin) is required. |

### Return type

[**User**](User.md)

### Authorization

[oauth2](../README.md#oauth2)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details

| Status code | Description           | Response headers |
| ----------- | --------------------- | ---------------- |
| **200**     | The updated user info | -                |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **post_auth_token**

> PostAuthToken200Response post_auth_token(post_auth_token_request=post_auth_token_request)

Request a new API token

Request a new API token to use with the JupyterHub REST API. If not already authenticated, username and password can be sent in the JSON request body. Logging in via this method is only available when the active Authenticator accepts passwords (e.g. not OAuth).

### Example

- OAuth Authentication (oauth2):

```python
import jupyterhub_client
from jupyterhub_client.models.post_auth_token200_response import PostAuthToken200Response
from jupyterhub_client.models.post_auth_token_request import PostAuthTokenRequest
from jupyterhub_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /hub/api
# See configuration.py for a list of all supported configuration parameters.
configuration = jupyterhub_client.Configuration(
    host = "/hub/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with jupyterhub_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = jupyterhub_client.DefaultApi(api_client)
    post_auth_token_request = jupyterhub_client.PostAuthTokenRequest() # PostAuthTokenRequest |  (optional)

    try:
        # Request a new API token
        api_response = api_instance.post_auth_token(post_auth_token_request=post_auth_token_request)
        print("The response of DefaultApi->post_auth_token:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->post_auth_token: %s\n" % e)
```

### Parameters

| Name                        | Type                                                | Description | Notes      |
| --------------------------- | --------------------------------------------------- | ----------- | ---------- |
| **post_auth_token_request** | [**PostAuthTokenRequest**](PostAuthTokenRequest.md) |             | [optional] |

### Return type

[**PostAuthToken200Response**](PostAuthToken200Response.md)

### Authorization

[oauth2](../README.md#oauth2)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details

| Status code | Description                        | Response headers |
| ----------- | ---------------------------------- | ---------------- |
| **200**     | The new API token                  | -                |
| **403**     | The user can not be authenticated. | -                |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **post_group**

> Group post_group(name)

Create a group

### Example

- OAuth Authentication (oauth2):

```python
import jupyterhub_client
from jupyterhub_client.models.group import Group
from jupyterhub_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /hub/api
# See configuration.py for a list of all supported configuration parameters.
configuration = jupyterhub_client.Configuration(
    host = "/hub/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with jupyterhub_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = jupyterhub_client.DefaultApi(api_client)
    name = 'name_example' # str | group name

    try:
        # Create a group
        api_response = api_instance.post_group(name)
        print("The response of DefaultApi->post_group:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->post_group: %s\n" % e)
```

### Parameters

| Name     | Type    | Description | Notes |
| -------- | ------- | ----------- | ----- |
| **name** | **str** | group name  |

### Return type

[**Group**](Group.md)

### Authorization

[oauth2](../README.md#oauth2)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details

| Status code | Description                | Response headers |
| ----------- | -------------------------- | ---------------- |
| **201**     | The group has been created | -                |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **post_group_users**

> Group post_group_users(name, post_group_users_request)

Add users to a group

### Example

- OAuth Authentication (oauth2):

```python
import jupyterhub_client
from jupyterhub_client.models.group import Group
from jupyterhub_client.models.post_group_users_request import PostGroupUsersRequest
from jupyterhub_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /hub/api
# See configuration.py for a list of all supported configuration parameters.
configuration = jupyterhub_client.Configuration(
    host = "/hub/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with jupyterhub_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = jupyterhub_client.DefaultApi(api_client)
    name = 'name_example' # str | group name
    post_group_users_request = jupyterhub_client.PostGroupUsersRequest() # PostGroupUsersRequest | The users to add to the group

    try:
        # Add users to a group
        api_response = api_instance.post_group_users(name, post_group_users_request)
        print("The response of DefaultApi->post_group_users:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->post_group_users: %s\n" % e)
```

### Parameters

| Name                         | Type                                                  | Description                   | Notes |
| ---------------------------- | ----------------------------------------------------- | ----------------------------- | ----- |
| **name**                     | **str**                                               | group name                    |
| **post_group_users_request** | [**PostGroupUsersRequest**](PostGroupUsersRequest.md) | The users to add to the group |

### Return type

[**Group**](Group.md)

### Authorization

[oauth2](../README.md#oauth2)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details

| Status code | Description                            | Response headers |
| ----------- | -------------------------------------- | ---------------- |
| **200**     | The users have been added to the group | -                |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **post_oauth_token**

> PostOauthToken200Response post_oauth_token(client_id, client_secret, grant_type, code, redirect_uri)

Request an OAuth2 token

Request an OAuth2 token from an authorization code. This request completes the OAuth process.

### Example

- OAuth Authentication (oauth2):
- Bearer Authentication (token):

```python
import jupyterhub_client
from jupyterhub_client.models.post_oauth_token200_response import PostOauthToken200Response
from jupyterhub_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /hub/api
# See configuration.py for a list of all supported configuration parameters.
configuration = jupyterhub_client.Configuration(
    host = "/hub/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Configure Bearer authorization: token
configuration = jupyterhub_client.Configuration(
    access_token = os.environ["BEARER_TOKEN"]
)

# Enter a context with an instance of the API client
with jupyterhub_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = jupyterhub_client.DefaultApi(api_client)
    client_id = 'client_id_example' # str | The client id
    client_secret = 'client_secret_example' # str | The client secret
    grant_type = 'grant_type_example' # str | The grant type (always 'authorization_code')
    code = 'code_example' # str | The code provided by the authorization redirect
    redirect_uri = 'redirect_uri_example' # str | The redirect url

    try:
        # Request an OAuth2 token
        api_response = api_instance.post_oauth_token(client_id, client_secret, grant_type, code, redirect_uri)
        print("The response of DefaultApi->post_oauth_token:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->post_oauth_token: %s\n" % e)
```

### Parameters

| Name              | Type    | Description                                          | Notes |
| ----------------- | ------- | ---------------------------------------------------- | ----- |
| **client_id**     | **str** | The client id                                        |
| **client_secret** | **str** | The client secret                                    |
| **grant_type**    | **str** | The grant type (always &#39;authorization_code&#39;) |
| **code**          | **str** | The code provided by the authorization redirect      |
| **redirect_uri**  | **str** | The redirect url                                     |

### Return type

[**PostOauthToken200Response**](PostOauthToken200Response.md)

### Authorization

[oauth2](../README.md#oauth2), [token](../README.md#token)

### HTTP request headers

- **Content-Type**: application/x-www-form-urlencoded
- **Accept**: application/json

### HTTP response details

| Status code | Description                       | Response headers |
| ----------- | --------------------------------- | ---------------- |
| **200**     | JSON response including the token | -                |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **post_proxy**

> post_proxy()

Force the Hub to sync with the proxy

### Example

- OAuth Authentication (oauth2):

```python
import jupyterhub_client
from jupyterhub_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /hub/api
# See configuration.py for a list of all supported configuration parameters.
configuration = jupyterhub_client.Configuration(
    host = "/hub/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with jupyterhub_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = jupyterhub_client.DefaultApi(api_client)

    try:
        # Force the Hub to sync with the proxy
        api_instance.post_proxy()
    except Exception as e:
        print("Exception when calling DefaultApi->post_proxy: %s\n" % e)
```

### Parameters

This endpoint does not need any parameter.

### Return type

void (empty response body)

### Authorization

[oauth2](../README.md#oauth2)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: Not defined

### HTTP response details

| Status code | Description | Response headers |
| ----------- | ----------- | ---------------- |
| **200**     | Success     | -                |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **post_share_code**

> PostShareCode200Response post_share_code(owner, server_name, post_share_code_request)

Issue share code

Issue a share code, which can be exchanged for shared access to a single server (new in 5.0)

### Example

- OAuth Authentication (oauth2):

```python
import jupyterhub_client
from jupyterhub_client.models.post_share_code200_response import PostShareCode200Response
from jupyterhub_client.models.post_share_code_request import PostShareCodeRequest
from jupyterhub_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /hub/api
# See configuration.py for a list of all supported configuration parameters.
configuration = jupyterhub_client.Configuration(
    host = "/hub/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with jupyterhub_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = jupyterhub_client.DefaultApi(api_client)
    owner = 'owner_example' # str | name of the user who owns the shared server
    server_name = 'server_name_example' # str | name of the shared server (empty string for default server, which means the URL ends with a trailing '/', e.g. `/username/`).
    post_share_code_request = jupyterhub_client.PostShareCodeRequest() # PostShareCodeRequest | The new share code properties, as a JSON dict.

    try:
        # Issue share code
        api_response = api_instance.post_share_code(owner, server_name, post_share_code_request)
        print("The response of DefaultApi->post_share_code:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->post_share_code: %s\n" % e)
```

### Parameters

| Name                        | Type                                                | Description                                                                                                                                     | Notes |
| --------------------------- | --------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | ----- |
| **owner**                   | **str**                                             | name of the user who owns the shared server                                                                                                     |
| **server_name**             | **str**                                             | name of the shared server (empty string for default server, which means the URL ends with a trailing &#39;/&#39;, e.g. &#x60;/username/&#x60;). |
| **post_share_code_request** | [**PostShareCodeRequest**](PostShareCodeRequest.md) | The new share code properties, as a JSON dict.                                                                                                  |

### Return type

[**PostShareCode200Response**](PostShareCode200Response.md)

### Authorization

[oauth2](../README.md#oauth2)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details

| Status code | Description                                                                                                                                                                                                                                                                                    | Response headers |
| ----------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------- |
| **200**     | The Share code you just created. The code itself will be in the &#x60;code&#x60; field. The code is not stored by JupyterHub and cannot be retrieved a second time. &#x60;accept_url&#x60; will be the actual URL to share (it will look like &#x60;/hub/accept-share?code&#x3D;abc123&#x60;). | -                |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **post_shares_server**

> Share post_shares_server(owner, server_name, post_shares_server_request)

Grant shared access

Grant shared access to a single server (new in 5.0)

### Example

- OAuth Authentication (oauth2):

```python
import jupyterhub_client
from jupyterhub_client.models.post_shares_server_request import PostSharesServerRequest
from jupyterhub_client.models.share import Share
from jupyterhub_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /hub/api
# See configuration.py for a list of all supported configuration parameters.
configuration = jupyterhub_client.Configuration(
    host = "/hub/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with jupyterhub_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = jupyterhub_client.DefaultApi(api_client)
    owner = 'owner_example' # str | name of the user who owns the shared server
    server_name = 'server_name_example' # str | name of the shared server (empty string for default server, which means the URL ends with a trailing '/', e.g. `/username/`).
    post_shares_server_request = jupyterhub_client.PostSharesServerRequest() # PostSharesServerRequest | The new group properties, as a JSON dict.

    try:
        # Grant shared access
        api_response = api_instance.post_shares_server(owner, server_name, post_shares_server_request)
        print("The response of DefaultApi->post_shares_server:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->post_shares_server: %s\n" % e)
```

### Parameters

| Name                           | Type                                                      | Description                                                                                                                                     | Notes |
| ------------------------------ | --------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | ----- |
| **owner**                      | **str**                                                   | name of the user who owns the shared server                                                                                                     |
| **server_name**                | **str**                                                   | name of the shared server (empty string for default server, which means the URL ends with a trailing &#39;/&#39;, e.g. &#x60;/username/&#x60;). |
| **post_shares_server_request** | [**PostSharesServerRequest**](PostSharesServerRequest.md) | The new group properties, as a JSON dict.                                                                                                       |

### Return type

[**Share**](Share.md)

### Authorization

[oauth2](../README.md#oauth2)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details

| Status code | Description                   | Response headers |
| ----------- | ----------------------------- | ---------------- |
| **200**     | The updated Share permissions | -                |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **post_shutdown**

> post_shutdown(post_shutdown_request=post_shutdown_request)

Shutdown the Hub

### Example

- OAuth Authentication (oauth2):

```python
import jupyterhub_client
from jupyterhub_client.models.post_shutdown_request import PostShutdownRequest
from jupyterhub_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /hub/api
# See configuration.py for a list of all supported configuration parameters.
configuration = jupyterhub_client.Configuration(
    host = "/hub/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with jupyterhub_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = jupyterhub_client.DefaultApi(api_client)
    post_shutdown_request = jupyterhub_client.PostShutdownRequest() # PostShutdownRequest |  (optional)

    try:
        # Shutdown the Hub
        api_instance.post_shutdown(post_shutdown_request=post_shutdown_request)
    except Exception as e:
        print("Exception when calling DefaultApi->post_shutdown: %s\n" % e)
```

### Parameters

| Name                      | Type                                              | Description | Notes      |
| ------------------------- | ------------------------------------------------- | ----------- | ---------- |
| **post_shutdown_request** | [**PostShutdownRequest**](PostShutdownRequest.md) |             | [optional] |

### Return type

void (empty response body)

### Authorization

[oauth2](../README.md#oauth2)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: Not defined

### HTTP response details

| Status code | Description                           | Response headers |
| ----------- | ------------------------------------- | ---------------- |
| **202**     | Shutdown successful                   | -                |
| **400**     | Unexpected value for proxy or servers | -                |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **post_user**

> User post_user(name)

Create a single user

### Example

- OAuth Authentication (oauth2):

```python
import jupyterhub_client
from jupyterhub_client.models.user import User
from jupyterhub_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /hub/api
# See configuration.py for a list of all supported configuration parameters.
configuration = jupyterhub_client.Configuration(
    host = "/hub/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with jupyterhub_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = jupyterhub_client.DefaultApi(api_client)
    name = 'name_example' # str | username

    try:
        # Create a single user
        api_response = api_instance.post_user(name)
        print("The response of DefaultApi->post_user:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->post_user: %s\n" % e)
```

### Parameters

| Name     | Type    | Description | Notes |
| -------- | ------- | ----------- | ----- |
| **name** | **str** | username    |

### Return type

[**User**](User.md)

### Authorization

[oauth2](../README.md#oauth2)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details

| Status code | Description               | Response headers |
| ----------- | ------------------------- | ---------------- |
| **201**     | The user has been created | -                |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **post_user_activity**

> post_user_activity(name, post_user_activity_request=post_user_activity_request)

Notify Hub of activity for a given user

Notify the Hub of activity by the user, e.g. accessing a service or (more likely) actively using a server.

### Example

- OAuth Authentication (oauth2):

```python
import jupyterhub_client
from jupyterhub_client.models.post_user_activity_request import PostUserActivityRequest
from jupyterhub_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /hub/api
# See configuration.py for a list of all supported configuration parameters.
configuration = jupyterhub_client.Configuration(
    host = "/hub/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with jupyterhub_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = jupyterhub_client.DefaultApi(api_client)
    name = 'name_example' # str | username
    post_user_activity_request = jupyterhub_client.PostUserActivityRequest() # PostUserActivityRequest |  (optional)

    try:
        # Notify Hub of activity for a given user
        api_instance.post_user_activity(name, post_user_activity_request=post_user_activity_request)
    except Exception as e:
        print("Exception when calling DefaultApi->post_user_activity: %s\n" % e)
```

### Parameters

| Name                           | Type                                                      | Description | Notes      |
| ------------------------------ | --------------------------------------------------------- | ----------- | ---------- |
| **name**                       | **str**                                                   | username    |
| **post_user_activity_request** | [**PostUserActivityRequest**](PostUserActivityRequest.md) |             | [optional] |

### Return type

void (empty response body)

### Authorization

[oauth2](../README.md#oauth2)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: Not defined

### HTTP response details

| Status code | Description                        | Response headers |
| ----------- | ---------------------------------- | ---------------- |
| **200**     | Successfully updated activity      | -                |
| **401**     | Authentication/Authorization error | -                |
| **404**     | No such user                       | -                |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **post_user_server**

> post_user_server(name, body=body)

Start a user's single-user notebook server

### Example

- OAuth Authentication (oauth2):

```python
import jupyterhub_client
from jupyterhub_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /hub/api
# See configuration.py for a list of all supported configuration parameters.
configuration = jupyterhub_client.Configuration(
    host = "/hub/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with jupyterhub_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = jupyterhub_client.DefaultApi(api_client)
    name = 'name_example' # str | username
    body = None # object | Spawn options can be passed as a JSON body when spawning via the API instead of spawn form. The structure of the options will depend on the Spawner's configuration. The body itself will be available as `user_options` for the Spawner.  (optional)

    try:
        # Start a user's single-user notebook server
        api_instance.post_user_server(name, body=body)
    except Exception as e:
        print("Exception when calling DefaultApi->post_user_server: %s\n" % e)
```

### Parameters

| Name     | Type       | Description                                                                                                                                                                                                                                             | Notes      |
| -------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| **name** | **str**    | username                                                                                                                                                                                                                                                |
| **body** | **object** | Spawn options can be passed as a JSON body when spawning via the API instead of spawn form. The structure of the options will depend on the Spawner&#39;s configuration. The body itself will be available as &#x60;user_options&#x60; for the Spawner. | [optional] |

### Return type

void (empty response body)

### Authorization

[oauth2](../README.md#oauth2)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: Not defined

### HTTP response details

| Status code | Description                                                                | Response headers |
| ----------- | -------------------------------------------------------------------------- | ---------------- |
| **201**     | The user&#39;s notebook server has started                                 | -                |
| **202**     | The user&#39;s notebook server has not yet started, but has been requested | -                |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **post_user_server_name**

> post_user_server_name(name, server_name, body=body)

Start a user's named server

### Example

- OAuth Authentication (oauth2):

```python
import jupyterhub_client
from jupyterhub_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /hub/api
# See configuration.py for a list of all supported configuration parameters.
configuration = jupyterhub_client.Configuration(
    host = "/hub/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with jupyterhub_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = jupyterhub_client.DefaultApi(api_client)
    name = 'name_example' # str | username
    server_name = 'server_name_example' # str | name given to a named-server (empty string for default server).  Note that depending on your JupyterHub infrastructure there are limitations to `server_name`. Default spawner with K8s pod will not allow Jupyter Notebooks to be spawned with a name that contains more than 253 characters (keep in hexaind that the pod will be spawned with extra characters to identify the user and hub).
    body = None # object | Spawn options can be passed as a JSON body when spawning via the API instead of spawn form. The structure of the options will depend on the Spawner's configuration.  (optional)

    try:
        # Start a user's named server
        api_instance.post_user_server_name(name, server_name, body=body)
    except Exception as e:
        print("Exception when calling DefaultApi->post_user_server_name: %s\n" % e)
```

### Parameters

| Name            | Type       | Description                                                                                                                                                                                                                                                                                                                                                                                               | Notes      |
| --------------- | ---------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| **name**        | **str**    | username                                                                                                                                                                                                                                                                                                                                                                                                  |
| **server_name** | **str**    | name given to a named-server (empty string for default server). Note that depending on your JupyterHub infrastructure there are limitations to &#x60;server_name&#x60;. Default spawner with K8s pod will not allow Jupyter Notebooks to be spawned with a name that contains more than 253 characters (keep in hexaind that the pod will be spawned with extra characters to identify the user and hub). |
| **body**        | **object** | Spawn options can be passed as a JSON body when spawning via the API instead of spawn form. The structure of the options will depend on the Spawner&#39;s configuration.                                                                                                                                                                                                                                  | [optional] |

### Return type

void (empty response body)

### Authorization

[oauth2](../README.md#oauth2)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: Not defined

### HTTP response details

| Status code | Description                                                                      | Response headers |
| ----------- | -------------------------------------------------------------------------------- | ---------------- |
| **201**     | The user&#39;s notebook named-server has started                                 | -                |
| **202**     | The user&#39;s notebook named-server has not yet started, but has been requested | -                |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **post_user_tokens**

> NewToken post_user_tokens(name, post_user_tokens_request=post_user_tokens_request)

Create a new token for the user

Creates a new token owned by the user. Permissions can be limited by specifying a list of `scopes` in the JSON request body (starting in JupyterHub 3.0; previously, permissions could be specified as `roles`, which is deprecated in 3.0).

### Example

- OAuth Authentication (oauth2):

```python
import jupyterhub_client
from jupyterhub_client.models.new_token import NewToken
from jupyterhub_client.models.post_user_tokens_request import PostUserTokensRequest
from jupyterhub_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /hub/api
# See configuration.py for a list of all supported configuration parameters.
configuration = jupyterhub_client.Configuration(
    host = "/hub/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with jupyterhub_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = jupyterhub_client.DefaultApi(api_client)
    name = 'name_example' # str | username
    post_user_tokens_request = jupyterhub_client.PostUserTokensRequest() # PostUserTokensRequest |  (optional)

    try:
        # Create a new token for the user
        api_response = api_instance.post_user_tokens(name, post_user_tokens_request=post_user_tokens_request)
        print("The response of DefaultApi->post_user_tokens:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->post_user_tokens: %s\n" % e)
```

### Parameters

| Name                         | Type                                                  | Description | Notes      |
| ---------------------------- | ----------------------------------------------------- | ----------- | ---------- |
| **name**                     | **str**                                               | username    |
| **post_user_tokens_request** | [**PostUserTokensRequest**](PostUserTokensRequest.md) |             | [optional] |

### Return type

[**NewToken**](NewToken.md)

### Authorization

[oauth2](../README.md#oauth2)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details

| Status code | Description                       | Response headers |
| ----------- | --------------------------------- | ---------------- |
| **201**     | The newly created token           | -                |
| **400**     | Body must be a JSON dict or empty | -                |
| **403**     | Requested role does not exist     | -                |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **post_users**

> List[User] post_users(post_users_request)

Create multiple users

### Example

- OAuth Authentication (oauth2):

```python
import jupyterhub_client
from jupyterhub_client.models.post_users_request import PostUsersRequest
from jupyterhub_client.models.user import User
from jupyterhub_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /hub/api
# See configuration.py for a list of all supported configuration parameters.
configuration = jupyterhub_client.Configuration(
    host = "/hub/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with jupyterhub_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = jupyterhub_client.DefaultApi(api_client)
    post_users_request = jupyterhub_client.PostUsersRequest() # PostUsersRequest |

    try:
        # Create multiple users
        api_response = api_instance.post_users(post_users_request)
        print("The response of DefaultApi->post_users:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->post_users: %s\n" % e)
```

### Parameters

| Name                   | Type                                        | Description | Notes |
| ---------------------- | ------------------------------------------- | ----------- | ----- |
| **post_users_request** | [**PostUsersRequest**](PostUsersRequest.md) |             |

### Return type

[**List[User]**](User.md)

### Authorization

[oauth2](../README.md#oauth2)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details

| Status code | Description                 | Response headers |
| ----------- | --------------------------- | ---------------- |
| **201**     | The users have been created | -                |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **put_group_properties**

> Group put_group_properties(name, body)

Set group properties

Set properties on a group (new in 3.2)

### Example

- OAuth Authentication (oauth2):

```python
import jupyterhub_client
from jupyterhub_client.models.group import Group
from jupyterhub_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /hub/api
# See configuration.py for a list of all supported configuration parameters.
configuration = jupyterhub_client.Configuration(
    host = "/hub/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with jupyterhub_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = jupyterhub_client.DefaultApi(api_client)
    name = 'name_example' # str | group name
    body = None # object | The new group properties, as a JSON dict.

    try:
        # Set group properties
        api_response = api_instance.put_group_properties(name, body)
        print("The response of DefaultApi->put_group_properties:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->put_group_properties: %s\n" % e)
```

### Parameters

| Name     | Type       | Description                               | Notes |
| -------- | ---------- | ----------------------------------------- | ----- |
| **name** | **str**    | group name                                |
| **body** | **object** | The new group properties, as a JSON dict. |

### Return type

[**Group**](Group.md)

### Authorization

[oauth2](../README.md#oauth2)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details

| Status code | Description                                                            | Response headers |
| ----------- | ---------------------------------------------------------------------- | ---------------- |
| **200**     | The properties have been updated. The updated group model is returned. | -                |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)
