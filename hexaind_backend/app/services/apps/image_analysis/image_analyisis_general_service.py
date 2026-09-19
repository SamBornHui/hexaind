from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
import os
import re
from typing import Sequence, Union, List
from app.services.apps.image_analysis.utils import fetchKeysValue
import cv2
from uuid import uuid4
import time
from app.services.apps.image_analysis.modules_image_analysis_common import *
import numpy as np
import pandas as pd
from pathlib import Path
import logging
import concurrent
import skimage
import asyncio
import traceback
from PIL import Image
import requests
import json
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from app.services.apps.image_analysis.cropinfobar import *
import plotly.express as px
import plotly.graph_objects as go
from skimage.measure import *
from skimage import measure
from app.services.apps.image_analysis.segmentation1 import (
    createImageNamefolder,
    checkEnv,
    getWfFromDB,
    cropAndSegimageMasking,
    filtersToBeApllied,
    callingVisualization,
    send_data
)
from skimage import data, io, filters, restoration, exposure, morphology, util, img_as_ubyte,img_as_float,feature, img_as_float64, segmentation
import sys
from app.config.env_vars import environment


logger = logging.getLogger(__package__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))


def getWfFromDB(wid):
    
    # db = establishConnection()
    collection = db.sampleworkflows
    report = collection.find_one(
                        {'_id': ObjectId(wid)})

    post_visu = ''
    mainwf = []
    if report['workflow']['preprocessingWorkflowSelected'] and report['workflow']['segmentationWorkflowSelected'] and report['workflow']['postprocessingWorkflowSelected']:
        mainwf = report['workflow']["preprocessingWorkflowFeatures"] + report['workflow']["segmentationWorkflowFeatures"] + report['workflow']["postprocessingWorkflowFeatures"]
        post_visu =  report['workflow']["segmentationWorkflowFeatures"][0]['Params']
    elif not report['workflow']['preprocessingWorkflowSelected'] and report['workflow']['segmentationWorkflowSelected'] and report['workflow']['postprocessingWorkflowSelected']:
        mainwf = report['workflow']["segmentationWorkflowFeatures"] + report['workflow']["postprocessingWorkflowFeatures"]
        post_visu =  report['workflow']["segmentationWorkflowFeatures"][0]['Params']
    elif not report['workflow']['preprocessingWorkflowSelected'] and report['workflow']['segmentationWorkflowSelected'] and not report['workflow']['postprocessingWorkflowSelected']:
        mainwf = report['workflow']["segmentationWorkflowFeatures"]
    elif report['workflow']['preprocessingWorkflowSelected'] and report['workflow']['segmentationWorkflowSelected'] and not report['workflow']['postprocessingWorkflowSelected']:
        mainwf = report['workflow']["preprocessingWorkflowFeatures"] + report['workflow']["segmentationWorkflowFeatures"]
        post_visu =  report['workflow']["segmentationWorkflowFeatures"][0]['Params']
    elif report['workflow']['preprocessingWorkflowSelected'] and not report['workflow']['segmentationWorkflowSelected']:
        mainwf = report['workflow']["preprocessingWorkflowFeatures"]  


    if mainwf:
        mainwf  = [i  for j,i in enumerate (mainwf) if i['selected']!=False]
    
    modification = None
    if 'modification' in report:
        modification = (report['modification'])   
    # try:
    #     feature_profile_type = report['feature_profile_type']
    # except:
    #     feature_profile_type = ['fpt']
    # try:
    #     tier_type = report['tier_type']
    # except:
    #     tier_type = ['tva']
    # try:
    #     metal_recess_type = report['metal_recess_type']
    # except:
    #     metal_recess_type = ['metalRecessAnalysis']
    
    # if fetchKeysValue('carryanalysis', report):
    #     carryanalysis = report['carryanalysis']    
    # else:
    #     carryanalysis = False
         
    
    if fetchKeysValue('carryscalebar', report):
        carryscalebar = report['carryscalebar']    
    else:
        carryscalebar = False
    
    output_directory_options = fetchKeysValue('output_directory_options', report) 
    # scaling_info = {'carryanalysis': carryanalysis, 'carryscalebar': carryscalebar,
    #                 'analysis_type': report['analysis_type'],
    #                   'feature_profile_type': feature_profile_type, 
    #                   'tier_type': tier_type, 'metal_recess_type': metal_recess_type}
    scaling_info = {'carryscalebar': carryscalebar}
    return mainwf, modification, post_visu, scaling_info, output_directory_options

def retrieveProcessedWfId(path):
    # db = establishConnection()
    collection = db.workflowimagespath
    name, _ = os.path.splitext(path)
    report = collection.find_one(
                    {'sample_name': name},
                    sort=[( '_id', pymongo.DESCENDING )]
                    )
    if report:
        return str(report['_id'])
    else:
        return 0

def retrieveWfId(path):
    # db = establishConnection()
    collection = db.multiplyimagesworkflow
    
    report = collection.find_one({'image_path': path},
              sort=[( '_id', pymongo.DESCENDING )])
    if report:   
        return report['w_id']
    else:
        return 0

def updtaeIncomingImagesWfStatus(fname):
    collection = db.sampleworkflows
    collection.update_many({"foldername":fname}, 
                { "$set":{              
                "wf_for_incomingimages":False}})
    
def generate_image_annotations_data(df):
    #insert new data
    annotation_details = ['Unique_object_id','Object','Label']
    return df[annotation_details]
  
def update_main_region_props_file_for_image(temp_file):
    try:
        temp_df = pd.read_csv(temp_file)
        folder_path, filtered_image_name = os.path.split(temp_file)
        region_properties_folder_path,_  = os.path.split(folder_path)
        image_name_path , _ = os.path.split(region_properties_folder_path)
        _ , image_name = os.path.split(image_name_path)
        main_file = os.path.join(region_properties_folder_path,f'{image_name}_saved_region_properties.csv')
        temp_df.to_csv(main_file,index=False)
        annotations_df = generate_image_annotations_data(temp_df)
        return main_file, annotations_df
    except Exception as e:
        logger.exception(f'Error occurred while updating main region properties with {temp_file} : {e}')

def remove_directory(path):
    try:
        if os.path.exists(path):
            for root, dirs, files in os.walk(path, topdown=False):
                for file in files:
                    file_path = os.path.join(root, file)
                    os.remove(file_path)
                for dir in dirs:
                    dir_path = os.path.join(root, dir)
                    os.rmdir(dir_path)
            os.rmdir(path)
    except Exception as e:
        logger.exception(f"Error occurred while deleting directory {path} : {e}")

def removeOldData(path, wfimages):
    now = time.time()
    for filename in os.listdir(path):
        filestamp = os.stat(os.path.join(path, filename)).st_mtime
        filecompare = now - 1 * 86400
        if  filestamp < filecompare:
            if filename not in wfimages:
                abs_file_path = os.path.join(path,filename)
                if os.path.isdir(abs_file_path):
                    remove_directory(abs_file_path)
                else:
                    os.remove(abs_file_path)
            
def SavingWfImages(wfimages, dirpath, mainwf, w_id, orignalimg, dataset_id):
    allimages = glob.glob(dirpath+"/*.png" )
    visualizations = ''
    preprocessedlayer = []
    segprocessedlayer = []
    postprocessedlayer = []
    segmentfilter = False
    visualization = False
    binaryimage = ''
    mainwf_len = len(mainwf)
    annotation_data_df = None
    for wf_index,i in enumerate(mainwf):
        
        if i['selected']== True :
            if i['Steps']==1 or i['Steps']==1.5:
                segmentedimg = i['result']['filtered_image']
                pth = i['result']['histogram_path']
                
                temp = {"fid": i["fid"], "filtername": i["Name"], 'filterd_image': segmentedimg, 'histogram_path':pth}
                preprocessedlayer.append(temp)
                wfimages.append(segmentedimg)
                wfimages.append(pth)
            elif i['Steps']==2:
                visualizations = i["Params"]
                try:
                    segmentfilter = True
                    binarypath = ''
                    if i['Value']=='segmentation.slic' or i['Value']=='filters.threshold_local' or i['Value']=='feature.match_template':
                        segmentedimg = i['result']['filtered_image']
                        pth = ''
                        binarypath = i['result']['black&white']
                        wfimages.append(segmentedimg)
                        wfimages.append(binarypath)
                    else:
                        segmentedimg = i['result']['filtered_image']
                        pth = i['result']['histogram_path']
                        binarypath = i['result']['black&white']
                        wfimages.append(segmentedimg)
                        wfimages.append(binarypath)
                        wfimages.append(pth)
                    binaryimage = binarypath
                    temp = {"fid": i["fid"], "filtername": i["Name"], "filterd_image": segmentedimg, "histogram_path":pth
                            , "black&white": binarypath,  'region_properties': i['result']['region_properties']} 
                    
                    if i['result'].get('temp_region_properties_csv_file') and i['result'].get('temp_region_properties_csv_file') != '':
                        temp['temp_region_properties_csv_file'] = i['result']['temp_region_properties_csv_file']
                        if wf_index == mainwf_len - 1 :   
                            temp['region_properties_csv_file'],annotation_data_df = update_main_region_props_file_for_image(i['result']['temp_region_properties_csv_file'])
                            temp_numpy_file = temp['temp_region_properties_csv_file'].replace('.csv','.npy')
                            numpy_file_name = temp['region_properties_csv_file'].replace('.csv','.npy')
                            binary_np_array = np.load(temp_numpy_file)
                            np.save(numpy_file_name, binary_np_array)
                            temp['binary_img_ndarray'] = numpy_file_name
                    segprocessedlayer.append(temp)
                    if visualizations and visualizations['visualization'] == 'Black/white (default)':
                        segmentedimg = binarypath
                        visualization = True
                except:
                    segmentfilter, visualization,  = False, False
    
            else:
                try:
                    segmentfilter = True
                    i['Name'] = i['Name'].replace('/','_')
                    segmentedimg = i['result']['filtered_image']
                    binarypath = i['result']['black&white']
                    try:
                        boundary_excel = i['result']['boundary_excel']
                        temp = {"fid":  i["fid"], "filtername": i["Name"], 'filterd_image': segmentedimg,
                                "black&white": binarypath, 'previewchanges': i['result']['previewchanges']
                                , 'region_properties': i['result']['region_properties'], 'boundary_excel': boundary_excel  } 
                    except:
                        temp = {"fid":  i["fid"], "filtername": i["Name"], 'filterd_image': segmentedimg,
                                "black&white": binarypath, 'previewchanges': i['result']['previewchanges']
                                , 'region_properties': i['result']['region_properties']} 
                    
                    if i['result'].get('temp_region_properties_csv_file') and i['result'].get('temp_region_properties_csv_file') != '':
                        temp['temp_region_properties_csv_file'] = i['result']['temp_region_properties_csv_file']
                        if wf_index == mainwf_len - 1 :   
                            temp['region_properties_csv_file'],annotation_data_df = update_main_region_props_file_for_image(i['result']['temp_region_properties_csv_file'])
                            temp_numpy_file = temp['temp_region_properties_csv_file'].replace('.csv','.npy')
                            numpy_file_name = temp['region_properties_csv_file'].replace('.csv','.npy')
                            binary_np_array = np.load(temp_numpy_file)
                            np.save(numpy_file_name, binary_np_array)
                            temp['binary_img_ndarray'] = numpy_file_name

                    binaryimage = binarypath
                    postprocessedlayer.append(temp)
                    wfimages.append(segmentedimg)
                    wfimages.append(binarypath)
                    
                    wfimages.append(i['result']['previewchanges'])
                    
                    if visualizations and visualizations['visualization'] == 'Black/white (default)':
                        segmentedimg = binarypath
                        visualization = True
                except:
                    segmentfilter, visualization = False, False

    cropthum, segthum, seg_orig = createThumbforCropandSegmentedImg(orignalimg, segmentedimg, dirpath, visualization
                                                                    , binaryimage, dataset_id,segmentfilter)
    im = rgbToGray(io.imread(orignalimg))
    h,w = im.shape
    wfimages.append(cropthum)
    wfimages.append(segthum)
    data = {'cropimg':orignalimg, "cropimg_shape": [h,w], "crop_thumb" :cropthum, "segmented_imgthumb": segthum
            , "segmented_img":segmentedimg,"preprocessedlayers": preprocessedlayer, "segmentationlayers": segprocessedlayer
            , "postprocessedlayers": postprocessedlayer}
    
    if annotation_data_df is not None:
        data['annotation_data_df'] = annotation_data_df

    removeOldData(dirpath, wfimages)
    allimages = glob.glob(dirpath+"/*.png" )
    foldername, _ = os.path.split(segmentedimg)
    foldername = os.path.basename(foldername)
    if IMAGESPORT in SOCKETURL:
        segpath = PLATPATH + foldername + '_seg.png'
        origpath = PLATPATH + foldername + '.png'
        shutil.copyfile(data['segmented_img'], segpath)
        shutil.copyfile(data['cropimg'], origpath)
    
    return foldername, data, seg_orig

