# DB packages
import pymongo
from bson import ObjectId
import os

# Math / Data packages
import math
import numpy as np
from scipy.stats import skew
import pandas as pd

# Plotting / Image tools
import cv2
import matplotlib.pyplot as plt
import skimage
from skimage.io import *
import seaborn as sns
# from IPython.display import Image, display
# import ipywidgets as widgets
import textwrap
import skimage.measure
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

# Import Databrick packages
# import hexaind3db_tsl, hexaind3heuristics_tsl
import datetime, time

import os

all_properties = [
    "image_convex",
    "slice",
    "moments_central",
    "eccentricity",
    "area_filled",
    "perimeter",
    "euler_number",
    "centroid_weighted",
    "moments_weighted_hu",
    "bbox",
    "centroid_weighted_local",
    "area_bbox",
    "moments_weighted",
    "centroid_local",
    "image_intensity",
    "moments",
    "image",
    "moments_hu",
    "moments_weighted_normalized",
    "intensity_max",
    "axis_major_length",
    "intensity_mean",
    "label",
    "area_convex",
    "centroid",
    "axis_minor_length",
    "moments_normalized",
    "image_filled",
    "orientation",
    "coords",
    "inertia_tensor",
    "feret_diameter_max",
    "area",
    "inertia_tensor_eigvals",
    "intensity_min",
    "solidity",
    "moments_weighted_central",
    "extent",
    "perimeter_crofton",
    "equivalent_diameter_area",
]
drop_props = ['inertia_tensor_eigvals', 'slice', 'moments_weighted', 'centroid', 'centroid_weighted', 
              'moments_central', 'centroid_local', 'inertia_tensor',  'moments_weighted_hu', 
              'centroid_weighted_local', 'moments_weighted_central', 'moments_weighted_normalized',
              'moments_weighted_hu', 'moments_hu','moments_weighted_central','moments_weighted_normalized',
              'moments_normalized', 'moments_hu', 'moments']
properties = [item for item in all_properties if item not in drop_props]

scale_length = ['perimeter', 'perimeter_crofton', 'feret_diameter_max', 
                'axis_minor_length','axis_major_length', 'bbox_length', 'bbox_height']
scale_area = ['area_convex', 'area_filled', 'area_bbox', 'area', 'equivalent_diameter_area']

# Function to scale appropriate properties
units_conversion_factors = {'mm': 1e-3,
                            'µm': 1e-6,
                            'cm': 1e-2,
                            'nm': 1e-9,
                            'm' : 1 }

def scaled_props(df, column_name , scale , unit):         
    if column_name in scale_length:
        return df[column_name] * scale * units_conversion_factors[unit]
    if column_name in scale_area:
        return df[column_name] * scale * scale * units_conversion_factors[unit]**2
    
# Function to calculate standard deviation & skewness of intensities as extra properties in regionprops
def sd_intensity(regionmask, intensity_image):
    return np.std(intensity_image[regionmask])
import warnings
def skew_intensity(regionmask, intensity_image):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return skew(intensity_image[regionmask])
    
def calc_regionprops(processed_data, show_images=False):
    print('Calculating region properties for all appropriate images in selected datasets..... Please wait')
    i = 0
    total_processed_item_count = len(processed_data)
    Objects_df = pd.DataFrame()

    for i in range(total_processed_item_count):
        # Pick segmented & RGB image paths from processed data dictionary
        original_img_path = processed_data[i]['original_img_path']
        seg_img_path = processed_data[i]['segmented_img_path']
        masked_img_path = processed_data[i]['masked_img_path']
        # Load segmented image
        img = cv2.imread(seg_img_path) 
    #     grayscale_img = skimage.color.rgb2gray(img)     
        seg_img = img[:,:,0]
        seg_img = (seg_img > 0) * 1

        # Load RGB image
        masked_img1 = cv2.imread(masked_img_path)
        
        if show_images == True:  
            plt.figure(figsize=(10, 5))  
            plt.subplot(1, 3, 1) 
            plt.imshow(masked_img1)
            plt.title(f'RGB Image {masked_img1.shape}')
            plt.axis('off')  
            plt.subplot(1, 3, 2)
            plt.imshow(seg_img)
            plt.title(f'Binary Image {seg_img.shape}')
            plt.axis('off')
