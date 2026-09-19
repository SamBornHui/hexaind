#!/usr/bin/env python
# coding: utf-8
from pymongo import MongoClient
import glob
import os

from app.config.env_vars import environment


HEXAIND_HOME = str(environment.hexaind_home)

configurations = {
                  "DB_NAME": "Databrick",
                  "DB_USERNAME":'',
                  "DB_PASSWORD":'',
                  "DB_IP": 'localhost',
                  "DB_PORT": 27017,
                  "HEXAIND_UI_IP": '',
                  "HEXAIND_UI_PORT": ''
                 }

env_list = set(os.environ.keys())
for i in configurations:
    if i in env_list:
        configurations[i] = os.environ.get(i)

configurations["db_address"] = f"{configurations['DB_IP']}:{configurations['DB_PORT']}"
configurations["db_name"] = configurations['DB_NAME']
configurations["db_password"] = configurations['DB_PASSWORD']
configurations["db_username"] = configurations['DB_USERNAME']
configurations["LogsPath"] = 'DefaultLogs.log'
HEXAIND_UI_IP = configurations['HEXAIND_UI_IP']
HEXAIND_UI_PORT = configurations['HEXAIND_UI_PORT']
HEXAIND_BACKEND_IP = "0.0.0.0"
if HEXAIND_UI_IP:
    SOCKETURL = 'https://{}:{}/'.format(HEXAIND_UI_IP, HEXAIND_UI_PORT)
else:
    SOCKETURL = os.environ.get('SPECIFY_THE_API_URL', None)
    if SOCKETURL is None:
        SOCKETURL = ''
    SOCKETURL = SOCKETURL + '/'
BACKEND_BATCH_URL = SOCKETURL + "imageSegmentation/downloadCompleteData?path="

MOUNT_PATH = HEXAIND_HOME

global PROGRESSCOUNT
PROGRESSCOUNT = 1

global MICRONM
mu_encode = b'\xce\xbcm'
MICRONM = mu_encode.decode(encoding='UTF-8')

MORPHOLOGYFILTERS = [{'fid':15,
                  'Name':'Opening',
                  'Value':'morphology.binary_opening',
                  'Params':{'structure_element':'reactangle','width':3,'height':10,'radius':''},
                  'Steps':3},
                      {'fid':15,
                  'Name':'Closing',
                  'Value':'morphology.binary_closing',
                  'Params':{'structure_element':'square','width':'','height':10,'radius':''},
                  'Steps':3},
                      {'fid':15,
                  'Name':'Dilation',
                  'Value':'morphology.binary_dilation',
                  'Params':{'structure_element':'square','width':'','height':10,'radius':''},
                  'Steps':3},
                      {'fid':15,
                  'Name':'Erosion',
                  'Value':'morphology.binary_erosion',
                  'Params':{'structure_element':'square','width':'','height':10,'radius':''},
                  'Steps':3}]

removeextra = glob.glob('*.pdf')
[os.remove(i) for i in removeextra]
# EXTS = ['tif','tiff' ,'png', 'bmp', 'BMP', 'jpeg', 'JPEG', 'jpg', 'JPG', 'gif', 'raw', 'webp', 'svg']

EXTS = ['tif','TIF','tiff' ,'png', 'bmp', 'BMP', 'jpeg', 'JPEG', 'jpg', 'JPG', 'gif', 'raw', 'webp', 'svg']

TESTPORT = '4060'
IMAGESPORT = '4050'
SPOCKPORT = ['4060','4040']

IngestionPort=7000
CurationPort=7001
InformaticsPort=7002
AnalyticsPort=7003

def establishConnection():
    
    db=None
    client = MongoClient(configurations["db_address"],
                         username=configurations["db_username"],
                         password=configurations["db_password"],
                         authSource=configurations["db_name"])

    db = client[configurations["db_name"]]

    return db


def fetchKeysValue(keyname, obj, defaultname=''):
    # extracting key value from object
    if keyname in obj:
        keyvalue = obj[keyname]
        del obj[keyname]
    else:
        keyvalue = defaultname
    
    return keyvalue

def addSlashonLastIndex(strr):
    if strr[-1] == '/':
        pass
    else:
        strr = strr + '/'
    return strr

def copyFile(src, dst):
    if os.path.isdir(dst):
        dst = os.path.join(dst, os.path.basename(src))
    shutil.copyfile(src, dst)
    return dst
