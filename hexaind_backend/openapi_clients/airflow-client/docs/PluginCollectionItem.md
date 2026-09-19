# PluginCollectionItem

A plugin Item.  *New in version 2.1.0* 

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** | The name of the plugin | [optional] 
**hooks** | **List[Optional[str]]** | The plugin hooks | [optional] 
**executors** | **List[Optional[str]]** | The plugin executors | [optional] 
**macros** | **List[Optional[str]]** | The plugin macros | [optional] 
**flask_blueprints** | **List[Optional[str]]** | The flask blueprints | [optional] 
**appbuilder_views** | **List[Optional[object]]** | The appuilder views | [optional] 
**appbuilder_menu_items** | **List[Optional[object]]** | The Flask Appbuilder menu items | [optional] 
**global_operator_extra_links** | **List[Optional[str]]** | The global operator extra links | [optional] 
**operator_extra_links** | **List[Optional[str]]** | Operator extra links | [optional] 
**source** | **str** | The plugin source | [optional] 
**ti_deps** | **List[str]** | The plugin task instance dependencies | [optional] 
**listeners** | **List[str]** | The plugin listeners | [optional] 
**timetables** | **List[str]** | The plugin timetables | [optional] 

## Example

```python
from airflow_client.models.plugin_collection_item import PluginCollectionItem

# TODO update the JSON string below
json = "{}"
# create an instance of PluginCollectionItem from a JSON string
plugin_collection_item_instance = PluginCollectionItem.from_json(json)
# print the JSON string representation of the object
print(PluginCollectionItem.to_json())

# convert the object into a dict
plugin_collection_item_dict = plugin_collection_item_instance.to_dict()
# create an instance of PluginCollectionItem from a dict
plugin_collection_item_from_dict = PluginCollectionItem.from_dict(plugin_collection_item_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