#             plt.suptitle(original_img_path.rsplit('/',1)[1])
            plt.show()

        # identify grayscale image for intensities
        grayscale = skimage.color.rgb2gray(masked_img1)

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
        df['A.R.'] = np.where(df['bbox_height'] > 0, df['bbox_length']/df['bbox_height'], 1000)
        df['A.R._ell'] = np.where(df['axis_minor_length'] > 0, df['axis_major_length']/df['axis_minor_length'], 1000)
        # Add No. of objects in the image to all rows of the the datafame
        df['No. of objects'] = df.shape[0]

        # Convert all real units columns from pixels to mm
        for column in list(df.columns):
            if column not in scale_length+scale_area: # Non-real units columns to be ignored
                continue
            if processed_data[i]['scale'] is None or processed_data[i]['popup_unit'] is None: #ignore rows without units
                print('No scale or units for', processed_data[i]['original_img_path'])
                continue
            # Scaling of pixel columns to mm based on the "scaled_props" function
            df[f"{column}_m"] = scaled_props(df, column, processed_data[i]['scale'],processed_data[i]['popup_unit'])
    #         df[f"{column}_{processed_data[i]['popup_unit']}"] = scaled_props(df[column], 
    #                                                                          processed_data[i]['scale'],
    #                                                                          processed_data[i]['popup_unit'])

        # Add folder_id, original_img_path,masked_img_path,segmented_img_path,segmented_data_id,scale,popup_unit to this df
        for x in processed_data[i]:
            if show_images == True:
                print(processed_data[i][x])
            df[x] = processed_data[i][x]

        # Add unique object id for each image
        # in actual code we calculate unique object id with uuid prefix NOW ITS NOT REQUIRED
        df['unique_object_id'] = df['label'].astype(str) 
        #f'{uuid4().hex}_' +  data_frame['label'].astype(str) #used to validate sync between db and csv    
        #df['Label'] = 'blank'

        # Add background intensity mean to all values in the dataframe
        df['bg_intensity'] = pd.DataFrame(bg_props)['intensity_mean'].mean()
    #     df['bg_intensity_sd'] = pd.DataFrame(bg_props)['sd_intensity'].mean() # Irrelevant for background
    #     df['bg_intensity_skew'] = pd.DataFrame(bg_props)['skew_intensity'].mean() # Irrelevant for background
        df['intensity_diff'] = df['intensity_mean']-df['bg_intensity'] # Relative intensity of object wrt background

        # Map annotation data onto this dataframe
        annotation_db_records = list(db.seg_image_annotations.find({'workflow_db_id' : 
                                                                    processed_data[i]['segmented_data_id']}))
        assert len(annotation_db_records) == 1

        db_annotation_data = annotation_db_records[0]['annotation_data']
        annotation_df = pd.DataFrame(db_annotation_data)
        annotation_df['Label_from_id'] = annotation_df['Unique_object_id'].apply(lambda x: x.split('_')[1])
        if show_images == True:
            print('Annotation df stats:', df.shape , annotation_df.shape)
        # Merge annotation df with props df
        merged_df = pd.merge(annotation_df, df, left_on='Label_from_id', right_on='unique_object_id', how='inner')
        # Append the props df with props, scale, uids, annotations & intensities to the master object dataframe
        Objects_df = pd.concat([Objects_df, merged_df], ignore_index=True, axis=0)
    
