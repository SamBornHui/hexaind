from kombu import Exchange, Queue, binding
from app.config.env_vars import celery_environment


ACTION_MANAGER_DEFAULT_QUEUE = "start_end"

ACTION_WORKER_DEFAULT_QUEUE = "actions"

ML_ACTIONS_DEFAULT_QUEUE = "ml_actions"

ML_ACTIONS_DEFAULT_2_QUEUE = "ml_actions_2"

MOBO_ACTION_WORKER_DEFAULT_QUEUE = "mobo_actions"

ACTIVE_LEARNING_ACTION_WORKER_DEFAULT_QUEUE = "active_learning_actions"

RESCALE_ACTION_WORKER_DEFAULT_QUEUE = "rescale_actions"

THERMOCALC_ACTION_WORKER_DEFAULT_QUEUE = "thermocalc_actions"

THERMOCALC_SUB_ACTION_WORKER_DEFAULT_QUEUE = "thermocalc_sub_actions"

GPR_ACTION_WORKER_DEFAULT_QUEUE = "gpr_actions"

GPC_ACTION_WORKER_DEFAULT_QUEUE = "gpc_actions"

AUTOML_ACTION_WORKER_DEFAULT_QUEUE = "automl_actions"

RF_ACTION_WORKER_DEFAULT_QUEUE = "rf_actions"

LINEAR_REGRESSION_ACTION_WORKER_DEFAULT_QUEUE = "linear_regression_actions"

LGBM_ACTION_WORKER_DEFAULT_QUEUE = "lgbm_actions"

XGB_ACTION_WORKER_DEFAULT_QUEUE = "xgb_actions"

CATBOOST_ACTION_WORKER_DEFAULT_QUEUE = "catboost_actions"

EXTRA_TREES_ACTION_WORKER_DEFAULT_QUEUE = "extra_trees_actions"

NN_TORCH_ACTION_WORKER_DEFAULT_QUEUE = "nn_torch_actions"

NNFASTAI_ACTION_WORKER_DEFAULT_QUEUE = "nnfastai_actions"

KNN_ACTION_WORKER_DEFAULT_QUEUE = "knn_actions"

SVM_ACTION_WORKER_DEFAULT_QUEUE = "svm_actions"

PREDICTION_ACTION_WORKER_DEFAULT_QUEUE = "prediction_actions"

MPR_ACTION_WORKER_DEFAULT_QUEUE = "mpr_actions"

DATA_CATALOG_QUEUE="data_catalog"

DATA_CATALOG_FD_TRACE_RK = "fd_trace"

CELERY_QUEUE_DEFAULT_EXCHANGE_TYPE = "direct"

ACTION_MANAGER_START_TASK_RK = "start"

ACTION_MANAGER_END_TASK_RK = "end"

ACTION_WORKER_RK = "perform_action"

ML_ACTIONS_WORKER_RK = "perform_ml_actions"

ML_ACTIONS_2_WORKER_RK = "perform_ml_actions_2"

MOBO_ACTION_WORKER_RK = "perform_mobo_action"

ACTIVE_LEARNING_ACTION_WORKER_RK = "perform_active_learning_action"

RESCALE_ACTION_WORKER_RK = "perform_rescale_action"

THERMOCALC_ACTION_WORKER_RK = "perform_thermocalc_action"

THERMOCALC_SUB_ACTION_WORKER_RK = "perform_thermocalc_sub_action"

GPR_ACTION_WORKER_RK = "perform_gpr_actions"

GPC_ACTION_WORKER_RK = "perform_gpc_actions"

AUTOML_ACTION_WORKER_RK = "perform_automl_action"

LINEAR_REGRESSION_ACTION_WORKER_RK = "perform_linear_regression_action"

RF_ACTION_WORKER_RK = "perform_rf_action"

LGBM_ACTION_WORKER_RK = "perform_lgbm_action"

XGB_ACTION_WORKER_RK = "perform_xgb_action"

CATBOOST_ACTION_WORKER_RK = "perform_catboost_action"

EXTRA_TREES_ACTION_WORKER_RK = "perform_extra_trees_action"

NN_TORCH_ACTION_WORKER_RK = "perform_nn_torch_action"

NNFASTAI_ACTION_WORKER_RK = "perform_nnfastai_action"

KNN_ACTION_WORKER_RK = "perform_knn_action"

SVM_ACTION_WORKER_RK = "perform_svm_action"

