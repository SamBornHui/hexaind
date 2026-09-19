# CreateDatasetEvent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**dataset_uri** | **str** | The URI of the dataset | 
**extra** | **object** | The dataset event extra | [optional] 

## Example

```python
from airflow_client.models.create_dataset_event import CreateDatasetEvent

# TODO update the JSON string below
json = "{}"
# create an instance of CreateDatasetEvent from a JSON string
create_dataset_event_instance = CreateDatasetEvent.from_json(json)
# print the JSON string representation of the object
print(CreateDatasetEvent.to_json())

# convert the object into a dict
create_dataset_event_dict = create_dataset_event_instance.to_dict()
# create an instance of CreateDatasetEvent from a dict
create_dataset_event_from_dict = CreateDatasetEvent.from_dict(create_dataset_event_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