def delDictKey(features):
    for i in features:
        try:
            del i['result']
        except:
            pass

def getUsername(_id, collection):
    report = collection.find_one({'_id': ObjectId(_id)})
    return report['first_name']+' '+report['last_name']

def save_image_annotations_data(name,workflow_id,df):
    try:
        #remove existing db doc associated with the record
        db.seg_image_annotations.delete_many({'name': name})
        
        db_data = {
            'name' : name,
            'workflow_db_id' : workflow_id,
            'annotation_data' : df.to_dict(orient='records')
        }
        #insert new data
        db.seg_image_annotations.insert_one(db_data)
    except Exception as e:
        raise e

def actionSummary( obj, collectionname='actionsummary'):
    datasetid = obj['datasetid']
    msg = obj['msg']
    userid = obj['userid']
    # db = establishConnection()
    
    user_name = getUsername(userid, db.users)
    collection = db[collectionname]
    dt = datetime.today().strftime('%Y-%m-%d %H:%M')
    data = {'action': msg, 'date': dt, 'user_id': userid, 'dataset_id': datasetid, 'user_name': user_name}
    collection.insert_one(data)
    
    return 'success'

def unlinkWfFromOtherSample(wid):
    # db = establishConnection()
    collection = db.workflowimagespath

    report = collection.delete_many(
                        {'workflow_id': wid})

def insertingDatainDB(obj, image_analysis_dao):
    global db
    db = image_analysis_dao
    # metal_voids_analysis = obj['metal_voids_analysis']
    name = obj['name']
    workflow = obj['workflow']
    imgpath = obj['image_path']
    typ = obj['type']
    w_id = obj['_id']
    dirpath = obj['dirpath']
    dirname = obj['foldername']
    orignalimg = obj['cropimg']
    username = obj['username']
    output_directory_options = fetchKeysValue('output_directory_options', obj)
    if output_directory_options:
        output_directory_options = obj['output_directory_options']
    else:
        output_directory_options = ''
    default = obj['default']
    removeconnection = obj['removeconnection']
    # carryanalysis = obj['carryanalysis']
    try:
        carrycrop = obj['carrycrop']
    except:
        carrycrop = obj['applyCropping']
    wf_for_incomingimages = obj['wf_for_incomingimages']
    dataset_id = obj["dataset_id"]
    # db = establishConnection()
    if wf_for_incomingimages:
        updtaeIncomingImagesWfStatus(dirname)
        
    # pdf_path = obj['pdf_path']
    # tier_analysis = obj['tier_analysis']
    # if len(tier_analysis)>1:
    #     tier_voids_annotated = obj['tier_analysis'][0]['annotate_img']#obj['tier_voids_annotated']
    #     tier_thick_annotated = obj['tier_analysis'][1]['annotate_img']
    
    # elif tier_analysis:
    #     tier_voids_annotated = obj['tier_analysis'][0]['annotate_img']#obj['tier_voids_annotated']
    #     tier_thick_annotated = ''
    # else:
    #     tier_voids_annotated = ''
    #     tier_thick_annotated = ''
    
    # tier_type = []
    # if len(tier_analysis)>1:
    #     tier_type = ['tva', 'tta']
    # elif tier_analysis:
    #     tier_type.append(tier_analysis[0]['analysis_type'])
    
    project_id = fetchKeysValue('project_id', obj)
    # metal_recess_analysis = obj['metal_recess_analysis']
    # metal_recess_type = []
    # if len(metal_recess_analysis)>1:
    #     metal_recess_type = ['metal_recess', 'metal_recess_sec_t', 'metal_recess_tier_thick']
    #     metal_recess_1 = metal_recess_analysis[0]['annotate_img']
    #     metal_recess_2 = metal_recess_analysis[1]['annotate_img']
    #     metal_recess_3 = metal_recess_analysis[2]['annotate_img']
    # elif len(metal_recess_analysis)>1:
    #     metal_recess_type.append(metal_recess_analysis[0]['analysis_type'])
    #     metal_recess_type.append(metal_recess_analysis[1]['analysis_type'])
    #     metal_recess_1 = metal_recess_analysis[0]['annotate_img']
    #     metal_recess_2 = metal_recess_analysis[1]['annotate_img']
    #     metal_recess_3 = ''
    # elif metal_recess_analysis:
    #     metal_recess_type.append(metal_recess_analysis[0]['analysis_type'])
    #     metal_recess_1 = metal_recess_analysis[0]['annotate_img']
    #     metal_recess_2 = ''
    #     metal_recess_3 = ''          
    # else:
    #     metal_recess_1 = ''
    #     metal_recess_2 = ''
    #     metal_recess_3 = ''
           
    try:
        manual_cord = obj['manualcoordinates']
        manual_cord['applyCropping'] = True #obj['applyCropping']  
    except:
        manual_cord = 'auto'
    
    
    # analysis = obj['analysis']
    # excel_path = obj['excel_path']
    # annotate_img = obj['annotate_img']
    # analysis_type = obj['analysis_type']
    # P_analysis = obj['profile_analysis']
    feature_profile_type = []
    
    # if P_analysis and len(P_analysis)>1:
    #     feature_profile_type = ['fpt', 'fpo']
    #     P_annotate_img = P_analysis[0]['annotate_img']
    #     outline_annotate = P_analysis[0]['annotate_img']
    # elif P_analysis and P_analysis['Analysis']:
    #     feature_profile_type.append(P_analysis[0]['analysis_type'])
    #     P_annotate_img = P_analysis[0]['annotate_img']
    #     outline_annotate = ''
    # else:
    #     outline_annotate = ''
    #     P_annotate_img = ''
    
    
    # bubble_analysis = obj['bubble_analysis']
    # if bubble_analysis:
    #     bubble_img = bubble_analysis[0]['annotate_img']
    # else:
    #     bubble_img = ''
    
    # pillar_c2c_analysis = obj['pillar_c2c_analysis']
    # pillar_anomaly_analysis = obj['pillar_anomaly_analysis']
    mainwf = []
    if obj['workflow']['preprocessingWorkflowSelected'] and obj['workflow']['segmentationWorkflowSelected'] and obj['workflow']['postprocessingWorkflowSelected']:
        mainwf = obj['workflow']["preprocessingWorkflowFeatures"] + obj['workflow']["segmentationWorkflowFeatures"] + obj['workflow']["postprocessingWorkflowFeatures"]
        mainwf  = [i  for j,i in enumerate (mainwf) if i['selected']!=False]
    elif not obj['workflow']['preprocessingWorkflowSelected'] and obj['workflow']['segmentationWorkflowSelected'] and obj['workflow']['postprocessingWorkflowSelected']:
        mainwf = obj['workflow']["segmentationWorkflowFeatures"] + obj['workflow']["postprocessingWorkflowFeatures"]
        mainwf  = [i  for j,i in enumerate (mainwf) if i['selected']!=False]
    elif not obj['workflow']['preprocessingWorkflowSelected'] and obj['workflow']['segmentationWorkflowSelected'] and not obj['workflow']['postprocessingWorkflowSelected']:
        mainwf = obj['workflow']["segmentationWorkflowFeatures"]
        mainwf  = [i  for j,i in enumerate (mainwf) if i['selected']!=False]
    elif obj['workflow']['preprocessingWorkflowSelected'] and obj['workflow']['segmentationWorkflowSelected'] and not obj['workflow']['postprocessingWorkflowSelected']:
        mainwf = obj['workflow']["preprocessingWorkflowFeatures"] + obj['workflow']["segmentationWorkflowFeatures"] 
        mainwf  = [i  for j,i in enumerate (mainwf) if i['selected']!=False]
    elif obj['workflow']['preprocessingWorkflowSelected'] and not obj['workflow']['segmentationWorkflowSelected']:
            mainwf = obj['workflow']["preprocessingWorkflowFeatures"]  
            mainwf  = [i  for j,i in enumerate (mainwf) if i['selected']!=False]
    
    if mainwf:
        # wfimages = [orignalimg, annotate_img, P_annotate_img, outline_annotate, tier_voids_annotated, tier_thick_annotated, metal_recess_1, metal_recess_2, metal_recess_3, bubble_img]
        wfimages = [orignalimg]
        fname, imgdata, seg_orig = SavingWfImages(wfimages, dirpath, mainwf, w_id, orignalimg, dataset_id)
    else:
        folderp, fname = os.path.split(obj['image_path'])
        fname = os.path.splitext(fname)[0]
        wfimagesdir = folderp + '/' + 'wf_images'
        
        if not os.path.exists(wfimagesdir):
            os.mkdir(wfimagesdir)
        
        cimg = cv2.imread(obj['cropimg'])
        h, w = cimg.shape[:2]
        cimg = cv2.resize(cimg, (300, 300))
        croppath = wfimagesdir + '/' + 'thumbnail_crop'+str(int(round(time.time() * 1000)))+'.png'
        cv2.imwrite(croppath, cimg)
        croppath = croppath.replace('\\','/')
        imgdata = {}
        
        imgdata['cropimg'] = obj['cropimg']
        imgdata['crop_thumb'] = croppath
        imgdata['segmented_imgthumb'] = croppath
        imgdata['cropimg_shape'] = [h,w]
        imgdata['segmented_img'] = obj['cropimg']
        seg_orig = obj['cropimg']
        imgdata['preprocessedlayers'] = []
        imgdata['segmentationlayers'] = []
        imgdata['postprocessedlayers'] = []
        imgdata['postprocessedlayers'] = []
    
    annotation_data_df = None
    if 'annotation_data_df' in imgdata:
        annotation_data_df = imgdata['annotation_data_df']
        del imgdata['annotation_data_df']

    data = []
    collection = db.sampleworkflows
    delDictKey(workflow['preprocessingWorkflowFeatures'])
    delDictKey(workflow['segmentationWorkflowFeatures'])
    delDictKey(workflow['postprocessingWorkflowFeatures'])
    savingname, _ = os.path.splitext(obj['image_path'])
    if typ =='new':
        msg = f" Create new '{name}' "
        actionSummary({'datasetid': dataset_id, 'msg': msg, 'userid': obj['userId']}, 'curationsummary')
        dt=datetime.today().strftime('%Y-%m-%d %H:%M')
    
        # rec_id2 = collection.insert_one( {'orignal_thumb': imgdata['crop_thumb'], 
        #                                   'segment_thumb': imgdata['segmented_imgthumb'], 
        #                                   'orig_full': obj['cropimg'],
        #                                  'seg_full': seg_orig, "Wname": name, "dataset_id":dataset_id, 
        #                                  "foldername":dirname, 'image_path': imgpath,
        #                                   'workflow': workflow, 'created_date': dt, 'modify_date': dt,
        #                                     'username': username, "default":default,
        #                                   'modification': manual_cord, 'favorited_by': [{'user_id':obj['userId'],'favorite':False}], 
        #                                   'carryanalysis': carryanalysis,'carrycrop': carrycrop,
        #                                   'wf_for_incomingimages': wf_for_incomingimages, 'analysis_type': analysis_type,
        #                                     'feature_profile_type': feature_profile_type,
        #                                   'tier_type': tier_type, 'metal_recess_type':metal_recess_type, 
        #                                   'output_directory_options': output_directory_options, 'project_id': project_id,
        #                                     'user_id': obj['userId'] })
        # rec_id2 = collection.insert_one( {'orignal_thumb': imgdata['crop_thumb'], 
        #                                   'segment_thumb': imgdata['segmented_imgthumb'], 
        #                                   'orig_full': obj['cropimg'],
        #                                  'seg_full': seg_orig, "Wname": name, "dataset_id":dataset_id, 
        #                                  "foldername":dirname, 'image_path': imgpath,
        #                                   'workflow': workflow, 'created_date': dt, 'modify_date': dt,
        #                                     'username': username, "default":default,
        #                                    'favorited_by': [{'user_id':obj['userId'],'favorite':False}], 
        #                                   'carryanalysis': carryanalysis,'carrycrop': carrycrop,
        #                                   'wf_for_incomingimages': wf_for_incomingimages,
        #                                     'feature_profile_type': feature_profile_type,
        #                                   'output_directory_options': output_directory_options, 'project_id': project_id,
        #                                     'user_id': obj['userId'] })
        rec_id2 = collection.insert_one( {'orignal_thumb': imgdata['crop_thumb'], 
                                          'segment_thumb': imgdata['segmented_imgthumb'], 
                                          'orig_full': obj['cropimg'],
                                         'seg_full': seg_orig, "Wname": name, "dataset_id":dataset_id, 
                                         "foldername":dirname, 'image_path': imgpath,
                                          'workflow': workflow, 'created_date': dt, 'modify_date': dt,
                                            'username': username, "default":default,
                                           'favorited_by': [{'user_id':obj['userId'],'favorite':False}], 
                                          'carrycrop': carrycrop,'modification': manual_cord,
                                          'wf_for_incomingimages': wf_for_incomingimages,
                                            'feature_profile_type': feature_profile_type,
                                          'output_directory_options': output_directory_options, 'project_id': project_id,
                                            'user_id': obj['userId']}
                                            )
        report = collection.find_one({},sort=[( '_id', pymongo.DESCENDING )])
        w_id = str(report['_id'])
        nn = os.path.basename(savingname)
        msg = f" Applied '{name}' on '{nn}' "
        actionSummary({'datasetid': dataset_id, 'msg': msg, 'userid': obj['userId']}, 'curationsummary')
        collection = db.workflowimagespath
        report = collection.delete_many(
                {'sample_name': savingname})
                
        rec_id2 = collection.insert_one({'sample_name': savingname, "path": obj['image_path'], 
                                         "data":imgdata, "workflow_id": w_id, 
                                            
                                           } )
        data = {'workflow_id': w_id}
        if annotation_data_df is not None:
            inserted_id = str(rec_id2.inserted_id)
            save_image_annotations_data(savingname,inserted_id,annotation_data_df)
    
    
    else:
        if removeconnection:
            unlinkWfFromOtherSample(w_id)
        
        msg = f" Modify '{name}' "

        
        dt=str(datetime.today().strftime('%Y-%m-%d %H:%M'))
        result = collection.update_one( 
        {"_id":ObjectId(w_id)}, 
        { "$set":{ "workflow":workflow, "Wname": name, "modify_date": dt, 
                  "dataset_id": dataset_id, 'modification': manual_cord, 
                   'orignal_thumb': imgdata['crop_thumb'],
                     'segment_thumb': imgdata['segmented_imgthumb'],
                   'orig_full': obj['cropimg'], 'seg_full': seg_orig, 
                   'output_directory_options': output_directory_options
        }})

        # { "workflow":workflow, "Wname": name, "modify_date": dt, 
        #           "dataset_id": dataset_id, 'modification': manual_cord, 
        #           'analysis_type': analysis_type, 'feature_profile_type': feature_profile_type, 
        #           'tier_type':tier_type,
        #            'metal_recess_type':metal_recess_type, 
        #            'orignal_thumb': imgdata['crop_thumb'],
        #              'segment_thumb': imgdata['segmented_imgthumb'],
        #            'orig_full': obj['cropimg'], 'seg_full': seg_orig, 
        #            'output_directory_options': output_directory_options
        # }
    
        collection = db.workflowimagespath
        report = collection.delete_many({'sample_name': savingname})
        # dat = {'sample_name': savingname, "path": obj['image_path'],
        #         "data":imgdata, "workflow_id": w_id, 'analysis': analysis, 
        #         'excel_path': excel_path, 'annotate_img': annotate_img , 
        #         'profile_analysis': P_analysis, 'pdf_path':pdf_path, 
        #         'tier_analysis': tier_analysis, 'metal_recess_analysis': metal_recess_analysis,
        #           'bubble_analysis': bubble_analysis, 'pillar_c2c_analysis': pillar_c2c_analysis, 
        #           'pillar_anomaly_analysis': pillar_anomaly_analysis, 
        #           'metal_voids_analysis':metal_voids_analysis}
        dat = {'sample_name': savingname, "path": obj['image_path'],
                "data":imgdata, "workflow_id": w_id, }
        
        rec_id2 = collection.insert_one(dat)
        data = {'workflow_id': w_id}    
        if annotation_data_df is not None:
            inserted_id = str(rec_id2.inserted_id)
            save_image_annotations_data(savingname, inserted_id, annotation_data_df)
    
    
    return data

