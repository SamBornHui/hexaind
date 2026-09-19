active_learning = {
    "widgets": [
        {
            "urn": "583bc662-eafe-4cff-9a27-cb1585067b1a",
            "name": "CSV",
            "description": "DefaultWidgetDescription",
            "type": "DATA_COPY",
            "config": {
                "version": "1.0",
                "widget_type": "DATA_COPY",
                "source": {
                    "type": "LOCAL",
                    "configuration": {
                        "version": "1.0",
                        "dataset_id": "668cffa371aa5e0e76fc6367"
                    }
                },
                "sink": {
                    "dataset_name": "csv_dataset",
                    "dataset_description": "csv_dataset_description"
                }
            },
            "state": "IDLE",
            "on_success": [
                "c8aa43ff-e95e-49a8-9cdd-f259abf74558"
            ],
            "on_failure": [],
            "on_complete": [],
            "inputs": [],
            "outputs": [
                {
                    "urn": "583bc662-eafe-4cff-9a27-cb1585067b1a",
                    "map_to_argument": "",
                    "type": "DATASET",
                    "name": "Demo Project_CSV_FILE-B35F_Tabular"
                }
            ],
            "use_gpu": False,
            "retry_interval_in_sec": 30,
            "retry_count": 30,
            "client_tags": {
                "PositionX": 440,
                "PositionY": 120,
                "Width": 90,
                "Height": 90,
                "Color": "#1A7A7F",
                "ClientType": "CSV_FILE"
            }
        },
        {
            "urn": "8a50e0e3-2a09-4154-a0f4-fc4f3015c590",
            "name": "SAVE",
            "description": "DefaultWidgetDescription",
            "type": "SAVE",
            "config": {
                "version": "1.0",
                "widget_type": "SAVE",
                "datasetConfig": [
                    {
                        "dataset_name": "Demo Project_ACTIVE_LEARNING-ccU3_Tabular",
                        "destination_type": "HEXAIND_PLATFORM",
                        "destination_config": {
                            "file_Format": "CSV",
                            "save_options": "SAVE_AS",
                            "save_option_config": {
                                "file_name": "p1_active_learning_results"
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
                    "urn": "a28961ea-45de-4be1-96c2-48d912126f19",
                    "map_to_argument": "",
                    "type": "DATASET",
                    "name": "Demo Project_ACTIVE_LEARNING-ccU3_Tabular"
                }
            ],
            "outputs": [],
            "use_gpu": False,
            "retry_interval_in_sec": 30,
            "retry_count": 30,
            "client_tags": {
                "PositionX": 1160,
                "PositionY": 120,
                "Width": 90,
                "Height": 90,
                "Color": "#1A7A7F",
                "ClientType": "SAVE"
            }
        },
        {
            "urn": "c8aa43ff-e95e-49a8-9cdd-f259abf74558",
            "name": "LOOP_START",
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
                "a28961ea-45de-4be1-96c2-48d912126f19"
            ],
            "on_failure": [],
            "on_complete": [],
            "inputs": [
                {
                    "urn": "099a1f61-3c71-42c7-9a08-a1f6215b43bd",
                    "map_to_argument": "",
                    "type": "DATASET",
                    "name": "Demo Project_RESCALE-KByq_Tabular"
                }
            ],
            "outputs": [
                {
                    "urn": "583bc662-eafe-4cff-9a27-cb1585067b1a",
                    "map_to_argument": "",
                    "type": "DATASET",
                    "name": "Demo Project_CSV_FILE-B35F_Tabular"
                },
                {
                    "urn": "099a1f61-3c71-42c7-9a08-a1f6215b43bd",
                    "map_to_argument": "",
                    "type": "DATASET",
                    "name": "Demo Project_RESCALE-KByq_Tabular"
                }
            ],
            "use_gpu": False,
            "retry_interval_in_sec": 30,
            "retry_count": 30,
            "client_tags": {
                "PositionX": 600,
                "PositionY": 120,
                "Width": 90,
                "Height": 90,
                "Color": "#1A7A7F",
                "ClientType": "LOOP_START"
            }
        },
        {
            "urn": "d7c05988-ccc0-4873-8746-31cefef643d7",
            "name": "LOOP_END",
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
                    "099a1f61-3c71-42c7-9a08-a1f6215b43bd"
                ],
                "on_termination": [
                    "8a50e0e3-2a09-4154-a0f4-fc4f3015c590"
                ]
            },
            "state": "IDLE",
            "on_success": [
                "099a1f61-3c71-42c7-9a08-a1f6215b43bd",
                "8a50e0e3-2a09-4154-a0f4-fc4f3015c590"
            ],
            "on_failure": [],
            "on_complete": [],
            "inputs": [
                {
                    "urn": "a28961ea-45de-4be1-96c2-48d912126f19",
                    "map_to_argument": "",
                    "type": "DATASET",
                    "name": "Demo Project_ACTIVE_LEARNING-ccU3_Tabular"
                }
            ],
            "outputs": [
                {
                    "urn": "a28961ea-45de-4be1-96c2-48d912126f19",
                    "map_to_argument": "",
                    "type": "DATASET",
                    "name": "Demo Project_ACTIVE_LEARNING-ccU3_Tabular"
                }
            ],
            "use_gpu": False,
            "retry_interval_in_sec": 30,
            "retry_count": 30,
            "client_tags": {
                "PositionX": 920,
                "PositionY": 140,
                "Width": 90,
                "Height": 90,
                "Color": "#1A7A7F",
                "ClientType": "LOOP_END"
            }
        },
        {
            "urn": "a28961ea-45de-4be1-96c2-48d912126f19",
            "name": "ACTIVE_LEARNING",
            "description": "DefaultWidgetDescription",
            "type": "ACTIVE_LEARNING",
            "config": {
                "version": "1.0",
                "widget_type": "ACTIVE_LEARNING",
                "experiment_type": "ACTIVE_LEARNING",
                "features_detail": [
                    {
                        "name": "dcp_spacer",
                        "dataType": "Numerical",
                        "selected": True,
                        "input": True,
                        "output": False
                    },
                    {
                        "name": "pp_spacer",
                        "dataType": "Numerical",
                        "selected": True,
                        "input": True,
                        "output": False
                    },
                    {
                        "name": "ips_pressure",
                        "dataType": "Numerical",
                        "selected": True,
                        "input": True,
                        "output": False
                    },
                    {
                        "name": "up_pressure",
                        "dataType": "Numerical",
                        "selected": True,
                        "input": True,
                        "output": False
                    },
                    {
                        "name": "friction_coeff",
                        "dataType": "Numerical",
                        "selected": True,
                        "input": True,
                        "output": False
                    },
                    {
                        "name": "upper_radius",
                        "dataType": "Numerical",
                        "selected": True,
                        "input": True,
                        "output": False
                    },
                    {
                        "name": "lower_radius",
                        "dataType": "Numerical",
                        "selected": True,
                        "input": True,
                        "output": False
                    },
                    {
                        "name": "t_value",
                        "dataType": "Numerical",
                        "selected": True,
                        "input": True,
                        "output": False
                    },
                    {
                        "name": "lr_opening",
                        "dataType": "Numerical",
                        "selected": True,
                        "input": True,
                        "output": False
                    },
                    {
                        "name": "catcher_depth",
                        "dataType": "Numerical",
                        "selected": True,
                        "input": True,
                        "output": False
                    },
                    {
                        "name": "ips_radius",
                        "dataType": "Numerical",
                        "selected": True,
                        "input": True,
                        "output": False
                    },
                    {
                        "name": "dcr_radius",
                        "dataType": "Numerical",
                        "selected": True,
                        "input": True,
                        "output": False
                    },
                    {
                        "name": "dcp_radius_1",
                        "dataType": "Numerical",
                        "selected": True,
                        "input": True,
                        "output": False
                    },
                    {
                        "name": "dcp_radius_2",
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
                        "name": "max_thinning",
                        "dataType": "Numerical",
                        "selected": True,
                        "input": False,
                        "output": True
                    }
                ],
                "input_variables": [
                    "dcp_spacer",
                    "pp_spacer",
                    "ips_pressure",
                    "up_pressure",
                    "friction_coeff",
                    "upper_radius",
                    "lower_radius",
                    "t_value",
                    "lr_opening",
                    "catcher_depth",
                    "ips_radius",
                    "dcr_radius",
                    "dcp_radius_1",
                    "dcp_radius_2"
                ],
                "input_variables_constraints": [
                    [
                        0.18,
                        0.18001799999999998
                    ],
                    [
                        0.144,
                        0.1440144
                    ],
                    [
                        61.75703273,
                        116.5307904
                    ],
                    [
                        60,
                        60.006
                    ],
                    [
                        0.05,
                        0.050005
                    ],
                    [
                        0.005153495,
                        0.031429292
                    ],
                    [
                        0.005101214,
                        0.030728065
                    ],
                    [
                        0.010755824,
                        0.036
                    ],
                    [
                        1.679,
                        1.729843213
                    ],
                    [
                        0.085417634,
                        0.1
                    ],
                    [
                        0.029229092,
                        0.1
                    ],
                    [
                        0.060678336,
                        0.123677806
                    ],
                    [
                        0.027145029,
                        0.1
                    ],
                    [
                        0.02,
                        0.1
                    ]
                ],
                "output_variables": [
                    "buckle_pressure",
                    "max_thinning"
                ],
                "output_variables_objectives": [
                    "MAXIMUM",
                    "MINIMUM"
                ],
                "output_variables_thresholds": [
                    111,
                    11
                ],
                "num_iterations": 1,
                "batch_size": 1,
                "constraints_module_id": "",
                "outcome_constraints_active": False,
                "outcome_constraints_variable": None,
                "outcome_constraints_operator": None,
                "outcome_constaints_inputvalue": None,
                "dataset": None
            },
            "state": "IDLE",
            "on_success": [
                "d7c05988-ccc0-4873-8746-31cefef643d7"
            ],
            "on_failure": [],
            "on_complete": [],
            "inputs": [
                {
                    "urn": "c8aa43ff-e95e-49a8-9cdd-f259abf74558",
                    "map_to_argument": "",
                    "type": "DATASET",
                    "name": "Demo Project_CSV_FILE-B35F_Tabular"
                }
            ],
            "outputs": [
                {
                    "urn": "a28961ea-45de-4be1-96c2-48d912126f19",
                    "map_to_argument": "",
                    "type": "DATASET",
                    "name": "Demo Project_ACTIVE_LEARNING-ccU3_Tabular"
                }
            ],
            "use_gpu": False,
            "retry_interval_in_sec": 30,
            "retry_count": 30,
            "client_tags": {
                "PositionX": 756,
                "PositionY": 223,
                "Width": 90,
                "Height": 90,
                "Color": "#1A7A7F",
                "ClientType": "ACTIVE_LEARNING"
            }
        },
        {
            "urn": "099a1f61-3c71-42c7-9a08-a1f6215b43bd",
            "name": "RESCALE",
            "description": "DefaultWidgetDescription",
            "type": "RESCALE",
            "config": {
                "widget_type": "RESCALE",
                "rescale_connector_id": "668cfeb67208febb3f5514c8",
                "rescale_configs": {
                    "name": "Sample ABAQUS Simulation",
                    "test_mode": True,
                    "run_job": False,
                    "software": {
                        "hardware": {
                            "coreType": "starlite_max",
                            "slots": 1,
                            "coresPerSlot": 4,
                            "walltime": 3,
                            "type": None
                        },
                        "analysis": {
                            "version": "2023-golden-DSLS",
                            "code": "abaqus-dsls"
                        },
                        "reusable_job_file": "custom_driver.py,MG_Forming.py,MG_Springback.py,MG_Buckling.py,PostProcessing.py,Visualizer.py,scaler.pkl,gp_scaling.pkl,sedata.csv",
                        "dynamic_job_file": "param_values.csv",
                        "pre_python": None,
                        "post_python": "custom_driver.py,scaler.pkl,gp_scaling.pkl",
                        "command": "abaqus cae noGUI=MG_Forming.py; abaqus job=FormingJob.inp cpus=$RESCALE_CORES_PER_SLOT mp_mode=mpi interactive parallel=domain double=both output_precision=full; abaqus cae noGUI=MG_Springback.py; abaqus job=SpringbackJob.inp cpus=$RESCALE_CORES_PER_SLOT mp_mode=mpi interactive double=both output_precision=full; abaqus cae noGUI=MG_Buckling.py; abaqus job=BucklingJob.inp cpus=$RESCALE_CORES_PER_SLOT mp_mode=mpi interactive double=both output_precision=full; abaqus python PostProcessing.py;abaqus cae noGUI=Visualizer.py",
                        "output_file": "PerfMetricsFile.csv",
                        "visualize_files": [
                            "ShellGeometry.png",
                            "ShellGeometry_Closeup.png",
                            "FormingAnimation_Script.avi"
                        ],
                        "envVars": {
                            "DSLS_LICENSE_FILE": "4085@novelis",
                            "LSTC_LICENSE_SERVER": None
                        },
                        "onDemandLicenseSeller": None
                    },
                    "files_detail": [
                        {
                            "file_name": "custom_driver.py",
                            "file_path": "/hexaind-data/hexaind-datasets/connection/668cfeb67208febb3f5514c8/668cfcb97208febb3f551498/custom_driver.py",
                            "upload_rescale": True,
                            "rescale_id": ""
                        },
                        {
                            "file_name": "MG_Forming.py",
                            "file_path": "/hexaind-data/hexaind-datasets/connection/668cfeb67208febb3f5514c8/MG_Forming.py",
                            "upload_rescale": True,
                            "rescale_id": ""
                        },
                        {
                            "file_name": "MG_Springback.py",
                            "file_path": "/hexaind-data/hexaind-datasets/connection/668cfeb67208febb3f5514c8/MG_Springback.py",
                            "upload_rescale": True,
                            "rescale_id": ""
                        },
                        {
                            "file_name": "MG_Buckling.py",
                            "file_path": "/hexaind-data/hexaind-datasets/connection/668cfeb67208febb3f5514c8/MG_Buckling.py",
                            "upload_rescale": True,
                            "rescale_id": ""
                        },
                        {
                            "file_name": "PostProcessing.py",
                            "file_path": "/hexaind-data/hexaind-datasets/connection/668cfeb67208febb3f5514c8/PostProcessing.py",
                            "upload_rescale": True,
                            "rescale_id": ""
                        },
                        {
                            "file_name": "Visualizer.py",
                            "file_path": "/hexaind-data/hexaind-datasets/connection/668cfeb67208febb3f5514c8/Visualizer.py",
                            "upload_rescale": True,
                            "rescale_id": ""
                        },
                        {
                            "file_name": "scaler.pkl",
                            "file_path": "/hexaind-data/hexaind-datasets/connection/668cfeb67208febb3f5514c8/668cfcb97208febb3f551498/scaler.pkl",
                            "upload_rescale": True,
                            "rescale_id": ""
                        },
                        {
                            "file_name": "gp_scaling.pkl",
                            "file_path": "/hexaind-data/hexaind-datasets/connection/668cfeb67208febb3f5514c8/668cfcb97208febb3f551498/gp_scaling.pkl",
                            "upload_rescale": True,
                            "rescale_id": ""
                        },
                        {
                            "file_name": "sedata.csv",
                            "file_path": "/hexaind-data/hexaind-datasets/connection/668cfeb67208febb3f5514c8/sedata.csv",
                            "upload_rescale": True,
                            "rescale_id": ""
                        }
                    ]
                },
                "version": "1.0"
            },
            "state": "IDLE",
            "on_success": [
                "c8aa43ff-e95e-49a8-9cdd-f259abf74558"
            ],
            "on_failure": [],
            "on_complete": [],
            "inputs": [
                {
                    "urn": "d7c05988-ccc0-4873-8746-31cefef643d7",
                    "map_to_argument": "",
                    "type": "DATASET",
                    "name": "Demo Project_ACTIVE_LEARNING-ccU3_Tabular"
                }
            ],
            "outputs": [
                {
                    "urn": "099a1f61-3c71-42c7-9a08-a1f6215b43bd",
                    "map_to_argument": "",
                    "type": "DATASET",
                    "name": "Demo Project_RESCALE-KByq_Tabular"
                }
            ],
            "use_gpu": False,
            "retry_interval_in_sec": 30,
            "retry_count": 30,
            "client_tags": {
                "PositionX": 756,
                "PositionY": 43,
                "Width": 90,
                "Height": 90,
                "Color": "#1A7A7F",
                "ClientType": "RESCALE"
            }
        }
    ],
    "start": [
        "583bc662-eafe-4cff-9a27-cb1585067b1a"
    ],
    "end": [
        "8a50e0e3-2a09-4154-a0f4-fc4f3015c590"
    ],
    "user_id": "667e965d9dfff9bbfd09fc54",
    "user_name": "Hamza Hassan",
    "client_tags": {
        "StartWidgetPosition": {
            "X": 240,
            "Y": 120
        },
        "EndWidgetPosition": {
            "X": 1360,
            "Y": 120
        },
        "Arrows": [
            {
                "start_urn": "START",
                "start_connector_point_type": 2,
                "end_urn": "583bc662-eafe-4cff-9a27-cb1585067b1a",
                "end_connector_point_type": 1,
                "arrow_type": 0
            },
            {
                "start_urn": "583bc662-eafe-4cff-9a27-cb1585067b1a",
                "start_connector_point_type": 2,
                "end_urn": "c8aa43ff-e95e-49a8-9cdd-f259abf74558",
                "end_connector_point_type": 1,
                "arrow_type": 0
            },
            {
                "start_urn": "c8aa43ff-e95e-49a8-9cdd-f259abf74558",
                "start_connector_point_type": 2,
                "end_urn": "a28961ea-45de-4be1-96c2-48d912126f19",
                "end_connector_point_type": 1,
                "arrow_type": 0
            },
            {
                "start_urn": "a28961ea-45de-4be1-96c2-48d912126f19",
                "start_connector_point_type": 2,
                "end_urn": "d7c05988-ccc0-4873-8746-31cefef643d7",
                "end_connector_point_type": 1,
                "arrow_type": 0
            },
            {
                "start_urn": "d7c05988-ccc0-4873-8746-31cefef643d7",
                "start_connector_point_type": 1,
                "end_urn": "099a1f61-3c71-42c7-9a08-a1f6215b43bd",
                "end_connector_point_type": 2,
                "arrow_type": 0
            },
            {
                "start_urn": "099a1f61-3c71-42c7-9a08-a1f6215b43bd",
                "start_connector_point_type": 1,
                "end_urn": "c8aa43ff-e95e-49a8-9cdd-f259abf74558",
                "end_connector_point_type": 2,
                "arrow_type": 0
            },
            {
                "start_urn": "d7c05988-ccc0-4873-8746-31cefef643d7",
                "start_connector_point_type": 2,
                "end_urn": "8a50e0e3-2a09-4154-a0f4-fc4f3015c590",
                "end_connector_point_type": 1,
                "arrow_type": 0
            },
            {
                "start_urn": "8a50e0e3-2a09-4154-a0f4-fc4f3015c590",
                "start_connector_point_type": 2,
                "end_urn": "END",
                "end_connector_point_type": 1,
                "arrow_type": 0
            }
        ]
    }
}