#     display(Objects_df)#, Objects_df.columns)
    
    # Add short file name without path for plotting histograms for intensities of each image
    Objects_df.insert(4, 'File_name', [item.rsplit('/',1)[1] for item in Objects_df['original_img_path']])
    Objects_df.insert(4, 'Folder_name', [item.rsplit('/',2)[0].rsplit('/',1)[1][:11]+'/'+item.rsplit('/',2)[1]
                       for item in Objects_df['original_img_path']])
    # Adding shape indices
    Objects_df['Compactness'] = np.where(Objects_df['area'] > 0,
                                         (Objects_df['perimeter']**2)/(4*math.pi*Objects_df['area']), 0)
    Objects_df['Circularity'] = np.where(Objects_df['area'] > 0,
                                         Objects_df['area']/Objects_df['area_convex'], 0)
#     print("*"*50)
#     print('Returning a dataframe with file information & properties calculated as listed in:', list(Objects_df.columns))

    return Objects_df

def get_defect_characteristics(Objects_df):
    initial_shape = Objects_df.shape
    # Read defect characteristics excel file
    Week0_2024_char_df = pd.read_excel('./DefectCharacteristicsCorrelated2Images.xlsx', sheet_name='Week0_2024')
    Week9_2024_char_df = pd.read_excel('./DefectCharacteristicsCorrelated2Images.xlsx', sheet_name='Week9_2024')
    Week10_2024_char_df = pd.read_excel('./DefectCharacteristicsCorrelated2Images.xlsx', sheet_name='Week10_2024')
    
    defect_char_df = pd.DataFrame()
    # Merge data from all sheets(/weeks) into a single DataFrame
    defect_char_df = pd.concat([Week0_2024_char_df, Week9_2024_char_df, Week10_2024_char_df], ignore_index=True)
    # defect_char_df.drop(['Length', 'Width', 'A.R.', 'Orientation'], axis=1, inplace=True)
    defect_char_df.insert(0, 'File_name', defect_char_df['Image Name'].astype(str)+'.JPG')
    
    print('\033[36m'+ 'The defect characteristics were captured by experts as follows:' +'\033[36m')
    # display(defect_char_df.head(), defect_char_df.shape)
#     print('Columns in defect_char_df that are not there in Objects_df:', 
#           [item for item in defect_char_df.columns if item not in Objects_df.columns])
    Objects_df = pd.merge(Objects_df, defect_char_df, on='File_name', how='left') #, suffixes=None)
    print('\033[94m'+ '\033[1m' +'The segmentation metrics consolidated alongside the captured defect characteristics:'
            + '\033[1m' +'\033[94m')
    # display(Objects_df.head(), Objects_df.shape)#, Objects_df.columns)#[~Objects_df['Alt Defect label'].isna()])
    print("*"*80)
    print('\033[94m'+ '\033[1m' +"Assigned expert identified defect characteristics for all training images."+ '\033[1m' +'\033[94m')
    print("*"*80)
    
    # Intiate the a heuristics model by next step of running roviding a button
    
    # Call the function to display the button (optional, if you want the button to show immediately)
    if Objects_df.shape[1] > initial_shape[1]: # if the defect characteristics have been augemented then,
        pass
        # create_heuristic_button(Objects_df) # display the heuristics button
    else:
        print('\033[91m'+'No defect characteristics have been added to the segmentation data. Stopping the run. Please check defect characteristics excel sheet for datasets used to train the model.'+'\033[91m')

    return Objects_df


##############################################
### NEXT STEP : RUN THE HEURISTICS BASED MODEL
##############################################
# output_heuristics = widgets.Output()

heur_rev_imgs_pltd = False # Initialize the flag variable to check if the images for review after heuristics model have been plotted

# Function to create and display the heuristics model button
# def create_heuristic_button(Objects_df):
#     def on_button_click(b):
#         global Obj_df, heur_bttn_created  # Declare Obj_df as global to make it accessible globally
#         with output_heuristics:
#             output_heuristics.clear_output()
#             # clear_output(wait=True)
#             Obj_df = hexaind3heuristics_tsl.create_Obj_df(Objects_df)  # Call the function from hexaind3heuristics_tsl.py
#             print('\033[92m'+"Training dataframe (Obj_df) created successfully......"+'\033[92m')
#             print('\033[94m'+"Running Heuristics on Obj_df to generate defect labels & characteristics......"+'\033[94m')
#             Obj_df, Heuristics_Img_df = hexaind3heuristics_tsl.run_heuristics_model(Obj_df)
#             print('\033[92m'+'\033[1m'+"Heuristics model applied successfully."+'\033[1m'+'\033[92m.\n'+'\033[94m'+'The Images for review are being generated.....\nPlease wait. Thank you for your patience.'+'\033[94m')
            