#delete workflow

def retrieveObjectbyId(_id, collection):
    obj = collection.find_one(
                        {'_id': ObjectId(_id)})
    obj['_id'] = str(obj['_id'])
    return obj

def getWfName(_id):
    # db = establishConnection()
    collection2 = db.sampleworkflows
    report2 = collection2.find_one({'_id': ObjectId(_id)})
    return report2['Wname'], report2['dataset_id']

def removewfimages(wid):
    # db = establishConnection()
    collection = db.sampleworkflows
    report = retrieveObjectbyId(wid, collection)
    wfimages = []
    if fetchKeysValue('segment_thumb', report):
        wfimages.append(report['orignal_thumb'])
        wfimages.append(report['segment_thumb'])
        wfimages.append(report['seg_full'])
        for i in wfimages:
            if 'wf_images' in i and os.path.exists(i):
                os.remove(i)

def deleteWf(obj, image_analysis_dao):
    global db
    db = image_analysis_dao
    wid = obj['_id']
    if 'user_id' in obj:
        user_id = obj['user_id']
    else:
        user_id = obj['userId']
    # db = establishConnection()
    collection = db.multiplyimagesworkflow
    report = collection.delete_many({'w_id': wid})
    collection = db.workflowimagespath
    report = collection.delete_many({'workflow_id': wid})
    removewfimages(wid)
    wfname, dataset_id = getWfName(wid)
    msg = f" Delete '{wfname}' "
    actionSummary({'datasetid': dataset_id, 'msg': msg, 'userid': user_id}, 'curationsummary')
    collection = db.sampleworkflows
    report = collection.delete_one(
        {'_id': ObjectId(wid)}
        )
    
#assign workflow    

def getAssignedData(wid, db):
    collection = db.multiplyimagesworkflow
    report = collection.find(
                    {'w_id': {'$in':[wid]}})

    assignedwf  = []
    if report:
        for doc in report:
            assignedwf.append(doc)
        return assignedwf
    else:
        return assignedwf
    
def deleteAppliedData(path):
    # db = establishConnection()
    collection = db.workflowimagespath
    name, _ = os.path.splitext(path)
    report = collection.delete_many(
                    {'sample_name': name})
    
def copyWfimages(image, report):
    folderpath = os.path.splitext(image)[0]
    if not os.path.exists(folderpath):
        os.mkdir(folderpath)
    wf_images = os.path.join(folderpath , 'wf_images')
    if not os.path.exists(wf_images):
        os.mkdir(wf_images)

    report['orignal_thumb'] = copyFile(report['orignal_thumb'], wf_images)
    report['segment_thumb'] = copyFile(report['segment_thumb'], wf_images)
    report['seg_full'] = copyFile(report['seg_full'], wf_images)

def createDuplicateWf(wid, username, foldername, image, db, project_id, userId, dataset_id = ''):
    collection = db.sampleworkflows
    report = collection.find_one({'_id': ObjectId(wid)})
    del report['_id']
    dt = datetime.today().strftime('%Y-%m-%d %H:%M')
    _, fname = os.path.split(image)
    fname, _ = os.path.splitext(fname)
    fname = fname + 'workflow'
    wname = report['Wname']
    report['Wname'] = report['Wname'] + " - copy"
    report['created_date'] = dt
    report['modify_date'] = dt
    report['foldername'] = foldername
    report['user_id'] = userId
    report['image_path'] = image
    report['dataset_id'] = dataset_id
    report['project_id'] = project_id
    copyWfimages(image, report)
    rec_id = collection.insert_one(report)
    return str(report['_id']), wname


def assignWf(obj,image_analysis_dao):
    global db
    db = image_analysis_dao
    user_id = obj['userId']
    wid = obj['_id']
    image_path = obj['image_path']
    duplicate = obj['duplicate']
    aftersavingwf = obj['aftersavingwf']
    otherdir = False
    dataset_id = obj['dataset_id']
    appliedwf = fetchKeysValue('applied_workflow', obj)

    applieddata = []
    assignedwf = getAssignedData(wid, db)
    wfname, d_id = getWfName(wid)
    if not dataset_id:
        dataset_id = d_id
    if len(image_path) <= 1:
        imname = os.path.basename(os.path.splitext(image_path[0]['image'])[0])
        msg = f" Assign '{wfname}' on '{imname}' "
    else:
        
        imglen = len(image_path)
        msg = f" Assign '{wfname}' to '{imglen}' images"
    
    actiondata = {'datasetid': dataset_id, 'msg': msg, 'userid': user_id}
    actionSummary(actiondata, 'curationsummary')
    for i in image_path:
        try:
            wfapplied = i['workflow_applied']
            multicase = 0
        except:
            wfapplied = 0
            multicase = 1        

        if multicase and appliedwf!=i['image'] :
            deleteAppliedData(i['image'])

        elif multicase and appliedwf==i['image']:
            pass
        elif not (len(image_path)==1 and aftersavingwf) or appliedwf==i['image']:
            if wfapplied != wid and not aftersavingwf:
                deleteAppliedData(i['image'])

        collection = db.multiplyimagesworkflow
        if duplicate :
            
            username = obj['username']
            foldername = obj['foldername']
            wid, wname = createDuplicateWf(wid, username, foldername, i["image"], db, obj['project_id'], user_id, dataset_id)
            msg = f" Duplicate '{wname}' "
            if dataset_id:
                actionSummary({'datasetid': dataset_id, 'msg': msg, 'userid': user_id}, 'curationsummary')
            fulldata = {'image_path': i["image"], 'w_id': wid}
            duplicate = False
            otherdir = True

        else:
            fulldata = {'image_path': i["image"], 'w_id': wid}

        report = collection.delete_one(
                {'image_path': i['image']})


        rec_id2 = collection.insert_one( fulldata )
        appliedpath = i['image']
        appliedid = retrieveProcessedWfId(i['image'])
        temp = {'appliedpath':i['image'], "applied_id": appliedid,'workflow_id':wid}
        applieddata.append(temp)
        if assignedwf:
            assignedwf = [im for im in assignedwf if not (im['image_path'] == i['image'])]
    
    if not aftersavingwf and not otherdir:
        for i in  assignedwf:
            deleteRemainingData(i['image_path'], db)
            temp = {'appliedpath':i['image_path'], "applied_id": 0,'workflow_id':0}
            applieddata.append(temp)
        
    data = {'Status': 'Updated', "applieddata":applieddata}
    return data

#de_associate workflow
def DissociateWfFromImage(obj, image_analysis_dao):
    global db
    name = obj['path']
    db = image_analysis_dao
    try:
        wid = obj['wid']
        multicase = obj['multicase']
    except:
        multicase = False

    if multicase:
        collection = db.multiplyimagesworkflow
        report = collection.delete_many({'w_id': wid})
        collection = db.workflowimagespath
        report = collection.delete_many({'workflow_id': wid})
        
    else:
        deleteRemainingData(name, db)
        imname = os.path.basename(os.path.splitext(name)[0])
        wfname, dataset_id = getWfName(wid)
        msg = f" Dissociate '{wfname}' from '{imname}' "
        actionSummary({'datasetid': dataset_id, 'msg': msg, 'userid': obj['userId']}, 'curationsummary')
    return {"Status":"completed"}

#masking

def getDirPath(path, name):
    name = name.replace('_test','')
    if name in path and name == os.path.basename(path):
        return path
    elif "modifiedimages" in path:
        path = path.replace("modifiedimages",name)
        return path
    elif "preprocessingtep" in path:
        path = path.replace("preprocessingtep",name)
        return path
    elif "segmentationstep" in path:
        path = path.replace("segmentationstep",name)
        return path
    elif "processedimg" in path:
        path = path.replace("processedimg",name)
        return path
    else:
        path = path.replace("postprocessingtep",name)
        return path

def createImageNameDir(sample_image:str):
    dirpath, name = os.path.split(sample_image)
    fname, _ = os.path.splitext(name)
    
    if "modifiedimages" in sample_image or "processedimg" in sample_image: 
        if TESTPORT in SOCKETURL:
            fname = fname + '_test'
            
        newpath = getDirPath(dirpath,fname)
        if not os.path.exists(newpath):
            os.mkdir(newpath)
        else:
            pass 
    else:
        newpath = dirpath
    return newpath

