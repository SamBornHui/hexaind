from pathlib import Path

import pandas as pd
import pytest
import pytest_mock
from bson import ObjectId
from mongomock import MongoClient

from app.core.schemas.action_result import ActionResultType
from app.core.services.action.schemas import Action
from app.core.services.action_handler.handler import ActionHandler
from app.services.workflows.designer.schemas import Widget
from app.services.workflows.runner.schemas import Run
from app.utils.dataset_utils import generate_dataset_object
from app.workers.custom_code.worker import task_custom


# ToDo : move these methods to common place or create jsons and use
def get_csv_action(result_ids):
    return {
        "version": "1.0",
        "run_id": "65d200cf250faac3b28129d7",
        "is_cycle": False,
        "action_config": {
            "urn": "1",
            "name": "Widget-CSV_FILE-oMcL",
            "description": "DefaultWidgetDescription",
            "type": "DATA_COPY",
            "config": {
                "version": "1.0",
                "source": {
                    "type": "LOCAL",
                    "configuration": {
                        "version": "1.0",
                        "dataset_id": "65d1b7ae4ac81e6849610523"
                    }
                },
                "sink": {
                    "dataset_name": "csv_dataset",
                    "dataset_description": "data from csv"
                }
            },
            "state": "IDLE",
            "on_success": [
                "3"
            ],
            "on_failure": [],
            "on_complete": [],
            "inputs": [],
            "outputs": [
                {
                    "urn": "1",
                    "map_to_argument": "",
                    "name": "dataset1"
                }
            ],
            "use_gpu": False,
            "retry_interval_in_sec": 30,
            "retry_count": 30,
            "client_tags": {}
        },
        "depends_on": [],
        "status": "SUCCEEDED",
        "result_ids": result_ids,
        "custom_run_state": None
    }


def get_custom_code_action(result_ids):
    return {
        "version": "1.0",
        "run_id": "65d1ff7179e1b4d0b4590616",
        "is_cycle": False,
        "action_config": {
            "urn": "3",
            "name": "append-v1-1",
            "description": "append recipe",
            "type": "CUSTOM_CODE",
            "config": {
                "version": "1.0",
                "module_id": "65d1b7fe27aafedb3b7cb1e6",
                "function_inputs": [
                    {
                        "type": "<class 'pandas.core.frame.DataFrame'>",
                        "arg_name": "df1"
                    },
                    {
                        "type": "<class 'pandas.core.frame.DataFrame'>",
                        "arg_name": "df2"
                    }
                ],
                "widget_parameters": [
                    {
                        "type": "<class 'str'>",
                        "arg_name": "column_names",
                        "value": {"type": "STRING", "result": {"string_value": "ID"}},
                        "is_mandatory": True
                    },
                    {
                        "type": "<class 'str'>",
                        "arg_name": "how",
                        "value": {"type": "STRING", "result": {"string_value": "inner"}},
                        "is_mandatory": True
                    }
                ],
                "function_outputs": [
                    {
                        "type": "<class 'pandas.core.frame.DataFrame'>",
                        "arg_name": "ignored"
                    }
                ]
            },
            "state": "IDLE",
            "on_success": [],
            "on_failure": [],
            "on_complete": [],
            "inputs": [
                {
                    "urn": "1",
                    "map_to_argument": "df1",
                    "type": None,
                    "name": "dataset1"
                },
                {
                    "urn": "2",
                    "map_to_argument": "df2",
                    "type": None,
                    "name": "dataset2"
                }
            ],
            "outputs": [
                {
                    "urn": "3",
                    "map_to_argument": "",
                    "type": "DATASET",
                    "name": "joined_dataset"
                }
            ],
            "use_gpu": False,
            "retry_interval_in_sec": 0,
            "retry_count": 0,
            "client_tags": {}
        },
        "depends_on": [
            "1",
            "2"
        ],
        "status": "FAILED",
        "result_ids": result_ids,
        "custom_run_state": None
    }


def get_sample_run():
    return {
        "name": "",
        "description": "",
        "run_source": "WORKFLOW",
        "run_state": "START",
        "run_status": "FAILED",
        "actions": [
            {
                "urn": "1",
                "action_id": "65d211097128a848e256a9a2"
            },
            {
                "urn": "3",
                "action_id": "65d211097128a848e256a9a4"
            }
        ],
        "owner_id": "",
        "owner_name": "",
        "created_at": "2024-02-18T19:45:37.913Z",
        "last_modified_by_id": "",
        "last_modified_at": "2024-02-18T19:45:38.251Z",
        "project_id": "1",
        "site_id": "1",
        "workflow_id": "65d1fcd05ae68ab512d06efc",
        "version": "1.0"
    }