#             Heur_rev_df = Heuristics_Img_df[(Heuristics_Img_df['Pred_Label_Proportions']=='Other/Review 100.0%') | 
#                                             (Heuristics_Img_df['Img_Labels_pred']=='Other/Review') | 
#                                             (Heuristics_Img_df['Label']!=Heuristics_Img_df['Img_Labels_pred'])]
#             review_files = Heur_rev_df['File_name'] 
    
#             # Number of images
#             num_images = len(review_files)
    
#             # Create a figure
#             fig, axs = plt.subplots(num_images, 2, figsize=(14, 3.5*num_images))
    
#             for i, file in enumerate(review_files):
#                 img_raw = imread(Obj_df[Obj_df['File_name']==file]['original_img_path'].unique()[0])
#                 raw_file_path = str(Obj_df[Obj_df['File_name']==file]['Folder_name'].unique()[0]+'/'+file)
#                 img_seg = imread(Obj_df[Obj_df['File_name']==file]['segmented_img_path'].unique()[0])
#                 seg_file_path = str(Obj_df[Obj_df['File_name']==file]['Folder_name'].unique()[0]+'/'+file)
    
#                 # Display the image twice side by side
#                 axs[i, 0].imshow(img_raw)
#                 axs[i, 1].imshow(img_seg)
                
#                 # Image location as title
#                 act_label = Heuristics_Img_df[Heuristics_Img_df['File_name']==file]['Label'].values[0]
#                 pred_label = Heuristics_Img_df[Heuristics_Img_df['File_name']==file]['Img_Labels_pred'].values[0]
#                 raw_img_title = str(raw_file_path+'\n Defect Label:'+ act_label)
#                 seg_img_title = str(seg_file_path+'\n Defect Label:'+ pred_label)
#                 axs[i, 0].set_title(raw_img_title)
#                 axs[i, 1].set_title(seg_img_title)
    
#                 # Remove the axes
#                 axs[i, 0].axis('off')
#                 axs[i, 1].axis('off')
                
#                 if i == num_images-1:
                    
#                     heur_rev_imgs_pltd = True
#                     # print('heur_rev_imgs_pltd variable value in line 279 of create_heuristic_button function is:', 
#                     #       heur_rev_imgs_pltd, 'at', datetime.datetime.now())
    
#             # Display the plot
#             plt.suptitle('The images for review of Heuristic model predictions are', fontsize=18, y=1.005)
#             plt.tight_layout()
#             plt.show(block=True)
            
#             print('Reached the end of the images plotting. Going to change heur_bttn_created variable state.')
# #         global heur_bttn_created
# #         while not heur_bttn_created:
# #             print('Plotting of images for review of heuristic model predcition is done at', datetime.datetime.now(),
# #                   'during the creation of the ML model button in line 218 of get_defect_characteristics function. Please wait 5 sec...')
# #             time.sleep(5)
#             create_ML_button(Objects_df)

#     # #### THE BELOW LINES BELONG TO THE CREATE HEURISTIC BUTTON FUNCTION ####
#     # # Create the button with the specified formatting and icon
#     # button = widgets.Button(
#     #     description='Run Heuristic Model',
#     #     button_style='primary',  # You can change the style ('success', 'info', 'warning', etc.)
#     #     icon='cogs',  # 'cogs' is a suitable icon for something like a "Heuristic Model",  # FontAwesome icon # robot, brain, chart-line
#     #     layout=widgets.Layout(width='220px', height='40px')
#     # )
    
#     # # Assign the button click event to the handler function
#     # button.on_click(on_button_click)
    
#     # # Display the button
#     # display(button)
    
