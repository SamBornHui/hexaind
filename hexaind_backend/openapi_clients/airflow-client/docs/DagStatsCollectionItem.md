# DagStatsCollectionItem

DagStats entry collection item.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**dag_id** | **str** | The DAG ID. | [optional] 
**stats** | [**List[DagStatsStateCollectionItem]**](DagStatsStateCollectionItem.md) |  | [optional] 

## Example

```python
from airflow_client.models.dag_stats_collection_item import DagStatsCollectionItem

# TODO update the JSON string below
json = "{}"
# create an instance of DagStatsCollectionItem from a JSON string
dag_stats_collection_item_instance = DagStatsCollectionItem.from_json(json)
# print the JSON string representation of the object
print(DagStatsCollectionItem.to_json())

# convert the object into a dict
dag_stats_collection_item_dict = dag_stats_collection_item_instance.to_dict()
# create an instance of DagStatsCollectionItem from a dict
dag_stats_collection_item_from_dict = DagStatsCollectionItem.from_dict(dag_stats_collection_item_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


