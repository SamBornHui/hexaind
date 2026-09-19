from app.services.workflows.designer.schemas import *

class UIWidgetType(str, Enum):

    CSV = "CSV"

    BIGQUERY = "BIGQUERY"

    FILTER = "FILTER"
    
    CUSTOM_CODE = "CUSTOM_CODE"
    
    SAVE = "SAVE"
    
    LGBM = "LGBM"

    MOBO = "MOBO"

    RESCALE = "RESCALE"

    LOOP_START = "LOOP_START"

    LOOP_END = "LOOP_END"

    APPEND = 'APPEND'

    JOIN = 'JOIN'

csv_widget_schema = WidgetRule(
    
    inputs = WidgetInputOutputs(
        count = 0,    
        config = []
    ),

    outputs = WidgetInputOutputs(
        count = 1,
        config = [
            WidgetInputOutputConfig(
                count = 1,
                expected_type = ActionResultType.DATASET,
                expected_type_constraints = DatasetConstraints(
                    sub_type = DatasetTypes.TABULAR
                )
            )
        ]
    )
)

bigquery_widget_schema = WidgetRule(

    inputs = WidgetInputOutputs(
        count = WidgetInputOutputConfigBounds(
            min=0,
            max=1
        ),
        config = [
            WidgetInputOutputConfig(
                count = 1,
                expected_type = ActionResultType.STRING,
                optional = True
            )
        ]
    ),

    outputs = WidgetInputOutputs(
        count = 1,
        config = [
            WidgetInputOutputConfig(
                count = 1,
                expected_type = ActionResultType.DATASET
            )
        ]
    )
)

filter_widget_schema = WidgetRule(

    inputs = WidgetInputOutputs(
        count = 1,
        config = [
            WidgetInputOutputConfig(
                count = 1,
                expected_type = ActionResultType.DATASET,
                expected_type_constraints = DatasetConstraints(
                    sub_type = DatasetTypes.TABULAR
                )
            )
        ]
    ),

    outputs = WidgetInputOutputs(
        count = 1,
        config = [
            WidgetInputOutputConfig(
                count = 1,
                expected_type = ActionResultType.DATASET,
                expected_type_constraints = DatasetConstraints(
                    sub_type = DatasetTypes.TABULAR
                )
            )
        ]
    )
)

custom_code_widget_schema = WidgetRule(

    inputs = WidgetInputOutputs(
        count = -1,
        config = []
    ),

    outputs = WidgetInputOutputs(
        count = -1,
        config = []
    )
)

save_widget_schema = WidgetRule(

    inputs = WidgetInputOutputs(
        count = 1,
        config = [
            WidgetInputOutputConfig(
                count = 1,
                expected_type = ActionResultType.DATASET
            )
        ]
    ),

    outputs = WidgetInputOutputs(
        count = 0,
        config = []
    )
)

lgbm_widget_schema = WidgetRule(

    inputs = WidgetInputOutputs(
        count = 1,
        config = [
            WidgetInputOutputConfig(
                count = 1,
                expected_type = ActionResultType.DATASET,
                expected_type_constraints = DatasetConstraints(
                    sub_type = DatasetTypes.TABULAR
                )
            )
        ]
    ),

    outputs = WidgetInputOutputs(
        count = 1,
        config = [
            WidgetInputOutputConfig(
                count = 1,
                expected_type = ActionResultType.MODEL
            )
        ]
    )
)

mobo_widget_schema = WidgetRule(

    inputs = WidgetInputOutputs(
        count = 1,
        config = [
            WidgetInputOutputConfig(
                count = 1,
                expected_type = ActionResultType.DATASET,
                expected_type_constraints = DatasetConstraints(
                    sub_type = DatasetTypes.TABULAR
                )
            )
        ]
    ),

    outputs = WidgetInputOutputs(
        count = 1,
        config = [
            WidgetInputOutputConfig(
                count = 1,
                expected_type = ActionResultType.DATASET,
                expected_type_constraints = DatasetConstraints(
                    sub_type = DatasetTypes.TABULAR
                )
            )
        ]
    )
)

rescale_widget_schema = WidgetRule(

    inputs = WidgetInputOutputs(
        count = 1,
        config = [
            WidgetInputOutputConfig(
                count = 1,
                expected_type = ActionResultType.DATASET,
                expected_type_constraints = DatasetConstraints(
                    sub_type = DatasetTypes.TABULAR
                )
            )
        ]
    ),

    outputs = WidgetInputOutputs(
        count = 1,
        config = [
            WidgetInputOutputConfig(
                count = 1,
                expected_type = ActionResultType.DATASET,
                expected_type_constraints = DatasetConstraints(
                    sub_type = DatasetTypes.JSON
                )
            )
        ]
    )
)

loop_start_widget_schema = WidgetRule(

    inputs = WidgetInputOutputs(
        count = 2,
        config = []
    ),

    outputs = WidgetInputOutputs(
        count = 1,
        config = []
    )
)

loop_end_widget_schema = WidgetRule(

    inputs = WidgetInputOutputs(
        count = 1,
        config = []
    ),

    outputs = WidgetInputOutputs(
        count = 2,
        config = []
    )
)
append_widget_schema = WidgetRule(
    inputs = WidgetInputOutputs(
        count = 2,
        config = [
        {
            "count": 1,
            "expected_type": "DATASET",
            "expected_type_constraints": {
            "sub_type": "TABULAR",
            "constraints": None
            },
            "optional": False
        },
        {
            "count": 1,
            "expected_type": "DATASET",
            "expected_type_constraints": {
            "sub_type": "TABULAR",
            "constraints": None
            },
            "optional": False
        }
        ]
    ),
    outputs = WidgetInputOutputs(
        count = 1,
        config = [
            {
                "count": 1,
                "expected_type": "DATASET",
                "expected_type_constraints": {
                "sub_type": "TABULAR",
                "constraints": None
                },
                "optional": False
            }
        ]
    )
)
join_widget_schema = WidgetRule(
    inputs = WidgetInputOutputs(
        count = 2,
        config = [
        {
            "count": 1,
            "expected_type": "DATASET",
            "expected_type_constraints": {
            "sub_type": "TABULAR",
            "constraints": None
            },
            "optional": False
        },
        {
            "count": 1,
            "expected_type": "DATASET",
            "expected_type_constraints": {
            "sub_type": "TABULAR",
            "constraints": None
            },
            "optional": False
        }
        ]
    ),
    outputs = WidgetInputOutputs(
        count = 1,
        config = [
            {
                "count": 1,
                "expected_type": "DATASET",
                "expected_type_constraints": {
                "sub_type": "TABULAR",
                "constraints": None
                },
                "optional": False
            }
        ]
    )
)