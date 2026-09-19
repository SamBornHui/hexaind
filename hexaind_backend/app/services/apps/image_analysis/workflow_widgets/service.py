import asyncio
import pickle
import sys
from app.services.apps.image_analysis.schema import QuantTechRequest, BatchProcessingRequest, SpatialStatisticsConfig, SpatialStatisticsResponse
from pymongo import MongoClient
import skimage
from skimage import io
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os
# Math / Data packages
import math
import numpy as np
from scipy.stats import skew
import pandas as pd
# Plotting / Image tools
import cv2
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt

from skimage.io import *
import seaborn as sns
import textwrap
from PIL import Image
from skimage.color import rgb2gray
from skimage.util import *
# ML model libraries
from sklearn.preprocessing import LabelEncoder, RobustScaler, StandardScaler, MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from app.services.data.assets.datasets.service import DatasetsService
import traceback
# Download tools
# Import Databrick packages
# import hexaind3db_tsl, hexaind3_datasetselector_tsl, hexaind3regionprops_tsl, hexaind3imgintensityhist_tsl, hexaind3heuristics_tsl
from app.services.apps.image_analysis.workflow_widgets.calc_region_props import *
from app.services.apps.image_analysis.workflow_widgets.utils.Visualizations import *
from app.services.apps.image_analysis.workflow_widgets.utils.Two_Point_Statistics import *
from app.services.apps.image_analysis.workflow_widgets.utils.Pair_Correlation import *
from app.services.apps.image_analysis.workflow_widgets.utils.Utilities import *
from app.services.apps.image_analysis.workflow_widgets.utils.Chord_Length_Distribution import *
from app.services.apps.image_analysis.workflow_widgets.utils.Rotationally_Invariant_Statistics import *
import plotly
import plotly.graph_objs as go


import time
import logging
#Suppress warnings
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

from app.services.apps.image_analysis.dao import ImageAnalysisDao

logger = logging.getLogger(__package__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))

