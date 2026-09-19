import shutil
from pathlib import Path

from app.config.env_vars import environment

_DUMMY_FILES_FOLDER = Path(__file__).parent.absolute()
DUMMY_FILES_FOLDER = environment.hexaind_data / "dummy_data"
DUMMY_FILES_FOLDER.mkdir(exist_ok=True, parents=True)

DUMMY_FILES = {
    "facilities": DUMMY_FILES_FOLDER / "facilities.parquet",
    "tech_nodes": DUMMY_FILES_FOLDER / "tech_nodes.parquet",
    "design_ids": DUMMY_FILES_FOLDER / "design_ids.parquet",
    "traveler_steps": DUMMY_FILES_FOLDER / "traveler_steps.parquet",
    "sensors": DUMMY_FILES_FOLDER / "sensors.parquet",
    "contexts": DUMMY_FILES_FOLDER / "contexts.parquet",
    "traces": DUMMY_FILES_FOLDER / "traces.parquet",
    "traveler_ids": DUMMY_FILES_FOLDER / "traveler_ids.parquet",
    "lot_ids": DUMMY_FILES_FOLDER / "lot_ids.parquet",
    "tools": DUMMY_FILES_FOLDER / "tools.parquet",
    "step_ids": DUMMY_FILES_FOLDER / "step_ids.parquet",
    "final_data_aggr": DUMMY_FILES_FOLDER / "final_data_aggr.parquet",
    "uc2_sigma": DUMMY_FILES_FOLDER / "uc2_sigma.parquet",
    "empty_tools": DUMMY_FILES_FOLDER / "empty" / "tools.parquet",
    "empty_step_ids_sensors": DUMMY_FILES_FOLDER / "empty"/ "stepid_sensors.parquet",
    "empty_context": DUMMY_FILES_FOLDER / "empty" / "context.parquet",
    "final_aggregate_data_context": DUMMY_FILES_FOLDER / "final_aggregate_data_context.parquet",
    "empty_final_aggregate_data_context": DUMMY_FILES_FOLDER / "empty" / "final_aggregate_data_context.parquet",
    "probe_context": DUMMY_FILES_FOLDER / "probe_context.parquet",
    "probe_datapull": DUMMY_FILES_FOLDER / "probe_datapull.parquet",
}
