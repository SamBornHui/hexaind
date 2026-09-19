from PIL import Image
import os.path
import sys
import pymongo
import json
import time
import shutil
from bson.objectid import ObjectId
import csv
from math import pow , exp, pi
from datetime import datetime, date
from itertools import chain 
import shutil
# import pytesseract
# import multiprocessing
# from icecream import ic


from collections import Counter

# from flask import Flask
# from flask_restful import reqparse, Api, Resource
# from flask import request

from operator import itemgetter
import glob
import functools
import cv2
import re
import threading
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

import skimage
from skimage import io, data
from skimage.color import rgb2gray, gray2rgb, label2rgb
from skimage.feature import * 
from skimage.filters import * 
from skimage.util import *
from skimage.transform import *

from skimage import color
from skimage.exposure import *
from matplotlib import pyplot as plt
from skimage import data, io, filters, restoration, exposure, morphology, util, img_as_ubyte,img_as_float,feature, img_as_float64, segmentation

# from configurations import *
# from action_summary_common import *
# from modules_image_analysis_common import *
import pandas as pd
import warnings
warnings.filterwarnings('ignore')


global APPLICABLE

APPLICABLE = True

EXTS = ['tif','TIF','tiff' ,'png', 'bmp', 'BMP', 'jpeg', 'JPEG', 'jpg', 'JPG', 'gif', 'raw', 'webp', 'svg']
# ----Encoding N/A Samples-----
def getDataForNa(i, uimages, utyp, dirpath, na, dirName, modified_images_path,image_analysis_dao):
    try:
        img = io.imread(uimages[i], plugin='pil')
    except:
        img = io.imread(uimages[i])
    path, imgname = os.path.split(uimages[i])
    nameimg, ext = os.path.splitext(imgname)

#     dirName = dirpath + 'processedimg/'

#     dirName = checkEnv(dirName)
#     if not os.path.exists(dirName):
#         os.mkdir(dirName)    
#     else:    
#         pass

    if len(img.shape)>=3:
        height, width, _ = img.shape
    else:
        height, width = img.shape

    img = img_as_ubyte(img)        
    newp, newj = getFileNameAndPath(imgname, nameimg, ext, dirName)
    io.imsave(newp, img)
    im = cv2.resize(img, (300, 300))
    try:
        io.imsave(newj, im)
    except:
        plt.imsave(newj, im)

    newpPath = newp.replace('\\','/')
    newjPath = newj.replace('\\','/')
    mainImagePath = uimages[i]
    mainImagePath = mainImagePath.replace('\\', '/')
        
    temp = {'path':mainImagePath,'type':'--','shape':[height, width], 'ImageStripSize': 0, 'sourcecrop': 'undefined',  
            'sourcescalebar': 'undefined','pixelsize': 0, 'unit': '', 'PixelSizeX':0,'PixelSizeY':0,'image':newpPath,
              'thumpnail':newjPath ,"image_masks":[]}
    dirpath, name = os.path.split(mainImagePath)
#     modified_images_path = dirpath + '/modifiedimages'
#     modified_images_path = checkEnv(modified_images_path)
#     if not os.path.exists(modified_images_path):
#         os.mkdir(modified_images_path)    
    cropdata = cropImageUsingMetadata(temp, modified_images_path, image_analysis_dao,'categorizeAPI')
    
    temp['crop_type'] = 'manual'
    temp['manual_coordinates'] = {'x1':0,'y1':0,'x2':width,'y2':height,'w':width,'h':height,'autoCropBar':False}

    temp['manual_image'] = cropdata['path']
    temp['default_manual_image'] = cropdata['path']
    temp['manual_thumbnail'] = cropdata['modified_thumbnail']
    temp['manual_shape'] = cropdata['shape']

    temp['rotate_options'] = {'auto_rotate': False, 'manual_rotate': False, 'rotateval': 0}
    temp['scalebar_options'] = {'scalebar_type': '', 'auto_scale': '', 'auto_scale_unit': '', 'scalebarByImage': '', 'scalebarByPhysical': 0,'scalebarByPhysicalUnit':''}

    return temp   

def cropImageUsingMetadata(i, newdirpath,image_analysis_dao, callfrom=''):
    img = cv2.imread(i['path'])
    _, name = os.path.split(i['path'])
    name, ext = os.path.splitext(name)
    stripsize = i['ImageStripSize']
    if ext == '.tif' or ext == '.tiff' or ext == '.TIF':
        ext = '.png'
        
    newpathh = newdirpath + '/'+name+ext
    thumbpath  = newdirpath + '/'+'thumb_'+name+'.jpg'
    data = []
    if stripsize!=0:
        if len(img.shape) == 3:
            h,w,m=img.shape
        else:
            h,w=img.shape
        img = img[0:h-stripsize, 0:w]
        shape = [img.shape[0],img.shape[1]]
        im = cv2.resize(img, (300, 300))
        cv2.imwrite(thumbpath, im)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB) # Convert BGR to RGB
        io.imsave(newpathh, img_rgb) # Save the RGB image
        # io.imsave(newpathh, img)
    elif stripsize==0:
        shape = [img.shape[0],img.shape[1]]
        im = cv2.resize(img, (300, 300))
        cv2.imwrite(thumbpath, im)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB) # Convert BGR to RGB
        io.imsave(newpathh, img_rgb) # Save the RGB image
        # io.imsave(newpathh, img)
    else:  
        #coordinates: {x1: "188", y1: "57", w: "685", h: "692"}
        cord  = obj['coordinates']
        x1 = cord['x1']
        y1 = cord['y1']
        x2 = cord['w']
        y2 = cord['h']
        cropimg = gray2rgb(img)
        cropimg= Image.fromarray(cropimg)
        img = cropimg.crop((int(x1),int(y1),int(x2),int(y2)))
        im_thumb = cv2.resize(img, (300, 300))
        cv2.imwrite(thumbpath, im_thumb)
        img.save(+newpathh)
        im = np.array(img)
        shape = [im.shape[0],im.shape[1]]

    newpathh = newpathh.replace('\\','/')
    thumbpath  = thumbpath.replace('\\','/')
    idd = retrieveWfId(i['path'],image_analysis_dao)
    if idd:
        appliedid = retrieveProcessedWfId(i['path'],image_analysis_dao)
    else:
        appliedid = 0

    temp = {"tif_path": i['path'], 'path': newpathh, "workflow_id": idd, "modified_thumbnail":thumbpath, "applied_id": appliedid, 'shape': shape}
    data.append(temp)
    if callfrom == 'categorizeAPI':
        return temp
    else:
        return data