class ImageAnalysisWidgetsService:

    def __init__(self, db_sync_client: MongoClient = None, db_async_client: AsyncIOMotorClient = None) -> None:
        self.image_analysis_dao = ImageAnalysisDao(db_sync_client=db_sync_client,db_async_client = db_async_client)

    async def process_region_props(self, selected_datasets, region_props_config, project_id):
    # Call async functions in sequence or parallel as needed
        self.dataset_service = DatasetsService()
        processed_data = await self.process_datasets(selected_datasets)
        Objects_df = await self.calc_regionprops(processed_data, region_props_config)
        df_reg_props = await self.get_defect_characteristics(selected_datasets, Objects_df)
        reg_props_results_file = self.dataset_service.generate_file_info(input_data=df_reg_props,project_id=project_id)
        reg_props_stats = df_reg_props.describe()
        results = {
            "reg_props_stats":reg_props_stats.to_dict(),
            "reg_props_results_file":reg_props_results_file.path
        }
        return results
    
    async def process_datasets(self, s_datasets):
        dataset_ids = []
        dataset_dict = {}
        for dataset in s_datasets:
            datasets = await self.image_analysis_dao.find_DM_dataset_by_id(dataset['dataset_id'])
            dataset_id = str(datasets["_id"])
            dataset_dict[dataset_id] = datasets["dataset_name"]
            dataset_ids.append(dataset_id)

        folders_ids = []
        folders_metadata = {}
        for dataset_id in dataset_ids:
            folderdata =  await self.image_analysis_dao.find_cat_data_by_dataset_id(dataset_id)
             
            for record in folderdata :
                record["dataset_name"] = dataset_dict[record['dataset_id']]
                folders_metadata[str(record['_id'])] = record
                folders_ids.append(str(record['_id']))
        
        count = 0
        processed_data = []
        size_mismatch_files = []

        for folder_id in folders_ids:
            cat_data_filter = {'_id': ObjectId(folder_id) }
            folder_data = await self.image_analysis_dao.get_document(filter_document= cat_data_filter, collection="categorizeddata")
            images_data = folder_data["data"]["SEM"] + folder_data["data"]["OM"] + folder_data["data"]["NA"] 
            for img_data in images_data:        

                scale=None
                if (img_data['scalebar_options'].get('scalebarByPhysical') and 
                    img_data['scalebar_options']['scalebarByPhysical'] != '' and 
                    img_data['scalebar_options'].get('scalebarByImage') and 
                    img_data['scalebar_options'].get('scalebarByImage') != ''):
                    scale = int(img_data['scalebar_options']['scalebarByPhysical'])/ img_data['scalebar_options']['scalebarByImage']
                
                popup_unit = (img_data['scalebar_options']['scalebarByPhysicalUnit'] 
                            if (img_data['scalebar_options'].get('scalebarByPhysicalUnit') and 
                                img_data['scalebar_options']['scalebarByPhysicalUnit'] != '' and scale) else None)
                
                imgpathwithname = os.path.splitext(img_data['path'])[0]        
                workflowid = self.retrieveWfId(img_data['path'])
                wf_processed_data = self.retrieveProcessedWfId(imgpathwithname,True)
                if wf_processed_data is None:
                    continue
                segmented_img_path = wf_processed_data['data']['segmented_img']
                cropped_img_path = wf_processed_data['data']['cropimg']
                original_img_path = img_data['path']
                masked_img_path= None
                if 'masked_image' in img_data and img_data['masked_image']:
                    masked_img_path = img_data['masked_image']
                if not os.path.exists(segmented_img_path):
                    logger.info('DATA MALFORMED; segmentation img path DOESN\'T EXIST:: ',segmented_img_path)
                    continue
                if not os.path.exists(cropped_img_path):
                    logger.info('DATA MALFORMED; cropped img path DOESN\'T EXIST:: ',cropped_img_path)
                    continue
                processed_data.append({            
                    'folder_id' : folder_id,
                    'original_img_path' : original_img_path,
                    'cropped_img_path' : cropped_img_path,
                    'masked_img_path' : masked_img_path,
                    'segmented_img_path' : segmented_img_path,
                    'segmented_data_id' : str(wf_processed_data['_id']), #we use it applied data on wf.
                    'scale' : scale,
                    'popup_unit' : popup_unit            
                }) 
                count+=1
        

        return processed_data
    
    def retrieveWfId(self, path):
        multiplyimagesworkflow_filter = {'image_path': path}
        report = self.image_analysis_dao.get_document_sort(filter_document= multiplyimagesworkflow_filter, collection="multiplyimagesworkflow")
        if report:           
            return report['w_id']
        else:
            return 0

    def retrieveProcessedWfId(self, path , get_all_details = False):
        name, _ = os.path.splitext(path)
        workflowimagespath_filter = {'sample_name': name}
        report =  self.image_analysis_dao.get_document_sort(filter_document= workflowimagespath_filter, collection="workflowimagespath")
        if report:
            if get_all_details:
                return report
            return str(report['_id'])        
        else:
            return None

    async def calc_regionprops(self, processed_data, region_props_config):
        logger.info('Calculating region properties for all appropriate images in selected datasets.')
        i = 0
        total_processed_item_count = len(processed_data)
        Objects_df = pd.DataFrame()
        properties = region_props_config.region_properties
        a_r_ell = "A.R_ell" in properties
        a_r = "A.R" in properties
        no_of_obj = "No. of objects" in properties
        if a_r_ell:
            properties.remove("A.R_ell")
        if a_r:
            properties.remove("A.R")
        if no_of_obj:
            properties.remove("No. of objects")
            
        for i in range(total_processed_item_count):
            # Pick segmented & RGB image paths from processed data dictionary
            original_img_path = processed_data[i]['original_img_path']
            seg_img_path = processed_data[i]['segmented_img_path']
            masked_img_path = processed_data[i]['masked_img_path']
            cropped_img_path = processed_data[i]['cropped_img_path']
            # Load segmented image
            if os.path.exists(seg_img_path):
                img = cv2.imread(seg_img_path) 
            #     grayscale_img = skimage.color.rgb2gray(img)     
                seg_img = img[:,:,0]
                seg_img = (seg_img > 0) * 1
            else:
                raise ValueError("segmented image does not exist on the given path.")
            # Load RGB image

            cropped_img1 = cv2.imread(cropped_img_path)
            grayscale = skimage.color.rgb2gray(cropped_img1)
            
            if masked_img_path and os.path.exists(masked_img_path):
                masked_img1 = cv2.imread(masked_img_path)
                grayscale_masked = skimage.color.rgb2gray(masked_img1)
                if seg_img.shape == grayscale_masked.shape:
                    grayscale = grayscale_masked

            # Calculate object region props & intensities
            props = skimage.measure.regionprops_table(skimage.measure.label(seg_img),
                                                        intensity_image = grayscale, 
                                                        properties=properties,
                                                        extra_properties=(sd_intensity, skew_intensity))
            # Identify inverse segmented image i.e background mask
            bg_seg_img = (seg_img == 0) * 1
            # Calculate background intensities
            bg_props = skimage.measure.regionprops_table(skimage.measure.label(bg_seg_img),
                                                        intensity_image = grayscale, 
                                                        properties=['intensity_mean'])
            # Store the segmented image properties to a dataframe
            df = pd.DataFrame(props) #everything we get now is in pixels
            # Add the bbox length and height by calculation
            df['bbox_length'] = df['bbox-3']-df['bbox-1']
            df['bbox_height'] = df['bbox-2']-df['bbox-0']
            # Add aspect ratio columns (length/height & axis_major/axis_minor)
            if a_r:
                df['A.R.'] = np.where(df['bbox_height'] > 0, df['bbox_length']/df['bbox_height'], 1000)
            if a_r_ell:
                df['A.R._ell'] = np.where(df['axis_minor_length'] > 0, df['axis_major_length']/df['axis_minor_length'], 1000)
            # Add No. of objects in the image to all rows of the the datafame
            if no_of_obj:
                df['No. of objects'] = df.shape[0]

            # Convert all real units columns from pixels to mm
            for column in list(df.columns):
                if column not in scale_length+scale_area: # Non-real units columns to be ignored
                    continue
                if processed_data[i]['scale'] is None or processed_data[i]['popup_unit'] is None: #ignore rows without units
                    continue
                # Scaling of pixel columns to mm based on the "scaled_props" function
                df[f"{column}_m"] = scaled_props(df, column, processed_data[i]['scale'],processed_data[i]['popup_unit'])
        #         df[f"{column}_{processed_data[i]['popup_unit']}"] = scaled_props(df[column], 
        #                                                                          processed_data[i]['scale'],
        #                                                                          processed_data[i]['popup_unit'])

            # Add folder_id, original_img_path,masked_img_path,segmented_img_path,segmented_data_id,scale,popup_unit to this df
            for x in processed_data[i]:
                df[x] = processed_data[i][x]

            # Add unique object id for each image
            # in actual code we calculate unique object id with uuid prefix NOW ITS NOT REQUIRED
            df['unique_object_id'] = df['label'].astype(str) 
            

            # Add background intensity mean to all values in the dataframe
            df['bg_intensity'] = pd.DataFrame(bg_props)['intensity_mean'].mean()
            df['intensity_diff'] = df['intensity_mean']-df['bg_intensity'] # Relative intensity of object wrt background

            # Map annotation data onto this dataframe
            seg_image_annotations_filter ={'workflow_db_id' : processed_data[i]['segmented_data_id']}
            annotation_db_records = await self.image_analysis_dao.get_all_document(filter_document= seg_image_annotations_filter, collection="seg_image_annotations")
            annotation_records = list(annotation_db_records)
            assert len(annotation_records) == 1

            db_annotation_data = annotation_records[0]['annotation_data']
            annotation_df = pd.DataFrame(db_annotation_data)
            annotation_df['Label_from_id'] = annotation_df['Unique_object_id'].apply(lambda x: x.split('_')[1])
            
            # Merge annotation df with props df
            merged_df = pd.merge(annotation_df, df, left_on='Label_from_id', right_on='unique_object_id', how='inner')
            # Append the props df with props, scale, uids, annotations & intensities to the master object dataframe
            Objects_df = pd.concat([Objects_df, merged_df], ignore_index=True, axis=0)
        
        # Add short file name without path for plotting histograms for intensities of each image
        Objects_df.insert(0, 'File_name', [item.rsplit('/',1)[1] for item in Objects_df['original_img_path']])
        Objects_df.insert(1, 'Folder_name', [item.rsplit('/',2)[0].rsplit('/',1)[1][:11]+'/'+item.rsplit('/',2)[1]
                        for item in Objects_df['original_img_path']])
        # Adding shape indices
        Objects_df['Compactness'] = np.where(Objects_df['area'] > 0,
                                            (Objects_df['perimeter']**2)/(4*math.pi*Objects_df['area']), 0)
        Objects_df['Circularity'] = np.where(Objects_df['area'] > 0,
                                            Objects_df['area']/Objects_df['area_convex'], 0)
        # Specify the column order
        first_columns = ["File_name", "Folder_name", "Label"]
        last_columns = ["Object", "Unique_object_id"]

        # Get the list of all other columns
        middle_columns = [col for col in df.columns if col not in first_columns + last_columns]


        Objects_df = Objects_df[first_columns + middle_columns + last_columns]
        Objects_df= Objects_df.drop(columns=["label"])
        Objects_df= Objects_df.drop(columns=["unique_object_id"])
        return Objects_df
    
    async def get_defect_characteristics(self, selected_dataset, Objects_df):
        initial_shape = Objects_df.shape
        defect_char_df = pd.DataFrame()
        for dataset in selected_dataset:
        # Extract file path and sheet name
            metadata_path = dataset.get("defect_metadata_path")
            sheet_name = dataset.get("dataset_name")
            if metadata_path and os.path.exists(metadata_path):
                # Read data from the Excel sheet
                sheet_data = pd.read_csv(metadata_path)
                # Concatenate data into the main DataFrame
                defect_char_df = pd.concat([defect_char_df, sheet_data], ignore_index=True)
        if not defect_char_df.empty:
            if 'Image Name' in defect_char_df.columns:
                defect_char_df.insert(0, 'File_name', defect_char_df['Image Name'].astype(str)+'.JPG')
                Objects_df = pd.merge(Objects_df, defect_char_df, on='File_name', how='left') #, suffixes=None)
        
        return Objects_df
    

    def checkSegmented(self, path):
        img = io.imread(path)
        if img.ndim == 3:
            img = rgb2gray(img)
        if len(np.unique(img))==2:
            return path    
        return 
   

    def retrieve_fe_data(self, dataset_id):
        
        filter = {"_id" : ObjectId(dataset_id)}
        datasets_data = self.image_analysis_dao.get_document_sync(filter_document = filter, collection="datasets")
        dm_dataset_data = self.image_analysis_dao.get_document_sync(filter_document = filter, collection="DMCreatedDatasets")
        if 'file_type' in dm_dataset_data and dm_dataset_data['file_type'] == 'csv':
            return {'status': False, 'message': 'Try with Images data'}
        fedata = []
        metadata = f"{datasets_data['dataset_location'][0]['path']}/csv_metadata/metadata.csv"
        # if not metadata:
        #     metadata = self.fetchKeysValue('metadata',data)
            
        for i in dm_dataset_data['foldersdata']:
            for j in i['selectedimages']:
                folderpath, _ = os.path.split(j['orignalpath'])
                _, imext = os.path.split(j['convertedpath'])
                imext = os.path.splitext(imext)[0] + '.png'
                segdir = os.path.join(folderpath, 'segment_dir')
                filename = os.path.join(segdir, imext)
                filename2 = os.path.join(segdir, 'thumbnail', imext)

                if os.path.isfile(filename):
                    fedata.append({'path': filename, 'thumbnail_path': filename2})

                elif self.checkSegmented(j['orignalpath']):
                    os.makedirs(segdir, exist_ok=True)
                    copyFile(j['convertedpath'], filename)
                    thumbnail_dir = os.path.join(segdir  , 'thumbnail')
                    os.makedirs(thumbnail_dir, exist_ok=True)
                    copyFile(j['thumbnailpath'], filename2)
                    fedata.append({'path': filename, 'thumbnail_path': filename2})
                else:
                    pass
        
        if not fedata:
            return {'status': False, 'message': 'Segment data does not exist'}           
            
        featuredata = {}
        featurelist = []    
        if metadata and os.path.exists(metadata):
            if metadata.endswith("csv"):
                df = pd.read_csv(metadata)
            elif metadata.endswith("parquet"):
                df = pd.read_parquet(metadata)
            df = df.dropna()
            featurelist = list(df)
            length = len(featurelist)
            featurelist = featurelist[2:]
            for i in featurelist:
                featuredata[i] = list(df[i])
        
        data = {'status': True, 'data':{'imagesdata': fedata, 'metadata': metadata, 'featurelist': featurelist, 'featuredata': featuredata}}
        return data

    def fetchKeysValue(self, keyname, obj):
        if keyname in obj:
            value = obj[keyname]
        else:
            value = None
            
        return value

    async def quantification_techniques(self, obj:QuantTechRequest):
        path_image = obj.path_image
        quantTech = obj.quantTech
        cutoff = obj.cutoff
        user_id = obj.user_id
        local_state_1 = obj.local_state_1
        local_state_2 = obj.local_state_2
        ang_int = int(obj.ang_int)
        coarsening = self.fetchKeysValue('coarsening', obj)
        ls1 = local_state_1
        ls2 = local_state_2
        y_lims = None
        
        # collection = db[quantTech]
        collection = 'quantech'
        visualized_plots=[]
        for j,k in enumerate(path_image):
            visualized_plot_string, m, imgpath, y_lims = self.getVisualization(j, k, ls1, ls2, cutoff, y_lims, quantTech, collection,
                                                                user_id, len(path_image), coarsening, path_image)
            microstructure_image =  imgpath + '_microstructure.html'
            
            fig = go.Figure()
            Visualize_Microstructure(m, num_ls = 2, fig = fig, return_fig = True, interactive = True, resolution = 22/1024, resolution_unit = 'μm')
            fig.write_html(microstructure_image)
            
            visualized_plot_string['microstructure_image'] = microstructure_image
            visualized_plot_string['orignal_path'] = k
        
            visualized_plots.append(visualized_plot_string)
        data = {'status': 'done', "visualized_plots":visualized_plots}
        return data
    
    def getVisualization(self, ind ,k , ls1, ls2, cutoff, y_lims, quantTech, collection, user_id, totalno, coarsening, path_image, callfrom = ''):
    
        ang_int = 15
        i =  k
        m = rgb2gray((io.imread(i)))
        m = img_as_float(m)
        img = m
        p, imgnameext = os.path.split(i)
        
        imgname, _ = os.path.splitext(imgnameext)
        p = self.addSlashonLastIndex(p)

        dirpath = p + 'allvisualization'
        if not os.path.exists(dirpath):
            os.mkdir(dirpath)
        
        self.removeOldData(dirpath)
        dirpath = self.addSlashonLastIndex(dirpath)
            
        resolution = 22/1024
        resolution_unit = 'μm'
        
        visualized_plot_string = {}

        imgpath = dirpath + imgname + str(int(round(time.time() * 1000)))
        fig = go.Figure()
        
        if quantTech == 'TwoPointStats':
            visualpath = imgpath + '.html'
            m1 = m == ls1
            m2 = m == ls2
            TP = TwoPoint(m1, M2 = m2, periodicity = True, cutoff = cutoff, ls_ind = [ls1,ls2], resolution = resolution,
                        resolution_unit = resolution_unit)
            
            TP.visualize(fig = fig, interactive = True, return_fig = True, colorbar_lims = None)                
            
            fig.write_html(visualpath)
            visualized_plot_string = { 'visualized_plot': visualpath}

        elif quantTech == 'PairCorrelation':
            
            visualpath = imgpath + '.html'
            m1 = m == ls1
            m2 = m == ls2
            PC = PairCorr(m1, M2 = m2, cutoff = cutoff, ls_ind = [ls1, ls2], resolution = resolution,
                        resolution_unit = resolution_unit)
            
            if len(path_image)>1 and ind == 0:
                tempm = rgb2gray((io.imread(path_image[ind+1])))
                tempm = img_as_float(tempm)

                tm1 = tempm == ls1
                tm2 = tempm == ls2
                tPC = PairCorr(tm1, M2 = tm2, cutoff = cutoff, ls_ind = [ls1, ls2], resolution = resolution,
                        resolution_unit = resolution_unit)
                y_lims = get_y_lims(PC.PC, tPC.PC)

            PC.visualize(fig = fig, interactive = True, return_fig = True, y_lims = y_lims)
    #         fig.show()
            fig.write_html(visualpath)
            visualized_plot_string = { 'visualized_plot': visualpath}
        elif quantTech == 'ChordLengthDist':
            visualcldpath = imgpath + '.html'
            m1 = m == ls1
            C1 = ChordLengthDistribution(m1, ang_int = ang_int, cutoff = cutoff, resolution = resolution,
                        resolution_unit = resolution_unit, coarsening = coarsening)
            
            if len(path_image)>1 and ind == 0:
                tempm = rgb2gray((io.imread(path_image[ind+1])))
                tempm = img_as_float(tempm)
                tm1 = tempm == ls1
                tC1 = ChordLengthDistribution(tm1, ang_int = ang_int, cutoff = cutoff, resolution = resolution,
                        resolution_unit = resolution_unit, coarsening = coarsening)
                y_lims = get_y_lims(C1.CLD[ls1], tC1.CLD[ls1])

                
            C1.visualize_CLD(ls1, fig = fig, interactive = True, return_fig = True, y_lims = y_lims)
            fig.write_html(visualcldpath)
    #         fig.show()
            visualized_plot_string =  {'visualized_plot': visualcldpath}

        elif  quantTech == 'RotatInvariance':
            visualpath = imgpath + '.png'
            visualimg, _ = os.path.splitext(visualpath)
            m1 = m == ls1
            m2 = m == ls2
            RI = RotInv(m1, M2 = m2, cutoff = cutoff, ls_ind = [ls1,ls2], resolution = resolution,
                        resolution_unit = resolution_unit)
            RI.visualize(imageloc = visualimg, colorbar_lims = None)
            visualized_plot_string = { 'visualized_plot': visualpath}


        else:
            visualarcldpath = imgpath + '.png'
            visualarcldpathangle = imgpath + '.html'

            m1 = m == ls1
            C1 = ChordLengthDistribution(m1, ang_int = ang_int, cutoff = cutoff, resolution = resolution,
                        resolution_unit = resolution_unit, coarsening = coarsening)
            C1.visualize_ARCLD_Angle([0, 45, 90], local_state = ls1, fig = fig, interactive = True, return_fig = True)
            fig.write_html(visualarcldpathangle)
            v1, _ = os.path.splitext(visualarcldpath)
            C1.visualize_ARCLD(ls1, imageloc = v1)
            visualized_plot_string = { 'visualized_plot': visualarcldpath, 'visualize_ARCLD_Angle': visualarcldpathangle}
                
        visualized_plot_string['user_id'] = user_id    

        return visualized_plot_string, img, imgpath, y_lims
    
    def removeOldData(self,path):
        now = time.time()
        for filename in os.listdir(path):
            filestamp = os.stat(os.path.join(path, filename)).st_mtime
            filecompare = now - 2 * 86400
            if  filestamp < filecompare:
                os.remove(os.path.join(path,filename))
                
                
    def addSlashonLastIndex(self, strr):
        if strr[-1] == '/':
            pass
        else:
            strr = strr + '/'
        return strr

    def removeSlashonLastIndex(self, path):
        if path[-1]=='/':
            path, _ = os.path.split(path)
            return path
        else:
            return path  

    def createVisualPath(self, ls1, ls2, path):
        localstate = 'phase_' + str(ls1) + '_' + str(ls2)
        folderpath = path + localstate
        if not os.path.exists(folderpath):
            os.mkdir(folderpath)
        
        return self.addSlashonLastIndex(folderpath)
    
    def findExistingBatchData(self, ls, path, quantTech, cutoff, phases, imagesdata, name, ang_int, coarsening):
        batch_file_paths=[]
        for i in ls:
            if quantTech == 'ChordLengthDist' or quantTech == 'AngularyResolvedChordLengthDistributions':
                fpath = path + 'phase_' + str(i[0])
                fpath = self.addSlashonLastIndex(fpath)
                filepath = fpath + 'batch_' + str(i[0]) + '_' + str(cutoff) + '.data'
            else:
                fpath = path + 'phase_' + str(i[0]) + '_' + str(i[1])
                fpath = self.addSlashonLastIndex(fpath)
                filepath = fpath + 'batch_' + str(i[0]) + '_' + str(i[1]) + '_' + str(cutoff)  + '.data'
            foldername = os.path.basename(os.path.split(os.path.split(os.path.split(path)[0])[0])[0])
            if os.path.isfile(filepath):
                with open(filepath, 'rb') as filehandle:
                    fileinfo = pickle.load(filehandle)
                imagesdataoffile = [file['sample'] for file in fileinfo]
                newimages = [im for im in imagesdata[name] if im not in imagesdataoffile]
                if newimages:
                    statsobj = {}
                    phases = [i]
                    for count,im in enumerate(newimages):
                        self.getbatchVisualization(count, im, phases, cutoff, ang_int, quantTech, '', '', len(newimages),
                                                            statsobj, coarsening, '', '', count, 'existfolder')
                    newfileinfo = fileinfo + statsobj[str(tuple(i))]
                    os.remove(filepath)
                    with open(filepath, 'wb') as filehandle:
                        pickle.dump(newfileinfo, filehandle)
                batch_file_paths.append(filepath)
            else:
                phases.append(i)
        return batch_file_paths


    def getbatchVisualization(self, indd, i, ls, cutoff, ang_int, quantTech, collection, user_id, totalno, statsobj, coarsening,
                            datasetId, db, COUNT, callfrom=''):
            
        local_states = ls
        impath = i
        resolution = 22/1024
        resolution_unit = 'μm'
    #     m = rgb2gray((io.imread(i)))
    #     m = img_as_float(m)
        
        m = rgb2gray(io.imread(i).astype('int')/255)
        img = m
        p, imgnameext = os.path.split(i)
        imgname, _ = os.path.splitext(imgnameext)
        p = self.addSlashonLastIndex(p)
        ls = [tuple(i) for i in ls]
        path = p + quantTech
        if not os.path.exists(path):
            os.mkdir(path)
        path = self.addSlashonLastIndex(path)
        dbobject = {}
        if quantTech == 'TwoPointStats':
            
            TP_coll = TwoPoint_Batch(m, ls, cutoff = cutoff, periodicity = True, resolution = resolution, resolution_unit = resolution_unit)
            batchdata = TP_coll.TP_batch
            for s in ls:
                visualpath = self.createVisualPath(s[0], s[1], path) + imgnameext
                visualimg, _ = os.path.splitext(visualpath)
                TP_coll.visualize([s[0],s[1]], imageloc = visualimg)
                dbobject[str(s)] = visualpath
                bb = 'TP_' +str(s[0])+str(s[1])
                strstate = str(s)
                temp = {'sample': impath, strstate:batchdata[bb].flatten()}            
                if strstate in statsobj:
                    tt = statsobj[strstate]
                    tt.append(temp)
                    statsobj[strstate] = tt
                else:
                    statsobj[strstate] = [temp]

    def batchProcessing(self, obj: SpatialStatisticsConfig, project_id):
        self.dataset_service = DatasetsService()
        quantTech = obj.quantTech
        cutoff = obj.cutoff
        local_states = obj.local_states
        ang_int = 5 
        userId = ""
        datasetId = obj.datasetId
        data = self.retrieve_fe_data(datasetId)
        imagesdata = {}
        dataa = data['data']['imagesdata']
        length = len(dataa)
        for i in dataa:
            subf = os.path.basename(os.path.split(os.path.dirname(i['path']))[0])
            if subf in imagesdata:
                imagesdata[subf].append(i['path'])
            else:
                imagesdata[subf] = [i['path']]
                
        coarsening = self.fetchKeysValue('coarsening', obj)
        if quantTech == 'ChordLengthDist' or quantTech == 'AngularyResolvedChordLengthDistributions': 
            for i in local_states:
                i.append(0)
        
        filter = {"datasetId" : datasetId}
        report =  self.image_analysis_dao.get_document_sync(filter_document = filter, collection="FEbatchinfo")
        phasesinfo = []
        temp2 = []
        if report:
            if  quantTech in report and 'phasesinfo' in report[quantTech]:
                quntch = report[quantTech]
                phasesinfo = quntch['phasesinfo']
                for st in local_states:
                    d = next((item for item in phasesinfo if item["phase"] == st), None)
                    if d:
                        d['status'] = 'inprogress'
                    else:
                        temp2.append({'phase': st, 'status':'inprogress'})
                        
                phasesinfo += temp2
            else:
                for st in local_states:
                    phasesinfo.append({'phase': st, 'status':'inprogress'})

            temp = {'phasesinfo': phasesinfo, 'ang_int': 15, 'cutoff': cutoff, 'coarsening': coarsening}
            filter = {'_id': report['_id']}
            self.image_analysis_dao.update_document_sync(filter_document = filter,new_value= { quantTech:temp}, collection="FEbatchinfo")
            
        else:
            for st in local_states:
                phasesinfo.append({'phase': st, 'status':'inprogress'})
            temp = {'phasesinfo': phasesinfo, 'ang_int': 15, 'cutoff': cutoff, 'coarsening': coarsening}
            document = {'datasetId': datasetId, quantTech: temp, 'userId': userId}
            self.image_analysis_dao.insert_document_sync(value = document, collection="FEbatchinfo")
        
        collection = 'quantTech'
        count = 0
        COUNT = 0
        status = True
        msg = " Success "
        batch_file_paths =[]
        try:
            for i in imagesdata:
                p, imgnameext = os.path.split(imagesdata[i][0])
                p = self.addSlashonLastIndex(p)
                path = p + quantTech
                path = self.addSlashonLastIndex(path)
                phases = []
                batch_file_paths = self.findExistingBatchData(local_states, path, quantTech, cutoff, phases, imagesdata, i, ang_int, coarsening)
                if phases:
                    statsobj = {}
                    for ind,j in enumerate(imagesdata[i]):
                        COUNT += 1
                        self.getbatchVisualization(count, j, phases, cutoff, ang_int, quantTech, collection, userId, length,
                                            statsobj, coarsening, datasetId, '',COUNT)
                        
                    batch_file_paths = self.createbatchdatafiles(statsobj, phases, path, quantTech, cutoff)
                else:        
                    COUNT += len(imagesdata[i])
            
            filter = {'datasetId': datasetId}
            report2 = self.image_analysis_dao.get_document_sync(filter_document = filter, collection="FEbatchinfo")
            phases = []
            if report2:
                if  quantTech in report2:
                    quntch = report2[quantTech]
                    phasesinfo = quntch['phasesinfo']
                    for st in phasesinfo:
                        if st['phase'] in local_states:
                            st['status'] = 'completed'
                    
                    temp = {'phasesinfo': phasesinfo, 'ang_int': 15, 'cutoff': cutoff, 'coarsening': coarsening}
                    filter = {'_id': report2['_id']}
                    self.image_analysis_dao.update_document_sync(filter_document = filter,new_value= { quantTech:temp}, collection="FEbatchinfo")
            
            data = {}
            msg = f" '{quantTech}' applied on '{datasetId}' "
            
            data = {"msg":msg, "batched_files": batch_file_paths, "quantTech":quantTech, "dataset_id":datasetId, "phases":phasesinfo }
            result_df = pd.DataFrame({
                "msg": [data["msg"]],
                "batched_files": [", ".join(data["batched_files"])],  # Join list into a single string
                "quantTech": [data["quantTech"]],
                "dataset_id": [data["dataset_id"]],
                "phases": [str(data["phases"])]  # Convert the list of dictionaries to a string
            })
            resultsfile = self.dataset_service.generate_file_info(input_data=result_df,project_id=project_id)
            return SpatialStatisticsResponse(tabular_path= resultsfile.path)

        except Exception as e:
            filter = {'datasetId': datasetId}
            report = self.image_analysis_dao.get_document_sync(filter_document = filter, collection="FEbatchinfo")
            quntch = report[quantTech]
            phasesinfo = quntch['phasesinfo']
            updated_phasesinfo = [
                phase for phase in quntch['phasesinfo']
                if not (phase['status'] == 'inprogress' and len(quntch['phasesinfo']) > 1)
            ]

            # Update the phasesinfo in quntch
            if updated_phasesinfo:
                quntch['phasesinfo'] = updated_phasesinfo
            else:
                del quntch['phasesinfo']
            filter_document = {'_id': report['_id']}
            self.image_analysis_dao.update_document_sync(filter_document = filter_document,new_value= report, collection=collection)
            
            status = False
            msg = " failed batch "
            logger.exception(f"Exception while trying to batch process spatial statistics. Error:{e}")
            return SpatialStatisticsResponse(exception_detail=str(e))
    

    def getbatchVisualization(self, indd, i, ls, cutoff, ang_int, quantTech, collection, user_id, totalno, statsobj, coarsening,
                          datasetId, db, COUNT, callfrom=''):
        
        local_states = ls
        impath = i
        resolution = 22/1024
        resolution_unit = 'μm'
    #     m = rgb2gray((io.imread(i)))
    #     m = img_as_float(m)
        
        m = rgb2gray(io.imread(i).astype('int')/255)
        img = m
        p, imgnameext = os.path.split(i)
        imgname, _ = os.path.splitext(imgnameext)
        p = self.addSlashonLastIndex(p)
        ls = [tuple(i) for i in ls]
        path = p + quantTech
        if not os.path.exists(path):
            os.mkdir(path)
        path = self.addSlashonLastIndex(path)
        dbobject = {}
        if quantTech == 'TwoPointStats':
            
            TP_coll = TwoPoint_Batch(m, ls, cutoff = cutoff, periodicity = True, resolution = resolution, resolution_unit = resolution_unit)
            batchdata = TP_coll.TP_batch
            for s in ls:
                visualpath = self.createVisualPath(s[0], s[1], path) + imgnameext
                visualimg, _ = os.path.splitext(visualpath)
                TP_coll.visualize([s[0],s[1]], imageloc = visualimg)
                dbobject[str(s)] = visualpath
                bb = 'TP_' +str(s[0])+str(s[1])
                strstate = str(s)
                temp = {'sample': impath, strstate:batchdata[bb].flatten()}            
                if strstate in statsobj:
                    tt = statsobj[strstate]
                    tt.append(temp)
                    statsobj[strstate] = tt
                else:
                    statsobj[strstate] = [temp]

        elif quantTech == 'PairCorrelation':
            PC_coll = PairCorr_Batch(m, ls, cutoff = cutoff, periodicity = True, resolution = resolution, resolution_unit = resolution_unit)
            batchdata = PC_coll.PC_batch
            for s in ls:
                visualpath = self.createVisualPath(s[0], s[1], path) + imgnameext
                visualimg, _ = os.path.splitext(visualpath)
                PC_coll.visualize([s[0],s[1]], imageloc = visualimg)
                dbobject[str(s)] = visualpath
                bb = 'PC_' +str(s[0])+str(s[1])
                strstate = str(s)
                temp = {'sample': impath, strstate:batchdata[bb].flatten()}            
                if strstate in statsobj:
                    tt = statsobj[strstate]
                    tt.append(temp)
                    statsobj[strstate] = tt
                else:
                    statsobj[strstate] = [temp]
            
        elif quantTech == 'ChordLengthDist':
            for st in ls:
                ls1 = st[0]
                visualcldpath = self.createVisualPathforCL(path, 'CLD', ls1) + imgnameext
                dbobject[str(st)] = visualcldpath
                m1 = m == ls1
                C1 = ChordLengthDistribution(m1, ang_int = ang_int, cutoff = cutoff, resolution = resolution,
                                            resolution_unit = resolution_unit, coarsening = coarsening)            
                v2, _ =  os.path.splitext(visualcldpath)
                C1.visualize_CLD(ls1, imageloc = v2)
                strstate = str(st)
                temp = {'sample': impath, strstate:np.array(C1.CLD).flatten()}            
                if strstate in statsobj:
                    tt = statsobj[strstate]
                    tt.append(temp)
                    statsobj[strstate] = tt
                else:
                    statsobj[strstate] = [temp]

        elif  quantTech == 'RotatInvariance':
            RI_coll = RotInv_Batch(m, ls, cutoff = cutoff, periodicity = False, resolution = resolution, resolution_unit = resolution_unit, ang_int = ang_int)
            batchdata = RI_coll.RI_batch
            for s in ls:
                visualpath = self.createVisualPath(s[0], s[1], path) + imgnameext
                visualimg, _ = os.path.splitext(visualpath)
                RI_coll.visualize([s[0],s[1]], imageloc = visualimg)
                dbobject[str(s)] = visualpath
                bb = 'RI_' +str(s[0])+str(s[1])
                strstate = str(s)
                temp = {'sample': impath, strstate:batchdata[bb].flatten()}            
                if strstate in statsobj:
                    tt = statsobj[strstate]
                    tt.append(temp)
                    statsobj[strstate] = tt
                else:
                    statsobj[strstate] = [temp]

        else:
            for st in ls:
                ls1 = st[0]
                visualarcldpath = self.createVisualPathforCL(path, 'ARCLD', ls1) + imgnameext            
                dbobject[str(st)] = visualarcldpath
                m1 = m == ls1
                C1 = ChordLengthDistribution(m1, ang_int = ang_int, cutoff = cutoff, resolution = resolution,
                                            resolution_unit = resolution_unit, coarsening = coarsening)            
                v2, _ =  os.path.splitext(visualarcldpath)
                C1.visualize_ARCLD(ls1, imageloc = v2)
                strstate = str(st)
                temp = {'sample': impath, strstate:np.array(C1.ARCLD).flatten()}            
                if strstate in statsobj:
                    tt = statsobj[strstate]
                    tt.append(temp)
                    statsobj[strstate] = tt
                else:
                    statsobj[strstate] = [temp]
        if not callfrom:
            dbobject['sample'] =  p+imgname
            dbobject['cutoff'] = cutoff
            dbobject['ang_int'] =  ang_int
            filter = {"sample" : p+imgname}
            report =  self.image_analysis_dao.get_document_sync(filter_document = filter, collection = collection)
            
            if report:
                for ind in ls:
                        report[str(ind)] = dbobject[str(ind)]

                report['sample'] = dbobject['sample'] 
                report['cutoff'] = dbobject['cutoff']
                report['ang_int'] = dbobject['ang_int']
                filter_document = {'_id': report['_id']}
                self.image_analysis_dao.update_document_sync(filter_document = filter_document,new_value = report, collection=collection)
            
            else:
                report =  self.image_analysis_dao.insert_document_sync(value = dbobject, collection = collection)
            
                # collection.insert_one(dbobject)


        #     COUNT = indd
            percent_done = int((COUNT/totalno)*100)
            data = {}
            data['user_id'] = user_id
            data['total'] = totalno
            data['percent_done'] =  percent_done
            data['completed'] = COUNT
            return data
            # url = SOCKETURL + 'featureEngineering/batchProcessing'    
            # x = requests.post(url, data=data)
                        

    def createVisualPathforCL(self, path1, name, ls1):    
        path1 = path1 + 'phase_'+ str(ls1)
        if not os.path.exists(path1):
            os.mkdir(path1)
        
        return self.addSlashonLastIndex(path1)
    
    def createbatchdatafiles(self, data, ls, path, quantTech, cutoff):
        batch_data_paths = []
        for i in ls:
            if quantTech == 'ChordLengthDist' or quantTech == 'AngularyResolvedChordLengthDistributions':
                fpath = path + 'phase_' + str(i[0])
                fpath = self.addSlashonLastIndex(fpath)
                filepath = fpath + 'batch_' + str(i[0]) + '_' + str(cutoff) + '.data'
            else:
                fpath = path + 'phase_' + str(i[0]) + '_' + str(i[1])
                fpath = self.addSlashonLastIndex(fpath)
                filepath = fpath + 'batch_' + str(i[0]) + '_' + str(i[1]) + '_' + str(cutoff)  + '.data'
            if os.path.exists(filepath):
                os.remove(filepath)
            ab = (i[0],i[1])
            ab = str(ab)
            with open(filepath, 'wb') as filehandle:
                # store the data as binary data stream
                pickle.dump(data[ab], filehandle)
                batch_data_paths.append(filepath)
        return filepath

