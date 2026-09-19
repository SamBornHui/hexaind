# DagStatsCollectionSchema

Collection of Dag statistics. 

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**total_entries** | **int** | Count of total objects in the current result set before pagination parameters (limit, offset) are applied.  | [optional] 
**dags** | [**List[DagStatsCollectionItem]**](DagStatsCollectionItem.md) |  | [optional] 

## Example

```python
from airflow_client.models.dag_stats_collection_schema import DagStatsCollectionSchema

# TODO update the JSON string below
json = "{}"
# create an instance of DagStatsCollectionSchema from a JSON string
dag_stats_collection_schema_instance = DagStatsCollectionSchema.from_json(json)
# print the JSON string representation of the object
print(DagStatsCollectionSchema.to_json())

# convert the object into a dict
dag_stats_collection_schema_dict = dag_stats_collection_schema_instance.to_dict()
# create an instance of DagStatsCollectionSchema from a dict
dag_stats_collection_schema_from_dict = DagStatsCollectionSchema.from_dict(dag_stats_collection_schema_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