def imageMasking(obj, image_analysis_dao):
    try:
        Ym = obj['ymax']
        base_image = obj['base_image']
        sample_image = obj['image']
        cord = obj['coordinates']

        img = io.imread(sample_image)
        # img = rgbToGray(img)
        shape = img.shape
        h=shape[0]
        w=shape[1]

        imgpath = base_image
        imgpath = imgpath.replace('/processedimg','')
        imgpath, _ = os.path.splitext(imgpath)
        
        newpath = createImageNameDir(base_image)
        newpathh = newpath + '/'+'image_masking'+'_'+str(int(round(time.time() * 1000)))+'.png'

        x1 = cord['x1']
        y1 = cord['y1']
        x2 = cord['w']
        y2 = cord['h']
        x1 = int(w *(x1/100))
        y1 = int(h *(y1/100))
        x2 = int(x1 +(w*(x2/100)))
        y2 = int(y1 +(h*(y2/100)))
        img = img[y1:y2, x1:x2]
        height = img.shape[0]
        width = img.shape[1]

        img = img_as_ubyte(img)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        cv2.imwrite(newpathh, img)
        
        return {'cropimg':newpathh, 'cropimg_shape': [height, width]}
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]



#scalebar

def getScaleBarValue(obj, db_sync_client):
    #PixelSizeX = obj['PixelSizeX']
    disp_width = obj['client_width']
    path = obj['modified_image']
    # = '/root/AlloyResearch/'
    px_scale = obj['px_scale']
    # scale_unit = obj['scale_unit']
    A = io.imread(path)
    
    scale_array = np.array([1,2,5,10,20,50,100,200,500]) # only look at these physical dimension in scale
    px_array = scale_array/px_scale # number of pixels corresponding to above array
    image_percent = px_array/A.shape[1]
    
    # only keep dimensions that are greater than 10% of the image
    image_percent_filt = image_percent[list(np.where(image_percent > 0.1)[0])]
    px_array_filt = px_array[list(np.where(image_percent > 0.1)[0])]
    scale_array_filt = scale_array[list(np.where(image_percent > 0.1)[0])]
    
    index = min(enumerate(image_percent_filt), key=lambda x: abs(x[1]-0.1))
    
    scalebar = int(scale_array_filt[index[0]])
    scalebar_width_px = float(px_array_filt[index[0]])
    image_percent_display = float(image_percent_filt[index[0]])

    disp_width_px = scalebar_width_px * ( disp_width / A.shape[1])

    data  = {'scalebar':scalebar,'scalebar_width (px)':scalebar_width_px, 'disp_width_px': disp_width_px}
    return data

def call_saveScalebar(imageindex,category,collection,scalebar_type,scalebarByImage,scalebarByPhysical,scalebarByPhysicalUnit):
    #for imageindex in range(len(collection['data'][category])):
    collection['data'][category][imageindex]['scalebar_options']['scalebar_type'] = scalebar_type
    collection['data'][category][imageindex]['scalebar_options']['scalebarByImage'] = scalebarByImage
    collection['data'][category][imageindex]['scalebar_options']['scalebarByPhysical'] = scalebarByPhysical
    collection['data'][category][imageindex]['scalebar_options']['scalebarByPhysicalUnit'] = scalebarByPhysicalUnit
    return collection

def saveScalebar(obj,db_sync):
    global db 
    db = db_sync
    scalebar_type = obj['scalebar_type']
    imgpath = obj['imgpath']
    image = obj['image']
    dataset_id = obj['datasetid']
    folderpath = obj['folderpath']
    foldername = obj['foldername']
    category = obj['category']
    applytoall = obj['applytoall'] 
    scalebarByImage = obj['scalebarByImage'] 
    scalebarByPhysical = obj['scalebarByPhysical'] 
    scalebarByPhysicalUnit = obj['scalebarByPhysicalUnit'] 
    
    # db = establishConnection()
    collection = db.categorizeddata.find_one({'dataset_id':dataset_id,'folderId':foldername}, sort=[( '_id', pymongo.DESCENDING )])
    
    if applytoall:
        categories = ['SEM','OM','NA']
        for category in categories:
            for imageindex in range(len(collection['data'][category])):
                collection =  call_saveScalebar(imageindex,category,collection,scalebar_type,scalebarByImage,scalebarByPhysical,scalebarByPhysicalUnit)
    else:
        folderdata = collection['data']

        folderCategoryData = []
        if category=='SEM':
            folderCategoryData = folderdata['SEM']
        elif category=='OM':
            folderCategoryData = folderdata['OM']
        else:
            folderCategoryData = folderdata['NA'] 

        imageindex = [i for i in range(len(folderCategoryData)) if folderCategoryData[i]['path'] == imgpath][0]
        collection = call_saveScalebar(imageindex,category,collection,scalebar_type,scalebarByImage,scalebarByPhysical,scalebarByPhysicalUnit)
        
    
    db.categorizeddata.update_one(
                {"_id":collection["_id"]},
                { "$set": {
                    "data":collection['data']
                }}
            )

    return {'scalebar_type': scalebar_type, 'scalebarByImage': scalebarByImage, 'scalebarByPhysical': scalebarByPhysical, 
    'scalebarByPhysicalUnit': scalebarByPhysicalUnit}    

#update output path

def updateOutputPathwf(obj, db_sync_client):
    
    output_directory_options = obj["output_directory_options"]
    workflow_id = obj['workflow_id']
    wfname, dataset_id = getWfName(workflow_id)
    msg = f" Update output directory path for '{wfname}' "
#     actionSummary({'datasetid': dataset_id, 'msg': msg, 'userid': obj['userId']})
    
    db = db_sync_client
    collection = db.sampleworkflows
    collection.update_one(
        {"_id":ObjectId(workflow_id)}, 
        { "$set": {
            "output_directory_options": output_directory_options
        }}
    )
    return "updated output path"


#batch processing

def getscaleandunitval(scalevalue):
    if scalevalue:
        pixel_size = scalevalue
        if scalevalue*1e9 <10:
            popup_unit = 'nm'
            scale = pixel_size*1e9
        elif scalevalue*1e9>10:
            popup_unit = 'Um'
            scale = pixel_size*1e6
    else:
        scale, popup_unit = '', ''
    
    return scale, popup_unit

def enableFeatureEngineering(dataset):
    # db = establishConnection()
    collection = db.DMCreatedDatasets
    collection.update_one({"_id" :ObjectId(dataset)}
                                   ,{'$set': {"enable_FE":True}},upsert=False)

def createThumbforCropandSegmentedImg(crop, segmented, newpath, visualization, 
                                      binaryimage, dataset_id,segmentfilter=False):
    try:
        logger.info("Inside createThumbforCropandSegmentedImg")
        imagename = os.path.basename(newpath)
        wf_imagedir = os.path.join(os.path.split(newpath)[0], 'wf_images')
        if not os.path.exists(wf_imagedir):
            os.mkdir(wf_imagedir)
            
        if segmentfilter:
    #         segment_imagedir = newpath.replace(imagename, 'segment_dir')
            segment_imagedir = os.path.join(os.path.split(newpath)[0], 'segment_dir')
            if not os.path.exists(segment_imagedir):
                os.mkdir(segment_imagedir)
            seg_image = segment_imagedir + '/' + imagename + '.png'
            copyFile(binaryimage, seg_image)
            
            thumb_dir = segment_imagedir + '/' + 'thumbnail'   
            if not os.path.exists(thumb_dir):
                os.mkdir(thumb_dir)
            
            
            cimg = cv2.imread(binaryimage)
            cimg = cv2.resize(cimg, (300, 300))
            segpath = thumb_dir + '/' + imagename +'.png'
            cv2.imwrite(segpath, cimg)
        
        
        seg_image = copyFile(segmented, wf_imagedir)    
        cimg = cv2.imread(segmented)
        cimg = cv2.resize(cimg, (300, 300))
        segpath = wf_imagedir+'/'+'thumbnail_segment'+str(int(round(time.time() * 1000)))+'.png'
        cv2.imwrite(segpath, cimg) 
            
        cimg = cv2.imread(crop)
        cimg = cv2.resize(cimg, (300, 300))
        croppath = wf_imagedir + '/' + 'thumbnail_crop'+str(int(round(time.time() * 1000)))+'.png'
        cv2.imwrite(croppath, cimg)
        
        segpath = segpath.replace('\\','/')
        croppath = croppath.replace('\\','/')
        seg_image = seg_image.replace('\\','/')

        if dataset_id:
            enableFeatureEngineering(dataset_id)
            
        return croppath, segpath, seg_image
    except Exception as e:
        logger.error(f"unable to createThumbforCropandSegmentedImg due to {str(e)}")
    
def applyingImageMasking(img, cord, path):

    img = rgbToGray(img)
    autoCropBar = fetchKeysValue('autoCropBar', cord)
    
    if autoCropBar == True:
        calldata = {'sample_img': path}             
        url = APIHITURL + "postAuto_crop_value"
        a = requests.post(url, data=json.dumps(calldata), headers={"Content-Type": "application/json"})
        a_data = json.loads(a.text)
        stripsize = a_data['strip_size']
        h,w = img.shape
        img = img[0:h-stripsize, 0:w]
        
    else:
        h,w=img.shape
        
        #cord  = obj['coordinates']
        x1 = cord['x1']
        y1 = cord['y1']
        x2 = cord['w']
        y2 = cord['h']
       
        x1 = int(w *(x1/100))
        y1 = int(h *(y1/100))
        x2 = int(x1 +(w*(x2/100)))
        y2 = int(y1 +(h*(y2/100)))
        img = img[y1:y2, x1:x2]    

    return img


