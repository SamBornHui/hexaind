# README

## Setup

### DevContainer (VSCode)

By installing the `devcontainer` extension, VSCode sets up devcontainer using `devcontainer.json` file.

This works for `Linux` and `Windows (WSL)`.

### Manual Setup

#### Ubuntu/Debian

Installing pyenv

```bash
# Installing pyenv dependencies
sudo apt install -y make build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev
export PYENV_ROOT=${XDG_DATA_HOME:-$HOME/.local/share}/pyenv
# Installing pyenv
curl https://pyenv.run | bash
cat >> $HOME/.bashrc << EOF
export PYENV_ROOT=\${XDG_DATA_HOME:-$HOME/.local/share}/pyenv
export PATH=\${PYENV_ROOT}/bin:\$PATH
eval "\$(pyenv init -)"
eval "\$(pyenv virtualenv-init -)"
EOF
source $HOME/.bashrc
# installing python 3.10.15
pyenv install 3.10.15
# creating python virtual environment
pyenv virtualenv 3.10.15 hexaind_backend
```

Cloning Repository

```bash
: ${HEXAIND_HOME:=/hexaind-home}
sudo mkdir -p ${HEXAIND_HOME}
sudo chown $(id -u):$(id -g) ${HEXAIND_HOME}
cd ${HEXAIND_HOME}
git clone git@bitbucket.org:databricktech1/hexaind_backend.git hexaind_backend
cd hexaind_backend
pyenv shell hexaind_backend
```

Installing System Requirements

```bash
sudo apt install -y curl ffmpeg gcc libcairo2-dev pkg-config python3-dev socat
```

Installing Requirements

```bash
cd ${HEXAIND_HOME}/hexaind_backend
pip install --editable .[prod] --constraint constraints.txt
```

```bash
# for ml related development
cd ${HEXAIND_HOME}/hexaind_backend
pip install --editable .[prod_ml] --constraint constraints.txt
```

## Environment Variables

The env files are as follows:

- .env
- backend.env
- azure.env
- celery.env
- jupyterhub.env
- thermocalc.env
- monitoring.env

For thermocalc the environment variables as present in `thermocalc-overrides.env.example`.
To override the environment create a copy of the above named as `thermocalc-overrides.env` and modify it.

```bash
cp thermocalc-overrides.env.example thermocalc-overrides.env
```

## Docker Deployment

### Locally Running All Containers

Change `IS_STANDALONE_DEPLOYMENT` to `False` in `thermocalc-overrides.env` and update instance addresses.

```bash
docker compose -f scheduling_compose.yml -f compose.micron.yml -f compose.micron.override.yml -f thermocalc_service_compose.yml --profile all up --detach --build
```

### Micron Containers

Change `TDAM_SHARED_PATH` to actual value.

```bash
docker compose -f scheduling_compose.yml -f compose.micron.yml -f compose.micron.override.yml --profile all up --detach --build
```

### Thermocalc Containers

Update values in `thermocalc-overrides.env`.

```bash
docker compose -f scheduling_compose.yml --profile all up --detach --build
docker compose -f thermocalc_service_compose.yml --profile all up --detach --build
```

**_ Tokens Transfer to end point with RBAC _**

- All the endpoins details avaialble in 'endpoints_features_mappings.json' file loaded into DB with >python -m app.init_db
- The endpoints with "exclude":true will be accessible without any token from header
- To access endpoints with "exclude":false you must pass token in the Header, otherwise you will get error like 'Not Authorized, Login and attempt again'
- if an endpoint needs the token, it must have and argument token: str = '', The token is pushed from Header to this argument from RBAC
- In swagger you can see token arg for many end points, but you need not to pass any value at endpoint, but you must provide one with Authorize/ any Lock button
- Endpoints not listed in 'endpoints_features_mappings.json' and routers not having route_class=CheckNameRoute will not come under RBAC

