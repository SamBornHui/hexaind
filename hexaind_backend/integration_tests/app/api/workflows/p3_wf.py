p3_wf = {
    "widgets": [
        {
            "urn": "0190bfa7-6a08-70e0-b811-85874680f473",
            "name": "Widget-CSV_FILE-g4Bg",
            "description": "DefaultWidgetDescription",
            "type": "DATA_COPY",
            "config": {
                "version": "1.0",
                "widget_type": "DATA_COPY",
                "source": {
                    "type": "LOCAL",
                    "configuration": {
                        "version": "1.0",
                        "dataset_id": "6627f36ec5e3c6479ef15651"
                    }
                },
                "sink": {
                    "dataset_name": "csv_dataset",
                    "dataset_description": "csv_dataset_description"
                }
            },
            "state": "IDLE",
            "on_success": [
                "0190bfa7-6a08-7cb7-92a9-afd2ec45db43"
            ],
            "on_failure": [],
            "on_complete": [],
            "inputs": [],
            "outputs": [
                {
                    "urn": "0190bfa7-6a08-70e0-b811-85874680f473",
                    "map_to_argument": "",
                    "type": "DATASET",
                    "name": "P1&P3-Demo_Widget-CSV_FILE-g4Bg_Tabular"
                }
            ],
            "use_gpu": False,
            "retry_interval_in_sec": 30,
            "retry_count": 30,
            "client_tags": {
                "PositionX": 220,
                "PositionY": 140,
                "Width": 90,
                "Height": 90,
                "Color": "#1A7A7F",
                "ClientType": "CSV_FILE"
            }
        },
        {
            "urn": "0190bfa7-6a08-7268-bb0e-418d13873776",
            "name": "Widget-SAVE-Qsea",
            "description": "DefaultWidgetDescription",
            "type": "SAVE",
            "config": {
                "version": "1.0",
                "widget_type": "SAVE",
                "datasetConfig": [
                    {
                        "dataset_name": "P1&P3-Demo_Widget-MOBO-Wblp_Tabular",
                        "destination_type": "HEXAIND_PLATFORM",
                        "destination_config": {
                            "file_Format": "CSV",
                            "save_options": "SAVE_AS",
                            "save_option_config": {
                                "file_name": "P3_results"
                            },
                            "destination_folder_path": ""
                        },
                        "doNotSaveFlag": False
                    }
                ]
            },
            "state": "IDLE",
            "on_success": [],
            "on_failure": [],
            "on_complete": [],
            "inputs": [
                {
                    "urn": "0190bfa7-6a08-7cb7-b89f-c50c84ca77ef",
                    "map_to_argument": "",
                    "type": "DATASET",
                    "name": "P1&P3-Demo_Widget-MOBO-Wblp_Tabular"
                }
            ],
            "outputs": [],
            "use_gpu": False,
            "retry_interval_in_sec": 30,
            "retry_count": 30,
            "client_tags": {
                "PositionX": 800,
                "PositionY": 140,
                "Width": 90,
                "Height": 90,
                "Color": "#1A7A7F",
                "ClientType": "SAVE"
            }
        },
        {
            "urn": "0190bfa7-6a08-7cb7-92a9-afd2ec45db43",
            "name": "Widget-LOOP_START-O3wF",
            "description": "DefaultWidgetDescription",
            "type": "LOOP_START",
            "config": {
                "version": "1.0",
                "widget_type": "LOOP_START",
                "loop_start_config": {
                    "xyz": 1,
                    "abc": 1
                }
            },
            "state": "IDLE",
            "on_success": [
                "0190bfa7-6a08-7cb7-b89f-c50c84ca77ef"
            ],
            "on_failure": [],
            "on_complete": [],
            "inputs": [
                {
                    "urn": "0190bfa7-6a09-73bc-8c58-2beab50a2ce3",
                    "map_to_argument": "",
                    "type": "DATASET",
                    "name": "P1&P3-Demo_Widget-RESCALE-1IfK_Tabular"
                }
            ],
            "outputs": [
                {
                    "urn": "0190bfa7-6a08-70e0-b811-85874680f473",
                    "map_to_argument": "",
                    "type": "DATASET",
                    "name": "P1&P3-Demo_Widget-CSV_FILE-g4Bg_Tabular"
                },
                {
                    "urn": "0190bfa7-6a09-73bc-8c58-2beab50a2ce3",
                    "map_to_argument": "",
                    "type": "DATASET",
                    "name": "P1&P3-Demo_Widget-RESCALE-1IfK_Tabular"
                }
            ],
            "use_gpu": False,
            "retry_interval_in_sec": 30,
            "retry_count": 30,
            "client_tags": {
                "PositionX": 380,
                "PositionY": 140,
                "Width": 90,
                "Height": 90,
                "Color": "#1A7A7F",
                "ClientType": "LOOP_START"
            }
        },
        {
            "urn": "0190bfa7-6a08-7f99-b973-8e29262c85d2",
            "name": "Widget-LOOP_END-DqLh",
            "description": "DefaultWidgetDescription",
            "type": "LOOP_END",
            "config": {
                "version": "1.0",
                "widget_type": "LOOP_END",
                "termination_criteria": "ON_LOOP_COUNT",
                "loop_end_config": {
                    "loop_count": 2
                },
                "on_loop": [
                    "0190bfa7-6a09-73bc-8c58-2beab50a2ce3"
                ],
                "on_termination": [
                    "0190bfa7-6a08-7268-bb0e-418d13873776"
                ]
            },
            "state": "IDLE",
            "on_success": [
                "0190bfa7-6a08-7268-bb0e-418d13873776",
                "0190bfa7-6a09-73bc-8c58-2beab50a2ce3"
            ],
            "on_failure": [],
            "on_complete": [],
            "inputs": [
                {
                    "urn": "0190bfa7-6a08-7cb7-b89f-c50c84ca77ef",
                    "map_to_argument": "",
                    "type": "DATASET",
                    "name": "P1&P3-Demo_Widget-MOBO-Wblp_Tabular"
                }
            ],
            "outputs": [
                {
                    "urn": "0190bfa7-6a08-7cb7-b89f-c50c84ca77ef",
                    "map_to_argument": "",
                    "type": "DATASET",
                    "name": "P1&P3-Demo_Widget-MOBO-Wblp_Tabular"
                }
            ],
            "use_gpu": False,
            "retry_interval_in_sec": 30,
            "retry_count": 30,
            "client_tags": {
                "PositionX": 680,
                "PositionY": 140,
                "Width": 90,
                "Height": 90,
                "Color": "#1A7A7F",
                "ClientType": "LOOP_END"
            }
        },
        {
            "urn": "0190bfa7-6a08-7cb7-b89f-c50c84ca77ef",
            "name": "Widget-MOBO-Wblp",
            "description": "DefaultWidgetDescription",
            "type": "MOBO",
            "config": {
                "version": "0.1",
                "widget_type": "MOBO",
                "experiment_type": "OPTIMIZATION",
                "features_detail": [
                    {
                        "name": "Fail",
                        "dataType": "Numerical",
                        "selected": False,
                        "input": False,
                        "output": False
                    },
                    {
                        "name": "t_0",
                        "dataType": "Numerical",
                        "selected": True,
                        "input": True,
                        "output": False
                    },
                    {
                        "name": "t_1",
                        "dataType": "Numerical",
                        "selected": True,
                        "input": True,
                        "output": False
                    },
                    {
                        "name": "t_2",
                        "dataType": "Numerical",
                        "selected": True,
                        "input": True,
                        "output": False
                    },
                    {
                        "name": "t_3",
                        "dataType": "Numerical",
                        "selected": True,
                        "input": True,
                        "output": False
                    },
                    {
                        "name": "t_4",
                        "dataType": "Numerical",
                        "selected": True,
                        "input": True,
                        "output": False
                    },
                    {
                        "name": "t_5",
                        "dataType": "Numerical",
                        "selected": True,
                        "input": True,
                        "output": False
                    },
                    {
                        "name": "t_6",
                        "dataType": "Numerical",
                        "selected": True,
                        "input": True,
                        "output": False
                    },
                    {
                        "name": "t_7",
                        "dataType": "Numerical",
                        "selected": True,
                        "input": True,
                        "output": False
                    },
                    {
                        "name": "t_8",
                        "dataType": "Numerical",
                        "selected": True,
                        "input": True,
                        "output": False
                    },
                    {
                        "name": "t_9",
                        "dataType": "Numerical",
                        "selected": True,
                        "input": True,
                        "output": False
                    },
                    {
                        "name": "r_1",
                        "dataType": "Numerical",
                        "selected": True,
                        "input": True,
                        "output": False
                    },
                    {
                        "name": "r_2",
                        "dataType": "Numerical",
                        "selected": True,
                        "input": True,
                        "output": False
                    },
                    {
                        "name": "r_3",
                        "dataType": "Numerical",
                        "selected": True,
                        "input": True,
                        "output": False
                    },
                    {
                        "name": "r_4",
                        "dataType": "Numerical",
                        "selected": True,
                        "input": True,
                        "output": False
                    },
                    {
                        "name": "r_5",
                        "dataType": "Numerical",
                        "selected": True,
                        "input": True,
                        "output": False
                    },
                    {
                        "name": "r_6",
                        "dataType": "Numerical",
                        "selected": True,
                        "input": True,
                        "output": False
                    },
                    {
                        "name": "r_7",
                        "dataType": "Numerical",
                        "selected": True,
                        "input": True,
                        "output": False
                    },
                    {
                        "name": "r_8",
                        "dataType": "Numerical",
                        "selected": True,
                        "input": True,
                        "output": False
                    },
                    {
                        "name": "r_9",
                        "dataType": "Numerical",
                        "selected": True,
                        "input": True,
                        "output": False
                    },
                    {
                        "name": "r_10",
                        "dataType": "Numerical",
                        "selected": True,
                        "input": True,
                        "output": False
                    },
                    {
                        "name": "buckle_pressure",
                        "dataType": "Numerical",
                        "selected": True,
                        "input": False,
                        "output": True
                    },
                    {
                        "name": "Weight",
                        "dataType": "Numerical",
                        "selected": True,
                        "input": False,
                        "output": True
                    }
                ],
                "input_variables": [
                    "t_0",
                    "t_1",
                    "t_2",
                    "t_3",
                    "t_4",
                    "t_5",
                    "t_6",
                    "t_7",
                    "t_8",
                    "t_9",
                    "r_1",
                    "r_2",
                    "r_3",
                    "r_4",
                    "r_5",
                    "r_6",
                    "r_7",
                    "r_8",
                    "r_9",
                    "r_10"
                ],
                "input_variables_constraints": [
                    [
                        39.3579977835738,
                        51.574678234082
                    ],
                    [
                        9.77159156212368,
                        12.7728658971109
                    ],
                    [
                        -42.519509532725,
                        -34.0215864556319
                    ],
                    [
                        36.3380364283033,
                        48.417423635541
                    ],
                    [
                        -3.72966234101399,
                        4.45735992697786
                    ],
                    [
                        -75.0230074912361,
                        -66.2097120787971
                    ],
                    [
                        -85.7403171402542,
                        -77.538919132725
                    ],
                    [
                        -4.28421664617977,
                        5.20129290577176
                    ],
                    [
                        29.8948322314041,
                        39.8778174510386
                    ],
                    [
                        -4.21569338159421,
                        3.69318699925818
                    ],
                    [
                        2.17654068477877,
                        2.89700712475637
                    ],
                    [
                        4.29190058640526,
                        5.71299484516714
                    ],
                    [
                        1.843764124993,
                        2.47265158452973
                    ],
                    [
                        173.305873972011,
                        223.217034153963
                    ],
                    [
                        0.241219153453138,
                        0.312236230733881
                    ],
                    [
                        0.569903621518138,
                        0.751732932431305
                    ],
                    [
                        26.1946339463934,
                        34.9127342836536
                    ],
                    [
                        0.510422015890195,
                        0.683696843422923
                    ],
                    [
                        70.3851180852223,
                        94.5768493483295
                    ],
                    [
                        0.464576798676445,
                        0.622901323722049
                    ]
                ],
                "output_variables": [
                    "buckle_pressure",
                    "Weight"
                ],
                "output_variables_objectives": [
                    "MAXIMUM",
                    "MINIMUM"
                ],
                "output_variables_thresholds": [
                    5,
                    3
                ],
                "num_iterations": 1,
                "batch_size": 1,
                "constraints_module_id": "6627e9cfc5e3c6479ef1558d",
                "outcome_constraints_active": False,
                "outcome_constraints_variable": None,
                "outcome_constraints_operator": "",
                "outcome_constaints_inputvalue": None,
                "dataset": None
            },
            "state": "IDLE",
            "on_success": [
                "0190bfa7-6a08-7f99-b973-8e29262c85d2"
            ],
            "on_failure": [],
            "on_complete": [],
            "inputs": [
                {
                    "urn": "0190bfa7-6a08-7cb7-92a9-afd2ec45db43",
                    "map_to_argument": "",
                    "type": "DATASET",
                    "name": "P1&P3-Demo_Widget-CSV_FILE-g4Bg_Tabular"
                }
            ],
            "outputs": [
                {
                    "urn": "0190bfa7-6a08-7cb7-b89f-c50c84ca77ef",
                    "map_to_argument": "",
                    "type": "DATASET",
                    "name": "P1&P3-Demo_Widget-MOBO-Wblp_Tabular"
                }
            ],
            "use_gpu": False,
            "retry_interval_in_sec": 30,
            "retry_count": 30,
            "client_tags": {
                "PositionX": 540,
                "PositionY": 160,
                "Width": 90,
                "Height": 90,
                "Color": "#1A7A7F",
                "ClientType": "MOBO"
            }
        },
        {
            "urn": "0190bfa7-6a09-73bc-8c58-2beab50a2ce3",
            "name": "Widget-RESCALE-1IfK",
            "description": "DefaultWidgetDescription",
            "type": "RESCALE",
            "config": {
                "widget_type": "RESCALE",
                "rescale_connector_id": "669795af9523d8940a1777c2",
                "rescale_configs": {
                    "name": "Sample LS-DYNA Simulation",
                    "test_mode": True,
                    "run_job": False,
                    "software": {
                        "hardware": {
                            "coreType": "starlite_max",
                            "slots": 1,
                            "coresPerSlot": 1,
                            "walltime": 96,
                            "type": "compute"
                        },
                        "analysis": {
                            "version": "12.0.0",
                            "code": "ls_dyna"
                        },
                        "reusable_job_file": "custom_driver.py",
                        "dynamic_job_file": "param_values.csv, _1883_XXXX.material, Blank.k, Tools.k, shellbuckleXXXX.k",
                        "pre_python": None,
                        "post_python": "custom_driver.py",
                        "command": "ls-dyna -i _ShellBuckle_V2.3.1.k -p single -s 1",
                        "output_file": "abstat",
                        "visualize_files": [],
                        "envVars": {
                            "DSLS_LICENSE_FILE": None,
                            "LSTC_LICENSE_SERVER": "31010@novelis"
                        },
                        "onDemandLicenseSeller": None
                    },
                    "files_detail": [
                        {
                            "file_name": "custom_driver.py",
                            "file_path": "/hexaind-data/hexaind-datasets/connection/661fdd495a76ce9ec0f1307e/6627f31ec5e3c6479ef15643/custom_driver.py",
                            "upload_rescale": True,
                            "rescale_id": ""
                        }
                    ]
                },
                "version": "1.0"
            },
            "state": "IDLE",
            "on_success": [
                "0190bfa7-6a08-7cb7-92a9-afd2ec45db43"
            ],
            "on_failure": [],
            "on_complete": [],
            "inputs": [
                {
                    "urn": "0190bfa7-6a08-7f99-b973-8e29262c85d2",
                    "map_to_argument": "",
                    "type": "DATASET",
                    "name": "P1&P3-Demo_Widget-MOBO-Wblp_Tabular"
                }
            ],
            "outputs": [
                {
                    "urn": "0190bfa7-6a09-73bc-8c58-2beab50a2ce3",
                    "map_to_argument": "",
                    "type": "DATASET",
                    "name": "P1&P3-Demo_Widget-RESCALE-1IfK_Tabular"
                }
            ],
            "use_gpu": False,
            "retry_interval_in_sec": 30,
            "retry_count": 30,
            "client_tags": {
                "PositionX": 540,
                "PositionY": 0,
                "Width": 90,
                "Height": 90,
                "Color": "#1A7A7F",
                "ClientType": "RESCALE"
            }
        }
    ],    
    "start": [
        "0190bfa7-6a08-70e0-b811-85874680f473"
    ],
    "end": [
        "0190bfa7-6a08-7268-bb0e-418d13873776"
    ],
    "user_id": "664c569824e6fd041c96c25b",
    "user_name": "Test User",
    "client_tags": {
        "StartWidgetPosition": {
            "X": 80,
            "Y": 140
        },
        "EndWidgetPosition": {
            "X": 960,
            "Y": 140
        },
        "Arrows": [
            {
                "start_urn": "START",
                "start_connector_point_type": 2,
                "end_urn": "0190bfa7-6a08-70e0-b811-85874680f473",
                "end_connector_point_type": 1,
                "arrow_type": 0
            },
            {
                "start_urn": "0190bfa7-6a08-70e0-b811-85874680f473",
                "start_connector_point_type": 2,
                "end_urn": "0190bfa7-6a08-7cb7-92a9-afd2ec45db43",
                "end_connector_point_type": 1,
                "arrow_type": 0
            },
            {
                "start_urn": "0190bfa7-6a08-7cb7-92a9-afd2ec45db43",
                "start_connector_point_type": 2,
                "end_urn": "0190bfa7-6a08-7cb7-b89f-c50c84ca77ef",
                "end_connector_point_type": 1,
                "arrow_type": 0
            },
            {
                "start_urn": "0190bfa7-6a08-7cb7-b89f-c50c84ca77ef",
                "start_connector_point_type": 2,
                "end_urn": "0190bfa7-6a08-7f99-b973-8e29262c85d2",
                "end_connector_point_type": 1,
                "arrow_type": 0
            },
            {
                "start_urn": "0190bfa7-6a08-7f99-b973-8e29262c85d2",
                "start_connector_point_type": 2,
                "end_urn": "0190bfa7-6a08-7268-bb0e-418d13873776",
                "end_connector_point_type": 1,
                "arrow_type": 0
            },
            {
                "start_urn": "0190bfa7-6a08-7268-bb0e-418d13873776",
                "start_connector_point_type": 2,
                "end_urn": "END",
                "end_connector_point_type": 1,
                "arrow_type": 0
            },
            {
                "start_urn": "0190bfa7-6a08-7f99-b973-8e29262c85d2",
                "start_connector_point_type": 0,
                "end_urn": "0190bfa7-6a09-73bc-8c58-2beab50a2ce3",
                "end_connector_point_type": 2,
                "arrow_type": 0
            },
            {
                "start_urn": "0190bfa7-6a09-73bc-8c58-2beab50a2ce3",
                "start_connector_point_type": 3,
                "end_urn": "0190bfa7-6a08-7cb7-92a9-afd2ec45db43",
                "end_connector_point_type": 2,
                "arrow_type": 0
            }
        ]
    }
}