def getFileNameAndPath(imgname, nameimg, ext, dirName):
    if '.tif' == ext or '.TIF' == ext or '.tiff' == ext:
        newp = imgname.replace(ext, '.png')
        imgname = 'thumbnail_' + imgname 
        newj = imgname.replace(ext, '.jpg')
    else:
        newp = imgname.replace(ext, ext)
        imgname = 'thumbnail_' + imgname 
        newj = imgname.replace(ext, '.png')
    
    newp = dirName+newp
    newj = dirName+newj
    
    return newp, newj


def retrieveWfId(path,image_analysis_dao):
    # db = establishConnection()
    collection = image_analysis_dao.multiplyimagesworkflow
    
    report = collection.find_one({'image_path': path},
              sort=[( '_id', pymongo.DESCENDING )])
    if report:   
        return report['w_id']
    else:
        return 0

def retrieveProcessedWfId(path,image_analysis_dao):
    # db = establishConnection()
    collection = image_analysis_dao.workflowimagespath
    name, _ = os.path.splitext(path)
    report = collection.find_one(
                    {'sample_name': name},
                    sort=[( '_id', pymongo.DESCENDING )]
                    )
    if report:
        return str(report['_id'])
    else:
        return 0
    
#---  Saving SEM and OM Sample After identifing their category------ 
def getDataForSemAndOm(i, images, typ, metadatafiles, stripsize, dirpath, PixelSizeX, PixelSizeY, sem, om, scalevalue, popupunits, dirName, modified_images_path,image_analysis_dao):
    
    try:
        img = io.imread(images[i], plugin='pil')
    except:
        img = io.imread(images[i])
    path, imgname = os.path.split(images[i])
    nameimg, ext = os.path.splitext(imgname)
#     dirName = dirpath + 'processedimg/'
    


    img = rgbToGray(img)
    height, width = img.shape

    img = img_as_ubyte(img)        
    newp, newj = getFileNameAndPath(imgname, nameimg, ext, dirName)

    if os.path.exists(newj):
        os.remove(newj)
        os.remove(newp)
    else:
        pass    

    cv2.imwrite(newp, img, [cv2.IMWRITE_PNG_COMPRESSION, 0])
    im = cv2.resize(img, (300, 300))
    try:
        io.imsave(newj, im)
    except:
        plt.imsave(newj, im)
        
    newpPath = newp.replace('\\','/')
    newjPath = newj.replace('\\','/')
    mainImagePath = images[i]
    mainImagePath = mainImagePath.replace('\\', '/')

    temp = {'path': mainImagePath, 'type': typ[i], 'shape': [height, width], 'ImageStripSize': stripsize[i],
          'PixelSizeX':PixelSizeX[i],'PixelSizeY':PixelSizeY[i], 'image':newpPath,'thumpnail':newjPath, 'sourcecrop': 'metadata',
           'sourcescalebar': 'metadata', 'pixelsize': PixelSizeX[i],'ext':ext[1:],"image_masks": []}
    dirpath, name = os.path.split(mainImagePath)
#     modified_images_path = dirpath + '/modifiedimages'
#     modified_images_path = addSlashonLastIndex(os.path.join(dirpath, 'modifiedimages'))
#     modified_images_path = checkEnv(modified_images_path)
#     if not os.path.exists(modified_images_path):
#         os.mkdir(modified_images_path)
    
    cropdata = cropImageUsingMetadata(temp, modified_images_path, image_analysis_dao,'categorizeAPI')

    temp['crop_type'] = 'auto'
    temp['manual_coordinates'] = {'x1':0,'y1':0,'x2':width,'y2':height,'w':width,'h':height,'autoCropBar':False}
    temp['manual_image'] = ''
    temp['default_manual_image'] = ''

    temp['manual_thumbnail'] = ''
    temp['manual_shape'] = []

    temp['modified_path'] = cropdata['path']
    temp['modified_thumbnail'] = cropdata['modified_thumbnail']
    temp['modified_shape'] = cropdata['shape']
    temp['rotate_options'] = {'auto_rotate': False, 'manual_rotate': False, 'rotateval': 0}  

#     scale_type, scale, popup_unit = '', '', ''
#     if PixelSizeX[i]>0:
#         scale_type = 'auto'

#         pixel_size = PixelSizeX[i]
#         if pixel_size*1e9 <10:
#             popup_unit = 'nm'
#             scale = pixel_size*1e9
#         elif pixel_size*1e9>10:
#             popup_unit = MICRONM
#             scale = pixel_size*1e6

    temp['scalebar_options'] = {'scalebar_type': 'auto', 'auto_scale': scalevalue[i], 'auto_scale_unit': popupunits[i], 'scalebarByImage': '', 'scalebarByPhysical': 0,'scalebarByPhysicalUnit':popupunits[i]}

    if typ[i]=='SEM':
        sem.append(temp)

    elif typ[i]=='OM':
        om.append(temp)


# In[ ]:


#---- Extracting Pixle values from metadata files-------
def getPixelVal(filedata, pixleX):
    va = [i.replace(pixleX,'') for i in filedata if pixleX in i  ]
    val = ''
    a = eval(val.join(va))
    if a:
        return a
    else:
        return 0


# In[ ]:

def extractdm3data(metafile):
    try:
        dm3f = dm3.DM3(metafile)
        values = [x for x in dm3f._storedTags if x.startswith('root.ImageList.1.ImageData.Calibrations.Dimension.1.Scale')]
        scale = float(values[0][-17:])
        popupunit = [y for y in dm3f._storedTags if y.startswith('root.ImageList.1.ImageData.Calibrations.Dimension.1.Units')]
        units = popupunit[0][-2:]
        typ = [x for x in dm3f._storedTags if x.startswith('root.ImageList.1.ImageTags.Microscope Info.Illumination Mode')]
        microscope_type = typ[0][-4:]
        return scale, units, microscope_type

    except:
        return '', '', ''