def get_sample_widget(sample_dataset_id):
    return {
        "urn": "3",
        "name": "append-v1-1",
        "description": "append recipe",
        "type": "CUSTOM_CODE",
        "config": {
            "version": "1.0",
            "module_id": "65d852d4f97c867ed1c08986",
            "function_inputs": [
                {
                    "type": "<class 'pandas.core.frame.DataFrame'>",
                    "arg_name": "df1"
                }
            ],
            "widget_parameters": [
                {
                    "type": "<class 'pandas.core.frame.DataFrame'>",
                    "arg_name": "df2",
                    "is_mandatory": False,
                    "default_value": {
                        "type": "DATASET",
                        "result": {
                            "dataset_id": sample_dataset_id
                        }
                    }
                },
                {
                    "type": "<class 'str'>",
                    "arg_name": "column_names",
                    "is_mandatory": False,
                    "default_value": {
                        "type": "STRING",
                        "result": {
                            "string_value": "ID"
                        }
                    }
                }
            ],
            "function_outputs": [
                {
                    "type": "<class 'pandas.core.frame.DataFrame'>",
                    "arg_name": "Output1"
                },
                {
                    "type": "<class 'pandas.core.frame.DataFrame'>",
                    "arg_name": "Output2"
                },
                {
                    "type": "<class 'str'>",
                    "arg_name": "Output3"
                }
            ]
        },
        "state": "IDLE",
        "on_success": [],
        "on_failure": [],
        "on_complete": [],
        "inputs": [
            {
                "urn": "1",
                "map_to_argument": "df1",
                "name": "dataset1"
            }
        ],
        "outputs": [
            {
                "urn": "3",
                "map_to_argument": "Output1",
                "type": "DATASET",
                "name": "output_1"
            },
            {
                "urn": "3",
                "map_to_argument": "Output2",
                "type": "DATASET",
                "name": "output_2"
            },
            {
                "urn": "3",
                "map_to_argument": "Output3",
                "type": "STRING",
                "name": "output_3"
            }
        ],
        "use_gpu": False,
        "retry_interval_in_sec": 0,
        "retry_count": 0,
        "client_tags": {}
    }


def get_tabular_action_results(dataset_id, name):
    return {
        "type": 'DATASET',
        "output_name": name,
        "result": {
            "dataset_id": dataset_id
        }
    }


def get_string_action_results(value):
    return {
        "type": 'STRING',
        "result": {
            "string_value": value
        }
    }


def true_if_instance_is_mongo_client(obj, cls):
    return type(obj) == MongoClient


@pytest.mark.fixme
def test_task_custom(mocker):
    # mocks and required db inserts
    mocked_sync_client = MongoClient()
    penguin_csv_file_path = str(Path(__file__).parent.parent.parent / "resources/penguin.csv")
    dataset1 = generate_dataset_object(penguin_csv_file_path)
    dataset_res = mocked_sync_client.Hexaind.datasets.insert_one(dataset1.model_dump())
    dataset_id = str(dataset_res.inserted_id)
    tabular_action_result = get_tabular_action_results(dataset_id,"dataset1")
    tabular_res1 = mocked_sync_client.Hexaind.action_results.insert_one(tabular_action_result)
    string_action_result = get_string_action_results("how")
    mocked_sync_client.Hexaind.action_results.insert_one(string_action_result)
    mock_run_record = Run(**get_sample_run())
    mock_run = mocked_sync_client.Hexaind.runs.insert_one(mock_run_record.model_dump())
    run_id = str(mock_run.inserted_id)
    mock_widget = Widget(**get_sample_widget(dataset_id))
    mock_action_custom_code = Action(**get_custom_code_action([]))
    mock_action_csv = Action(**get_csv_action([str(tabular_res1.inserted_id)]))
    mock_action_custom_code.run_id = run_id
    mock_action_csv.run_id = run_id
    custom_code_action = mocked_sync_client.Hexaind.actions.insert_one(mock_action_custom_code.model_dump())
    csv_action = mocked_sync_client.Hexaind.actions.insert_one(mock_action_csv.model_dump())
    mocker.patch('app.core.services.action_handler.handler.get_db_sync', return_value=mocked_sync_client)
    mocker.patch("app.core.dao.dao_base.isinstance", side_effect=true_if_instance_is_mongo_client)
    new_actions = [
        {"urn": "1", "action_id": str(csv_action.inserted_id)},
        {"urn": "2", "action_id": str(custom_code_action.inserted_id)}
    ]
    filter_query = {"workflow_id": mock_run_record.workflow_id}
    update_operation = {
        "$set": {
            "actions": new_actions
        }
    }
    mocked_sync_client.Hexaind.runs.update_one(filter_query, update_operation)
    mock_action_handler = ActionHandler(str(custom_code_action.inserted_id))
    action_id = custom_code_action.inserted_id
    mocked_cwm = mocker.patch('app.workers.custom_code.worker.common_widget_manager')
    mocked_cwm.return_value.__enter__.return_value = (
        mock_action_handler,
        mock_run_record,
        mock_widget
    )
    mocker.patch("app.workers.custom_code.worker.ModuleService.run_module",
                 return_value=[pd.read_csv(penguin_csv_file_path), pd.read_csv(penguin_csv_file_path), "Hello"])

    # actual test run
    task_custom(action_id)

    # assertions
    action_after_custom_code_is_run = mocked_sync_client.Hexaind.actions.find_one({"_id": ObjectId(action_id)})
    assert len(action_after_custom_code_is_run["result_ids"]) == 3

    for i, action_id in enumerate(action_after_custom_code_is_run["result_ids"]):
        action_result = mocked_sync_client.Hexaind.action_results.find_one({"_id": ObjectId(action_id)})
        if i < 2:
            assert action_result["type"] == ActionResultType.DATASET
            assert action_result["result"]["dataset_id"] is not None
        else:
            assert action_result["type"] == ActionResultType.STRING
            assert action_result["result"]["string_value"] == "Hello"