async def imagesParallelWfApplying(p, user_id, folderdata, obj, callfrom='',
                              batchoutput_dir='', data=''):
    starttime = time.time()

    global PROGRESSCOUNT
    error = False
    if p==0:
        PROGRESSCOUNT = 1
    workflowid = folderdata[p]["workflowid"]
    if 'datasetid' in obj:
        datasetid = obj['datasetid']
    else:
        datasetid = None
    fpath, name = os.path.split(folderdata[p]['path'])
    fullname  = name
    applied = folderdata[p]["appliedid"]
    if applied:
        collection = db.workflowimagespath
        report = collection.find_one({'_id': ObjectId(applied)})
        data = report['data']
        image = data['crop_thumb']
        segthum = data['segmented_imgthumb']
        
        img = cv2.imread(data['cropimg'])
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        
    elif workflowid:
        mainwf, modification, post_visu, Analysis_info, outputdir_info = getWfFromDB(workflowid)
        modtype = fetchKeysValue('applyCropping', modification)
        try:
            image_path = folderdata[p]["image"]
            rotate_options = folderdata[p]["rotate_options"]
            image_masks = folderdata[p]["image_masks"]
            manual_coordinates = folderdata[p]["manual_coordinates"]
            strip_size  = folderdata[p]["strip_size"]
            # reading image
            try:
                img = io.imread( image_path)
            except:
                img = Image.open(image_path)
                img = np.asarray(img)

            #applying rotate

            img = rotateAndSave( modified_path = folderdata[p]['image'], 
                                degrees = rotate_options['rotateval'] ,call_from='imagesParallelWfApplying')

            #applying crop
            if manual_coordinates['autoCropBar']:
                manual_coordinates['stripsize'] = strip_size
                img = crop_image_using_strip_size(cord=manual_coordinates, img=img )
            else:
                img = crop_image_using_coordinates(cord=manual_coordinates,img=img)

            logger.info(f"Image maskes-------------->{image_masks}")
            try:
                filtered_dict = next((d for d in image_masks if d.get("apply") == True), None)
                coordinates = filtered_dict['coordinates']
            except:
                coordinates ={"message":"no coordinates"}

            #applying mask
            if coordinates:
                # logger.info(f"filterd dict-------------->{filtered_dict}")
                logger.info(f"Coordinates------------------------------>{coordinates}")   
                try:
                    # logger.info(f"Applying image masking on image: {img} and folder {folderdata[p]['path']}")     
                    # img = applyingImageMasking(img, coordinates, folderdata[p]['path'])
                    img = cropAndSegimageMasking(img=img, cord=coordinates)
                    logger.info(f"shape after masking {str(img.shape)} ")
                except Exception as e:
                    logger.error(f"unable to maske the object due to:{str(e)}",)
                    
                # img = rgbToGray(img)
                newpath = createImageNamefolder(folderdata[p]["path"])
                newpathh = newpath +'/image_masking'+'_'+str(int(round(time.time() * 1000)))+'.png'
                logger.info(f"newpathh:{str(newpathh)}")
                img = img_as_ubyte(img)
                img = rgbToGray(img)

                cv2.imwrite(newpathh, img)   
                image = newpathh
            else:
                newpath = createImageNamefolder(folderdata[p]["path"])
                pathh = folderdata[p]['image']
                try:
                    img = io.imread(pathh)
                except:
                    img = Image.open(pathh)
                    img = np.asarray(img)
                img = rgbToGray(img)
                image = folderdata[p]['image']

        except Exception as e:
            logger.error(f"unable to APPLY operations due to:{str(e)}",)
            pass


        sample_image = img
        img = skimage.util.img_as_float(img)
        pixelX, pixelY = folderdata[p]['PixelSizeX'], folderdata[p]['PixelSizeY']
        default = False
        if mainwf:
            scale = None
            if folderdata[p].get('popup_val') and folderdata[p]['popup_val'] != '' and folderdata[p].get('draw_val') and folderdata[p].get('draw_val') != '':
                scale = int(folderdata[p]['popup_val'])/ folderdata[p]['draw_val']
            popup_unit = folderdata[p]['popup_unit'] if (folderdata[p].get('popup_unit') and folderdata[p]['popup_unit'] != '' and scale) else None
            data = await filtersToBeApllied( mainwf, post_visu, img, pixelX,
                                                pixelY, newpath, user_id, sample_image, default, 
                                                'assigningworkflow', folderdata[p]['path'], scale, popup_unit, True)
            data['cropimg'] = image
            segmentfilter = False
            visualization = False
            binaryimage = data['segmented_img']
            findsegmentfilter = (list(filter(lambda val: val['Steps'] == 2, mainwf)))
            if findsegmentfilter:
                vis = findsegmentfilter[0]['Params']['visualization']
                if vis == 'Black/white (default)':
                    visualization = False
                else:
                    visualization = True
                    try:
                        binaryimage = data['postprocessedlayers'][-1]['black&white']
                    except:
                        binaryimage = data['segmentationlayers'][-1]['black&white']

                segmentfilter = True
            else:
                segmentfilter = False    
            cropthum, segthum, seg_orig = createThumbforCropandSegmentedImg(image, data['segmented_img'], newpath,
                                                                             visualization, binaryimage, datasetid, segmentfilter)
            data['crop_thumb'] = cropthum
            data['segmented_imgthumb'] = segthum
            foldername, _ = os.path.split(data['segmented_img'])
        
        else:
            data = {}
            data['cropimg'] = image
            cimg = cv2.resize(img, (300, 300))
            cropthum = newpath + '/' + 'thumbnail_crop'+str(int(round(time.time() * 1000)))+'.png'
            cv2.imwrite(cropthum, cimg)
            cropthum = cropthum.replace('\\','/')
            data['crop_thumb'] = cropthum
            data['segmented_imgthumb'] = cropthum
            data['segmented_img'] = data['cropimg']
            data['preprocessedlayers'], data['segmentationlayers'], data['postprocessedlayers'] = [], [], []
            h, w = img.shape[:2]        
            data['cropimg_shape'] = [h, w]

            segthum = cropthum

        annotation_data_df = None
        if 'annotation_data_df' in data:
            annotation_data_df = data['annotation_data_df']
            del data['annotation_data_df']

        data['orignalpath'] = folderdata[p]['orignalpath']
        foldername, _ = os.path.split(data['segmented_img'])  
        basefoldername = os.path.split(os.path.dirname(data['segmented_img']))[0]
        if not batchoutput_dir:
            outputDirectory = fetchKeysValue('outputDirectory', outputdir_info)
            if outputDirectory:
                output_dir = outputDirectory
                output_dir = addSlashonLastIndex(output_dir)
            else:
                batchdir = basefoldername + '/batchprocessed/'
                batchdir = checkEnv(batchdir)
                if not os.path.exists(batchdir):
                    os.mkdir(batchdir)
                output_dir = batchdir
        else:
            output_dir = batchoutput_dir 
        
        # if callfrom == 'backgroundbatch':
        #     if obj['apply_wf_analysis']:
        #         Analysis_info['analysis_type'] = obj['analysis_type'] 
        #         Analysis_info['feature_profile_type'] = obj['feature_profile_type']
        #         Analysis_info['tier_type'] = obj['tier_type'] 
        #         Analysis_info['metal_recess_type'] = obj['metal_recess_type']
        #         Analysis_info['carryanalysis'] = obj['carryanalysis']
        #         Analysis_info['carryscalebar'] = obj['carryscalebar']
        #         if obj['reading_scalebar']:
        #             Analysis_info['popup_val'] = folderdata[p]['popup_val']
        #             Analysis_info['draw_val'] = folderdata[p]['draw_val']
        #             Analysis_info['popup_unit'] = folderdata[p]['popup_unit']
            
                
        # seg_img = data['segmented_img']

        # analysis, excel_path, annotated, p_analysis, pdf_path, tier_voids_analysis, metalrecess_analysis, bubble_analysis, pillar_c2c_analysis, pillar_anomaly_analysis, metal_voids_analysis = '', '', '', '', '', '', '', '', '', '', '',
        # if Analysis_info['carryanalysis'] and Analysis_info['analysis_type']:
            

        #     for ana in Analysis_info['analysis_type']:
        #         msg = 'Running analysis: '+ana
        #         # sendProgressNotification(obj['progressurl'],obj['runId'],status=msg)
        #         print('analysis:    ',ana)
        #         scalebarextarction = fetchKeysValue('scalebarextarction', folderdata[p])
        #         draw_val = int(folderdata[p]['draw_val'])
                
        #         if float(folderdata[p]['popup_val']) < 1 and folderdata[p]['popup_unit'] == MICRONM:
        #             popup_val = float(float(folderdata[p]['popup_val'])*1000)
        #             popup_unit = 'nm'
        #         else:
        #             popup_val = float(folderdata[p]['popup_val'])
        #             popup_unit = folderdata[p]['popup_unit']
                    
        #         scale = float(popup_val)/float(folderdata[p]['draw_val'])

        #         try:
        #             if ana == 'pillar_c2c_analysis' or ana == 'pillar2':
                        
        #                 pillar_c2c_analysis, error = batchpillarc2c(img, output_dir, os.path.splitext(fullname)[0], newpath, scale,
        #                                        folderdata[p]['popup_unit'], int(folderdata[p]['draw_val']),
        #                                        int(folderdata[p]['popup_val']), data['orignalpath'], user_id, obj, scalebarextarction)
                    
        #             elif ana == 'pillar_analysis' or ana == 'pillar_analysis_combined':
    
        #                 analysis, excel_path, annotated, pdf_path, error = batchpillaranalysis(data, output_dir, os.path.splitext(fullname)[0], newpath, scale, popup_unit,
        #                                draw_val, popup_val, data['orignalpath'], user_id, scalebarextarction)
                    
        #             elif ana == 'pillar_anomaly_analysis' or ana == 'pillar_anomaly':
                        
        #                 ellipticity_threshold = fetchKeysValue('ellipticity_threshold', obj)
        #                 sigma_threshold = fetchKeysValue('sigma_threshold', obj)
                        
        #                 pillar_anomaly_analysis, error = batchpillaranomalyanalysis(img, output_dir, os.path.splitext(fullname)[0], newpath, scale, popup_unit,
        #                                                    ellipticity_threshold, sigma_threshold, scalebarextarction)
    
        #             elif ana == 'profile_analysis':
        #                 both = False
        #                 p_analysis, profileanalysis, outlineanalysis, scaled_data, error = getProfileAnalysisData(data, popup_unit, draw_val, popup_val, user_id, both, callfrom, Analysis_info['feature_profile_type'], output_dir, error, scalebarextarction, os.path.splitext(fullname)[0])

        #             elif ana == 'tier_analysis':
        #                 tier_voids_analysis, error = getTierAnalysisData(data, user_id, callfrom, Analysis_info['tier_type'], popup_unit, draw_val, popup_val, output_dir, error, scalebarextarction) 

        #             elif ana == 'metal_recess_analysis':
        #                 metalrecess_analysis, error = getMetalRecessAnalysisData(data, user_id, callfrom, popup_unit, draw_val, popup_val, output_dir, Analysis_info[ 'metal_recess_type'], error, scalebarextarction)
        #             elif ana == 'bubble_analysis':
        #                 bubble_analysis, error = getBubbleAnalysisData(data, user_id, callfrom, popup_unit, draw_val, popup_val, output_dir, error, data['orignalpath'], scalebarextarction)
                        
        #             elif ana == 'metal_voids_analysis':
        #                 spacing = fetchKeysValue('spacing', folderdata[p])
        #                 scale = fetchKeysValue('scale', folderdata[p])
        #                 metal_voids_analysis, error = batch_mv(data, user_id, callfrom, popup_unit, draw_val, popup_val, output_dir, error, data['orignalpath'], spacing, scale, scalebarextarction)

        #         except:
        #             traceback.print_exc()

        # else:
        #     pass

        foldername, _ = os.path.splitext(folderdata[p]['path'])
        collection = db.workflowimagespath
        report = collection.delete_many({'sample_name': foldername})
        rec_id2 = collection.insert_one({'sample_name': foldername, "path": folderdata[p]['path'],
                                         "data":data, "workflow_id": workflowid} )

        # rec_id2 = collection.insert_one({'sample_name': foldername, "path": folderdata[p]['path'],"data":data, "workflow_id": workflowid, 'analysis': analysis, 'excel_path': excel_path, 'annotate_img': annotated,'pdf_path': pdf_path, 'profile_analysis': p_analysis, 'tier_analysis': tier_voids_analysis, 'metal_recess_analysis': metalrecess_analysis, 'bubble_analysis': bubble_analysis,  'pillar_c2c_analysis': pillar_c2c_analysis, 'pillar_anomaly_analysis': pillar_anomaly_analysis, 'metal_voids_analysis': metal_voids_analysis} )
        if annotation_data_df is not None:
            inserted_id = str(rec_id2.inserted_id)
            save_image_annotations_data(foldername,inserted_id,annotation_data_df)
    else:
        fpath, name = os.path.split(folderdata[p]["path"])
        image = folderdata[p]['image']
        segthum = ''
        
    progress = (PROGRESSCOUNT/len(folderdata))*100
    PROGRESSCOUNT = PROGRESSCOUNT +1
    appliedid = retrieveProcessedWfId(folderdata[p]['path'])
    data = {"user_id": user_id, "segmetedimg":segthum, "cropimg": image,
             'path': folderdata[p]['path'], "appliedid": appliedid , 'progressbar': progress}
    
    
    if callfrom == 'backgroundbatch':
    
        dummy = {'test':'123'}
        data = dummy
#        x = requests.post(obj['url'], data=data)
        data['error'] = error
    else:
        data['folderId'] = os.path.basename(os.path.split(folderdata[p]['path'])[0])
        url = environment.image_batch_processing_socket
        try:
            await send_data(data=data,url=url)
        except Exception as e:
            logger.error(f"Exception occurred: {str(e)}")

    return data    

async def startBatchProcess(obj, db_sync_client):
    global db
    db = db_sync_client
    user_id = obj['userId']
    folderids = obj['folderIds']
    maindata = []
    starttime = time.time()
    
    # if obj["jobType"]=="schedule": 
        
    #     import datetime
    #     # storing parameters: 
    #     json_file_name = "ImageBatchParallel_"+obj["userId"]+".json"
    #     with open(airflow_task_objects+json_file_name, "w") as outfile: 
    #         obj["jobType"] = "quick"
    #         json_object = json.dumps(obj, indent = 4) 
    #         outfile.write(json_object) 
    
    #     # creating scheduling file for the user:
    #     difference = obj["time"]            
    #     utc_now = datetime.datetime.utcnow()
    #     utc_after = utc_now + datetime.timedelta(minutes = difference)
    #     start_date = (utc_now.year, utc_now.month-1, utc_now.day, utc_after.hour)
    #     schedule_interval = "{0} {1} {2} * *".format(utc_after.minute, utc_after.hour, utc_after.day)
    
    #     params = dict()
    #     params['task_names'] = ["ImageBatchParallel"]
    #     params['dag_name'] = params['task_names'][0]+"_"+obj["userId"] 
    #     params['start_date'] = start_date
    #     params['schedule_interval'] = schedule_interval
    #     params['auto_deletion'] = True
    #     y = requests.post(url="http://0.0.0.0:8081/create_dag",data=json.dumps(params)) 
    #     return 
    
    
    # if 'generatedTaskId' in obj:
    #     task_id = obj["generatedTaskId"]
    # else:
    #     task_id = None
    
    
    collection = db.categorizeddata
    for folderid in folderids:
        report = collection.find_one({'_id': ObjectId(folderid) })
        data = report['data']
        imagesdata = data['SEM'] + data['OM'] + data['NA']
        folderid = report['folderId']
        datasetid = report['dataset_id']
        imageData = []
        for i in imagesdata:
            scalebar_options = i['scalebar_options']
            temp = {'orignalpath': i['path'], 'path': i['path'], 
                    'PixelSizeX': i['PixelSizeX'], 'PixelSizeY': i['PixelSizeY'],
                'draw_val': scalebar_options['scalebarByImage'], 
                'popup_val': scalebar_options['scalebarByPhysical'],
                    'popup_unit': scalebar_options['scalebarByPhysicalUnit'],'image_masks':i['image_masks'],
                    'rotate_options':i['rotate_options'],'manual_coordinates':i['manual_coordinates'],'strip_size':i['ImageStripSize']}
            
            scale, unit = getscaleandunitval(i['PixelSizeX'])
            if scale:
                temp['scale'] = scale
                temp['popup_unit'] = unit
                
            imgpathwithname = os.path.splitext(i['path'])[0]
            temp['workflowid'] = retrieveWfId(i['path'])
            temp['appliedid'] = retrieveProcessedWfId(imgpathwithname)
            if i['crop_type'] == 'manual':
                temp['image'] = i['manual_image']
            else:
                temp['image'] = i['modified_path']
            imageData.append(temp)

            
        obj = {'imageData': imageData, 'datasetid': datasetid}
        folderdata = imageData
        mode = 'noraml'
        if mode == 'parallel':
            with concurrent.futures.ThreadPoolExecutor(4) as executor:
                results = [executor.submit(imagesParallelWfApplying, p, user_id, folderdata, obj) for p in range(len(folderdata))]
        else:
            for p in range(len(folderdata)):
                await imagesParallelWfApplying(p, user_id, folderdata, obj)

    maindata = {"status":"completed"}
    msg = f"Workflow processed on '{folderid}' "
    actionSummary({'datasetid': datasetid, 'msg': msg, 'userid': user_id}, 'curationsummary')
    return maindata