#--- Categorizing Samples by looking into their metadata file---- 
def categorizeData(tiffile, dirpath, image_analysis_dao):

    sem = 'SEM'
    om = 'OM'

    typ = []
    images = []
    stripsize = []
    utyp = []
    uimages = []
    metadatafiles = []
    PixelSizeX  = []
    PixelSizeY  = []
    popupunits = []
    scalevalue = []
    for i in range(len(tiffile)):
        filee = tiffile[i]
        path = filee        
        path, extn = os.path.splitext(path)        
        extn = extn.replace('.', '-')
        path = path+ extn + '.hdr'
        dm3file = path + '.dm3'
        if os.path.exists(path):
            with open(path) as f:
                filedata = f.readlines()
                if [k for k in filedata if sem in k or 'sem' in k]:
                    key = 'SEM'
                elif [j for j in filedata if om in j or 'om' in j]:
                    key = 'OM'
                else:
                    key = 'Uncatergrize_tiff'
                
                pattern = 'ImageStripSize=[0-9]{1,3}'
                pixleX = 'PixelSizeX='
                pixleY = 'PixelSizeY='
                PixelSizeX.append(getPixelVal(filedata,pixleX))
                PixelSizeY.append(getPixelVal(filedata,pixleY))
                
                if PixelSizeX[-1]>0:
                    pixel_size = PixelSizeX[-1]
                    if pixel_size*1e9 <10:
                        popup_unit = 'nm'
                        scale = pixel_size*1e9
                    elif pixel_size*1e9>10:
                        popup_unit = MICRONM
                        scale = pixel_size*1e6
                        
                result = re.findall(pattern, str(filedata) )
                temp = re.findall(r'\d+', str(result)) 
                res = list(map(int, temp)) 
                if  key=='Uncatergrize_tiff':
                    key = 'NA'
                    utyp.append(key)
                    uimages.append(tiffile[i])
                    metadatafiles.append(filedata)
                else:
                    popupunits.append(popup_unit)
                    scalevalue.append(scale)
                    stripsize.append(res[0]) 
                    typ.append(key)
                    images.append(tiffile[i])
                    metadatafiles.append(filedata)
        
        elif os.path.exists(dm3file):
            scale, popup_unit, imtype = extractdm3data(dm3file)
            popupunits.append(popup_unit)
            scalevalue.append(scale)
            stripsize.append(0) 
            typ.append(imtype)
            images.append(tiffile[i])
            metadatafiles.append(dm3file)

        else:
            key = 'NA'
            utyp.append(key)
            uimages.append(tiffile[i])
            
    dirName = addSlashonLastIndex(os.path.join(dirpath, 'processedimg'))

    if not os.path.exists(dirName):
        os.mkdir(dirName)
        
    modified_images_path = addSlashonLastIndex(os.path.join(dirpath, 'modifiedimages'))

    if not os.path.exists(modified_images_path):
        os.mkdir(modified_images_path)
    mode = 'series'
    sem, om, na = [], [], []

    if mode == 'series':   
        if images:
            for ind in range(len(images)):
                getDataForSemAndOm(ind, images, typ, metadatafiles, stripsize, dirpath, PixelSizeX, PixelSizeY, sem, om, scalevalue, popupunits, dirName, modified_images_path,image_analysis_dao)
        elif not images:
            sem = []
            om = []
        
        for ind in range(len(uimages)):
            t = getDataForNa(ind, uimages, utyp, dirpath, na, dirName, modified_images_path,image_analysis_dao)
            na.append(t)
    else:
        if images:
            with concurrent.futures.ThreadPoolExecutor(6) as executor:
                [executor.submit(getDataForSemAndOm, ind, images, typ, metadatafiles, stripsize, dirpath, PixelSizeX,
                       PixelSizeY, sem, om, scalevalue, popupunits, dirName, modified_images_path,image_analysis_dao)  for ind in range(len(images))]

        elif not images:
            sem = []
            om = []
        with concurrent.futures.ProcessPoolExecutor(6) as executor:
            futures = [executor.submit(getDataForNa, ind, uimages, utyp, dirpath, na, dirName, modified_images_path,image_analysis_dao)  for ind in range(len(uimages))]
            concurrent.futures.wait(futures)
            na += [future.result() for future in futures]
#         for ind in range(len(uimages)):
#             t = getDataForNa(ind,uimages,utyp,dirpath,na, dirName, modified_images_path)
#             na.append(t)

    return sem, om, na


def rgbToGray(img):
    if len(img.shape)>=3:
        img = rgb2gray(img)
        return img
    else:
        return img

def getExtensionwiseData(data):
    result = {}
    for i in data:
        _ , extn = os.path.splitext(i)
        extn = extn[1:]
        if extn in result:
            result[extn] = result[extn] + 1
        else:
            result[extn] = 1
            
    return result

def addSlashonLastIndex(strr):
    if strr[-1] == '/':
        pass
    else:
        strr = strr + '/'
    return strr

def get_processing_attributes(csv_path):
    with open(csv_path, mode='r',encoding='utf-8-sig') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            # Assuming the first row contains the required metadata
            return {
                "sample_folder": row["sample_folder"],
                "Temperature_(C)": int(row["Temperature_(C)"]),
                "Time_(h)": int(row["Time_(h)"]),
                "Rupture stress_(MPa)": int(row["Rupture stress_(MPa)"]),
                "path": csv_path
            }
        
def image_save_dataset(dataset,image_analysis_dao):
    datasetpath = dataset.dataset_location[0].path
    file_path=  os.path.join(datasetpath, 'folder_struct.json')
    with open(file_path, 'r') as file:
        data = json.load(file)
    paths = data['uploaded_file_det_list']
    folders = []
    files = []
    for item in paths:
        if item['is_folder']:
            folders.append(item)
        else:
            files.append(item)
    foldersdata=[]

    for folder in folders:
        foldersdataobj={'tempsubfolderpath': folder['file_path'],
        'subfoldername':os.path.basename(os.path.normpath(folder['file_path'])),
        'selectedimages': [],
        'processing_attributes':{}
                    }
        for file in files:
            file_parent_path = os.path.dirname(file['file_path'])
            if file_parent_path == folder['file_path']:
            # if file['file_path'].startswith(folder['file_path']):
                if file['file_path'].endswith('metadata.csv'):
                    foldersdataobj['processing_attributes']= get_processing_attributes(file['file_path'])
                else:
                    foldersdataobj['selectedimages'].append(file['file_path'])
                foldersdataobj['tempsubfolderpath'] =folder['file_path']
            
                foldersdataobj['subfoldername']=os.path.basename(os.path.normpath(folder['file_path']))
        if foldersdataobj['processing_attributes'] or foldersdataobj['selectedimages']:
            foldersdata.append(foldersdataobj)
    data= {
        "_id":dataset.id,
        "connections_id":"",
        "data_type":dataset.dataset_type,
        "created_by":dataset.created_by,
        "dataset_name":dataset.name,
        "demo":False,
        "favorited_by":[],
        "file_type":"image",
        "foldersdata":foldersdata,
        "meta_data":{
            "contributors":['Databrick'],
            "description":dataset.description,
            "keywords":[],
            "schema":[]
        },
        "prefix":'PR036-D018_',
        "project_id": dataset.project_id,
        "remote_server": False,
        "source":"Local Drive",
        "user_id":dataset.user_id
    }
    
    datasetSave = imagesDatasetSave(data,image_analysis_dao)
    
    return datasetSave

def extract_image_paths(file_paths):
    image_extensions = [
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif", ".webp",
    ".svg", ".ico", ".heif", ".heic", ".raw", ".cr2", ".nef", ".orf", ".sr2"
    ]
    return [path for path in file_paths if any(path.lower().endswith(ext) for ext in image_extensions)]


