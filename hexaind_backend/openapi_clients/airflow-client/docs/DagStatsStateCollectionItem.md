# DagStatsStateCollectionItem

DagStatsState entry collection item.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**state** | **str** | The DAG state. | [optional] 
**count** | **int** | The DAG state count. | [optional] 

## Example

```python
from airflow_client.models.dag_stats_state_collection_item import DagStatsStateCollectionItem

# TODO update the JSON string below
json = "{}"
# create an instance of DagStatsStateCollectionItem from a JSON string
dag_stats_state_collection_item_instance = DagStatsStateCollectionItem.from_json(json)
# print the JSON string representation of the object
print(DagStatsStateCollectionItem.to_json())

# convert the object into a dict
dag_stats_state_collection_item_dict = dag_stats_state_collection_item_instance.to_dict()
# create an instance of DagStatsStateCollectionItem from a dict
dag_stats_state_collection_item_from_dict = DagStatsStateCollectionItem.from_dict(dag_stats_state_collection_item_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