def getBatchStatus(path, db):
    collection = db.multiplyimagesworkflow
    report = collection.find_one({'image_path': path})
    if report:
        collection = db.workflowimagespath
        fname, _ = os.path.splitext(path) 
        repo = collection.find_one(
                                {'sample_name': fname})
        if repo:
            return 1, 1
        else:
            return 1, 0
    else:
        return 0, 0

def getFolderStatus(i, db, folderId, maindata):
    cat = ['SEM', 'OM', 'NA']
    for c in cat:
        
        if i[c]:
            wf = []
            batch = []
            with concurrent.futures.ThreadPoolExecutor() as executor:
                results = [executor.submit(getBatchStatus, path['path'], db) for path in i[c]]
                for f in concurrent.futures.as_completed(results):
                    res = list(f.result())
                    if res[0]==0:
                        wf.append(0) 
                        batch.append(0) 
                    else:
                        wf.append(res[0]) 
                        batch.append(res[1])  

            if (0 in wf and 0 in batch) or not i[c]:
                i['batch'] = 0
                i['workflow'] = 0
            elif 0 not in wf and 0 in batch:
                i['batch'] = 0
                i['workflow'] = 1
            else:
                i['batch'] = 1
                i['workflow'] = 1

            maindata.append({'workflow': i['workflow'], 'batch': i['batch'], 'folderId': folderId,
                             'type': c})
        else:
            maindata.append({'workflow': 1, 'batch': 1, 'folderId': folderId,
                             'type': c})
    
def getFinalStatus(newlist):
    for s in newlist:
        if s['workflow'] == 1 and s['batch'] == 1:
            temp = {'workflow': 1, 'batch': 1, 'folderId': s['folderId']}
        
        elif s['workflow'] == 1 and s['batch'] == 0:
            temp = {'workflow': 1, 'batch': 0, 'folderId': s['folderId']}
            break
        elif s['workflow'] == 0:
            temp = {'workflow': 0, 'batch': 0, 'folderId': s['folderId']}
            break
    return temp

def updateWfandBatchStatus(obj, db_sync_client):
    global db
    dataset_id = obj['dataset_id']
    name = obj['dataset_name']
    demo = obj['demo']
    folders = obj['images']

    db = db_sync_client
    collection = db.categorizeddata
    # if demo:
    #     name = name + '_demo'
    # else:
    #     pass
    reports = collection.find({'dataset_id': dataset_id})
#     for report in reports:
#         print("report", report)
    maindata = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        [executor.submit(getFolderStatus, i['data'], db, i['folderId'], maindata) for i in reports]
     
    sorttesreuslt = sorted(maindata, key=lambda k: k['folderId']) 
    looplimit = len(sorttesreuslt)//3
    count = 0
    newdata = []
    for i in range(looplimit):
        newlist = []
        a = count
        count += 1
        b = count
        count += 1
        c = count
        count += 1
        newlist.append(sorttesreuslt[a])
        newlist.append(sorttesreuslt[b])
        newlist.append(sorttesreuslt[c])
        newdata.append(getFinalStatus(newlist))
    return newdata

def getWorkflowsFromDB(project_id, image_analysis_dao):
    db = image_analysis_dao
    collection = db.sampleworkflows 
    data = []
    cursor = collection.find({"project_id":project_id})

    for record in cursor:
        idd = (record['_id'])
        record['_id'] = str(idd) 
        try:
            d_id = record['dataset_id']
            datasets = db['datasets'].find_one({"_id":ObjectId(d_id)})
            record['dataset_name'] = datasets['name']
        except:
            continue
        data.append(record)
    return data

#crop image

def rotateAndSave(modified_path, degrees, call_from="default"):
    try:
        logger.info("Inside rotateAndSave ")
        img = Image.open(modified_path)
        rotatedImg = img.rotate(360-degrees, expand=1)
        img = img_as_ubyte(rotatedImg)
        path, img_name = os.path.split(modified_path)
        if path.split('/')[-1] == 'processedimg':
            path = path.replace('processedimg', 'modifiedimages')
        _, ext = os.path.splitext(img_name)
        new_path = path+'/'+'rotated_img_'+str(int(round(time.time() * 1000)))+ext
        thumbpath = path + '/'+'rotated_img_thumbnail'+'_'+str(int(round(time.time() * 1000)))+'.jpg'
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB) # Convert BGR to RGB
        im = cv2.resize(img, (300, 300))
        if call_from =='imagesParallelWfApplying':
            return img
        
        cv2.imwrite(thumbpath, im)
        cv2.imwrite(new_path, img)
        img1 = img
        # width, height = np.array(rgb2gray(img1)).shape
        height, width = img1.shape[:2]
        return {'modified_path':new_path,'modified_thumbnail':thumbpath,'modified_shape': [height, width]}
    except Exception as e:
        logger.error(f"Unable to rotate the image due to:{str(e)}")

def cropImageUsingMetadata(i, newdirpath, callfrom=''):
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
        io.imsave(newpathh, img)
    elif stripsize==0:
        shape = [img.shape[0],img.shape[1]]
        im = cv2.resize(img, (300, 300))
        cv2.imwrite(thumbpath, im)
        io.imsave(newpathh, img)
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
    idd = retrieveWfId(i['path'])
    if idd:
        appliedid = retrieveProcessedWfId(i['path'])
    else:
        appliedid = 0

    temp = {"tif_path": i['path'], 'path': newpathh, "workflow_id": idd, "modified_thumbnail":thumbpath, "applied_id": appliedid, 'shape': shape}
    data.append(temp)
    if callfrom == 'categorizeAPI':
        return temp
    else:
        return data    

def crop_image_using_strip_size(cord, img):
    logger.info("Inside crop_image_using_strip_size")
    logger.info(f"Image Shape: {img.shape}")
    shape = img.shape
    h  = shape[0]
    w  = shape[1]      
    stripsize = cord['stripsize']
    ym = h-stripsize
    img = img[0:ym, 0:w]
    return img

def crop_image_using_coordinates(cord, img):
    logger.info("Inside crop_image_using_coordinates")
    logger.info(f"Image Shape: {img.shape}")
    shape = img.shape
    h  = shape[0]
    w  = shape[1]    
    x1 = cord['x1']
    y1 = cord['y1']
    x2 = cord['w']
    y2 = cord['h']
    x1 = int(w *(x1/100))
    y1 = int(h *(y1/100))
    x2 = int(x1 +(w*(x2/100)))
    y2 = int(y1 +(h*(y2/100)))
    img = img[y1:y2, x1:x2]
    return img

def cropAndRotate(collection, obj, apply_crop=True):
    try:
        logger.info("Inside cropAndRotate")
        crop_type = obj['crop_type']
        Ym = obj['ymax']
        base_image = collection['image']
        img = io.imread(base_image)
        # img = rgbToGray(img)
        h = img.shape[0]
        w = img.shape[1]

        collection['crop_type'] = crop_type
        
        rotate_options = collection['rotate_options']
        
        if crop_type=='auto':
            if rotate_options['auto_rotate']:
                modified_path = collection['modified_path']
                modified_thumbnail = collection['modified_thumbnail']

                crop_obj = {"path": collection['path'], "ImageStripSize": collection['ImageStripSize']}
                folder_path, img_name = os.path.split(modified_path)
                cropped_data = cropImageUsingMetadata(crop_obj, folder_path, 'categorizeAPI')

                modified_data = rotateAndSave(cropped_data['path'],rotate_options['rotateval'])
                modified_thumbnail_data= rotateAndSave(cropped_data['modified_thumbnail'],rotate_options['rotateval'])
                # if modified_path!='' and os.path.exists(modified_path):
                #     os.remove(modified_path)
                # if modified_thumbnail!='' and os.path.exists(modified_thumbnail):
                #     os.remove(modified_thumbnail)
                # if cropped_data['path']!='' and os.path.exists(cropped_data['path']):
                #     os.remove(cropped_data['path'])
                # if cropped_data['modified_thumbnail']!='' and os.path.exists(cropped_data['modified_thumbnail']):
                #     os.remove(cropped_data['modified_thumbnail'])

                if rotate_options['rotateval']==0:
                    collection['rotate_options']['auto_rotate'] = False
                collection['modified_path'] = modified_data['modified_path']
                collection['modified_thumbnail'] =  modified_thumbnail_data['modified_path']
                collection['modified_shape'] = modified_data['modified_shape']
            collection['image_masks'] = [] 
            return collection

        else:
            imgpath = base_image
            imgpath = imgpath.replace('/processedimg','')
            imgpath, _ = os.path.splitext(imgpath)

            Ym = int(Ym)
            if Ym!=0:
                img = img[0:Ym, 0:w]
                newpath = createImageNameDir(base_image)
                newpathh = newpath + '/'+'automatic_croped'+'_'+str(int(round(time.time() * 1000)))+'.png'
                cv2.imwrite(newpathh, img)
                height, width = img.shape
                collection['crop_type'] = 'auto'
                collection['modified_path'] = newpathh
                collection['modified_thumbnail'] =  newpathh
                collection['modified_shape'] = [height, width]

                if rotate_options['auto_rotate']:
                    modified_path = newpathh
                    modified_thumbnail = newpathh

                    modified_data = rotateAndSave(modified_path,rotate_options['rotateval'])
                    modified_thumbnail_data= rotateAndSave(modified_thumbnail,rotate_options['rotateval'])
                    # if modified_path!='' and os.path.exists(modified_path):
                    #     os.remove(modified_path)
                    # if modified_thumbnail!='' and os.path.exists(modified_thumbnail):
                    #     os.remove(modified_thumbnail)

                    if rotate_options['rotateval']==0:
                        collection['rotate_options']['auto_rotate'] = False
                    collection['modified_path'] = modified_data['modified_path']
                    collection['modified_thumbnail'] =  modified_thumbnail_data['modified_path']
                    collection['modified_shape'] = modified_data['modified_shape']
                collection['image_masks'] = []    
                return collection

            else:
                modified_path = collection['manual_image']
                # img = io.imread(modified_path)        
                # if modified_path!='' and os.path.exists(modified_path):
                #     os.remove(modified_path)
                
                cord = obj['coordinates']
                                
                base_dirname, image_name = os.path.split(base_image)
                name, ext = os.path.splitext(image_name)
                
                # newpath = createImageNameDir(base_image)
                newpath = base_dirname.replace('/processedimg','')
                newpath = newpath+'/'+"modifiedimages"
                # newpathh = newpath + '/'+name+ext
                # thumbpath  = newpath + '/'+'thumb_'+name+'.jpg'
                newpathh = newpath + '/'+'manual_croped'+'_'+str(int(round(time.time() * 1000)))+'.png'
                thumbpath = newpath + '/'+'manual_croped_thumbnail'+'_'+str(int(round(time.time() * 1000)))+'.jpg'

                if cord['autoCropBar'] == True:
                    img = crop_image_using_strip_size(cord, img)
                    height, width = img.shape


                else:
                    rotate_image = None
                    if rotate_options['manual_rotate']:
                        modified_data = rotateAndSave(base_image,rotate_options['rotateval'])

                        if rotate_options['rotateval']==0:
                            collection['rotate_options']['manual_rotate'] = False
                        rotate_image = collection['rotate_image'] = collection['manual_image'] = modified_data['modified_path']
                        collection['rotate_thumbnail'] = collection['manual_thumbnail'] = modified_data['modified_thumbnail']                        
                        collection['rotate_options']['shape'] = collection['manual_shape'] = modified_data['modified_shape']
                    
                    if apply_crop:
                        if rotate_image:
                            img = io.imread(rotate_image)
                        img = crop_image_using_coordinates(cord, img)
                        height = img.shape[0]
                        width = img.shape[1]
                        collection['manual_shape'] = [height, width]
                        img = img_as_ubyte(img)
                        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB) # Convert BGR to RGB
                        cv2.imwrite(newpathh, img)
                        im = cv2.resize(img, (300, 300))
                        cv2.imwrite(thumbpath, im)
                        collection['crop_type'] = crop_type
                        collection['manual_coordinates'] = obj['coordinates']
                        collection['manual_image'] = newpathh
                        collection['manual_thumbnail'] = thumbpath

                    # try:
                    #     if collection['manual_image']!='' and os.path.exists(collection['manual_image']):
                    #         os.remove(collection['manual_image'])
                    #     if collection['manual_thumbnail']!='' and os.path.exists(collection['manual_thumbnail']):
                    #         os.remove(collection['manual_thumbnail'])
                    # except:
                    #     pass

                    
                    

                    collection['image_masks'] = [] 
                    return collection
    except Exception as e:
        logger.error(f"failed to execute cropAndRotatedue to {str(e)}")
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]        