def imageCategorizationUpdateDataset(dataset, new_folder_path, new_file_path, image_analysis_dao):
    dirpath = new_folder_path
    image_paths = extract_image_paths(new_file_path)
    categorizeData(image_paths, dirpath, image_analysis_dao)
    foldersdata = []
    foldersdataobj={'tempsubfolderpath': dirpath,
        'subfoldername':os.path.basename(os.path.normpath(dirpath)),
        'selectedimages': image_paths,
        'processing_attributes':{}
                    }
    foldersdata.append(foldersdataobj)
    obj ={
        "newfoldersdata": foldersdata,
        "datasetid": dataset.id,
        "remote_server": False,
    }
    updated_folder = updateFolderInDataset(obj,image_analysis_dao)
    return

def imageCategorization(dataset,image_analysis_dao):
    datasetpath = dataset.dataset_location[0].path
    file_path=  os.path.join(datasetpath, 'folder_struct.json')
    with open(file_path, 'r') as file:
        data = json.load(file)
    files= data['uploaded_file_det_list']
    cate_obj = {
        "images": [],
        "dataset_name": "",
        "modified": "",
        "demo": "",
        "main_file": "",
        "api_type": "upload"
    }
    for item in files:
        if item['is_folder'] or 'csv_metadata' in item['file_path']:
            directory_path = get_directory_path(item['file_path'], item['is_folder']) # Ensure path ends with '/'
            folder_id = os.path.basename(os.path.normpath(directory_path))
            folder_name = folder_id
            # folder_id = os.path.basename(os.path.normpath(item['file_path']))
            cate_obj['images'].append({
                "path": directory_path,
                "folderId": folder_id,
                "folderName": folder_id
            })
    imageCategorization= imageCategorizationProcess(cate_obj,image_analysis_dao)
    categorized_data = imagesData(imageCategorization)
    return categorized_data

def imagesData(data):
    folders_data = []

# Process each item in the data
    for item in data:
        na_data = json.loads(item['NA'])
        sem_data = json.loads(item['SEM'])
        om_data = json.loads(item['OM'])
        combined_data = na_data + sem_data + om_data
        
        images_data = {
            "images": combined_data,
            "extscount": item['extscount'],
            "folderId": item['folderId'],
            "metadatainfo": item['metadatainfo'],
            "tempPath": item['tempPath']
        }
        
        folders_data.append(images_data)
    return folders_data

def get_directory_path(file_path, is_folder):
    if is_folder:
        return file_path
    else:
        return os.path.dirname(file_path) + '/'
    
def imageCategorizationProcess(obj,image_analysis_dao):
    tifdata = obj['images']
    filepath = obj['main_file']
    name = obj['dataset_name']
    modified = obj['modified']
    api_type = obj['api_type']
    demo = obj['demo']
    dataset_id = ''
    try: 
        dataset_id = obj['dataset_id']
    except:
        pass
    data = []
    dbdata = []

    metadata = glob.glob(filepath+"*.xlsx") 
    try:   
        call_batch = obj['backgroundBatch']
        user_id = obj['userId']
    except:

        call_batch = False
        
    metadatafolder = list(filter(lambda i: i['folderName'] == 'metadata', tifdata))
    tifdata = list(filter(lambda i: i['folderName'] != 'metadata', tifdata))
    if metadatafolder:
        mpath = metadatafolder[0]['path']
        csvpath = glob.glob(mpath+'*.csv')
        try:
            df = pd.read_csv(csvpath[0])
        except:
            csvpath = None
    else:
        csvpath = None 
    
    collection = image_analysis_dao.categorizeddata
    maindata = []
    alldata = []
    foldernames = []
    # modified ='yes'
    # if modified =='no':
    #     report = collection.find_one(
    #                     {'dataset_name': name},
    #                     sort=[( '_id', pymongo.DESCENDING )]
    #                     )
    #     data = report['data']
    
    # else:
    for i in range(len(tifdata)):
        tiffile=[]
        pathh = tifdata[i]['path']
        folderid  = tifdata[i]['folderId']
        fname = tifdata[i]['folderName']
        
        tiffile = [(glob.glob(pathh+'/*.'+ext )) for ext in EXTS]
        tiffile = list(chain.from_iterable(tiffile))
        extdata = getExtensionwiseData(tiffile)
#             
        sem, om, na = categorizeData(tiffile, pathh, image_analysis_dao)
        alldata += sem + om + na
#            
        foldernames.append(tifdata[i]['folderName'])
        
        t  = ''
        tem = ''
        keyword = []
        metainfo = {}
        if csvpath:
#                 
            metadatarow = df[df.iloc[:,0] == fname]

            metadatarow = metadatarow.to_dict('records')
            metainfo = metadatarow[0]                
            metainfo['path'] = csvpath[0]
        else:
            metainfo['foldername'] = fname
        
        folderdata  = {'SEM': json.dumps(sem), 'OM': json.dumps(om), 'NA': json.dumps(na), 'folderId': folderid, 
        'Temperature': 0, 'Time': 0, 'keywords': '', 'extscount': extdata,'tempPath':pathh, 'batch': 0, 'workflow': 0,
                        'metadatainfo': metainfo}

        category = ""
        if len(sem)>0:
            category = 'SEM'
        elif len(om)>0:
            category = 'OM'
        else:
            category = "NA"

        folderdata['category'] = category            
        data.append(folderdata)

        if api_type=='create_dataset':
            report = collection.find_one({'dataset_id': dataset_id, 'folderId': folderid})
            if not report:
                insertdata  = {'dataset_id':dataset_id, 'folderId': folderid, 'Temperature': 0, 'Time': 0, 'keywords': '',
                                'extscount': extdata,'tempPath':pathh, 'category': category,'batch': 0, 'workflow': 0,
                                "data":{'SEM': sem, 'OM': om, 'NA': na}}
                rec_id2 = collection.insert_one(insertdata)
            else:
#                     
                rdata = report['data']
                rdata['SEM'] = sem
                rdata['OM'] = om    
                rdata['NA'] = na
                
                result = collection.update_one( 
                {"dataset_id":dataset_id, 'folderId': folderid}, 
                { "$set":{ "data":rdata, "extscount": extdata}})
    

    return data


def insertExtnwiseData(i, extn, data):
    result = {}
    exist = list(filter(lambda val: val['type'] == extn, data))
    if exist:
        result = exist[0]
        result[extn] = result[extn] + 1
        sizekey = 'size'
        sizefile = os.path.getsize(i)
        tempsize = result[sizekey]
        tempsize = tempsize + sizefile
        result[sizekey] = tempsize
    else:
        result[extn] = 1
        sizekey = 'size'
        sizefile = os.path.getsize(i)
        result[sizekey] = sizefile
        result['type'] = extn
        data.append(result)

