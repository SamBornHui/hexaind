from app.config.env_vars import environment
from app.config.resources import RESOURCES_PATH

HEXAIND_DATA = str(environment.hexaind_data)
DIR_PATH = f"{HEXAIND_DATA}/datasheet_data/datasheet_import/"
RESOURCES_PATH = str(RESOURCES_PATH)
IMPORT_PATH = f"{HEXAIND_DATA}/datasheet_data/datasheet_import/"
CONV_IMPORT_PATH = f"{HEXAIND_DATA}/datasheet_data/input/"
EXPORT_PATH = f"{HEXAIND_DATA}/datasheet_data/output/"

#for windows -  local path
# DIR_PATH = "D:/Databrick 3.0/datasheet_data/datasheet_import/"
# RESOURCES_PATH = "D:/Databrick 3.0/datasheet_data/Resources/"
# IMPORT_PATH = 'D:/Databrick 3.0/datasheet_data/datasheet_import/'
# WIN_IMPORT_PATH = './D:/Databrick 3.0/datasheet_data/datasheet_import/'
# CONV_IMPORT_PATH = 'D:/Databrick 3.0/datasheet_data/input/'
# EXPORT_PATH = 'D:/Databrick 3.0/datasheet_data/output/'