def updateCropData(category, collection, obj):
    
    for imageindex in range(len(collection['data'][category])):
        collection['data'][category][imageindex] = cropAndRotate(collection['data'][category][imageindex], obj)
    return collection 

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

def getCategorizationData(obj):
    dataset_id = obj['dataset_id']

    response_data = []
    # db = establishConnection()
    collection = db.categorizeddata
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
        [executor.submit(getcropandsegmentdata, db, i) for i in response_data]
    
    response_data[0]['img_details'].sort(key=lambda f: os.path.getmtime(f['path']))
#     response_data[0]['img_details'].reverse()
    for i in response_data[0]['img_details']:
        i['imagename'] =  os.path.split(i['path'])[1]
    return response_data

def cropImage(obj, db_sync_client):
    global db
    db = db_sync_client
    crop_type = obj['crop_type']
    flag = obj['save']
    userid = obj['user_id']
    cmplt = obj['image']
    folderpath = obj['folderpath']
    datasetid = obj['datasetid']
    foldername = obj['foldername']
    category = obj['category']
    originalimgpath = obj['imgpath']
    applytoall = obj['applytoall']

    return_data = {}

    # db = establishConnection()
    collection = db.categorizeddata.find_one({'dataset_id':datasetid,'folderId':foldername}, sort=[( '_id', pymongo.DESCENDING )])    
    if applytoall:
        categories = ['SEM','OM','NA']
        for category in categories:
            collection = updateCropData(category, collection, obj)

    else:
        folderdata = collection['data']
        folderCategoryData = []
        if category=='SEM':
            folderCategoryData = folderdata['SEM']
        elif category=='OM':
            folderCategoryData = folderdata['OM']
        else:
            folderCategoryData = folderdata['NA']
        imageindex = [i for i in range(len(folderCategoryData)) if folderCategoryData[i]['path'] == originalimgpath][0]
        image_mask = collection['data'][category][imageindex]['image_masks']
        if image_mask:
            logger.info("Cannot crop the image as it is already image masked")
            return {'status': False, 'message': 'Cannot crop the image as it is already image masked'}

        collection['data'][category][imageindex] = cropAndRotate(collection['data'][category][imageindex], obj)
        
        if collection['data'][category][imageindex]['crop_type']=='auto':
            return_data = {"croppedimagepath": collection['data'][category][imageindex]['modified_path'], "croppedthumbnail": collection['data'][category][imageindex]['modified_thumbnail'], "croppedshape":collection['data'][category][imageindex]['modified_shape']}
        else:
            return_data = {'croppedimagepath':collection['data'][category][imageindex]['manual_image'], 'croppedshape':collection['data'][category][imageindex]['manual_shape']}
            collection['data'][category][imageindex]['manual_coordinates'].update({'crop_cord': True})
    db.categorizeddata.update_one(
        {"_id":collection["_id"]}, 
        { "$set": {
            "data":collection['data']
        }}
    )

    if applytoall:
        return_data = getCategorizationData({'dataset_id': datasetid})

    return return_data

# update crop images
def getfoldersImages(obj, db_sync):
    global db
    db = db_sync
    folders = obj['folders']
    result = []

    for folder in folders:
        imagedata = folder['imageData']
        dirpath, name = os.path.split(imagedata[0]['path'])
        croppedimages = []

        workflow_id_collection = db.multiplyimagesworkflow
        appliedId_collection = db.workflowimagespath

        for image in imagedata:
            workflow_id = 0
            workflow_collection = workflow_id_collection.find_one(
                {'image_path': image['path']})
            if workflow_collection:
                workflow_id = workflow_collection['w_id']

            appliedId = 0
            applied_collection = appliedId_collection.find_one(
                {'path': image['path']})
            if applied_collection:
                appliedId = str(applied_collection['_id'])

            imagename = os.path.split(image['path'])[1]
            if (image['crop_type'] == 'auto'):
                data = {"tif_path": image['path'],
                        "croppedimage": image['modified_path'],
                        "croppedimage_thumb": image['modified_thumbnail'],
                        "croppedshape": image['modified_shape'],
                        "workflow_id": workflow_id,
                        "applied_id": appliedId,
                        'imagename': imagename}
            else:
                manual_thumbnail = image['manual_image']
                if fetchKeysValue('manual_thumbnail', image):
                    manual_thumbnail = image['manual_thumbnail']
                data = {"tif_path": image['path'],
                        "croppedimage": image['manual_image'],
                        "croppedimage_thumb": manual_thumbnail,
                        "croppedshape": image['manual_shape'],
                        "workflow_id": workflow_id,
                        "applied_id": appliedId,
                        'imagename': imagename}

            croppedimages.append(data)

        retdata = {'croppedimages': croppedimages}
        retdata['croppedimages'].sort(key=lambda f: os.path.getmtime(f['tif_path']))
        result.append(retdata)

    return result
def getResizeImages(obj, db_sync):
    global db
    db = db_sync
    demo  = obj['demo']
    imagedata = obj['imageData']
    dirpath, name = os.path.split(imagedata[0]['path'])
    foldername = obj['foldername']
    newdirpath = dirpath + '/modifiedimages'
    croppedimages = []

    # db = establishConnection()
    workflow_id_collection = db.multiplyimagesworkflow
    appliedId_collection = db.workflowimagespath
    
    for image in imagedata:
        
        workflow_id = 0
        workflow_collection = workflow_id_collection.find_one(
                {'image_path': image['path']})        
        if workflow_collection:
            workflow_id = workflow_collection['w_id']

        
        appliedId = 0
        applied_collection = appliedId_collection.find_one(
                {'path': image['path']})        
        if applied_collection:
            appliedId = str(applied_collection['_id'])
            
        imagename = os.path.split(image['path'])[1] 
        if(image['crop_type']=='auto'):
            data = {"tif_path":image['path'],
                    "croppedimage":image['modified_path'], 
                    "croppedimage_thumb":image['modified_thumbnail'],
                     "croppedshape":image['modified_shape'],
                     "workflow_id":workflow_id,
                     "applied_id":appliedId,
                   'imagename': imagename}
        else:
            manual_thumbnail = image['manual_image']
            if fetchKeysValue('manual_thumbnail', image):
                manual_thumbnail = image['manual_thumbnail']
            data = {"tif_path":image['path'],
                    "croppedimage": image['manual_image'],
                      "croppedimage_thumb":manual_thumbnail,
                      "croppedshape":image['manual_shape'],
                      "workflow_id":workflow_id,"applied_id":appliedId,
                        'imagename': imagename}
        
        croppedimages.append(data)
    
    retdata = {'croppedimages':croppedimages}
    
    retdata['croppedimages'].sort(key=lambda f: os.path.getmtime(f['tif_path']))
#     retdata['croppedimages'].reverse()

    
    return retdata

#rotateimage

def updateRotateData(category, collection, obj, degrees):
    
    for imageindex in range(len(collection['data'][category])):
        crop_type = collection['data'][category][imageindex]['crop_type']
        collection['data'][category][imageindex]['rotate_options']['rotateval'] = degrees
        collection['data'][category][imageindex]['rotate_options'][crop_type+'_rotate'] = True
        manual_coordinates = collection['data'][category][imageindex]['manual_coordinates']
        crop_obj = {'crop_type': crop_type, 'image': collection['data'][category][imageindex]['image'], 'ymax': 0, 'coordinates': manual_coordinates}
        collection['data'][category][imageindex] = cropAndRotate(collection['data'][category][imageindex], crop_obj, apply_crop=False)
        if degrees>0:
            collection['data'][category][imageindex]['rotate_options']['auto_rotate'] = True
            collection['data'][category][imageindex]['rotate_options']['manual_rotate'] = True
        else:
            collection['data'][category][imageindex]['rotate_options'][crop_type+'_rotate'] = False 
    return collection

def rotateImage(obj, db_sync_client):    
    try:
        global db
        db = db_sync_client
        category =  obj['category'] 
        crop_type =  obj['crop_type']
        floderpath =  obj['folderpath']
        path =  obj['path']
        degrees = obj['degrees']
        userid = obj['user_id']
        dataset_id = obj['dataset_id']
        foldername = obj['foldername']
        applytoall = obj['applytoall']

        return_data = {}
        rotate_image = None
        rotate_thumbnail = None
        
        # db = establishConnection()
        collection = db.categorizeddata.find_one({'dataset_id':dataset_id,'folderId':foldername}, sort=[( '_id', pymongo.DESCENDING )])
        
        if applytoall:
            categories = ['SEM','OM','NA']
            for category in categories:
                collection = updateRotateData(category, collection, obj, degrees)
        else:
            folderdata = collection['data']
            folderCategoryData = []
            if category=='SEM':
                folderCategoryData = folderdata['SEM']
            elif category=='OM':
                folderCategoryData = folderdata['OM']
            else:
                folderCategoryData = folderdata['NA']

            imageindex = [i for i in range(len(folderCategoryData)) if folderCategoryData[i]['path'] == path][0]
            
            crop_type = folderdata[category][imageindex]['crop_type']
            collection['data'][category][imageindex]['rotate_options']['rotateval'] = degrees
            collection['data'][category][imageindex]['rotate_options'][crop_type+'_rotate'] = True
            
            manual_coordinates = collection['data'][category][imageindex]['manual_coordinates']
            image_mask = collection['data'][category][imageindex]['image_masks']
            crop_cord = manual_coordinates.get('crop_cord', False)
            if crop_cord:
                logger.info("Cannot rotate the image as it is already cropped")
                return {'status': False, 'message': 'Cannot rotate the image as it is already cropped'}
            
            if image_mask:
                logger.info("Cannot rotate the image as it is already image masked")
                return {'status': False, 'message': 'Cannot rotate the image as it is already image masked'}
            
            
            crop_obj = {'crop_type': crop_type, 'image': collection['data'][category][imageindex]['image'], 
                        'ymax': 0, 'coordinates': manual_coordinates}
            
            collection['data'][category][imageindex] = cropAndRotate(collection['data'][category][imageindex], crop_obj, apply_crop=False)
            
            rotate_image = collection['data'][category][imageindex]['rotate_image']
            rotate_thumbnail = collection['data'][category][imageindex]['rotate_thumbnail']      

            if degrees>0:
                collection['data'][category][imageindex]['rotate_options']['auto_rotate'] = True
                collection['data'][category][imageindex]['rotate_options']['manual_rotate'] = True
            else:
                collection['data'][category][imageindex]['rotate_options'][crop_type+'_rotate'] = False 

            modified_path = ''  
            modified_thumbnail = ''
            modified_shape = ''   
            if crop_type ==  'auto':
                modified_path = collection['data'][category][imageindex]['modified_path']
                modified_thumbnail = collection['data'][category][imageindex]['modified_thumbnail']
                modified_shape = collection['data'][category][imageindex]['modified_shape']
            else:
                modified_path = collection['data'][category][imageindex]['manual_image']
                modified_thumbnail = collection['data'][category][imageindex]['manual_thumbnail']
                modified_shape = collection['data'][category][imageindex]['manual_shape']

            return_data = {'modified_path':modified_path, 'modified_thumbnail':modified_thumbnail,'modified_shape' : modified_shape, 'rotate_image':rotate_image, 'rotate_thumbnail':rotate_thumbnail}
        db.categorizeddata.update_one(
                    {"_id":collection["_id"]},
                    { "$set": {
                        "data":collection['data']
                    }}
                )
        
        if applytoall:
            return_data = getCategorizationData({'dataset_id': dataset_id})
        
        return return_data 
    except Exception as e:
        logger.error(f"Failed to execute  rotateImage due to {str(e)}")