def imagesdetail(obj):
    data = []
    images = obj['images']
    for im in images:
        i = im['path']
        mpath , mextn = os.path.splitext(i)
        extn = mextn[1:]
        insertExtnwiseData(i, extn, data)
        
        mextn = mextn.replace('.', '-')
        mpath = mpath + mextn + '.hdr'
        if os.path.isfile(mpath):
            insertExtnwiseData(mpath, 'hdr', data)
        
        
    totalsize = 0
    for i in data:
        i['bytesize'] = i['size']
        totalsize += i['bytesize']
        t = get_printable_size(i['size'])      
        i['size'] = t

    returnData = {
        "files" : data,
        "totalsize": get_printable_size(totalsize)
    }
          
    return returnData



def copyProcessedimgDirData(img, path, remote_server):
    path = os.path.join(path, 'processedimg')
    if not os.path.exists(path):
        os.mkdir(path)
        
    p, imgname = os.path.split(img)
    p = os.path.join(p, 'processedimg')
    name, ext = os.path.splitext(imgname)
    
    if '.tif' == ext or '.TIF' == ext or '.tiff' == ext:
        orig = imgname.replace(ext, '.png')
        imgname = 'thumbnail_' + imgname 
        thumb = imgname.replace(ext, '.jpg')
    else:
        orig = imgname.replace(ext, ext)
        imgname = 'thumbnail_' + imgname 
        thumb = imgname.replace(ext, '.png')
    
    origpath = os.path.join(p, orig)
    thumbpath = os.path.join(p, thumb)
    if not remote_server:
        origpath =  copyFile(origpath, path)
        thumbpath  = copyFile(thumbpath, path)
    return origpath, thumbpath




def createMetadatadict(metadatainfo, df, foldername):
#     metadatarow = df.loc[df.sample_folder == foldername]
    df_row = df[df.iloc[:,0] == foldername]
    metadatarow = df_row.to_dict('records')[0]
    col = list(metadatarow)
    if not metadatainfo:
        metadatainfo['sample_id'] = [foldername]
        col.pop(0)
        for c in col:
            try:
                metadatainfo[c] = [metadatarow[c]]
            except:
                metadatainfo[c] = ['']
    else:
        metadatainfo['sample_id'] += [foldername]
        col.pop(0)
        for c in col:
            try:
                metadatainfo[c] += [metadatarow[c]]
            except:
                metadatainfo[c] += ['']

    return metadatainfo, df_row


def getmetadatapath(p):
    p = removeSlashonLastIndex(p)
    p, _ = os.path.split(p)
    metap = p + '/metadata'
    if os.path.isdir(metap):
        return metap
    else:
        return ''


def removeSlashonLastIndex(path):
    if path[-1]=='/':
        path, _ = os.path.split(path)
        return path
    else:
        return path  
    
def removeOtherDatasetData(data):
    db = establishConnection()
    for i in data['foldersdata']:
        [deleteRemainingData(j['orignalpath'], db) for j in i['selectedimages']]
    collection = db.categorizeddata
    collection.delete_many({'dataset_id': data['_id']})
    collection = db.actionsummary
    deletekey = data['user_id'] + '.' + data['_id']
    report = collection.find( { deletekey : { "$exists" : True } })
    for i in report:    
        del i[data['user_id']][data['_id']]
        collection.update_one(
            {"_id":i['_id']}, 
            { "$set": i})
    

    
def deleteImagesData(obj):
    deltype = obj['type']
    
    if deltype == 'folder':
        subfoldername = obj['foldername']
        datasetid = obj['id']
        db = establishConnection()
        collection = db.DMCreatedDatasets
        report = collection.find_one({'_id': ObjectId(datasetid)})
        folderdata = (list(filter(lambda val: val['subfoldername'] == subfoldername, report['foldersdata'])))
        # for i in folderdata[0]['selectedimages']:
        #     deleteRemainingData(i['orignalpath'], db)

        [deleteRemainingData(i['orignalpath'], db) for i in folderdata[0]['selectedimages']]
        
        # removed from categorize collection
        collection = db.categorizeddata
        collection.delete_one({'dataset_id': str(report['_id']), 'folderId': subfoldername})
        
        #removed from metadatafile
        metadata = fetchKeysValue('metadata', report)
        if metadata:
            df = pd.read_csv(report['metadata'])
            df_filtered = df[df.iloc[:,1] != subfoldername]
            df_filtered.to_csv(report['metadata'], index=False)
        
        #remove physical data
        folderpath = folderdata[0]['path']
        if os.path.exists(folderpath):
            shutil.rmtree(folderpath)

        
        #update total datapoints and size
        report['kbsize'] = report['kbsize'] - folderdata[0]['kbsize']
        report['datapoints'] = report['datapoints'] - folderdata[0]['datapoints']
        report['size'] = get_printable_size(report['kbsize'])
        
        #removed from DMCreatedDatasets collection
        keepfolderdata = (list(filter(lambda val: val['subfoldername'] != subfoldername, report['foldersdata'])))
        report['foldersdata'] = keepfolderdata
        collection = db.DMCreatedDatasets
        _id = str(report['_id'])
        deleteObjectbyId(_id, collection)
        collection.insert_one(report)
        report['_id'] = str(report['_id'])
        msg = f" Delete subfolder '{subfoldername}' "
        actionSummary({'datasetid': report['_id'], 'msg': msg, 'userid': report['user_id']}, 'curationsummary')
        return report
    



def readMetadataDF(metadatapath):
    if metadatapath:
            csvpath = glob.glob(metadatapath +'/*.csv')
            try:
                df = pd.read_csv(csvpath[0])
                return df, csvpath
            except:
                pass
    
    return None, None



def datasetMetadataInfo(obj):
    folder_name = obj['folder_name']
    user_id = obj['user_id']
    dataset_preview = obj['dataset_preview']
    change_in_df = False
    temp = []
    if 'metadata' not in obj:
        for i in folder_name:
            temp.append({'Foldername': i})
        
    else:
        folder_name = obj['folder_name']
        metadata = obj['metadata']
        df = pd.read_csv(metadata, keep_default_na=False)
        df.rename(columns = {'sample_folder':'Foldername'}, inplace = True)
        Foldernames = df['Foldername'].to_list()
        for i in folder_name:
            if i not in Foldernames:
                folder_dict = dict.fromkeys(list(df.head(1)), '')
                folder_dict['Foldername'] = i
                temp.append(folder_dict)
                change_in_df = True
            else:
                folder_metadata = df[df.iloc[:,0] == i].to_dict('records')
                temp += folder_metadata
        
    if change_in_df:
        df = pd.DataFrame.from_dict(temp)
        df.to_csv(metadata, index=False)
    data = dict(status = True, data = temp)
    return data

def fetchKeysValue(keyname, obj):
    if keyname in obj:
        value = obj[keyname]
    else:
        value = None
        
    return value
    
