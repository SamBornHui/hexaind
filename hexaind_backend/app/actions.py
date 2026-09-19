from enum import Enum
class Actions(str,Enum):
    Create_workflow = "Create workflow"
    Update_workflow = "Update workflow"
    Run_workflow = "Run workflow"
    Save_workflow = "Save Workflow"
    Preview_Dataset_Result = "Preview Dataset Result"
    Preview_Model_Result = "Preview Model Result"
    Create_CPW = "Create CPW"
    Update_CPW = "Update CPW"
    EDA_visualization = "EDA visualization"
    UC2_Visualization = "UC2 Visualization"
    DC_data_download = "Data Catalog data download"