#scalebar
def extractScalebar(obj):

    A = obj['sample_image']
    A = io.imread(A)
    # if CURRENT_SOCKERPORT in SPOCKPORT:
    #     fig_annotated, scalebar, units, scalebar_width_px, pixel_resolution, image_crop = spocksExtractScalebar(A)
    # else:
    G = rgbToGray(A)
    image_cutoff, image_crop, infobar, G_crop, infobar_cutoff = cropinfobar(G)
    fig_annotated, scalebar, units, scalebar_width_px, pixel_resolution = extractscalebar(infobar, G, image_cutoff)
        
    path, fname  = os.path.split(obj['sample_image'])
    name, _ = os.path.splitext(fname)
    if 'processedimg_test' in path:
        path = path.replace('processedimg_test',name)
    else:
        path = path.replace('processedimg',name)
    
    if not os.path.exists(path):
        os.mkdir(path)
    filepath = path + '/scalebarannotated.png'
    fig_annotated.savefig(filepath, dpi=100, bbox_inches='tight', pad_inches=0) # save image as
    data = {'scalebar_annotated': filepath,'scalebar': int(scalebar), 'units': units, 'scalebar_width_px': int(scalebar_width_px),
          'pixel_resolution': int(pixel_resolution)}

    return data

# Annotation

def retrieveObjectbyQuery(collection, query):    
    obj = collection.find_one(query, sort=[( '_id', pymongo.DESCENDING )])
    if obj:
        obj['_id'] = str(obj['_id'])
    return obj    

def retrieveObjectbyId(_id, collection):
    obj = collection.find_one(
                        {'_id': ObjectId(_id)})
    obj['_id'] = str(obj['_id'])
    return obj

async def fetch_region_prop_details_from_db_document(db_document, check_if_objects_exists: bool =False):
    try:    
        binary_img_ndarray = None
        region_properties_csv_file = None
        crop_img = None
        if db_document and db_document.get('data'):
            post_processedlayers = db_document['data'].get('postprocessedlayers')
            segmentation_layers = db_document['data'].get('segmentationlayers')
            if post_processedlayers : 
                binary_img_ndarray = post_processedlayers[-1].get('binary_img_ndarray')
                region_properties_csv_file = post_processedlayers[-1].get('region_properties_csv_file')
                if check_if_objects_exists :
                    if 'region_properties' in segmentation_layers[-1]:
                        if post_processedlayers[-1]['region_properties'] == '':
                            raise KeyError('No segmented objects found. Please re-check the workflow')
                        elif isinstance(post_processedlayers[-1]['region_properties'],dict):
                            if int(post_processedlayers[-1]['region_properties']['No of objects:']) == 0:
                                raise KeyError('No segmented objects found. Please re-check the workflow.')
            elif segmentation_layers :
                binary_img_ndarray = segmentation_layers[-1].get('binary_img_ndarray')
                region_properties_csv_file = segmentation_layers[-1].get('region_properties_csv_file')
                if check_if_objects_exists :
                    if 'region_properties' in segmentation_layers[-1]:
                        if segmentation_layers[-1]['region_properties'] == '':
                            raise KeyError('No segmented objects found. Please re-check the workflow')
                        elif isinstance(segmentation_layers[-1]['region_properties'],dict):
                            if int(segmentation_layers[-1]['region_properties']['No of objects:']) == 0:
                                raise KeyError('No segmented objects found. Please re-check the workflow.')
            else:
                raise ValueError(f'No segmented layer found for {db_document}')
            crop_img = db_document['data'].get('cropimg')
        else:
            raise ValueError(f'DB document not found properly {db_document}')
        
        if binary_img_ndarray == '' or binary_img_ndarray == None:
            raise ValueError(f'No binary_img_ndarray found for {db_document}')
        
        if region_properties_csv_file == '' or region_properties_csv_file == None:
            raise ValueError(f'No region_properties_csv_file found for {db_document}')
        
        return binary_img_ndarray, region_properties_csv_file, crop_img
    except Exception as e:
        raise e

def generate_hover_info_html(row, df_properties):
    content_part = ''.join([f'<b>{prop_name}:{row[prop_name]}</b><br>' for prop_name in df_properties])
    return content_part

async def generate_interactive_fig_as_json(img, df, binary_labels):

    fig = px.imshow(img, binary_string=True)
    fig.update_traces(hoverinfo='skip')

    #df properties contains the data shown on hovering
    df_properties = []
    if df['Popup_unit'].isna().any():
        df['Units'] = 'px'
        df_properties = ['Object','Label', 'Area(px)','Major_axis_length(px)','Minor_axis_length(px)', 'Aspect_ratio','Units']
    else:
        df['Units'] = df['Popup_unit']
        df_properties = ['Object','Label', 'Area' ,'Length','Height', 'Aspect_ratio','Units']
    
    # Identify columns with numeric values and convert to strs
    numeric_cols = df.select_dtypes(include=['number']).columns
    df[numeric_cols] = df[numeric_cols].applymap(lambda x: f'{float(x):.3e}' if pd.notna(x) else x)
    df = df[['Original_label'] + df_properties].astype(str)
    df['hover_info'] = df.apply(generate_hover_info_html, axis=1, args=(df_properties,))
    df_dict = df[['Original_label', 'hover_info']].set_index('Original_label').to_dict(orient='index')
    for index in range(1, binary_labels.max()+1):
        label_i = f'{float(index):.3e}'
        contours = measure.find_contours(binary_labels == index, 0.5)
        if len(contours) <= 0:
            continue # no contour map can be generated , probably because of no objects
        contour = contours[0]
        y, x = contour.T
        fig.add_trace(go.Scatter(
            x=x, y=y, name=label_i,
            mode='lines', fill='toself', showlegend=False,
            hovertemplate=df_dict[label_i]['hover_info'], hoveron='points+fills'))

    return fig.to_json()

def get_aggregated_df_from_region_props_and_annotation_data(region_props_df, annotation_df):
    region_props_df = region_props_df.drop(columns=['Object','Label'])
    if len(region_props_df) == len(annotation_df):
        df = pd.merge(region_props_df, annotation_df, on='Unique_object_id',validate='one_to_one')
        if len(df) == len(annotation_df):
            return df
        else:
            raise ValueError(f'region_props_csv/annotation_db df length is not matching with merged df length {len(region_props_df)} {len(df)}')
    else:
        raise ValueError(f'region_props_csv df length is not matching with annotation_db df {len(region_props_df)} {len(annotation_df)}')

def get_aggregated_df_from_region_props_and_annotation_data(region_props_df, annotation_df):
    region_props_df = region_props_df.drop(columns=['Object','Label'])
    if len(region_props_df) == len(annotation_df):
        df = pd.merge(region_props_df, annotation_df, on='Unique_object_id',validate='one_to_one')
        if len(df) == len(annotation_df):
            return df
        else:
            raise ValueError(f'region_props_csv/annotation_db df length is not matching with merged df length {len(region_props_df)} {len(df)}')
    else:
        raise ValueError(f'region_props_csv df length is not matching with annotation_db df {len(region_props_df)} {len(annotation_df)}')

async def generate_interactive_image(obj, db_sync):
    try:
        # fetch details from db
        global db
        db = db_sync
        file_name = obj['name']
        # db = establishConnection()
        db_document = retrieveObjectbyQuery(db.workflowimagespath, {'sample_name': file_name})
        if db_document:
            binary_img_ndarray, region_properties_csv_file, crop_img_file = await fetch_region_prop_details_from_db_document(db_document , True)

            binary_img = np.load(binary_img_ndarray)
            df = pd.read_csv(region_properties_csv_file)

            #get annotation data too
            workflowimagespath_db_id = str(db_document['_id'])
            image_annotation_document = retrieveObjectbyQuery(db.seg_image_annotations, {'workflow_db_id': workflowimagespath_db_id})
            if image_annotation_document:
                annotation_df = pd.DataFrame(image_annotation_document['annotation_data'])
                df = get_aggregated_df_from_region_props_and_annotation_data(df, annotation_df)
            else:
                raise f'image_annotation_collection for this {db_document["_id"]} has not been found'
            
            #visualization
            visualization_details = obj['visualization_details']
            visualization = visualization_details['visualization']
            color = visualization_details['color']
            colurs = [{'color':'magenta','val': [1,0,1]},
                    {'color':'red','val' : [1,0,0]},
                    {'color':'yellow' ,'val' : [1,1,0]}]
            crop_img = cv2.imread(crop_img_file)
            crop_img = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY)
            bg_img = callingVisualization(visualization, visualization_details, binary_img, colurs, crop_img)

            interactive_fig_json = await generate_interactive_fig_as_json(bg_img, df, label(binary_img))
            data = {
                "object_labels": json.dumps(image_annotation_document['annotation_data']),
                "interactive_fig_json_data": interactive_fig_json,
                "image_annotation_document_id":str(image_annotation_document['_id'])
            }
            return {"data":json.dumps(data)}
        else:
            return {"message":"NO segmented image"}
    except ValueError as e:
        raise Exception(f"Unable to generate annotated image. Please try re-applying workflow for this image.")
    except KeyError as e:
        raise Exception(str(e))
    except Exception as e:
        img_name = os.path.splitext(obj.get('name'))[-1] if obj.get('name') else 'None'
        raise Exception(f'Unable to generate interactive image and annotation data for following image: {img_name} , error : {e}')
    
        

async def get_temp_region_props_folders_from_images_folder(folder_path):
    temp_folders = []
    try:
        for img_folder in os.listdir(folder_path):
            temp_folder = os.path.join(folder_path, f'{img_folder}/region_properties/temp')
            if os.path.exists(temp_folder):
                temp_folders.append(temp_folder)
    except Exception as e:
        logger.exception(f'Error occurred while fetching temp files from {folder_path} : {e}')
    return temp_folders

def delete_temp_region_props_files(folder_path):
    try:
        temp_folders = get_temp_region_props_folders_from_images_folder(folder_path)
        for temp_folder in temp_folders:
            remove_directory(temp_folder)
    except Exception as e:
        logger.exception(f'Unable to delete all temp region props files from {folder_path}: {e}')

async def replace_spl_chars_with_underscores(input_str: str):
    pattern = r'[^a-zA-Z0-9_]+'
    return re.sub(pattern,'_',input_str)


async def get_dataset_prefix_and_index(project_id, db):
    project_record = retrieveObjectbyId(project_id, db.projects)
    if project_record:
        project_prefix = project_record['prefix']
        def_index = 1
        datasets = retrieveObjectbyQuery(db.DMCreatedDatasets,{'project_id' : project_id})
        if datasets : 
            def_index = datasets.get('index',0) + 1
        return f'{project_prefix}-D0{def_index}_' , def_index
    else:
        raise f'No project record found for {project_id}'


def update_segmentation_labels(obj, db_sync_client):
    try:
        db = db_sync_client
        image_annotation_document_id = obj['image_annotation_document_id']
        annotation_data = obj['annotation_data']
        if image_annotation_document_id is None:
            return False , 'image_annotation_document_id is None'
        if annotation_data is None:
            return False , 'annotation_data is None'

        # db = establishConnection()
        result = db.seg_image_annotations.update_one(
            {'_id': ObjectId(image_annotation_document_id)},
            {'$set': {
                'annotation_data': annotation_data
            }}
        )
        if result.matched_count == 1 and result.modified_count == 1:
            return True ,"Updated Successfully"
        else:
            return False, f"Found {result.matched_count} records, modified {result.modified_count} records"
    except Exception as e:
        raise e
    

def get_all_distinct_segmentation_labels_for_images(db_sync_client, project_id:str):
    try:
        logger.info(project_id)
        db = db_sync_client

        sample_workflow_docs = db.sampleworkflows.find({"project_id": project_id},{"_id": 1})  # Fetch the document by project_id
        sample_workflows_id = [str(doc['_id']) for doc in sample_workflow_docs]
      

        workflow_images_path_doc = db.workflowimagespath.find({"workflow_id":{"$in" : sample_workflows_id}}, {"_id": 1})  # Fetch the document by project_id
        workflow_images_path_id  = [str(doc['_id']) for doc in workflow_images_path_doc]
        print("workflow_images_path_id", workflow_images_path_id)
        
        pipeline = [
            {"$match": {"workflow_db_id":{ "$in": workflow_images_path_id}}},  # Filter documents by project_id
            {"$unwind": "$annotation_data"},
            {"$group": {"_id": {}, "labels": {"$addToSet": "$annotation_data.Label"}}}
        ]
        result = list(db.seg_image_annotations.aggregate(pipeline))
        print("result",result)
        return result[0]['labels']
    except Exception as e:
        raise e