def copyFile(src, dst):
    if os.path.isdir(dst):
        dst = os.path.join(dst, os.path.basename(src))
    shutil.copyfile(src, dst)
    return dst
    
def imagesDatasetSave(obj,image_analysis_dao):
    categorizationInput = []    
    collection = image_analysis_dao.DMCreatedDatasets
    obj['foldersdata'].sort(key=lambda f: f['tempsubfolderpath'])
    remote_server = fetchKeysValue('remote_server', obj) 
    if remote_server:
        for i in obj['foldersdata']:
            selectedimages = []
            for j in range(len(i['selectedimages'])):
                if i['selectedimages'][j][-3:]!='hdr':
                    selectedimages.append(i['selectedimages'][j])
            i['selectedimages'] = selectedimages
    foldersdata = obj['foldersdata']
#     metadatapath = list(filter(lambda i: i['subfoldername'] == 'metadata', foldersdata))
    foldersdata = list(filter(lambda i: i['subfoldername'] != 'metadata', foldersdata))
    p = foldersdata[0]['tempsubfolderpath']
    temporarypath = foldersdata[0]['tempsubfolderpath']
    metadatapath = getmetadatapath(temporarypath)
    
    user_id = obj['user_id']
    csvpath = None         
    datasetid = fetchKeysValue('datasetid', obj)

    if remote_server:
        parentpath , _ = os.path.split(p)
        df, csvpath = readMetadataDF(metadatapath)
    else:
        while(1):
            if os.path.basename(p) == "datasets":
                p = os.path.join(p, 'image_datasets_2_0')
                os.makedirs(p, exist_ok=True)
                break
            else:
                p, _ = os.path.split(p)
        if datasetid:
            parentpath = obj['parentpath']
        else:
            parentname = obj['dataset_name'] + str(int(round(time.time() * 1000)))
            p = addSlashonLastIndex(p)
            parentpath = p + parentname
            if not os.path.exists(parentpath):
                os.mkdir(parentpath)
            df, csvpath = readMetadataDF(metadatapath)

    parentpath = addSlashonLastIndex(parentpath)    
    totalcount = 0
    totalsizefile = 0
    metadatainfo = {}
    imagesnamelist = []
    for i in foldersdata:
        categorization_data = {}
        tempdata = []
        foldercount = len(i['selectedimages'])
        foldername = i['subfoldername']
        subpath = parentpath + foldername
        if not os.path.exists(subpath):
            os.mkdir(subpath)
        subpath = addSlashonLastIndex(subpath)
        categorization_data['path'] = subpath
        categorization_data['folderId'] = foldername
        categorization_data['folderName'] = foldername
        sizefiles = 0
        typefiles = []
        i['selectedimages'] = sorted(i['selectedimages'])
        for im in i['selectedimages']:
            if csvpath:
                metadatainfo, folder_metadata = createMetadatadict(metadatainfo, df, i['subfoldername'])
                metadata_filename = foldername + '_metadata.csv'
                folder_metadata_path = os.path.join(subpath, metadata_filename)
                folder_metadata.to_csv(folder_metadata_path, index=False)
            imagesnamelist.append(os.path.basename(os.path.splitext(im)[0]))
            if remote_server:
                orig = im
            else:
                orig = copyFile(im, subpath)
                mpath, mextn = os.path.splitext(im)
                typefiles.append(mextn[1:].upper())
                mextn = mextn.replace('.', '-')
                mpath = mpath+ mextn + '.hdr'
                if os.path.isfile(mpath):
                    copyFile(mpath, subpath)

            convertedp, thumb = copyProcessedimgDirData(im, subpath, remote_server)
            tempdata.append({'orignalpath': orig, 'convertedpath': convertedp, 'thumbnailpath': thumb}) 
            sizefiles = sizefiles + os.path.getsize(im)
        totalsizefile += sizefiles
        i['foldersize'] = get_printable_size(sizefiles)
        i['kbsize'] = sizefiles
        i['foldertype'] = list(set(typefiles))
        i['selectedimages'] = tempdata
        i['path'] = subpath
        i['datapoints'] = foldercount
        totalcount += foldercount
        if not remote_server:
            del i['tempsubfolderpath']
        categorizationInput.append(categorization_data)
    obj['datapoints'] = totalcount
    obj['path'] = parentpath    
    obj['size'] = get_printable_size(totalsizefile)
    obj['kbsize'] = totalsizefile
    obj['curated'] = False
    obj['last_access'] = datetime.now()
    
    if 'segment' in obj['dataset_name'].lower():
        obj['Segmented'] = True
        
    if csvpath:
        imgid = list(range(1,totalcount+1))
        df2 = pd.DataFrame.from_dict(metadatainfo)
        df2.insert(0, "image_id", imgid)
        df2.insert(2, "sample_name", imagesnamelist)
        metadir = parentpath + 'metadata'
        if not os.path.exists(metadir):
            os.mkdir(metadir)
        aggregated_csv = obj['dataset_name'] + '_aggregated.csv'
        newcsvpath = os.path.join(metadir, aggregated_csv)
        df2.to_csv(newcsvpath, index=False, float_format='%g')
        obj['aggregated_metadata'] = newcsvpath
        metadata = shutil.copy(csvpath[0], metadir)
        obj['metadata'] = metadata
    if not datasetid:
        obj['_id'] = ObjectId(obj['_id']) 
        rec_id2 = collection.insert_one(obj)
        obj['_id'] = str(obj['_id'])
        dn = obj['dataset_name']
        msg = f" Created "
        # actionSummary({'datasetid': obj['_id'], 'msg': msg, 'userid': obj['user_id']})
    else:
        obj['_id'] = datasetid
    
    
    #shutil.rmtree(temporarypath)
    inpObj = {"dataset_id":obj['_id'],"images":categorizationInput,"main_file":parentpath,"dataset_name":obj['dataset_name'],
              "modified":"yes","demo":False,"api_type":"create_dataset"}

    imageCategorizationProcess(inpObj,image_analysis_dao)

    return obj


def moreDetail(obj):
    db = establishConnection()
    _id = obj['id']
    collection = db.DMCreatedDatasets
    data = retrieveObjectbyId(_id, collection)
    return data

def get_printable_size(byte_size):
    BASE_SIZE = 1024.00
    MEASURE = ["B", "KB", "MB", "GB", "TB", "PB"]
 
    def _fix_size(size, size_index):
        if not size:
            return "0"
        elif size_index == 0:
            return str(size)
        else:
            return "{:.3f}".format(size)
 
    current_size = byte_size
    size_index = 0
 
    while current_size >= BASE_SIZE and len(MEASURE) != size_index:
        current_size = current_size / BASE_SIZE
        size_index = size_index + 1
 
    size = _fix_size(current_size, size_index)
    measure = MEASURE[size_index]
    return size +" "+measure