#     #### THE BELOW LINES BELONG TO THE CREATE HEURISTIC BUTTON FUNCTION ####
#     # Create the button with the specified formatting and icon
#     heuristics_button = widgets.Button(
#         description='Run Heuristic Model',
#         button_style='primary',  # You can change the style ('success', 'info', 'warning', etc.)
#         icon='cogs',  # 'cogs' is a suitable icon for something like a "Heuristic Model",  # FontAwesome icon # robot, brain, chart-line
#         layout=widgets.Layout(width='220px', height='40px')
#     )

#     # Assign the button click event to the handler function
#     heuristics_button.on_click(on_button_click)

#     # Display the button
#     display(heuristics_button, output_heuristics)#, output_heuristics)
    
################################
### NEXT STEP : RUN THE ML-MODEL
################################

# output_ml_models = widgets.Output()

# def create_ML_button(Objects_df):
#     def on_button_click_ml(b):
#         with output_ml_models:
#             output_ml_models.clear_output()
#             print('\033[94m'+"Running ML model on Obj_df to generate defect labels......"+'\033[94m')
#             Obj_pred_df, ML_Img_df, lgbm_model, label_encoder = hexaind3heuristics_tsl.run_LGBM_model(Obj_df)
#             print('\033[92m'+'\033[1m'+"ML model trained successfully."+'\033[1m'+'\033[92m')
#             ML_rev_df = ML_Img_df[(ML_Img_df['ML_Pred_Label_Proportions']=='Other/Review 100.0%') |
#                                   (ML_Img_df['ML_pred_Img_Labels']=='Other/Review') | 
#                                   (ML_Img_df['Label']!=ML_Img_df['ML_pred_Img_Labels'])]
#             ML_review_files = ML_rev_df['File_name']
    
    
#             # Number of images
#             num_images = len(ML_review_files)
    
#             # Create a figure
#             fig, axs = plt.subplots(num_images, 2, figsize=(14, 3.5*num_images))
    
#             for i, file in enumerate(ML_review_files):
#                 img_raw = imread(Obj_df[Obj_df['File_name']==file]['original_img_path'].unique()[0])
#                 raw_file_path = str(Obj_df[Obj_df['File_name']==file]['Folder_name'].unique()[0]+'/'+file)
#                 img_seg = imread(Obj_df[Obj_df['File_name']==file]['segmented_img_path'].unique()[0])
#                 seg_file_path = str(Obj_df[Obj_df['File_name']==file]['Folder_name'].unique()[0]+'/'+file)
    
#                 # Display the image twice side by side
#                 axs[i, 0].imshow(img_raw)
#                 axs[i, 1].imshow(img_seg)
    
#                 # Image location as title
#                 act_label = ML_Img_df[ML_Img_df['File_name']==file]['Label'].values[0]
#                 pred_label = ML_Img_df[ML_Img_df['File_name']==file]['ML_pred_Img_Labels'].values[0]
#                 raw_img_title = str(raw_file_path+'\n Defect Label:'+ act_label)
#                 seg_img_title = str(seg_file_path+'\n Defect Label:'+ pred_label)
#                 axs[i, 0].set_title(raw_img_title)
#                 axs[i, 1].set_title(seg_img_title)
    
#                 # Remove the axes
#                 axs[i, 0].axis('off')
#                 axs[i, 1].axis('off')
    
#             # Display the plot
#             plt.suptitle('The images for review of ML model predictions are', fontsize=18, y=1.005)
#             plt.tight_layout()
#             plt.show()

#     # Create the button with the specified formatting and icon
#     button = widgets.Button(
#         description='Run ML Model',
#         button_style='primary',  # You can change the style ('success', 'info', 'warning', etc.)
#         icon='robot',  # 'cogs' is a suitable icon for something like a "Heuristic Model",  # FontAwesome icon
#         layout=widgets.Layout(width='220px', height='40px')
#     )

#     # Assign the button click event to the handler function
#     button.on_click(on_button_click_ml)

#     # Display the button
#     display(button, output_ml_models)#, output_ml_models)