PREDICTION_ACTION_WORKER_RK = "perform_prediction_action"

MPR_ACTION_WORKER_RK = "perform_mpr_action"

EVENTS_QUEUE = "events_queue"

EVENTS_RK = "events_rk"

CUSTOM_CODE_ACTION_WORKER_DEFAULT_QUEUE = "custom_code_actions"

CUSTOM_CODE_ACTION_WORKER_RK = "perform_custom_code_action"

API_JOBS_QUEUE = "api_jobs_queue"

API_JOBS_RK = "api_jobs_rk"



broker_url = str(celery_environment.celery_broker_url)
celery_result_backend_url = str(celery_environment.celery_result_backend_url)
broker_connection_retry = celery_environment.broker_connection_retry
broker_connection_max_retries = celery_environment.broker_connection_max_retries
broker_connection_retry_delay = celery_environment.broker_connection_retry_delay
broker_connection_retry_on_startup = (
    celery_environment.broker_connection_retry_on_startup
)
task_ignore_result = celery_environment.task_ignore_result

# task messages will be acknowledged after the task has been executed, not just before (the default behavior).
task_acks_late = celery_environment.task_acks_late

# One worker taks 1 tasks from queue at a time and will increase the performance
worker_prefetch_multiplier = celery_environment.worker_prefetch_multiplier

# worker task terimination if connection lost with message broker
worker_cancel_long_running_tasks_on_connection_loss = (
    celery_environment.worker_cancel_log_running_tasks_on_connection_loss
)

# maximum number of tasks per child, this will make child process to be teriminated after executing the #of tasks mentioned below.
# It is useful to clear up memory(since killing child process)
worker_max_tasks_per_child = celery_environment.worker_max_tasks_per_child