def deleteObjectbyId(_id, collection):
     collection.delete_one({'_id': ObjectId(_id)})


def getUsername(_id, collection):
    report = collection.find_one({'_id': ObjectId(_id)})
    return report['firstName']+' '+report['lastName']

def objectidToStr(data):
    data['_id'] = str(data['_id'])
    return data

def getactionsummary(obj):
    try:
        datasetid = obj['datasetid']
    except:
        datasetid = obj['dataset_id']
    db = establishConnection()
  
    collection = db.actionsummary
    report = collection.find( {'dataset_id':  datasetid})
    actions = [objectidToStr(i) for i in report]
    collection = db.curationsummary
    report = collection.find( {'dataset_id':  datasetid})
    curations = [objectidToStr(i) for i in report]
    if actions:
        last_mod = actions[0].copy()
    else:
        return {'status': True, 'action': [], 'curation': []}
    if curations:    
        last_mod['date'] = curations[-1]['date']
        last_mod['user_name'] = curations[-1]['user_name']
        last_mod['user_id'] = curations[-1]['user_id']
        
    last_mod['action'] = "Last Modified"
    actions.append(last_mod)

    return {'status': True, 'action': actions, 'curation': curations}


def updateImagesInDataset(obj):
    _id = obj['datasetid']
    db = establishConnection()
    collection = db.DMCreatedDatasets
    obj3 = retrieveObjectbyId(_id, collection)
    obj['parentpath'] = obj3['path']
    obj2 = imagesDatasetSave(obj)
    
    obj = obj3
    totalcountnew = 0
    totalsizenew = 0
    subfoldername = ''
    sampleimages = []
    for i in obj['foldersdata']:
        fdata = list(filter(lambda val: val['subfoldername'] == i['subfoldername'], obj2['foldersdata']))
        if fdata:
            subfoldername = i['subfoldername']
            temp = i['selectedimages']  
            i['selectedimages'] += fdata[0]['selectedimages']
            sampleimages = fdata[0]['selectedimages']
            t = len(fdata[0]['selectedimages'])
            i['datapoints'] += t
            totalcountnew += t
            i['foldertype'] += fdata[0]['foldertype']
            i['foldertype'] = list(set(i['foldertype']))
            i['kbsize'] += fdata[0]['kbsize']
            i['foldersize'] = get_printable_size(i['kbsize'])
            totalsizenew = fdata[0]['kbsize']
            
    
    metadata = fetchKeysValue('metadata', obj)
    if metadata:
        df = pd.read_csv(metadata)
        idx = df.index[df.iloc[:,1] == subfoldername].tolist()
        newindex = idx[-1] + 1
        existdata = df.loc[newindex-1]
        existdata = existdata.to_dict()
        for i in sampleimages:
            i = os.path.basename(os.path.splitext(i['orignalpath'])[0])
            existdata[list(existdata)[2]] = i
            newline = pd.DataFrame(existdata, index=[newindex])
            df2 = pd.concat([df.iloc[:newindex], newline, df.iloc[newindex:]]).reset_index(drop=True)
            df = df2
            newindex += 1
        totalcount = df2.shape[0]
        imgid = list(range(1,totalcount+1))
        df2["image_id"] =  imgid
        df2.to_csv(metadata, index=False)

    obj['datapoints'] += totalcountnew 
    obj['kbsize'] += totalsizenew
    obj['size'] = get_printable_size(obj['kbsize'])
    deleteObjectbyId(_id, collection)
    obj['_id'] = ObjectId(obj['_id'])
    rec_id2 = collection.insert_one(obj)
    obj['_id'] = str(obj['_id'])
    
    msg = f"Add Images in '{subfoldername}' "
    actionSummary({'datasetid': obj['_id'], 'msg': msg, 'userid': obj['user_id']}, 'curationsummary')
    return obj


def updateFolderInDataset(obj,image_analysis_dao):
    _id = obj['datasetid']
    # db = establishConnection()
    collection = image_analysis_dao.DMCreatedDatasets
    data = collection.find_one({'_id':ObjectId(_id)})
    parentpath = data['path']
    obj['newfoldersdata'].sort(key=lambda f: f['tempsubfolderpath'])
    newfolder = obj['newfoldersdata']
    newcsvpath = glob.glob(newfolder[0]['tempsubfolderpath'] + '*.csv')
    if newcsvpath:
        newdf = pd.read_csv(newcsvpath[0])
    remote_server = fetchKeysValue('remote_server', obj)
    metadatainfo = {}
    categorizationInput = []    
    totalcount = 0
    totalsizefile = 0   
    imagesnamelist = []
    foldername = ''
    for i in newfolder:
        categorization_data = {}
        tempdata = []
        foldercount = len(i['selectedimages'])
        foldername = i['subfoldername']
        subpath = parentpath + foldername
        if not os.path.exists(subpath):
            os.mkdir(subpath)
        subpath = addSlashonLastIndex(subpath)
        categorization_data['path'] = subpath
        categorization_data['folderId'] = foldername
        categorization_data['folderName'] = foldername
        sizefiles = 0
        typefiles = []
        i['selectedimages'] = sorted(i['selectedimages'])
        for im in i['selectedimages']:
            if newcsvpath:
                metadatainfo = createMetadatadict(metadatainfo, newdf, i['subfoldername'])
            
            imagesnamelist.append(os.path.basename(os.path.splitext(im)[0]))
            orig = copyFile(im, subpath)
            mpath, mextn = os.path.splitext(im)
            typefiles.append(mextn[1:].upper())
            mextn = mextn.replace('.', '-')
            mpath = mpath+ mextn + '.hdr'
            if os.path.isfile(mpath):
                copyFile(mpath, subpath)    
            convertedp, thumb = copyProcessedimgDirData(im, subpath, remote_server)
            tempdata.append({'orignalpath': orig, 'convertedpath': convertedp, 'thumbnailpath': thumb}) 
            sizefiles = sizefiles + os.path.getsize(im)
        totalsizefile += sizefiles
        i['foldersize'] = get_printable_size(sizefiles)
        i['kbsize'] = sizefiles
        i['foldertype'] = list(set(typefiles))
        i['selectedimages'] = tempdata
        i['path'] = subpath
        i['datapoints'] = foldercount
        totalcount += foldercount
        del i['tempsubfolderpath']
        categorizationInput.append(categorization_data)

    dpoint = data['datapoints']
    data['datapoints'] = data['datapoints'] + totalcount
    data['size'] = get_printable_size(data['kbsize'] + totalsizefile)
    data['kbsize'] = data['kbsize'] + totalsizefile

    data['foldersdata'] += newfolder
    if newcsvpath:
        df2 = pd.DataFrame.from_dict(metadatainfo)
        metadir = parentpath + 'metadata'
        if not os.path.exists(metadir):
            os.mkdir(metadir)
        if fetchKeysValue('metadata', data):
            imgid = list(range(dpoint+1,dpoint+totalcount+1))
            df2.insert(0, "image_id", imgid)
            df2.insert(2, "sample_name", imagesnamelist)
            df = pd.read_csv(data['metadata'])
            df2 = pd.concat([df, df2])
            df2.to_csv(data['metadata'], index=False)
        else:
            imgid = list(range(1,totalcount+1))
            df2.insert(0, "image_id", imgid)
            df2.insert(2, "sample_name", imagesnamelist)
            newcsvpath = metadir + '/' + obj['dataset_name'] + '.csv'
            df2.to_csv(newcsvpath, index=False)
            obj['metadata'] = newcsvpath


    # shutil.rmtree(temporarypath)
    inpObj = {"dataset_id":_id,"images":categorizationInput,"main_file":parentpath,"dataset_name":data['dataset_name'],
              "modified":"yes","demo":False,"api_type":"create_dataset"}
    imageCategorizationProcess(inpObj,image_analysis_dao)

    deleteObjectbyId(_id, collection)
    data['_id'] = ObjectId(data['_id'])
    rec_id2 = collection.insert_one(data)
    data['_id'] = str(data['_id'])
    
    msg = f"Add data '{foldername}' "
    # actionSummary({'datasetid': data['_id'], 'msg': msg, 'userid': data['user_id']}, 'curationsummary')

    return data