**_ The Following config/environment values will be taken from Azure KeyVault _**
-mongo_details (To use your local mongo DB keep string like 'mongodb://localhost:27017' in env_vars.py)
-gcp_client_id
-sendgrid_api_key

**_ Communication Email method settings like Invitations mails Set any one in Azure Secret key: send-email-using Below are values are valid_**
-sendgrid: This need extra keys: sendgrid-api-key
-smtp: This needs extra keys: smtp_server_port_email_password_csv
-azure_email_communication: This needs the extra keys: azure-email-conn-string, azure-comm-reply-email

**_ To use docker build on your local/ test env _**

1. Check the credentials in compose.yml (values against MONGO_INITDB_ROOT_USERNAME & MONGO_INITDB_ROOT_PASSWORD)
2. Apply the credentials to your existing DB before you build
3. Build the docker images
4. Test your DB with credentials (ie: 'mongodb://<uid>:<pwd>@<localhost/mongo>:27017)
   NOTE: For more details look into the details of JIRA ID - HEXAIND-9200

**_ To Run API Server _**

> python -m uvicorn app.main:app --port 8080

**_ To Run MOBO worker _**

> python -m celery -A app.workers.AI.mobo.worker worker -Q mobo_actions --pool solo -l INFO

**_ To Run Active Learning worker _**

> python -m celery -A app.workers.AI.active_learning.worker worker -Q active_learning_actions --pool solo -l INFO

**_ To Run RESCALE worker _**

> python -m celery -A app.workers.AI.rescale.worker worker -Q rescale_actions -l INFO

**_ To Run Action Manager _**

> celery -A app.core.services.action_manager.worker worker -Q start_end -l INFO

**_ To Run Action Worker _**

> celery -A app.workers.celery_worker worker -Q actions -l INFO

**_ For testing _**

- navigate to localhost:8080/docs
- run create connector api with below payload

```json
{
  "name": "BigQueryTest",
  "description": "Demo BigQuery Connector",
  "type": "BIGQUERY",
  "configuration": {
    "authentication_type": "SERVICE_ACCOUNT",
    "authentication_details": {
      "type": "service_account",
      "project_id": "healthy-saga-327423",
    }
  }
}
```

- run create workflow API with below payload (replace connector id with the id from above API response)

```json
{
  "name": "Demo Workflow",
  "description": "Worfklow Execution demo",
  "owner_id": "12345",
  "owner_name": "xyz",
  "widgets": [
    {
      "urn": "1",
      "name": "BigQueryDemo",
      "description": "data from BigQuery",
      "type": "DATA_COPY",
      "config": {
        "source": {
          "type": "BIGQUERY",
          "configuration": {
            "bigquery_connector_id": "65c54390b7429f1fccb75a13",
            "dataset_configuration": {
              "project_id": "healthy-saga-327423",
              "dataset_type": "TABLE",
              "dataset": {
                "dataset_name": "test_demo",
                "table_name": "BOSTONTRAIN"
              }
            }
          }
        },
        "sink": {
          "dataset_name": "demo_dataset",
          "dataset_description": "data from BigQuery"
        }
      },
      "state": "IDLE",
      "on_success": ["2"],
      "inputs": [],
      "outputs": [
        {
          "urn": "1",
          "name": "tab1"
        }
      ],
      "on_failure": [],
      "on_complete": [],
      "retry_interval_in_sec": 0,
      "retry_count": 0
    },
    {
      "urn": "2",
      "name": "Filter1",
      "description": "apply column filter on Demo dataset",
      "type": "FILTER",
      "config": {
        "version": "1.0",
        "type": "FILTER_BY_COLUMN_VALUES",
        "config": {
          "version": "1.0",
          "filter_operands": ["AND"],
          "filter_values": [
            { "column_name": "age", "operator": "GT", "value": 50 },
            { "column_name": "ptratio", "operator": "GTE", "value": 18 }
          ]
        }
      },
      "state": "IDLE",
      "on_success": ["3"],
      "inputs": [
        {
          "urn": "1",
          "name": "tab1"
        }
      ],
      "outputs": [
        {
          "urn": "2",
          "name": "tab2"
        }
      ],
      "on_failure": [],
      "on_complete": [],
      "retry_interval_in_sec": 0,
      "retry_count": 0
    },

    {
      "urn": "3",
      "name": "Save1",
      "description": "saving the filter widget output to assets",
      "type": "SAVE",
      "config": {
        "version": "1.0",
        "type": "DATASET",
        "config": {
          "name": "save_filter_output_assets",
          "description": "save_filter_output_assets",
          "scope": "GLOBAL"
        }
      },
      "state": "IDLE",
      "on_success": [],
      "inputs": [
        {
          "urn": "2",
          "name": "tab2"
        }
      ],
      "outputs": [],
      "on_failure": [],
      "on_complete": [],
      "retry_interval_in_sec": 0,
      "retry_count": 0
    }
  ],
  "start": ["1"],
  "end": ["3"]
}
```

**_ Testing LightGBM widget payload _**

```json
{
  "urn": "2",
  "name": "Model Building",
  "description": "Model Building",
  "type": "MODEL_BUILDER",
  "config": {
    "version": "1.0",
    "input_columns": [
      "crim",
      "zn",
      "indus",
      "nox",
      "rm",
      "age",
      "dis",
      "rad",
      "tax"
    ],
    "output_column": "ptratio",
    "scaling_method": "STANDARD",
    "hyper_parameter_optimization_method": "RANDOM_SEARCH",
    "test_data_split_ratio": 30,
    "random_search_params": { "n_iter": 10 },
    "n_folds": 5,
    "random_state": 42,
    "model": "LIGHT_GBM",
    "parameters": {
      "min_depth": 10,
      "max_depth": 15,
      "sample_no_depth": 4,
      "min_num_leaves": 10,
      "max_num_leaves": 50,
      "sample_no_num_leaves": 4,
      "min_child_samples": 20,
      "max_child_samples": 100,
      "sample_no_child_samples": 4
    }
  },
  "state": "IDLE",
  "on_success": [],
  "on_failure": [],
  "on_complete": [],
  "retry_interval_in_sec": 0,
  "retry_count": 0
}
```

```

```

**_ Testing CUSTOM_CODE widget _**

\***\* as per latest PRD custom code widget has changed a lot,
earlier code module can be directly ingested in workflow.
Now this custom code needs to be in form of a published CUSTOM_PYTHON_WIDGET.
To Publish a CUSTOM_PYTHON_WIDGET, Advanced user need to create a custom python widget recipes via builder tool \*\***

To test code in BE, use APIs tagged with custom_python_widget.

- upload zip file (at least in one file we should have `custom_python_widget_function()` with all params and output types: eg: /tests/resources/join_module.zip)
- pass file path to find metadata
- validate code with metadata
- once validation is done, create a recipe
- recipe is created, select how parameters needs to be send (i.e via from prior widgets or enter on widget)
- once selection is done -> publish the widget.
- once widget is published , then it can be used in workflow.
- sample_workflow can be found in /app/tests/workers/custom_code/test_worker.py

**_ Scenario-1 _**



- create a python file with below code:

```python
import pandas as pd
import json

def custom_function() -> dict:

    sql_query = "SELECT * FROM healthy-saga-327423.test_demo.BOSTONTRAIN;"

    return {"sql_query": sql_query}
```

- use Upload Module API to upload this file will get module_id

- replace module id and connector id in the below command

- create workflow and Run the workflow to get the results.

```json
{
  "name": "Demo Workflow",
  "description": "Worfklow Execution demo",
  "owner_id": "12345",
  "owner_name": "xyz",
  "widgets": [
    {
      "urn": "1",
      "name": "BigQueryDemo",
      "description": "data from BigQuery",
      "type": "DATA_COPY",
      "config": {
        "source": {
          "type": "BIGQUERY",
          "configuration": {
            "bigquery_connector_id": "658aea3e9b4341f250e66888",
            "dataset_configuration": {
              "project_id": "healthy-saga-327423",
              "dataset_type": "TABLE",
              "dataset": {
                "dataset_name": "test_demo",
                "table_name": "BOSTONTRAIN"
              }
            }
          }
        },
        "sink": {
          "dataset_name": "demo_dataset",
          "dataset_description": "data from BigQuery"
        }
      },
      "state": "IDLE",
      "on_success": ["2"],
      "on_failure": [],
      "on_complete": [],
      "retry_interval_in_sec": 0,
      "retry_count": 0
    },
    {
      "urn": "1",
      "name": "CUSTOM_CODE_1",
      "description": "Generate BigQuery SQL",
      "type": "CUSTOM_CODE",
      "config": {
        "module_id": "658aeaa79b4341f250e6688a",
        "function_inputs": [],
        "function_outputs": [
          {
            "type": "STRING",
            "arg_name": "sql_query"
          }
        ]
      },
      "state": "IDLE",
      "on_success": ["2"],

      "on_failure": [],
      "on_complete": [],
      "retry_interval_in_sec": 0,
      "retry_count": 0
    },
    {
      "urn": "2",
      "name": "BigQueryDemo",
      "description": "data from BigQuery",
      "type": "DATA_COPY",
      "config": {
        "source": {
          "type": "BIGQUERY",
          "configuration": {
            "bigquery_connector_id": "658aea3e9b4341f250e66888",
            "dataset_configuration": {
              "project_id": "healthy-saga-327423",
              "dataset_type": "QUERY",
              "dataset": {
                "query": ""
              }
            }
          }
        },
        "sink": {
          "dataset_name": "demo_dataset",
          "dataset_description": "data from BigQuery"
        }
      },
      "state": "IDLE",
      "on_success": [],
      "on_failure": [],
      "on_complete": [],
      "retry_interval_in_sec": 0,
      "retry_count": 0
    }
  ],
  "start": ["1"],
  "end": ["2"]
}
```

**_ Scenario-2 _**

- using CUSTOM_CODE widget to take data frame as input and apply dropna on all columns

- create a python file with below code:

```python
import pandas as pd
import json

def custom_function(test_df: pd.DataFrame) -> dict:

    df_dropped = test_df.dropna()

    return {"df_dropped": df_dropped}
```

- use Upload Module API to upload this file will get module_id

- replace module id and connector id in the below command

- create workflow and Run the workflow to get the results.

```json
{
    "name": "Demo Workflow",
    "description": "Worfklow Execution demo",
    "owner_id": "12345",
    "owner_name": "xyz",
    "widgets": [
        {
            "urn": "1",
            "name": "BigQueryDemo",
            "description": "data from BigQuery",
            "type": "DATA_COPY",
            "config": {
              "source": {
                "type": "BIGQUERY",
                "configuration": {
                  "bigquery_connector_id": "65c54390b7429f1fccb75a13",
                  "dataset_configuration": {
                    "project_id": "healthy-saga-327423",
                    "dataset_type": "TABLE",
                    "dataset": {
                        "dataset_name": "test_demo",
                        "table_name": "BOSTONTRAIN"
                    }
                  }
                }
              },
              "sink": {
                "dataset_name": "demo_dataset",
                "dataset_description": "data from BigQuery"
              }
            },
            "state": "IDLE",
            "on_success": ["2"],
            "inputs": [],
            "outputs": [
              {
                "urn": "1",
                "name": "tab1"
              }
            ],
            "on_failure": [],
            "on_complete": [],
            "retry_interval_in_sec": 0,
            "retry_count": 0
        },
        {
            "urn": "2",
            "name": "CUSTOM_CODE_2",
            "description": "Generate BigQuery SQL",
            "type": "CUSTOM_CODE",
            "config": {
              "module_id": "65c5a42fe28a88504b6dca97",
              "function_inputs": [
                {
                    "type": "DATA_FRAME",
                    "input_urn": "1",
                    "arg_name": "test_df"
                }

              ],
              "function_outputs": [
                {
                  "type": "DATA_FRAME",
                  "arg_name": "df_dropped"
                }
              ]
            },
            "state": "IDLE",
            "on_success": [],
            "inputs": [
              {
                "urn": "1",
                "map_to_argument": "test_df",
                "name": "tab1"
              }
            ],
            "outputs": [
              {
                "urn": "2",
                "name": "tab2"
              }
            ],
            "on_failure": [],
            "on_complete": [],
            "retry_interval_in_sec": 0,
            "retry_count": 0
        }
    ],
    "start": ["1"],
    "end": ["2"]
}

## MOBO Widget Test

{
    "name": "Demo Workflow",
    "description": "Worfklow Execution demo",
    "owner_id": "1",
    "owner_name": "1",
    "widgets": [
        {
        "urn": "1",
        "name": "MOBO DATA",
        "description": "MOBO data from LOCAL file",
        "type": "DATA_COPY",
        "config": {
          "source": {
            "type": "LOCAL",
            "configuration": {
              "dataset_id": "65cdb26da7498eccf8a415ec"
            }
          },
          "sink": {
            "dataset_name": "AICED",
            "dataset_description": "AICED"
          }
        },
        "state": "IDLE",
        "on_success": ["2"],
        "on_failure": [],
        "on_complete": [],
        "retry_interval_in_sec": 0,
        "retry_count": 0
        },

        {
        "urn": "2",
        "name": "Loop start",
        "description": "Loop start widget",
        "type": "LOOP_START",
        "config": {"loop_start_config": {"xyz": 1, "abc": 1}},
        "state": "IDLE",
        "on_success": ["3"],
        "on_failure": [],
        "on_complete": [],
        "retry_interval_in_sec": 0,
        "retry_count": 0
        },
        {
            "urn": "3",
            "name": "MOBO",
            "description": "generate recommendations",
            "type": "MOBO",
            "config": {
              "input_variables": ["dcp_spacer", "pp_spacer", "ips_pressure", "up_pressure", "friction_coeff", "upper_radius",     "lower_radius", "t_value", "lr_opening", "catcher_depth", "ips_radius", "dcr_radius", "dcp_radius_1", "dcp_radius_2"],
              "input_variables_constraints": [[0.18, 0.18001799999999998], [0.144, 58], [61.75703273, 116.5307904], [60, 60.006], [0.05,  5], [0.005153495, 25], [0.005101214, 20.030728065], [0.010755824, 35.036], [1.679, 51.729843213], [0.085417634, 40.1], [0.029229092, 50.1], [0.060678336, 30.123677806], [0.027145029, 38.1], [0.02, 25.1]],
              "output_variables": ["buckle_pressure", "max_thinning"],
              "output_variables_objectives": ["MAXIMUM", "MINIMUM"],
              "output_variables_thresholds": [111, 11],
              "num_iterations": 2,
              "run_iterations": true,
              "experiment_type": "OPTIMIZATION",
              "batch_size": 2
              },
            "state": "IDLE",
            "on_success": ["4"],
            "on_failure": [],
            "on_complete": [],
            "retry_interval_in_sec": 0,
            "retry_count": 0
        },

        {
        "urn": "4",
        "name": "Loop End",
        "description": "Loop End widget",
        "type": "LOOP_END",
        "config": {"termination_criteria": "ON_LOOP_COUNT",
                  "loop_end_config": {"loop_count": 4},
                  "on_loop": ["5"],
                  "on_termination": ["7"]
                  },
        "state": "IDLE",
        "on_success": ["5", "7"],
        "on_failure": [],
        "on_complete": [],
        "retry_interval_in_sec": 0,
        "retry_count": 0
        },

        {
            "urn": "5",
            "name": "RESCALE",
            "description": "generate recommendations",
            "type": "RESCALE",
            "config": {
              "rescale_connector_id": "659d5ec5dc18e4cfbd266396",
              "rescale_configs":{"name": "Sample ABAQUS Simulation",
                        "test_mode": true,
                        "run_job": false,
                        "files_detail": [{"file_name": "abaqus_job.py",
                          "file_path": "/hexaind-data/hexaind-datasets/connection/65a517707518c363e4c0d3fb/abaqus_job.py",
                          "upload_rescale": true,
                          "rescale_id": ""},
                        {"file_name": "PostProcessing.py",
                          "file_path": "PostProcessing.py",
                          "upload_rescale": true,
                          "rescale_id": "GZNYxh"}],
                        "software": {"analysis": {"code": "abaqus-dsls",
                          "version": "2021-golden-DSLS"},
                        "hardware": {"walltime": 3,
                          "coreType": "starlite_max",
                          "slots": 1,
                          "coresPerSlot": 4},
                        "command": "abaqus cae noGUI=MG_Forming.py; abaqus job=FormingJob.inp cpus=$RESCALE_CORES_PER_SLOT mp_mode=mpi interactive parallel=domain double=both output_precision=full; abaqus cae noGUI=MG_Springback.py; abaqus job=SpringbackJob.inp cpus=$RESCALE_CORES_PER_SLOT mp_mode=mpi interactive double=both output_precision=full; abaqus cae noGUI=MG_Buckling.py; abaqus job=BucklingJob.inp cpus=$RESCALE_CORES_PER_SLOT mp_mode=mpi interactive double=both output_precision=full; abaqus python PostProcessing.py;abaqus cae noGUI=Visualizer.py",
                        "reusable_job_file": "PostProcessing.py,abaqus_job.py",
                        "dynamic_job_file": "param_values.csv",
                        "pre_python": null,
                        "post_python": null,
                        "output_file": "PerfMetricsFile.csv",
                        "visualize_files": ["ShellGeometry.png",
                          "ShellGeometry_Closeup.png",
                          "FormingAnimation_Script.avi"],
                        "envVars": {"DSLS_LICENSE_FILE": "4085@novelis"}}}
              },
            "state": "IDLE",
            "on_success": ["2"],
            "on_failure": [],
            "on_complete": [],
            "retry_interval_in_sec": 0,
            "retry_count": 0
        },
        {
          "urn": "7",
          "name": "Save1",
          "description": "saving the filter widget output to assets",
          "type": "SAVE",
          "config": {
                      "type":"DATASET",
                      "config":{"name":"save_mobo_output_assets",
                                "description":"save_mobo_output_assets",
                                "scope":"GLOBAL"
                               }
                       },
          "state": "IDLE",
          "on_success": [],
          "on_failure": [],
          "on_complete": [],
          "retry_interval_in_sec": 0,
          "retry_count": 0
        }
    ],
    "start": ["1"],
    "end": ["7"]
}



# post-resscale(custom function)

import pandas as pd
import json

def custom_function(test_df: pd.DataFrame) -> dict:

    df_dropped = test_df.dropna()

    return {"df_dropped": df_dropped}



## ThermoCalc Connector

Discription: To make ThermoCalc Connector work seamlessly, you need to set up environment variables in the system. Environment variables are dynamic values that can affect the behavior of software processes. In the case of ThermoCalc Connector, these variables typically include paths to necessary files or directories, Host informations and other configuration details.

For windows:


set LSHOST=KSWNNAWPLICAP01

set TC23A_HOME=/apps/Thermo-Calc/Thermo-Calc/2023b/



For ubuntu:


export LSHOST="KSWNNAWPLICAP01"

export TC23A_HOME="/apps/Thermo-Calc/Thermo-Calc/2023b/"


Simply run these two cammands on the terminal for tesing of the termoCalc connector.
After that run the server and call the API.
```