# Define the task queues
task_queues = (
    Queue(
        ACTION_MANAGER_DEFAULT_QUEUE,
        bindings=[
            binding(
                Exchange(
                    ACTION_MANAGER_DEFAULT_QUEUE,
                    type=CELERY_QUEUE_DEFAULT_EXCHANGE_TYPE,
                ),
                routing_key=ACTION_MANAGER_START_TASK_RK,
            ),
            binding(
                Exchange(
                    ACTION_MANAGER_DEFAULT_QUEUE,
                    type=CELERY_QUEUE_DEFAULT_EXCHANGE_TYPE,
                ),
                routing_key=ACTION_MANAGER_END_TASK_RK,
            ),
        ],
    ),
    Queue(
        ACTION_WORKER_DEFAULT_QUEUE,
        bindings=[
            binding(
                Exchange(
                    ACTION_WORKER_DEFAULT_QUEUE, type=CELERY_QUEUE_DEFAULT_EXCHANGE_TYPE
                ),
                routing_key=ACTION_WORKER_RK,
            )
        ],
    ),
    Queue(
        MOBO_ACTION_WORKER_DEFAULT_QUEUE,
        bindings=[
            binding(
                Exchange(
                    MOBO_ACTION_WORKER_DEFAULT_QUEUE,
                    type=CELERY_QUEUE_DEFAULT_EXCHANGE_TYPE,
                ),
                routing_key=MOBO_ACTION_WORKER_RK,
            )
        ],
    ),
    Queue(
        ACTIVE_LEARNING_ACTION_WORKER_DEFAULT_QUEUE,
        bindings=[
            binding(
                Exchange(
                    ACTIVE_LEARNING_ACTION_WORKER_DEFAULT_QUEUE,
                    type=CELERY_QUEUE_DEFAULT_EXCHANGE_TYPE,
                ),
                routing_key=ACTIVE_LEARNING_ACTION_WORKER_RK,
            )
        ],
    ),
    Queue(
        RESCALE_ACTION_WORKER_DEFAULT_QUEUE,
        bindings=[
            binding(
                Exchange(
                    RESCALE_ACTION_WORKER_DEFAULT_QUEUE,
                    type=CELERY_QUEUE_DEFAULT_EXCHANGE_TYPE,
                ),
                routing_key=RESCALE_ACTION_WORKER_RK,
            )
        ],
    ),
    Queue(
        THERMOCALC_ACTION_WORKER_DEFAULT_QUEUE,
        bindings=[
            binding(
                Exchange(
                    THERMOCALC_ACTION_WORKER_DEFAULT_QUEUE,
                    type=CELERY_QUEUE_DEFAULT_EXCHANGE_TYPE,
                ),
                routing_key=THERMOCALC_ACTION_WORKER_RK,
            )
        ],
    ),
    Queue(
        THERMOCALC_SUB_ACTION_WORKER_DEFAULT_QUEUE,
        bindings=[
            binding(
                Exchange(
                    THERMOCALC_SUB_ACTION_WORKER_DEFAULT_QUEUE,
                    type=CELERY_QUEUE_DEFAULT_EXCHANGE_TYPE,
                ),
                routing_key=THERMOCALC_SUB_ACTION_WORKER_RK,
            )
        ],
    ),
    Queue(
        GPR_ACTION_WORKER_DEFAULT_QUEUE,
        bindings=[
            binding(
                Exchange(
                    GPR_ACTION_WORKER_DEFAULT_QUEUE,
                    type=CELERY_QUEUE_DEFAULT_EXCHANGE_TYPE,
                ),
                routing_key=GPR_ACTION_WORKER_RK,
            )
        ],
    ),
    Queue(
        GPC_ACTION_WORKER_DEFAULT_QUEUE,
        bindings=[
            binding(
                Exchange(
                    GPC_ACTION_WORKER_DEFAULT_QUEUE,
                    type=CELERY_QUEUE_DEFAULT_EXCHANGE_TYPE,
                ),
                routing_key=GPC_ACTION_WORKER_RK,
            )
        ],
    ),
    Queue(
        AUTOML_ACTION_WORKER_DEFAULT_QUEUE,
        bindings=[
            binding(
                Exchange(
                    AUTOML_ACTION_WORKER_DEFAULT_QUEUE,
                    type=CELERY_QUEUE_DEFAULT_EXCHANGE_TYPE,
                ),
                routing_key=AUTOML_ACTION_WORKER_RK,
            )
        ],
    ),
    Queue(
        RF_ACTION_WORKER_DEFAULT_QUEUE,
        bindings=[
            binding(
                Exchange(
                    RF_ACTION_WORKER_DEFAULT_QUEUE,
                    type=CELERY_QUEUE_DEFAULT_EXCHANGE_TYPE,
                ),
                routing_key=RF_ACTION_WORKER_RK,
            )
        ],
    ),
    Queue(
        LINEAR_REGRESSION_ACTION_WORKER_DEFAULT_QUEUE,
        bindings=[
            binding(
                Exchange(
                    LINEAR_REGRESSION_ACTION_WORKER_RK,
                    type=CELERY_QUEUE_DEFAULT_EXCHANGE_TYPE,
                ),
                routing_key=LINEAR_REGRESSION_ACTION_WORKER_RK,
            )
        ],
    ),
    Queue(
        LGBM_ACTION_WORKER_DEFAULT_QUEUE,
        bindings=[
            binding(
                Exchange(
                    LGBM_ACTION_WORKER_DEFAULT_QUEUE,
                    type=CELERY_QUEUE_DEFAULT_EXCHANGE_TYPE,
                ),
                routing_key=LGBM_ACTION_WORKER_RK,
            )
        ],
    ),
    Queue(
        XGB_ACTION_WORKER_DEFAULT_QUEUE,
        bindings=[
            binding(
                Exchange(
                    XGB_ACTION_WORKER_DEFAULT_QUEUE,
                    type=CELERY_QUEUE_DEFAULT_EXCHANGE_TYPE,
                ),
                routing_key=XGB_ACTION_WORKER_RK,
            )
        ],
    ),
    Queue(
        CATBOOST_ACTION_WORKER_DEFAULT_QUEUE,
        bindings=[
            binding(
                Exchange(
                    CATBOOST_ACTION_WORKER_DEFAULT_QUEUE,
                    type=CELERY_QUEUE_DEFAULT_EXCHANGE_TYPE,
                ),
                routing_key=CATBOOST_ACTION_WORKER_RK,
            )
        ],
    ),
    Queue(
        EXTRA_TREES_ACTION_WORKER_DEFAULT_QUEUE,
        bindings=[
            binding(
                Exchange(
                    EXTRA_TREES_ACTION_WORKER_DEFAULT_QUEUE,
                    type=CELERY_QUEUE_DEFAULT_EXCHANGE_TYPE,
                ),
                routing_key=EXTRA_TREES_ACTION_WORKER_RK,
            )
        ],
    ),
    Queue(
        NN_TORCH_ACTION_WORKER_DEFAULT_QUEUE,
        bindings=[
            binding(
                Exchange(
                    NN_TORCH_ACTION_WORKER_DEFAULT_QUEUE,
                    type=CELERY_QUEUE_DEFAULT_EXCHANGE_TYPE,
                ),
                routing_key=NN_TORCH_ACTION_WORKER_RK,
            )
        ],
    ),
    Queue(
        NNFASTAI_ACTION_WORKER_DEFAULT_QUEUE,
        bindings=[
            binding(
                Exchange(
                    NNFASTAI_ACTION_WORKER_DEFAULT_QUEUE,
                    type=CELERY_QUEUE_DEFAULT_EXCHANGE_TYPE,
                ),
                routing_key=NNFASTAI_ACTION_WORKER_RK,
            )
        ],
    ),
    Queue(
        KNN_ACTION_WORKER_DEFAULT_QUEUE,
        bindings=[
            binding(
                Exchange(
                    KNN_ACTION_WORKER_DEFAULT_QUEUE,
                    type=CELERY_QUEUE_DEFAULT_EXCHANGE_TYPE,
                ),
                routing_key=KNN_ACTION_WORKER_RK,
            )
        ],
    ),
    Queue(
        SVM_ACTION_WORKER_DEFAULT_QUEUE,
        bindings=[
            binding(
                Exchange(
                    SVM_ACTION_WORKER_DEFAULT_QUEUE,
                    type=CELERY_QUEUE_DEFAULT_EXCHANGE_TYPE,
                ),
                routing_key=SVM_ACTION_WORKER_RK,
            )
        ],
    ),
    Queue(
        MPR_ACTION_WORKER_DEFAULT_QUEUE,
        bindings=[
            binding(
                Exchange(
                    MPR_ACTION_WORKER_DEFAULT_QUEUE,
                    type=CELERY_QUEUE_DEFAULT_EXCHANGE_TYPE,
                ),
                routing_key=MPR_ACTION_WORKER_RK,
            )
        ],
    ),
    Queue(
        PREDICTION_ACTION_WORKER_DEFAULT_QUEUE,
        bindings=[
            binding(
                Exchange(
                    PREDICTION_ACTION_WORKER_DEFAULT_QUEUE,
                    type=CELERY_QUEUE_DEFAULT_EXCHANGE_TYPE,
                ),
                routing_key=PREDICTION_ACTION_WORKER_RK,
            )
        ],
    ),
    Queue(
        EVENTS_QUEUE,
        bindings=[
            binding(
                Exchange(EVENTS_QUEUE, type=CELERY_QUEUE_DEFAULT_EXCHANGE_TYPE),
                routing_key=EVENTS_RK,
            )
        ],
    ),
    Queue(
        DATA_CATALOG_QUEUE,
        bindings=[
            binding(
                Exchange(DATA_CATALOG_QUEUE, type=CELERY_QUEUE_DEFAULT_EXCHANGE_TYPE),
                routing_key=DATA_CATALOG_FD_TRACE_RK,
            )
        ],
    ),
    Queue(
        ML_ACTIONS_DEFAULT_QUEUE,
        bindings=[
            binding(
                Exchange(ML_ACTIONS_DEFAULT_QUEUE, type=CELERY_QUEUE_DEFAULT_EXCHANGE_TYPE),
                routing_key=ML_ACTIONS_WORKER_RK,
            )
        ],
    ),
    Queue(
        ML_ACTIONS_DEFAULT_2_QUEUE,
        bindings=[
            binding(
                Exchange(ML_ACTIONS_DEFAULT_2_QUEUE, type=CELERY_QUEUE_DEFAULT_EXCHANGE_TYPE),
                routing_key=ML_ACTIONS_2_WORKER_RK,
            )
        ],
    ),
    Queue(
        CUSTOM_CODE_ACTION_WORKER_DEFAULT_QUEUE,
        bindings=[
            binding(
                Exchange(
                    CUSTOM_CODE_ACTION_WORKER_DEFAULT_QUEUE,
                    type=CELERY_QUEUE_DEFAULT_EXCHANGE_TYPE,
                ),
                routing_key=CUSTOM_CODE_ACTION_WORKER_RK,
            )
        ],
    ),
    Queue(
        API_JOBS_QUEUE,
        bindings=[
            binding(
                Exchange(API_JOBS_QUEUE, type=CELERY_QUEUE_DEFAULT_EXCHANGE_TYPE),
                routing_key=API_JOBS_RK,
            )
        ],
    ),
)