def updateDataset(obj):
    dtyp = fetchKeysValue('type', obj)
    if dtyp == 'folder':
        data = updateFolderInDataset(obj)
    else:
        data = updateImagesInDataset(obj)
    
    return data



def datetimeToTimestamp(obj):
    """Default JSON serializer."""
    import calendar, datetime

    if isinstance(obj, datetime.datetime):
        if obj.utcoffset() is not None:
            obj = obj - obj.utcoffset()
        millis = int(
            calendar.timegm(obj.timetuple()) * 1000 +
            obj.microsecond / 1000
        )
        return millis
    raise TypeError('Not sure how to serialize %s' % (obj,))


def getMaterialsInfo(obj):
    project_id = obj['project_id']
    user_id = obj['user_id']
    db = establishConnection()
    data = db.DMCreatedDatasets.find({'project_id': project_id, 'data_type': 'image'})
    response = []
    for i in data:
        for folder in i['foldersdata']:
            response.append({'dataset_name':  i['prefix']+i['dataset_name'], 'material': folder['subfoldername'], 'created_by': i['created_by'], 'created_date': json.dumps(i['last_access'], default=datetimeToTimestamp)})

    return {'status': True, 'data': response}



def extractDataFromPath(obj):
    path = obj['path']
    subfolders = obj['subfolders']
    subdirs = []
    if subfolders:
        subdirs = [f.path for f in os.scandir(path) if f.is_dir() and 'ipynb_checkpoints' not in f.path]
        imgs = glob.glob(path+'/*')
        imgs = list(chain.from_iterable([glob.glob(t + '/*') for t in imgs]))
    else:
        subdirs.append(path)
        imgs = [(glob.glob(path+'*.'+img )) for img in EXTS]
        imgs = list(chain.from_iterable(imgs))

    data = {}
    for i in imgs:
        extn = (os.path.splitext(i)[1])[1:].upper()
        if extn in data:
            data[extn] += [{'name': os.path.split(i)[1], 'size': get_printable_size(os.path.getsize(i)), 'path': i, 'foldername': os.path.basename(os.path.split(i)[0]), 'folderpath': os.path.split(i)[0]}]
        else:
            data[extn] = [{'name': os.path.split(i)[1], 'size': get_printable_size(os.path.getsize(i)), 'path': i, 'foldername': os.path.basename(os.path.split(i)[0]), 'folderpath': os.path.split(i)[0]}]
    
    images = []
    for i in subdirs:
        images.append({'path': i, 'folderId': os.path.basename(i), 'folderName': os.path.basename(i)})
    
    inputobj = {'images': images, 'dataset_name': '', 'modified': '', 'demo': '', 'main_file': '', 'api_type': 'upload'}    
    background_thread = threading.Thread(target=imageCategorization, args=(inputobj,))
    background_thread.start()
    
    if '' in data:
        del data['']
    
    return {'status': True, 'data': data}  


def getcropandsegmentdata(db, i):
    for j in i['img_details']:
        collection = db.workflowimagespath
        searchval, _ = os.path.splitext(j['path'])
        report = collection.find_one({'sample_name': searchval})
        if report:
            collection2 = db.sampleworkflows
            report2 = collection2.find_one({'_id': ObjectId(report['workflow_id'])})
            j['wfname'] = report2['Wname']
            j['cropimg'] = report['data']['cropimg']
            j['segmented_img'] = report['data']['segmented_img']
            j['crop_thumb'] = report['data']['crop_thumb']
            j['segmented_imgthumb'] = report['data']['segmented_imgthumb']
        else:
            j['wfname'] = ''
            j['cropimg'] = ''
            j['segmented_img'] = ''
            j['crop_thumb'] = ''
            j['segmented_imgthumb'] = '' 
            
def get_categorization_data(dataset_id, image_analysis_dao):
    # dataset_id = obj['dataset_id']

    response_data = []
   
    collection = image_analysis_dao.categorizeddata
    get_all_data = collection.find({'dataset_id': dataset_id})

    for get_data in get_all_data:
        get_data['_id'] = str(get_data['_id'])
        images_data = []
        semdata = get_data['data']['SEM']
        omdata = get_data['data']['OM']
        nadata = get_data['data']['NA']
        if(len(semdata)>0):
            for j in range(len(semdata)):
                get_data['data']['SEM'][j]['category'] = 'SEM'
        if(len(omdata)>0):
            for j in range(len(omdata)):
                get_data['data']['OM'][j]['category'] = 'OM'
        if(len(nadata)>0):
            for j in range(len(nadata)):
                get_data['data']['NA'][j]['category'] = 'NA'

        images_data = get_data['data']['SEM'] + get_data['data']['OM'] + get_data['data']['NA']
        get_data['img_details'] = images_data
        del get_data['data']['NA']
        del get_data['data']['OM']
        del get_data['data']['SEM']
        del get_data['data']
        del get_data['dataset_id']
        response_data.append(get_data)

    #getcropandsegmentdata(response_data, db)
    with concurrent.futures.ThreadPoolExecutor(6) as executor:
        [executor.submit(getcropandsegmentdata, image_analysis_dao, i) for i in response_data]
    
    response_data[0]['img_details'].sort(key=lambda f: os.path.getmtime(f['path']))
#     response_data[0]['img_details'].reverse()
    for i in response_data[0]['img_details']:
        i['imagename'] =  os.path.split(i['path'])[1]
    return response_data