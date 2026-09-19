from app.services.AI.thermocalc.service import ThermocalcService
from app.core.dao import dao_base
from pymongo import MongoClient
from app.services.AI.thermocalc.schemas import ThermocalcConfig, ScriptFile, ThermocalcResponse
from pathlib import Path
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import pytest


# celery -A app.services.AI.thermocalc.tasks worker -n thermocalc_task_executor
# db_config = dict(db_address = '127.0.0.1' + ':27017', db_name = "Databrick")
# client = AsyncIOMotorClient(db_config['db_address'],connect=False)
@pytest.mark.fixme
def test_thermocalc():
    db_address = 'localhost:27017'
    db_name = 'Databrick'
    client = AsyncIOMotorClient(db_address, connect=False)
    thermocalc_input_payload = {
        "thermocalc_connector_id" : "conection123",
        "script_file":{
            "file_path":"/home/umer/PycharmProjects/hexaind_backend_Thermocalc_Widget/app/services/AI/thermocalc/test/baa056b7-57e9-483f-83ed-dd383f36042d.py",
            "file_name":"abced.py"},
        "input_features": ["Si", "Fe", "Cu", "Mn", "Mg", "AA_Temperature(C)", "AA_Time(min)", "CASH_PMT", "temper"],
        # "output_features": ["Si", "Fe", "Cu", "Mn", "Mg", "AA_Temperature(C)", "AA_Time(min)", "CASH_PMT",
        #                     "temper", "HO_Avg_Temp(C)", "FCC_A1", "DIAMOND_A4", "AL15SI2M4", "MG2SI_C1",
        #                     "AL9FE2SI2", "AL2CU_C16", "Q_ALCUMGSI", "AL13FE4", "ALMG_BETA", "AL6MN",
        #                     "Si_ss", "Fe_ss", "Cu_ss", "Mn_ss", "Mg_ss", "ys_cal", "pcpt_radius", "pcpt_volfrac",
        #                     "solvus_temp", "solidus_temp", "Si_pss", "Fe_pss", "Cu_pss", "Mn_pss", "Mg_pss"],
        "output_features": ["Mean","Sum","Product"],
        # "batch_size": 4,
        "json_config":{"name" : "Sample Thermocalc",
                        "batch_size" : 4
                        }
    }
    input_file_path="/home/umer/PycharmProjects/hexaind_backend_Thermocalc_Widget/app" \
                    "/services/AI/thermocalc/test/d9516b28-3fa7-4571-a0e8-e2cbff4b65fa.csv"
    thermocalc_config = ThermocalcConfig(**thermocalc_input_payload)
    thermocalc_obj =Thermocalc(db_async_client = client)
    aa = asyncio.run(thermocalc_obj.run_thermocalc(thermocalc_config,input_file_path,'userid123','projectid123'))
    print(aa)

    assert type(aa) ==ThermocalcResponse



