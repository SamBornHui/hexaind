from PIL import Image
import glob
import os.path
import asyncio
import pymongo
from pymongo import MongoClient
from bson.objectid import ObjectId
from websocket import create_connection,WebSocketConnectionClosedException
import websocket
import random
import base64
import pandas as pd
import traceback
import requests
import json
import time
import random
import csv
import os
import sys
from math import pow , exp, pi
import math
import difflib
from datetime import datetime, date
from itertools import chain 
import shutil
# import pytesseract
import multiprocessing
import websockets

# from icecream import ic

import matplotlib
matplotlib.use('cairo')
from matplotlib import cm
from matplotlib import pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.colors as colors
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.colors import ListedColormap, LinearSegmentedColormap
plt.rcParams.update({'figure.max_open_warning': 0})
plt.ioff()

from io import BytesIO
from collections import Counter


from operator import itemgetter
 
import functools
import numpy as np
import cv2
import re
import pickle
from collections import defaultdict
import threading
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

from sklearn.linear_model import LinearRegression as LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.decomposition import PCA

import skimage
from skimage import io, data
from skimage.color import rgb2gray, gray2rgb, label2rgb
from skimage.feature import * 
from skimage.filters import * 
from skimage.util import *
from skimage.segmentation import watershed
from skimage.transform import rotate, resize, hough_line, hough_line_peaks
from skimage.transform import *

from skimage.draw import rectangle, line
from skimage.segmentation import * 
from skimage.measure import *
from skimage import color
from skimage.exposure import *
from skimage.filters.rank import entropy
from skimage.morphology import *
from skimage import data, io, filters, restoration, exposure, morphology, util, img_as_ubyte,img_as_float,feature, img_as_float64, segmentation
# from PyPDF2 import PdfFileMerger

# import reportlab
# from reportlab.lib.units import mm
# from reportlab.pdfgen import canvas

# from pdf2image import convert_from_path
# from PyPDF2 import PdfFileWriter, PdfFileReader
# import fitz

# from weasyprint import HTML

from scipy.spatial.distance import cdist
from scipy import ndimage, misc
from scipy import fftpack
from scipy.signal import find_peaks, peak_widths, fftconvolve
from skimage.transform import resize

import statsmodels.api as sm
import tifffile
import scipy.stats as stats
from scipy.stats import norm
import logging

from app.services.apps.image_analysis.configurations import *
# from action_summary_common import *
# from modules_image_analysis_common import *
# from annotations_image import *

# from cropinfobar import *
# from extractscalebar import *
# from pathlib import Path
from uuid import uuid4


# from hexaind_common.hexaind_logging.hexaind_logger import HexaindLogger
# from databrick.ingestion.tabular import write_ingestion_dag_by_data, write_ingestion_dag_by_dataset

# from spocksextractscalebar import spocksExtractScalebar
from app.config.env_vars import environment

import warnings
warnings.filterwarnings('ignore')
logger = logging.getLogger(__package__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))



global APPLICABLE

APPLICABLE = True
# hexaind_logger = HexaindLogger("HexaindLoggerApp")

def checkEnv(path):
    t = path
    if TESTPORT in SOCKETURL:
        if path[-1] =='/':
            path = path[:-1]
            path = path + '_test/'
        else:
            path = path + '_test'
        
    return path

def checkWorkflowMode(wid, image_analysis_dao):
    if wid:
        db = image_analysis_dao
        collection = db.sampleworkflows
        report = collection.find_one(
                {'_id': ObjectId(wid)})
                
        return report['default']
    else:
        return False
    
def createImageNamefolder(path):
    fpath, name = os.path.split(path)
    name, _ = os.path.splitext(name)
    newpath = fpath + '/' + name
    newpath = checkEnv(newpath)
    if not os.path.exists(newpath):
        os.mkdir(newpath)
    return newpath

def rgbToGray(img):
    # print("imgae: ", img)
    if len(img.shape)>=3:
        img = rgb2gray(img)
        return img
    else:
        return img

# def rgbToGray(img):
#     # Check if the image is already in grayscale (2D array), if so, return it as is.
#     if len(img.shape) < 3:
#         return img
#     # Convert the RGB image to grayscale
#     gray_img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
#     return gray_img


def cropAndSegimageMasking(img, cord):
    try:
        print("Inside cropAndSegimageMasking")
        h, w = img.shape[:2]  
        
        # Convert relative percentages to absolute pixel values
        x1 = int(max(0, w * (cord['x1'] / 100)))
        y1 = int(max(0, h * (cord['y1'] / 100)))
        x2 = int(min(w, x1 + (w * (cord['w'] / 100))))
        y2 = int(min(h, y1 + (h * (cord['h'] / 100))))

        # Ensure valid dimensions
        if x2 <= x1 or y2 <= y1:
            raise ValueError(f"Invalid crop dimensions: ({x1}, {y1}, {x2}, {y2})")
        
        img = img[y1:y2, x1:x2]
        return img
    except Exception as e:
        logger.error(f"Unable to mask the image due to: {str(e)}")
        return img  # Return None to handle invalid crops


def shadowRemoval(IM):
    if IM.ndim == 3:
        IM = rgbToGray(IM)
        
    if IM.dtype == 'uint8':
        IM = img_as_float64(IM)    

    # Resizing the image so we do not apply regression on large number of points    
    IM_low = resize(IM, (np.round(IM.shape[0]*100/IM.shape[1]), 100), preserve_range = True)    
    
    # Extracting input and output for regression
    Iy,Ix = np.meshgrid(np.arange(0,IM_low.shape[1]),np.arange(0,IM_low.shape[0]))
    X = np.concatenate((Ix.flatten()[:,None], Iy.flatten()[:,None]), axis = 1)
    Y = IM_low.flatten()[:,None]
    
    # Setting up the polynomials for feature space
    poly = PolynomialFeatures(2, include_bias = False)
    
    # Casting the input variables to feature space
    Xf = poly.fit_transform(X)
    
    # Applying regression with second order polynomial to remove gradient
    R = LinearRegression()
    R.fit(Xf, Y)
    Yh = R.predict(Xf)
    
    # Resizing the gradient predictions back to the original image size
    Yh = resize(Yh.reshape(IM_low.shape), IM.shape, preserve_range = True)   
    
    # Removing the shadow gradient
    IM_new = IM - Yh
    
    diff = IM_new.max()-IM_new.min()
    if diff<=1:
        IM_new = IM_new+abs(IM_new.min())+(1-diff)/2
    else:
        IM_new = IM_new+abs(IM_new.min())
        IM_new = IM_new/IM_new.max()
    
    return IM_new, Yh, IM


def defaultGaussianFilter(img, sigstep = 0.25, start = 0.5):
    from numpy.linalg import norm
    sigstep = 0.25
    n = int(np.ceil(4/sigstep))
    dos = np.empty(n)
    nb = np.empty(n)
    dd = np.empty(n)
    for ii in range(n):
        dos[ii] = start+ii*sigstep
        B = filters.gaussian(img,sigma=0.5+ii*sigstep, preserve_range = True, mode='reflect')
        R = img-B
        dd[ii] = norm(np.dot(np.ravel(B),np.ravel(R)))/norm(np.ravel(B),2)
    
    ind  = np.argmin(dd[1:])+1
    if dd[ind]<dd[0]:
        sel = ind
    else:
        sel = 1
    
    par = dos[sel]
    G = filters.gaussian(img,par)
    return(G,dd,par)

def defaultValueForManualThresh(img):
    C = img_as_ubyte(img)
    tt = int(filters.threshold_otsu(C))
    manual_threshold = tt # default value for manual threshold
    threshold_min = C.min()+1 # minimum value of threshold on slidebar
    threshold_max = C.max()-1 # maximum value of threshold on slidebar

    data = {"default_val": int(tt), "min_range": int(threshold_min), "max_range": int(threshold_max)}
    
    return data

def plotSegmentedImgHistogram(B, T, newpath,  filtername):
    h1 = img_as_ubyte(B)
    bin_edges = np.arange(-0.5,255,1)

    fig, ax = plt.subplots()
    ax.axes.yaxis.set_visible(False)
    ax.hist(h1.ravel(), bin_edges, alpha = 0.5, label = 'Image intensities', align = 'mid', rwidth=1)
    plt.xlim(0, 255)
    plt.title('Image histogram', fontsize = 16)

    if type(T) != int:
        for thresh in T:
            ax.axvline(thresh*255, color='r')
            ax.legend({'Threshold'},loc = 'best')
            plt.rc('xtick', labelsize=16)    # fontsize of the tick labels
            plt.rc('legend', fontsize=16)    # legend fontsize
    else:
        ax.axvline(T, color='r')
        ax.legend({'Threshold'},loc = 'best')
        plt.rc('xtick', labelsize=16)    # fontsize of the tick labels
        plt.rc('legend', fontsize=16)    # legend fontsize

   
    histt = newpath+'/'+filtername+'_histogram'+str(int(round(time.time() * 1000)))+'.png'
    fig.savefig(histt)
    plt.close(fig)
    
    return histt

def exact_crop(image, target_shape):
            height, width = target_shape
            cropped_image = image[:height, :width]  # Trim to match target dimensions exactly
            return cropped_image

def segmentationVisualization(visualization, para1, img, colors, sample):

    # Apply the cropping
    # sample_cropped = exact_crop(sample, img.shape)
    # logger.debug(f"IMG====={str(img)}")
    # logger.debug(f"Sample image====={str(sample)}")
    sample_cropped = sample
    if visualization =='label segmented':
        CC = img*1
        img = label2rgb(label(CC), image=sample_cropped, alpha=0.4, bg_label=0, bg_color=None, kind='overlay')

    elif visualization == 'overlay_segmented':
        CC = img*1
        color = para1['color']
        clrdata=(list(filter(lambda val: val['color'] == color, colors)))
        clrlist = []
        clrlist.append(clrdata[0]['val'])
        img = label2rgb(CC, image=sample_cropped, colors=clrlist, alpha=0.3, bg_label=0, bg_color=None, image_alpha=1, kind='overlay')

    elif visualization=='outline_segmented':

        color = para1['color']
        clrdata = (list(filter(lambda val: val['color'] == color, colors)))
        img = mark_boundaries(sample_cropped, img, color=clrdata[0]['val'], outline_color=None, mode='thick', background_label=0)

    return img

def callingVisualization(visualization, para1, img, colurs, croppimg):
    if visualization and visualization != 'Black/white (default)':
        img = segmentationVisualization(visualization, para1, img, colurs, croppimg)
    elif not visualization:
        img = multiSegPlot(img)
        
    return img

def multiSegPlot(img): 
    n = len(np.unique(img))
    h,w = img.shape
    cdict = {'red':[[0.0,  0.2392, 0.2392],
                    [0.25,  0.1961, 0.1961],
                   [0.5,  0.09412, 0.09412],
                    [0.75,  0.8196, 0.8196],
                    [0.80,  0.9765, 0.9765],
                   [1.0,  0.466, 0.466]],
             
         'green': [[0.0,  0.149, 0.149],
                   [0.25, 0.4824, 0.4824],
                   [0.5, 0.749, 0.749],
                   [0.75,  0.749, 0.749],
                   [0.80,  0.9804, 0.9804],
                   [1.0,  0.7450, 0.7450]],
             
         'blue':  [[0.0,  0.6588, 0.6588],
                   [0.25,  0.9882, 0.9882],
                   [0.5,  0.7098, 0.7098],
                   [0.75,  0.1529, 0.1529],
                   [0.8,  0.07843, 0.07843],
                   [1.0,  0.9330, 0.933]]}
    newcmp = LinearSegmentedColormap('testCmap', segmentdata=cdict, N=5)
    from_list = matplotlib.colors.LinearSegmentedColormap.from_list
    cm = from_list(None, newcmp(range(0,n)), n)
    plt.figure()#figsize=(20,20))
    ax = plt.gca()
    plt.imshow(img, cmap=cm)
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.2)
    plt.clim(-0.5, n-0.5)
    cb = plt.colorbar(ticks=range(0,n),cax=cax, label='Layer',orientation = 'vertical')
    cb.ax.tick_params(length=0)
    ax.axes.yaxis.set_visible(False) # do not show y-axis labels or ticks
    ax.axes.xaxis.set_visible(False) # do not show y-axis labels or ticks
    plt.imsave('plot.png',img,cmap=cm)
    
    img = io.imread('plot.png')
    os.remove('plot.png')
    return img

def plotPreprocessedHistogram(h1, h2, newpath,  user_id, name, filtername, intensityimg=''):
            
    if name == 'intensitygradientreduction':
        plt.figure(figsize=(10,10))
        ax = plt.gca()
        ax.axes.yaxis.set_visible(False)
        plt.yticks([])
        plt.xticks([])
        
        plotimage = newpath+'/'+filtername+'_histogram'+'_'+str(int(round(time.time() * 1000)))+'.png'
        plt.imsave(plotimage,intensityimg, cmap = 'gray')
    
    else:
        
        h2 = img_as_ubyte(h2)
        h1 = img_as_ubyte(h1)
    
        bin_edges = np.arange(-0.5,255,1)
        
        fig, ax = plt.subplots()
        ax.axes.yaxis.set_visible(False)
        ax.hist(h1.ravel(), bin_edges, label = 'Input Image ', alpha = 0.5, align = 'mid', rwidth=1)
        ax.hist(h2.ravel(), bin_edges, label = 'Filtered Image ', alpha = 0.5, align = 'mid', rwidth=1 )
        plt.xlim(0, 255)
        ax.legend(loc = 'upper right')
        plt.title('Histogram', fontsize = 16)
        plt.rc('xtick', labelsize=16)    # fontsize of the tick labels\n",
        plt.rc('legend', fontsize=16)    # legend fontsize\n",
        
        plotimage =newpath+'/'+filtername+'_histogram'+'_'+str(int(round(time.time() * 1000)))+'.png'
        fig.savefig(plotimage)
        plt.close(fig)
    
    
    return plotimage

def showDiff(img1, img2):
    d  = np.asarray(img2*1,dtype="float")-np.asarray(img1,dtype="float")
    d_add = np.asarray(d>0,dtype="float") # added pixels
    d_neg = np.asarray(d<0,dtype="float") # removed pixels
    d_rem = img2-d_add    
    d_add_rgb = np.dstack((d_add,np.zeros(img1.shape),d_add))
    d_neg_rgb = np.dstack((np.zeros(img1.shape),d_neg,d_neg))
    d_rem_rgb = np.dstack((d_rem,d_rem,d_rem))
    d_all = d_add_rgb+d_neg_rgb+d_rem_rgb
    
    return d_add, d_neg, d_all

def save_region_props_as_csv_for_image(filtered_image_path, data_frame, popup_unit):
    try:
        #create temp df to store
        df_ = pd.DataFrame()
        default_cols_names = {
            'area' : 'Area(px)',
            'major_axis_length' : 'Major_axis_length(px)',
            'minor_axis_length' : 'Minor_axis_length(px)',
            'aspect_ratio' : 'Aspect_ratio',
            'label' : 'Original_label'
        }
        for col in ['area' , 'major_axis_length', 'minor_axis_length','aspect_ratio', 'label']:
            df_[default_cols_names[col]] = data_frame[col]

        if popup_unit:
            cols_names = {
                f'area_{popup_unit}2' : 'Area',
                f'length_{popup_unit}' : 'Length',
                f'height_{popup_unit}' : 'Height'
            }
            cols = [f'area_{popup_unit}2' , f'length_{popup_unit}', f'height_{popup_unit}']
            for col in cols:
                df_[cols_names[col]] = data_frame[col]
            
        df_['Popup_unit'] = popup_unit
        folder_path, filtered_image_name = os.path.split(filtered_image_path)
        folder_name , image_name = os.path.split(folder_path)
        main_folder_path, main_folder_name = os.path.split(folder_name)
        df_['Folder_name'] = main_folder_name
        df_['Image_name'] = image_name
        #Region
        df_['Unique_object_id'] =  f'{uuid4().hex}_' +  data_frame['label'].astype(str) #used to validate sync between db and csv
        df_['Object'] = 'Object ' + df_.index.astype(str)
        df_['Label'] = 'blank'

        #create temp folder if doesnt exist
        region_props_directory = os.path.join(folder_path,'region_properties/temp/')
        if not os.path.exists(region_props_directory):
            os.makedirs(region_props_directory)
        #temp file name    
        region_props_file_name = filtered_image_name.split('.')[0] + '_region_properties.csv'
        region_props_full_path = os.path.join(region_props_directory, region_props_file_name)
        
        df_.to_csv(region_props_full_path, index=False)

        return region_props_full_path
    except Exception as e:
        logger.exception(f'Error occurred while saving region properties in temp file, filtered_image_path : {filtered_image_path}, {e}')
        raise e

def convert_pixels_measurement_into_popup_units(df, scale, popup_unit):
    df[f'area_{popup_unit}2'] = df['area'] * (scale ** 2)
    df[f'length_{popup_unit}'] = df['major_axis_length'] * scale
    df[f'height_{popup_unit}'] = df['minor_axis_length'] * scale
    df['aspect_ratio'] = df[f'length_{popup_unit}'] / df[f'height_{popup_unit}']
    return df

def generate_region_properties_subset(df,popup_unit):
    #calculating region properties for area , length , aspect_ratio
    CONST_ROUNDING_VAL = 3
    cols = [f'area_{popup_unit}2', f'length_{popup_unit}', 'aspect_ratio']
    if popup_unit == 'px':
        cols = ['area', 'major_axis_length' , 'aspect_ratio']
    
    #while calculating mean then only ignore the np.inf
    df_temp = df.replace([np.inf, -np.inf], np.nan)
    df_temp = df_temp.fillna(df_temp.dropna().mean())
    stats = df_temp.describe().loc[['count','mean', 'min','max']]
    #no need to ignore np.inf while calculating max
    stats = pd.concat([stats,pd.DataFrame({'new_max' : df.max()}).T]).round(CONST_ROUNDING_VAL).astype(str)
    region_properites_subset = {
        f'Average object area ({popup_unit}):' : stats[cols[0]]['mean'],
        f'Min object area ({popup_unit}):' : stats[cols[0]]['min'],
        f'Max object area ({popup_unit}):' : stats[cols[0]]['new_max'],
        f'Average object length ({popup_unit}):' : stats[cols[1]]['mean'],
        f'Min object length ({popup_unit}):' : stats[cols[1]]['min'],
        f'Max object length ({popup_unit}):' : stats[cols[1]]['new_max'],
        'Average object aspect ratio:' : stats[cols[2]]['mean'],
        'Min object aspect ratio:' : stats[cols[2]]['min'],
        'Max object aspect ratio:' : stats[cols[2]]['new_max'],
    }
    return region_properites_subset

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

def writePropsInMetadata(sample_id, sample_name, metadata_dir, region_properties):
    csvs_list = glob.glob(metadata_dir + '/*.csv')
    if csvs_list:
        path = csvs_list[0]

        if len(csvs_list)>1:
            path = list(filter(lambda k: '_aggregated' in k, csvs_list))[0]
            df = pd.read_csv(path)
        else:
            df = pd.read_csv(path)
        col_names = list(df.columns)
        for i in region_properties:
            col = i.replace(':','').replace(' ','_')
            if col not in col_names:
                df[col] = ''

            df[col] = np.where((df['sample_name'] == sample_name) & (df['sample_id'] == sample_id), region_properties[i], df[col])

        df.to_csv(path,index=False)

async def send_data(data, url):
    async with websockets.connect(url) as websocket:
        # Convert data to JSON string
        data_str = json.dumps(data)
        # Send data to the WebSocket server
        await websocket.send(data_str)
        # Wait for a second before sending the next data
        await asyncio.sleep(1)

def send_data_sync(data, url):
    # Convert data to JSON string
    data_str = json.dumps(data)
    # Connect to the WebSocket server
    ws = websocket.create_connection(url)
    try:
        # Send data to the WebSocket server
        ws.send(data_str)
        # Wait for a second before sending the next data
        time.sleep(1)
    except WebSocketConnectionClosedException:
        logger.info('Connection closed')
    finally:
        # Close the WebSocket connection
        ws.close()

def fft_convolve_dilation(img,foot_print):
    return fftconvolve(img,foot_print,'same')>0.5

def fft_convolve_erosion(img,foot_print):
     
    padding_r,padding_c = foot_print.shape
    
    A_inv = np.logical_not(img)
    A_inv = np.pad(A_inv, (padding_r,padding_c), mode='edge')
    tmp = fftconvolve(A_inv, foot_print, 'same') > 0.5
    temp_r ,temp_c = tmp.shape
    return np.logical_not(tmp[padding_r:temp_r-padding_c, padding_r:temp_c-padding_c])

def fft_convolve_closing(img,foot_print):
    res = fft_convolve_dilation(img,foot_print)
    return fft_convolve_erosion(res,foot_print)

def fft_convolve_opening(img,foot_print):
    res = fft_convolve_erosion(img,foot_print)
    return fft_convolve_dilation(res,foot_print)
    


async def filtersToBeApllied(mainwf, post_visu, img, pixelX, pixelY, 
                       newpath, user_id, sample, default, callreceived,
                         cropimg='', scale = 1.5151, popup_unit=None,
                           save_region_props = False):
    print("Inside filtersToBeApllied")


    
    thresholdhist, boundary_excel, perula  = '', '', ''
    preprocessedgraph, intensityimg, thresholdhistgraph, preprocessedlayer, segprocessedlayer, postprocessedlayer = [], [], [], [], [], [] 
    croppimg = sample
    lastwfimage = img
    minrange, maxrange, val = 0,0, 0
    colurs = [{'color':'magenta','val': [1,0,1]},
                {'color':'red','val' : [1,0,0]},
                {'color':'yellow' ,'val' : [1,1,0]}]

    region_properties = dict()    
    count = 1  
    mainwf_len = len(mainwf)
    for wf_index, wfff in enumerate(mainwf):
        starttime = time.time()
        img = rgbToGray(img)
        cmap, binary = 'gray', ''
        minrange, maxrange, default_val, pltsave = 0, 0, 0, 0
        funcname = wfff['Value']
        paralen = len(wfff['Params'])
        para1 = wfff['Params']
        lastimg = img
        if paralen < 1:
            if funcname == 'intensitygradientreduction':
                imgs = shadowRemoval(img)
                pltsave = 1
                img = imgs[0]
                intensityimg = imgs[1]
                
            elif 'invertimage'==funcname:
                wfff['Name'] = wfff['Name'].replace('/','_')
                img = img_as_ubyte(img)
                img = invert(img)
                img = img_as_float(img)
                
            elif 'exposure.rescale_intensity'==funcname:
                im = exposure.rescale_intensity(img, in_range='image', out_range='dtype')
                img = im
            elif 'segmentation.find_boundaries' ==funcname:
                img = img_as_ubyte(img)
                img = segmentation.find_boundaries(img, connectivity=2, mode='outer', background=0)
                
                i,j = np.nonzero(img)
                df = pd.DataFrame(j, columns=["x_img"])
                df['y_img'] = i
                y_dim = img.shape[0]-1
                df['x'] = df['x_img']
                df['y'] = y_dim-df['y_img']
                print("scale:",scale)
                df['x_scale'] = df['x']*scale
                df['y_scale'] = df['y']*scale
                df['x_normalized'] = (df['x']-np.min(df['x']))/np.max(df['x'])
                df['y_normalized'] = (df['y']-np.min(df['y']))/np.max(df['y'])
                df['x_scale'] = df['x']*scale
                df['y_scale'] = df['y']*scale
                df['x_scale_zeroed'] = df['x_scale']-np.min(df['x_scale'])
                df['y_scale_zeroed'] = df['y_scale']-np.min(df['y_scale'])
                
                df = df.round(3)
                boundary_excel = newpath+'/'+ 'outline_output'+str(int(round(time.time() * 1000)))+'.xlsx'
                with pd.ExcelWriter(boundary_excel, engine="xlsxwriter") as writers:  # doctest: +SKIP
                    df[['x','y','x_normalized','y_normalized','x_scale','y_scale','x_scale_zeroed','y_scale_zeroed']].to_excel(writers, sheet_name='outline_coords')
                    
                foldername, _ = os.path.split(boundary_excel)
                basefoldername = os.path.split(os.path.dirname(boundary_excel))[0]
    
                batchdir = basefoldername + '/batchprocessed/'
                batchdir = checkEnv(batchdir)
                if not os.path.exists(batchdir):
                    os.mkdir(batchdir)
                
                foldername = os.path.basename(foldername)                
                newbatchpath = batchdir + foldername + '_outline_output.xlsx'
                shutil.copyfile(boundary_excel, newbatchpath)
                    
            else:
                filtername = eval(funcname)
                img = filtername(img)
    
        elif paralen == 1:
            if 'filters.gaussian' == funcname:
                key = (list(para1)[0])
                val = para1[key]
                val = int(val)
                
                if val==-1:
                    res = defaultGaussianFilter(img)
                    img = res[0]
                    default_val = res[2]
                else:
                    img = filters.gaussian(img, sigma=val, output=None, mode='nearest', cval=0, 
                                           channel_axis=None, preserve_range=False, truncate=4.0)
                    default_val = 0
            
            elif 'filters.median'==funcname:
                filtername = eval(funcname)
                key = (list(para1)[0])
                val = para1[key]
                val = int(val)
                img = filtername(img, square(val))
            
            elif 'minimum size to be removed' in para1:
                filtername = eval(funcname)
                key = (list(para1)[0])
                val = para1[key]
                val = float(val)
                img = img_as_float(img)
                img = filtername(img==1, min_size=val, connectivity=2)
                
                    
            elif 'morphology.remove_small_holes' == funcname:
                filtername = eval(funcname)
                key = (list(para1)[0])
                val = para1[key]
                val = float(val)
                img = filtername(img==1 , area_threshold=val)#, connectivity=2)
                    
            else:
                key = (list(para1)[0])
                val = para1[key]
                val = int(val)
                filtername = eval(funcname)
                img = filtername(img, val)
                
        else:
            if funcname == 'restoration.denoise_bilateral':
                
                sc = para1['sigma_color']
                ss = para1['sigma_spatial']
                img = restoration.denoise_bilateral(img,sigma_color = sc, sigma_spatial = ss, mode = 'reflect')
                
            elif 'manualthreshold'==funcname:
                img = skimage.img_as_ubyte(img)
                val = para1['threshold_value']
                if val==-1:
                    defaultinfo = defaultValueForManualThresh(img)
                    maxrange = defaultinfo['max_range']
                    minrange = defaultinfo['min_range']
                    val = defaultinfo['default_val']
                else:
                    defaultinfo = defaultValueForManualThresh(img)
                    maxrange = defaultinfo['max_range']
                    minrange = defaultinfo['min_range']
                    minrange = 0
                
                C_manual = img < val
                default_val = val
              
                thresholdhist = plotSegmentedImgHistogram(img, val, newpath,  wfff['Name'])
                img = C_manual
                binary = img
                visualization = para1['visualization']
                img = callingVisualization(visualization, para1, img, colurs, croppimg)
                
            
            # elif 'filters.threshold_multiotsu'==funcname:
            #     key = (list(para1)[0])
            #     val = para1[key]
            #     val = int(val)
            #     filtername = eval(funcname)
            #     T = filtername(img, classes=val)
            #     thresholdhist = plotSegmentedImgHistogram(img, T, newpath,   wfff['Name'])
            #     img = np.digitize(img, bins=T)
            #     regions = img
            #     selectedlayers = para1['selected_layers']['local_state_1']
            #     perula = multiSegPlot(regions)
            #     binary = img
            #     cmap = 'Accent'
            #     visualization = para1['visualization']
            #     binary, cmap, pltsave, img, visualization = selectLayersAndVisualization(img, selectedlayers, visualization, para1, colurs, croppimg)
                        
            # elif 'segmentation.slic'==funcname:
            #     sc = para1['classes']
            #     ss = para1['compactness']
            #     filtername = eval(funcname)
            #     segments = filtername(img, n_segments=sc, compactness=ss, enforce_connectivity=False)
            #     binary = segments
            #     perula = multiSegPlot(segments)
            #     selectedlayers = para1['selected_layers']['local_state_1']
            #     visualization = para1['visualization']
            #     binary, cmap, pltsave, img, visualization = selectLayersAndVisualization(segments, selectedlayers, visualization, para1, colurs, croppimg)
                
            elif 'feature.match_template' == funcname:
                img = img_as_ubyte(img)
                cord = para1['template_cord']
                x0, x1, y0, y1 = int(cord['x1']), int(cord['x2']), int(cord['y1']), int(cord['y2'])
                t = img[x0:x1, y0:y1] # template
                thresh = para1['threshold_value']
                filtername = eval(funcname)
                img = filtername(img, t)
                img = img>thresh  # send back platform
                pltsave = 1
                cmap = 'gray'
                thresholdhist = ''
                img = img < thresh
                binary = img
                visualization = para1['visualization']
                img = callingVisualization(visualization, para1, img, colurs, croppimg)
                
            
            elif 'filters.threshold_otsu' == funcname:
                img = rgbToGray(img)
                img = img_as_ubyte(img)
                defaultinfo = defaultValueForManualThresh(img)
                default_val = defaultinfo['default_val']
                maxrange = defaultinfo['max_range']
                minrange = defaultinfo['min_range']
                filtername = eval(funcname)
                thresh = filters.threshold_otsu(img)
                T = int(thresh)
                thresholdhist = plotSegmentedImgHistogram(img, T, newpath,  wfff['Name'])
                img = img < thresh
                binary = img
                visualization = para1['visualization']
                img = callingVisualization(visualization, para1, img, colurs, croppimg)
                
            elif 'filters.threshold_local' == funcname:
                sc = para1['block_size']
                ss = para1['offset']
                img  = img_as_ubyte(img)
                filtername = eval(funcname)
                local_thresh = filtername(img, sc, 'mean', offset=ss)
                img = img < local_thresh
                binary = img
                visualization = para1['visualization']
                img = callingVisualization(visualization, para1, img, colurs, croppimg) 
    
            elif 'Maskoutobjectclusters' == funcname:
                selement = para1['structure_element']
                if selement == 'rectangle':
                    width = para1['width']
                    height = para1['height']
                    se = morphology.rectangle(nrows=width, ncols=height)
                    
                elif selement == 'square':
                    width = para1['height']
                    se = morphology.square(width=width)
                    
                else:
                    radius = para1['radius']
                    se = morphology.disk(radius=radius)
                    
                D1 = morphology.binary_dilation(img, se)
                try:
                    val = para1['size_removed']
                except:
                    val = -1
                if val==-1:
                    D1 = morphology.remove_small_objects(D1,int(len(np.ravel(D1))/2))
                    val = int(len(np.ravel(D1))/2)
                else:
                    D1 = morphology.remove_small_objects(D1,val)
                    
                maxrange = int(len(np.ravel(D1))/1.5)
                minrange = int(len(np.ravel(D1))/40)
                img = img*D1
              
            elif (list(filter(lambda val: val['Value'] == funcname, MORPHOLOGYFILTERS))):
                selement = para1['structure_element']
                if selement == 'rectangle':
                    width = para1['width']
                    height = para1['height']
                    se = morphology.rectangle(nrows=width, ncols=height)
              
                elif selement == 'square':
                    width = para1['height']
                    se = morphology.square(width=width)
                    
                else:
                    radius = para1['radius']
                    se = morphology.disk(radius=radius)
                    
                skimage_functions_to_fft_functions_map = {
                    'morphology.binary_opening' : 'fft_convolve_opening',
                    'morphology.binary_closing' : 'fft_convolve_closing',
                    'morphology.binary_dilation' : 'fft_convolve_dilation',
                    'morphology.binary_erosion' : 'fft_convolve_erosion',
                }
                funcname = skimage_functions_to_fft_functions_map.get(funcname,funcname)
                filtername = eval(funcname)
                img = filtername(img, se)
                    
            else:    
                filtername = eval(funcname)
                key = (list(para1)[0])
                fval = para1[key]
                skey = (list(para1)[1])
                sval = para1[skey]
                img = filtername(img, fval, sval)
                

        step = wfff['Steps']
        fid = wfff['fid']
        imgg = img_as_ubyte(img)
        imgg = Image.fromarray(imgg).convert('RGB')
        # imgg = gray2rgb(imgg)
        endtime = time.time()-starttime
        annotation_data_df = None
        if step==1 or step==1.5:
            segmentedimg =newpath+'/'+ wfff['Name']+'_preprocessed'+str(int(round(time.time() * 1000)))+'.png'
            if(pltsave):
                plt.imsave(segmentedimg,img,cmap=plt.cm.gray)
                plt.close('all')
            else:
                imgg.save(segmentedimg)
            
            pth = plotPreprocessedHistogram(lastimg,img, newpath,  user_id, wfff['Value'], wfff['Name'], intensityimg)  
            temp = {"fid": fid, "filtername": wfff["Name"], 'filterd_image': segmentedimg, 
                    'histogram_path':pth, "gaussain_defaultval": default_val, "time":endtime}
            preprocessedlayer.append(temp)
            
    
        elif step==2:
            
            try:
                lastwfimage = wfff['result']['black&white']
                lastwfimage = rgbToGray(plt.imread(lastwfimage))
                h, w = img.shape
                lastwfimage = cv2.resize(lastwfimage, (w, h))
                diff = showDiff(lastwfimage, img_as_float(img))
                diffimg = newpath+'/'+ wfff['Name']+'_difference_segmented'+str(int(round(time.time() * 1000)))+'.png'
                plt.imsave( diffimg, diff[2], cmap='gray')
            except:
                diffimg = ''
            
            if wfff['Name']=='Global multithreshold' or wfff['Name']=='K means segmentation':
                segmentedimg = newpath + '/' + wfff['Name'] + '_segmented'+str(int(round(time.time() * 1000)))+'.png'
                binarypath = newpath + '/' + wfff['Name'] + '_segmented_binary'+str(int(round(time.time() * 1000)))+'.png'
                perulapath = newpath + '/' + wfff['Name'] + 'perula_segmented_binary'+str(int(round(time.time() * 1000)))+'.png'
                plt.imsave(perulapath, perula)
                perula = perulapath
            else:
                segmentedimg = newpath+'/'+ wfff['Name']+'_segmented'+str(int(round(time.time() * 1000)))+'.png'
                binarypath = newpath+'/'+ wfff['Name']+'_segmented_binary'+str(int(round(time.time() * 1000)))+'.png'
            
            img = img_as_float(binary)
            lastwfimage = img
            binaryimg = img_as_ubyte(binary)
            binaryimg = gray2rgb(binaryimg)
            binaryimg = Image.fromarray(binaryimg)
            
            metrics = ('area', 'centroid', 'bbox', 'perimeter', 'orientation', 
                        'major_axis_length', 'minor_axis_length', 'label') # remaining properties recommended by George
            props = regionprops_table(label(binary), properties = metrics)
            df = pd.DataFrame(props)
            # mutiplying the scale value to the area # HEXAIND-6083
            region_properties_subset = {}
            if scale and popup_unit: 
                df = convert_pixels_measurement_into_popup_units(df,scale,popup_unit)
                region_properties_subset = generate_region_properties_subset(df, popup_unit)
            else:
                df['aspect_ratio'] = df['major_axis_length']/df['minor_axis_length'] 
                region_properties_subset = generate_region_properties_subset(df, "px")

            fraction = round(float(np.sum(binary==1)/np.size(binary)),3)
            num_objects = int(df['area'].count())
            region_properties = {'Fraction:': fraction, 'No of objects:': num_objects}
            region_properties.update(region_properties_subset)
        
            if(pltsave):
                plt.imsave(segmentedimg,img,cmap=cmap)
                plt.imsave(binarypath,binary,cmap='gray')
                plt.close('all')
            else:
                imgg.save(segmentedimg)
                binaryimg.save(binarypath)
            
            img = binary
            af = np.sum(img)/np.size(img)
            temp = {"fid": fid, "filtername": wfff["Name"], 
                    "filterd_image": segmentedimg, "histogram_path":thresholdhist,
                      "black&white": binarypath, "min_range": minrange, "maxrange": maxrange,
                        "default_val":default_val, "area_fraction":af, "previewchanges": diffimg, 
                        'perula': perula, 'region_properties': region_properties, "time":endtime}
            if wf_index == (mainwf_len-1):
                region_properties_csv_file = save_region_props_as_csv_for_image(temp['filterd_image'], df, popup_unit)
                temp['temp_region_properties_csv_file'] = region_properties_csv_file
                np.save(region_properties_csv_file.replace('.csv','.npy'),binary)
                if save_region_props:
                    temp['region_properties_csv_file'],annotation_data_df = update_main_region_props_file_for_image(region_properties_csv_file)
                    numpy_file_name = temp['region_properties_csv_file'].replace('.csv','.npy')
                    np.save(numpy_file_name, binary)
                    temp['binary_img_ndarray'] = numpy_file_name
                
            segprocessedlayer.append(temp)
            if visualization and visualization == 'Black/white (default)':
                segmentedimg = binarypath
                    
        else:
            binary = img
            try:
                lastwfimage = wfff['result']['black&white']
                lastwfimage = rgbToGray(plt.imread(lastwfimage))
                h, w = img.shape
                lastwfimage = cv2.resize(lastwfimage, (w, h))
            except:
                lastwfimage = lastimg
            diff = showDiff(lastwfimage, img)
            lastwfimage = binary
            visualization = post_visu['visualization']
            img = callingVisualization(visualization, post_visu, img, colurs, croppimg)
            
            binaryimg = img_as_ubyte(binary)
            # binaryimg = gray2rgb(binaryimg)
            binaryimg = Image.fromarray(binaryimg).convert('RGB')
            imgg = img_as_ubyte(img)
            # imgg = gray2rgb(imgg)
            imgg = Image.fromarray(imgg).convert('RGB')
            df = pd.DataFrame()
            if np.sum(np.ravel(binary)):
                metrics = ('area', 'centroid', 'bbox', 'perimeter', 'orientation',  'major_axis_length', 'minor_axis_length', 'label') # remainng properties recommended by George
                props = regionprops_table(label(binary), properties = metrics)
                df = pd.DataFrame(props)
                region_properties_subset = {}
                if scale and popup_unit: 
                    df = convert_pixels_measurement_into_popup_units(df,scale,popup_unit)
                    region_properties_subset = generate_region_properties_subset(df, popup_unit)
                else:
                    df['aspect_ratio'] = df['major_axis_length']/df['minor_axis_length'] 
                    region_properties_subset = generate_region_properties_subset(df, "px")

                fraction = round(float(np.sum(binary==1)/np.size(binary)),3)
                num_objects = int(df['area'].count())
                region_properties = {'Fraction:': fraction, 'No of objects:': num_objects}
                region_properties.update(region_properties_subset)
            else:
                region_properties = ''
                expected_cols = ['area','major_axis_length','minor_axis_length','label','aspect_ratio']
                df = pd.DataFrame(columns=expected_cols)
                if scale and popup_unit: 
                    df = convert_pixels_measurement_into_popup_units(df,scale,popup_unit)
                
            segmentedimg =newpath+'/'+ wfff['Name']+'_postprocessed'+'_'+str(int(round(time.time() * 1000)))+'.png'
            binarypath = newpath+'/'+ wfff['Name']+'_postprocessed_binary'+str(int(round(time.time() * 1000)))+'.png'
            diffimg = newpath+'/'+ wfff['Name']+'_difference_segmented'+str(int(round(time.time() * 1000)))+'.png'
            plt.imsave(diffimg, diff[2], cmap='gray')
            
            if(pltsave):
                plt.imsave(segmentedimg,img,cmap=plt.cm.gray)
                plt.imsave(binarypath,binary,cmap="gray")
                plt.close('all')
            else:
                imgg.save(segmentedimg)
                binaryimg.save(binarypath)
            
            img = binary
            af = np.sum(img)/np.size(img)
            temp = {"fid": fid, "filtername": wfff["Name"], 'filterd_image': segmentedimg, 
                    "black&white": binarypath, "previewchanges": diffimg, "area_fraction":af, 
                    "min_range": minrange, "maxrange": maxrange, "default_val":val, 
                    'region_properties': region_properties, 'boundary_excel':boundary_excel,"time":endtime}
            
            if wf_index == (mainwf_len-1):
                region_properties_csv_file = save_region_props_as_csv_for_image(temp['filterd_image'], df, popup_unit)
                temp['temp_region_properties_csv_file'] = region_properties_csv_file
                #binary save
                temp_numpy_file = region_properties_csv_file.replace('.csv','.npy')
                np.save(temp_numpy_file, binary)
                temp['temp_binary_img_ndarray'] = temp_numpy_file
                np.save(region_properties_csv_file.replace('.csv','.npy'),binary)
                if save_region_props:
                    temp['region_properties_csv_file'],annotation_data_df = update_main_region_props_file_for_image(region_properties_csv_file)
                    numpy_file_name = temp['region_properties_csv_file'].replace('.csv','.npy')
                    np.save(numpy_file_name, binary)
                    temp['binary_img_ndarray'] = numpy_file_name
                
            postprocessedlayer.append(temp)
            if visualization and visualization == 'Black/white (default)':
                segmentedimg = binarypath
       

        url  = environment.image_progress_socket

        h,w = img.shape[:2]
        data = {"cropimg": cropimg, "cropimg_shape":[h,w],
                "segmented_img":segmentedimg,"preprocessedlayers": preprocessedlayer,
                  "segmentationlayers": segprocessedlayer, 
                  "postprocessedlayers": postprocessedlayer, 
                  "user_id":user_id,'progressbar':int((count/len(mainwf))*100)}
        data_str = json.dumps(data)
            # Send data to the WebSocket server
        try:
            result = await send_data(data, url)
        except Exception as e:
            print("Exception occurred: ", e)
        # finally:
        #     ws.close()

        # if callreceived == 'segmentationapi': #or callreceived=='assigningworkflow':
        #     count = count+1
        #     x = requests.post(url, data=data)
        # else:
        #     pass
    
    if region_properties:
        # region_properties = {key: 0 if value == np.inf else value for key, value in region_properties.items()}
        sample_id, sample_name = os.path.split(newpath)
        parent_dir , sample_id = os.path.split(sample_id)
        metadata_dir = os.path.join(parent_dir, 'metadata')
        if metadata_dir:
            writePropsInMetadata(sample_id, sample_name, metadata_dir, region_properties)

    if annotation_data_df is not None:
        data['annotation_data_df'] = annotation_data_df
    # print("filter_to_applied_data:**************>",data)
    return data

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

def applyingPillar2wf(A, output_dir, image_name, junk_folder, pixel_size, popup_unit):
    
    scale = pixel_size
    if popup_unit == MICRONM: 
        scale = scale*1000
        popup_unit = 'nm'
    
    
    A = rgb2gray(A)
    A = gaussian(A,1)
    thresholds = threshold_multiotsu(A, 4)
    regions = np.digitize(A, bins=thresholds)
    S = regions==0
#     S = S[:,:,0]
#     S = remove_small_objects(S==1,100) #relate to image size
#     S = binary_dilation(S*1, disk(10)) #relate to image size
    S = remove_small_objects(S==1,int(S.shape[1]/12)) #relate to image size
    S = binary_dilation(S*1, disk(int(S.shape[1]/120))) #relate to image size
    c_magenta = [1,0,1]
    c_yellow = [1,1,0]
    
    if np.sum(S*1)/S.size > 0.6:
        stage_3 = True
        S = np.zeros_like(S)
    
    # M2 = label2rgb(S, A, colors=list([c_magenta]), alpha=0.7, bg_label=0, bg_color=None, image_alpha=1, kind='overlay')
    # plt.figure(figsize=(15,15))
    # plt.imshow(M2)
    
    D1 = np.ravel(A - S*1.1)
    D1 = np.sort(D1)
    D2 = np.where(D1>0)
    D1 = D1[D2[0][0]:]
    t2 = threshold_otsu(D1, nbins = 256)
    S2 = A>t2
    S2 = (S2-S*1)>0
    S2 = binary_opening(S2, disk(1))
    # S2 = binary_closing(S2, disk(1))
    S2 = remove_small_objects(S2,300)
    rings = S2
    S2 = remove_small_holes(S2,3000)
    holes = S2-rings*1
    holes = remove_small_objects(holes==1,300)
    holes = clear_border(holes)
    # S2 = binary_opening(S2, disk(8))
    
    M3 = mark_boundaries(A, S2, color=(1, 0, 1), outline_color=None, mode='thick', background_label=0)
    MH = mark_boundaries(A, holes, color=(1, 0, 1), outline_color=None, mode='thick', background_label=0)
    
    
    metrics = ('area', 'centroid', 'coords', 'eccentricity', 'equivalent_diameter', 'major_axis_length', 'minor_axis_length', 'solidity', 'perimeter')
    prop_h = pd.DataFrame(regionprops_table(label(S2), properties = metrics))
    prop_h['area dev'] = abs(prop_h['area']-prop_h['area'].median())
    area_th = prop_h['area'].std()*3
    
#     H1 = clean_by(S2*1, clear_img_border = False, solidity = 0.7) #c2c image
    
    Index_label = prop_h[(prop_h['solidity'] < 0.7)].index.tolist()
    H1 = S2*1
    if Index_label !=[]:
        for rem in Index_label:
            H1 = flood_fill(H1, (prop_h['coords'][rem][0][0], prop_h['coords'][rem][0][1]), 2)
    H1 = H1==2
    H1 = binary_closing(H1, disk(int(S.shape[1]/140))) #related to image size
    H1 = remove_small_holes(H1, 3000)
    S2 = (H1+S2)>0
    # plt.figure(figsize=(10,10))
    # plt.imshow(H1+S2)
    
    # check for aspect ratio to find connected holes
    noisy_lowcontrast = False
    if len(Index_label) > 15:
        noisy_lowcontrast = True
    
    
    if noisy_lowcontrast == True:
        B = shadowRemoval(A) # apply shadow removal
        BB = gaussian(B[0],1)
        thresholds = threshold_multiotsu(BB, 4)
        regions = np.digitize(BB, bins=thresholds)
    
        # get str. el. size
        metrics = ('area', 'centroid', 'coords', 'eccentricity', 'equivalent_diameter', 'major_axis_length', 'minor_axis_length', 'solidity', 'perimeter')
        reg = remove_small_objects(regions==0, 200)
        reg = binary_opening(reg, disk(4))
        prop_reg = pd.DataFrame(regionprops_table(label(reg), properties=metrics))
        se = int(prop_reg['equivalent_diameter'].mean()/5)
    
        S1 = regions==1
        S1 = remove_small_holes(S1,200)
        S1 = binary_opening(S1, disk(se-2)) #6
    
        props = pd.DataFrame(regionprops_table(label(S1), properties = metrics))
        props['area dev'] = abs(props['area']-props['area'].median())
        props['compactness'] = props['area']*4*np.pi/(props['perimeter']**2)
        area_th = props['area'].std()*1
        props['ellipticity'] = props['major_axis_length']/props['minor_axis_length']
        Index_label = props[(props['ellipticity'] > 1.4) | (props['compactness'] < 0.45)].index.tolist()
        S1 = S1*1
        if Index_label !=[]:
            for rem in Index_label:
                S1 = flood_fill(S1, (props['coords'][rem][0][0], props['coords'][rem][0][1]), 0)
    
        # #remove by area
        prop_temp = pd.DataFrame(regionprops_table(label(S1), properties = metrics))
        prop_temp['area dev'] = abs(prop_temp['area']-prop_temp['area'].median())
        area_th = prop_temp['area'].std()*1.5
    
        S1 = remove_small_objects(S1==1,area_th)
        S1 = clear_border(S1)
        S1 = binary_closing(S1, disk(se-1)) #5
    
        ### clean S by area
        prop_temp = pd.DataFrame(regionprops_table(label(S1), properties = metrics))
        prop_temp['area dev'] = abs(prop_temp['area']-prop_temp['area'].median())
        area_th = prop_temp['area'].std()*3
        Index_label = prop_temp[(prop_temp['area dev'] > area_th)].index.tolist()
        S1 = S1*1
        if Index_label !=[]:
            for rem in Index_label:
                S1 = flood_fill(S1, (prop_temp['coords'][rem][0][0], prop_temp['coords'][rem][0][1]), 0)
        ###
        c_magenta = [1,0,1]
        M2 = label2rgb(S1, A, colors=list([c_magenta]), alpha=0.7, bg_label=0, bg_color=None, image_alpha=1, kind='overlay')
        plt.figure(figsize=(15,15))
        plt.imshow(M2)
    
    
    # get ring outlines if image is noisy and low contrast
    if noisy_lowcontrast == True:
        tl = threshold_local(BB, block_size=(se*2+1))
        S3 = BB > tl
        R = binary_dilation(S1,disk(se+5))
        R = binary_closing(R,disk(se-2))
        R = R*S3-S1*1
        R = R>0
        R = binary_closing(R, disk(se-2))
    
        L1 = (R*1+S1*2)>1
        rings = (R*1-L1*1)>0
        holes = L1
        LL = rings*1+holes*2
        voids = (LL==0)*1
        voids = flood_fill(voids,(0,0),0)
        LL = LL+voids*1
    
        RR = clear_border(LL>0)
        RR = binary_opening(RR, disk(4))
        RR = remove_small_objects(RR==1, 50)
        S2 = RR
        SR2 = S1
        MSR2 = mark_boundaries(A, SR2, color=(1, 0, 1), outline_color=None, mode='thick', background_label=0)
        MM = mark_boundaries(MSR2, S2, color=(1, 1, 0), outline_color=None, mode='outer', background_label=0)
    else:
        # identify holes
        R1 = np.ravel(A*S2)
        R1 = np.sort(R1)
        R2 = np.where(R1>0)
        R1 = R1[R2[0][0]:]
        HR = np.histogram(R1, bins=256)
        Rt2 = threshold_otsu(R1, nbins = 256)
        SR2 = A<Rt2
        SR2 = SR2*S2
        SR2 = remove_small_holes(SR2, 200)
        SR2 = remove_small_objects(SR2, 500)
        MSR2 = mark_boundaries(A, SR2, color=(1, 0, 1), outline_color=None, mode='thick', background_label=0)
        MM = mark_boundaries(MSR2, S2, color=(1, 1, 0), outline_color=None, mode='outer', background_label=0)
    
    # image for analysis
    SC = clean_by(SR2, clear_img_border = True, aspect_hw = 1.75) #c2c image
    SC = clean_by(SC, clear_img_border = False, aspect_wh = 1.2) #c2c image
    SC = SC==1
    
    MM = mark_boundaries(MM, SC==2, color=(0, 1, 1), outline_color=None, mode='outer', background_label=0)
    
    c_magenta = [1,0,1]
    c_yellow = [1,1,0]
    M2 = label2rgb(S, A, colors=list([c_magenta]), alpha=0.7, bg_label=0, bg_color=None, image_alpha=1, kind='overlay')
        
    seg_path = junk_folder + '/'+image_name+ '_segmented.png'
    plt.imsave(seg_path, SC, cmap='gray')
    
    imgg = img_as_ubyte(A)
    imgg = gray2rgb(imgg)
    imgg = Image.fromarray(imgg)
    prepprocesspath = junk_folder + '/'+image_name+ '_preprocessed.png'
    imgg.save(prepprocesspath)  
    
    S2 = SC.tolist()
    if noisy_lowcontrast == False:
        se = 1
    
    return prepprocesspath, seg_path, se, S2

def batchpillarc2c(image_crop, output_dir, image_name, junk_folder, scale, popup_unit, draw_val, popup_val, orignalpath, userId, obj, scalebarextarction):
    
    error = False
    reference_image = fetchKeysValue('reference_image', obj)
    threshold_type = fetchKeysValue('threshold_type', obj)
    threshold_range = fetchKeysValue('threshold_range', obj)
    
    if reference_image == orignalpath:
        msg = 'image is the same as reference image. skipping analysis.'
        # sendProgressNotification(obj['progressurl'],obj['runId'],status=msg)
        
        data = {'cropimg': '', 'segmented_img': '', 'seg_overlay': '', 't_flip': '', 'pillar_type': 'pillar2', 'se': '', 'scale': scale, 'S2': '', 'reference_image': reference_image, 'threshold_type': threshold_type,'threshold_range': threshold_range, 'applying_ref': '', 'orignalpath': orignalpath}
        error = False
#         data = []
    else:    
        try:     
            prepprocesspath, seg_path, se, S2 = applyingPillar2wf(image_crop, output_dir, image_name, junk_folder, scale, popup_unit)
            data = {'cropimg': prepprocesspath, 'segmented_img': seg_path, 'seg_overlay': '', 't_flip': '', 'pillar_type': 'pillar2', 'se': se, 'scale': scale, 'S2': S2, 'reference_image': reference_image, 'threshold_type': threshold_type,'threshold_range': threshold_range, 'applying_ref': '', 'orignalpath': orignalpath}
            annotate, excel_path, annotated, analysis, pdf_path, objanalysis = getPillarAnalysisData(data, popup_unit, int(draw_val), int(popup_val), userId, 'pillarc2c', output_dir)
            
            extraannotated = [{ 'c2cx_plot': objanalysis['c2cx_plot']}, {'c2cy_plot': objanalysis['c2cy_plot']},{'C2Cx_C2Cy_plot': objanalysis['C2Cx_C2Cy_plot']}, {'annoatate_img': annotated}]
            extracsv = [{'c2cx_csv': objanalysis['c2cx_csv']}, {'c2cy_csv': objanalysis['c2cy_csv']}, {'gap_cdx_csv': objanalysis['gap_cdx_csv']}, {'gap_cdy_csv': objanalysis['gap_cdy_csv']}]
            data  = [{'analysis_type': 'pillar2', 'annotate_img': pdf_path, 'excel_path': excel_path, 'otherannotated': extraannotated, 'othercsvs': extracsv}]
            error = False
        except:
#             traceback.print_exc()
            error = True
            data = []    
    # notification_data = [{'ImageName': image_name, 'Analysis': 'Pillar C2C', 'Applicable': True, 'Failed': error, 'Scale bar': scalebarextarction}]
    notification_data = [{'ImageName': image_name, 'Analysis': 'Pillar C2C', 'Failed': error, 'Scale bar': scalebarextarction}]

    return data, notification_data

def applyingPillarcombinedWf(image_crop, output_dir, image_name, 
                             junk_folder, pixel_size, popup_unit):
    scale = pixel_size
    if popup_unit == MICRONM: 
        scale = scale*1000
        popup_unit = 'nm'
    
    c_magenta = [1,0,1]
    c_yellow = [1,1,0]
    BB = shadowRemoval(image_crop) # apply shadow removal
    B1 = BB[0]
    C = image_crop
    t = threshold_otsu(B1)
    S1 = B1 >= t
    ## check if pillar intensity flip
    ST = clear_border(S1)
    metrics = ('area', 'eccentricity', 'equivalent_diameter', 'solidity')
    props = regionprops_table(label(remove_small_objects(ST, 100)), properties = metrics)
    data_prem = pd.DataFrame(props)
    
    t_flip = False
    if len(data_prem.loc[data_prem['eccentricity']<0.7])<5:
        S1 = S1==0
        t_flip = True
    
    metrics = ('area', 'centroid', 'coords', 'eccentricity', 'equivalent_diameter', 'major_axis_length', 'minor_axis_length', 'solidity')
    props = regionprops_table(label(S1), properties = metrics)
    data_prem = pd.DataFrame(props)
    
    #keep pillars with 'holes' by closing
    if scale>1.8:
        m = 0.5
    else:
        m = 1
    
    #remove holes and unnecessary small objects
    S1 = remove_small_holes(S1,np.pi*((120/scale)**2)*m)
    S1 = remove_small_objects(S1,np.pi*((100/scale)**2)/8*m)
    
    
    SC = binary_closing(S1,disk(radius=int(scale*4*m)))
    SC = remove_small_holes(SC,np.pi*((140/scale)**2)*m)
    SC = binary_opening(SC,disk(radius=int(scale*4)*m))
    SC = remove_small_objects(SC,np.pi*((100/scale)**2)/8)
    SC = clear_border(SC)
    SC = SC*1
    propsc = pd.DataFrame(regionprops_table(label(SC), properties = metrics))
    Index_label = propsc[propsc['eccentricity'] > 0.7].index.tolist()
    for rem in Index_label:
        SC = flood_fill(SC, (propsc['coords'][rem][0][0], propsc['coords'][rem][0][1]), 0, connectivity =2 )
    
    #smooth seg results
    S1 = binary_opening(S1,disk(radius=int(scale*8)*m)) #7 all; #3
    S1 = clear_border(S1)
    
    #filter pillars by eccentricity
    S2 = S1
    props = regionprops_table(label(S1), properties = metrics)
    data = pd.DataFrame(props)
    
    ecc_label = data[data['eccentricity'] > 0.7].index.tolist()
    for rem in ecc_label:
        S2 = S2*1
        S2 = flood_fill(S2, (data['coords'][rem][0][0], data['coords'][rem][0][1]), 0)
    data.drop(ecc_label, inplace=True)
    data.reset_index(inplace=True, drop=True)
    
    #filter pillars by solidity
    sol_label = data[data['solidity'] < 0.9].index.tolist()
    for rem in sol_label:
        S2 = S2*1
        S2 = flood_fill(S2, (data['coords'][rem][0][0], data['coords'][rem][0][1]), 0)
    data.drop(sol_label, inplace=True)
    data.reset_index(inplace=True, drop=True)
    
    # if pillar intensity flip
    if t_flip==True:    
        E = feature.canny(B1, sigma=3)
        metrics = ('area', 'centroid', 'coords', 'eccentricity', 'equivalent_diameter', 'solidity')
        props = regionprops_table(label(E), properties = metrics)
        data_prem = pd.DataFrame(props)
    
        Index_label = data_prem[data_prem['eccentricity'] > 0.7].index.tolist()
        E1 = E
        E1 = E1*1
        for rem in Index_label:
            E1 = flood_fill(E1, (data_prem['coords'][rem][0][0], data_prem['coords'][rem][0][1]), 0, connectivity =2 )
    
        data_prem.drop(Index_label, inplace=True)
        data_prem.reset_index(inplace=True, drop=True)
    
        E1 = clear_border(E1)
        E1 = remove_small_holes(E1,np.pi*((140/scale)**2))
        E1 = remove_small_objects(E1,np.pi*((100/scale)**2)/6)
        
        #combine the edge and threshold results
        props_E = regionprops_table(label(E1), properties = metrics)
        d_ave = np.mean(props_E['equivalent_diameter'])
    
    #     SE = S2+E1*1
    #     SE1 = binary_opening(SE==1, disk(int(d_ave/3)))
        SE1 = binary_opening(S2, disk(int(d_ave/4)))
        SE = SE1+E1
    #     SE = SE==2
    #     SE = SE+SE1
    
        ME = label2rgb(SE, C, colors=list([c_magenta]), alpha=0.3, bg_label=0, bg_color=None, image_alpha=1, kind='overlay')
        S2 = SE
        
        
    if t_flip == False:
        SC2 = S2
        # check if any incomplete pillars still remain and can be filled
        data = pd.DataFrame(regionprops_table(label(SC2), properties = metrics))
        data['area dev'] = abs(data['area']-data['area'].median())
        area_th = data['area'].std()*3
        Index_label = data[(data['eccentricity'] > 0.4) & (data['area dev']>area_th)].index.tolist()
        if Index_label !=[]:
            SC = SC*1
            ZC = np.zeros_like(S1)
            for rem in Index_label:
                FC = flood(SC, (data['coords'][rem][0][0], data['coords'][rem][0][1]))
                ZC = ZC + FC
            SC2 = SC2 + ZC    
            SC2 = SC2>0
        else:
            print('incomplete pillars not found')
    
        if np.sum(SC2*1)>len(np.ravel(SC2))*0.5:
        #     raise ValueError('Incomplete pillar segmentation.')
            propsc = pd.DataFrame(regionprops_table(label(S2), properties = metrics))
            propsc['ell'] = propsc['major_axis_length']/propsc['minor_axis_length']
            Index_label = propsc[propsc['ell'] > 1.15].index.tolist()
            for rem in Index_label:
                S2 = flood_fill(S2, (propsc['coords'][rem][0][0], propsc['coords'][rem][0][1]), 0, connectivity =2 )
        else:
            S2 = SC2
            propsc = pd.DataFrame(regionprops_table(label(S2), properties = metrics))
            propsc['ell'] = propsc['major_axis_length']/propsc['minor_axis_length']
            Index_label = propsc[propsc['eccentricity'] > 0.7].index.tolist()
            for rem in Index_label:
                S2 = flood_fill(S2, (propsc['coords'][rem][0][0], propsc['coords'][rem][0][1]), 0, connectivity =2 )


            
    
    seg_overlay = output_dir + image_name +'_seg_overlay.png'
    
    fig, ax = plt.subplots(figsize=(10, 6))
    c_magenta = [1,0,1]
    M2 = label2rgb(S2, C, colors=list([c_magenta]), alpha=0.3, bg_label=0, bg_color=None, image_alpha=1, kind='overlay')
    ax.imshow(M2,cmap='gray')
    ax.axis('off')
    fig.savefig(seg_overlay, dpi=100, bbox_inches='tight', pad_inches=0) # save image as 
    
    imgg = img_as_ubyte(B1)
    imgg = gray2rgb(imgg)
    imgg = Image.fromarray(imgg)
    prepprocesspath = junk_folder + '/'+image_name+ '_preprocessed.png'
    imgg.save(prepprocesspath)  
    
    
    seg_path = junk_folder + '/'+image_name+ '_segmented.png'
    plt.imsave(seg_path, S2, cmap='gray')
    
    return prepprocesspath, seg_path, seg_overlay, t_flip

def plotAnnotatedImage(S, data, annotateimg, typ, d_ave, thet, pillar_type, A):
    len_mod = 1.5
    len_mod_ax = len_mod*0.8
    figg, axx = plt.subplots(figsize=(10,10))
    c_magenta = [1,0,1]
    if pillar_type == 'pillar2':
        #M2 = label2rgb(S, A, colors=list([c_magenta]), alpha=0.7, bg_label=0, bg_color=None, image_alpha=1, kind='overlay')
        axx.imshow(A, cmap='gray')
        fontsize = 'small'
        color = 'y'
        directionlooprange = 2
        width = 4
        alpha = 1
        fontsize2 = 'xx-large'
        color2 = 'w'
    else:
        axx.imshow(S, cmap='gray')
        fontsize = 'large'
        color = 'm'
        directionlooprange = 3
        width = 3
        alpha = 0.7
        fontsize2 = 'xx-large'
        color2 = 'c'
    for obj in range(len(data)):
        axx.text(data['centroid-1'][obj], data['centroid-0'][obj], str(data['Object'][obj]), horizontalalignment='center', verticalalignment='center', color = color, fontsize=fontsize, fontweight='bold')

    # SAVE ANNOTATED IMAGE
    box_props = dict(boxstyle='round', facecolor='wheat', alpha=1)
    for direction in range(directionlooprange):
        xd1 = int(np.round(np.cos(thet[direction])*d_ave))
        yd1 = int(np.round(np.sin(thet[direction])*d_ave))
        axx.arrow(S.shape[1]/2, S.shape[0]/2, xd1, yd1, width = width, color = 'c', alpha = alpha)
        axx.text(S.shape[1]/2+xd1, S.shape[0]/2+yd1, str(direction+1), horizontalalignment='left', verticalalignment='bottom', color = color2, fontsize=fontsize2, fontweight='bold')
         
    axx.axis('off')       
    figg.savefig(annotateimg, dpi=100, bbox_inches='tight', pad_inches=0) # save image as ""<img_name>_annotated"
    plt.close(figg)


def calculateDataforAnalysis(obj):
    img_path = obj['image_path']
    sampleimg = obj['sample_image']
    S = rgbToGray(io.imread(img_path))
    G = rgbToGray(io.imread(sampleimg))
    output_dir = fetchKeysValue('output_dir', obj)
    if output_dir:
        callfrom = 'backgroundbatch'
    else:
        callfrom = 'normalcall'
        
    pillar_analysis = obj['pillar_analysis']
    popup_unit = obj['popup_unit']
    draw_val = obj['draw_val']
    popup_val = int(obj['popup_val'])    
    scale = fetchKeysValue('scale', obj)
    orignalpath = fetchKeysValue('orignalpath', obj)
    if not scale:
        scale = (popup_val/ draw_val) #*unitval
        mu_encode = b'\xce\xbcm'
        units = mu_encode.decode(encoding='UTF-8')
        if popup_unit == units: 
            scale = scale*1000
            popup_unit = 'nm'
        
    t_flip = fetchKeysValue('t_flip', obj)
    pillar_type = fetchKeysValue('pillar_type', obj)
    if not pillar_type:
        pillar_type = 'pillar1'
        
    metrics = ('area', 'centroid', 'bbox', 'coords', 'eccentricity', 'equivalent_diameter', 'major_axis_length', 'minor_axis_length', 'solidity')
    
    if pillar_type == 'pillar2': 
        props = regionprops_table(label(S==1), properties = metrics)
    else: 
        props = regionprops_table(label(S), properties = metrics)
    
    data = pd.DataFrame(props)
    data['centroid-0-float'] = data['centroid-0']
    data['centroid-1-float'] = data['centroid-1']
    data['centroid-0'] = data['centroid-0'].astype(int)
    data['centroid-1'] = data['centroid-1'].astype(int)
    data['CD_'+popup_unit] = data['equivalent_diameter']*scale
    # data['flattening'] = (data['major_axis_length']-data['minor_axis_length'])/data['major_axis_length']
    data['flattening'] = data['major_axis_length']/data['minor_axis_length']
    data['centroid-0-round'] = np.round(data['centroid-0'])
    data['centroid-1-round'] = np.round(data['centroid-1'])
    if pillar_type == 'pillar2':
        data.sort_values(['centroid-1', 'centroid-0'], ascending = [True, False], ignore_index = True, inplace = True)

    data['Object'] = range(1, len(data) + 1)
    d_ave = np.mean(data['equivalent_diameter'])*1
        
    
    mult_clusters = False
    S2 = S
    if t_flip:
        ZZ = np.zeros_like(S2)
    #     D1 = binary_dilation(S2,disk(radius=(100/scale/4)))
        D1 = ndimage.binary_dilation(S2, disk(int(100/scale/4)))
        D1 = D1*1
        if len(np.unique(label(D1)))>2:
            props_d1 = pd.DataFrame(regionprops_table(label(D1), properties = ('area', 'centroid', 'coords')))
            props_d1.sort_values(by=['area'], ascending=False)
            D1 = flood(D1,(props_d1['coords'][0][0][0],props_d1['coords'][0][0][1]))
            DS2 = D1*S2
            mult_clusters = True
    
    
    # determine dominant directions
    if mult_clusters == True:
        props_ds2 = pd.DataFrame(regionprops_table(label(DS2), properties = ('area', 'centroid', 'coords')))
        yc  = props_ds2[['centroid-0']].to_numpy()
        xc  = props_ds2[['centroid-1']].to_numpy()
    else:
        yc  = data[['centroid-0']].to_numpy()
        xc  = data[['centroid-1']].to_numpy()
    
    ddd = cdist(xc,yc)
    ddd = ddd[np.triu_indices(ddd.shape[0], k = 2)]
    dil2 = int((np.median(ddd)-d_ave)/2)
    
    if d_ave>200:
        dil = int(d_ave/10*1.75)
    else:
        dil = dil2
        if dil >=50:
            dil = int(d_ave/10*1.75)
    #         dil = int(dil/3)
        elif dil >100:
            dil = int(dil/10)
    
#     if dil > 20:
#         dil = 12
#         print('dil modified', dil)   
        
    dy = cdist(yc,yc, lambda u, v: (u-v))
    dx = cdist(xc,xc, lambda u, v: (u-v))
    dx = dx[np.triu_indices(dx.shape[0], k = 1)]+1e-9
    dy = dy[np.triu_indices(dy.shape[0], k = 1)]
    td = np.arctan(dy/dx) #need to substitute zeros with nan
    td = td[~np.isnan(td)]
    
    (n, binedges) = np.histogram(td, bins=np.arange(np.radians(-92.5), np.radians(93), np.radians(5)))
    bincenters = np.mean(np.vstack([binedges[0:-1],binedges[1:]]), axis=0)
    counts = np.column_stack((n,bincenters))
    counts[0,0] = counts[0,0] + counts[-1,0]
    counts_order = counts[np.argsort(counts[:, 0])]
    counts_order = counts_order[::-1][:counts_order.shape[0]]
    thet = counts_order[:,1]
    
    co = pd.DataFrame(counts_order)
    co.columns = ['counts', 'radians']
    co['degrees'] = np.degrees(co['radians'])

    inds = [0]
    for jj in range(2):
        if jj==0:
            co['diff'+str(jj)] = np.degrees(abs(co['radians'][inds[jj]:]-co['radians'][inds[jj]]))
            x = co[(co['diff'+str(jj)] > 35)].index.tolist()
        else:
            co['diff'+str(jj)] = np.degrees(abs(co['radians'][inds[jj]:]-co['radians'][inds[jj]]))
            x = co[(co['diff'+str(jj)] > 35) & (co['diff'+str(jj-1)] > 35)].index.tolist()
        inds.append(x[0])
    thet = thet[inds]
    
    if pillar_type == 'pillar2':
        pair_radius = (d_ave+dil)*1.75
    else:
        pair_radius = d_ave+dil
      
    x1 = int(np.round(np.cos(thet[0])*pair_radius))
    x0 = int(np.round(np.sin(thet[0])*pair_radius))
    y1 = int(np.round(np.cos(thet[1])*pair_radius))
    y0 = int(np.round(np.sin(thet[1])*pair_radius))
    z1 = int(np.round(np.cos(thet[2])*pair_radius))
    z0 = int(np.round(np.sin(thet[2])*pair_radius))
    
    Z = np.zeros_like(G)
    data['centroid-0-round'] = data['centroid-0-round'].astype(int)
    data['centroid-1-round'] = data['centroid-1-round'].astype(int)
    Z[data['centroid-0-round'],data['centroid-1-round']]=1
    
    data['c0-x'] = data['centroid-0'] + x0
    data['c1-x'] = data['centroid-1'] + x1
    data['c0-y'] = data['centroid-0'] + y0
    data['c1-y'] = data['centroid-1'] + y1
    data['c0-z'] = data['centroid-0'] + z0
    data['c1-z'] = data['centroid-1'] + z1
    
    
    addit = {'x0': x0, 'x1': x1, 'y0': y0, 'y1': y1, 'z0': z0, 
             'z1': z1, 'd_ave': d_ave, 'xc':xc.tolist(), 'yc':yc.tolist(), 'dil': dil}
   
    if pillar_analysis:
        data_key = 'data'
        annotated_key = 'annotate_img'
        
        p, _ = os.path.split(img_path)
        annotateimg = p + '/annotate'+'_'+str(int(round(time.time() * 1000)))+'.png' 
        plotAnnotatedImage(S, data, annotateimg, 'pillar', d_ave, thet, pillar_type, G)
        
        foldername, _ = os.path.split(annotateimg)
        basefoldername = os.path.split(os.path.dirname(annotateimg))[0]
        
        
        if callfrom == 'backgroundbatch':
            output_dir = obj['output_dir']
            batchdir = output_dir
        else:
            output_dir = ''
            batchdir = basefoldername + '/batchprocessed/'
            batchdir = checkEnv(batchdir)
            if not os.path.exists(batchdir):
                os.mkdir(batchdir)
    
        
        foldername = os.path.basename(foldername)
        
        newbatchpath = batchdir + foldername + '_pillar_annoated.png'
        if callfrom == 'backgroundbatch' and output_dir:
            shutil.copyfile(annotateimg, newbatchpath)
            newbatchpath = output_dir + foldername + '_pillar_annoated.png'
            shutil.copyfile(annotateimg, newbatchpath)
        else:
            shutil.copyfile(annotateimg, newbatchpath)
    
    else:
                   
        count = 1
        data_key = 'profile_data'
        annotated_key = 'profile_annotated'
        annotateimg = ''
        
    # db = establishConnection()
    collection = db.intialanalysisdata
    path, fname = os.path.split(sampleimg)
    fulldata = {'sample':path, data_key: data.to_json(), 
                'additional_data': addit, annotated_key: annotateimg}
    report = collection.find_one(
                        {'sample': path})
    if report:
        
        result = collection.update_one( 
        {"sample":path}, 
        { "$set":{              
         data_key:data.to_json(),
         annotated_key: annotateimg,
          "additional_data": addit
          
                }   } )
    else:
        
        rec_id2 = collection.insert_one( fulldata )
    
    res = {'data': 'Done', 'annotate_img': annotateimg}
    
    return res

def XDirectionPilAnalysis(data, x0, x1, S, scale, popup_unit, dil, pillar_type, scalebar):
    #scale = 100/(67-1)
    data_x = data.copy()
    data_x['c0-x'] = data_x['centroid-0'] - x0
    data_x['c1-x'] = data_x['centroid-1'] - x1
    data_x.drop(data_x[data_x['c0-x'] >= S.shape[0]].index, inplace = True) 
    data_x.drop(data_x[data_x['c1-x'] >= S.shape[1]].index, inplace = True) 
    data_x.drop(data_x[data_x['c0-x'] < 0].index, inplace = True) 
    data_x.drop(data_x[data_x['c1-x'] < 0].index, inplace = True)
    data_x.index = range(len(data_x))
    
    metrics_p = ('area', 'centroid')
    pairs_x = np.empty(S.shape)
    dist_x = []
    pitch_x = []
    obj_pairs = []
    S = S*1
    for circle in range(len(data_x)):
        c_orig = flood(S, (data_x['centroid-0'][circle], data_x['centroid-1'][circle]))
        cx = flood(S, (data_x['c0-x'][circle], data_x['c1-x'][circle]))
        pairs = c_orig+cx
        c_labels = label(pairs, background=None, return_num=True)
        if c_labels[1]==2:
    #         pairs_x = np.dstack((pairs_x, pairs))
    
            pair_rp = regionprops_table(label(pairs),properties = metrics_p)
            temp = []
            for obj in range(len(pair_rp['centroid-0'])):
                rr = data.loc[(data['centroid-0'] == int(pair_rp['centroid-0'][obj])) & (data['centroid-1'] == int(pair_rp['centroid-1'][obj]))]['Object']
                temp.append(rr[:])
            temp1 = list(chain.from_iterable(temp))
            obj_pairs.append(temp1)
            
            if pillar_type == 'pillar2':
                dist = np.linalg.norm(np.array((pair_rp['centroid-0'][0], pair_rp['centroid-1'][0])) - np.array((pair_rp['centroid-0'][1], pair_rp['centroid-1'][1])))
                dist_x.append(dist)
            else:
                g = find_boundaries(pairs, connectivity=2, mode = 'inner')
                pairs_x_rp = regionprops(label(g))
                d = cdist(pairs_x_rp[0].coords,pairs_x_rp[1].coords)
                dist_x.append(np.min(d))
                
                pairs_xmod = binary_closing(g, disk(dil), out=None)
                b = find_boundaries(pairs_xmod, connectivity=2, mode = 'inner')
                pairs_xmod_rp = regionprops(label(b))
                p = cdist(pairs_xmod_rp[0].coords,pairs_xmod_rp[0].coords)
                pitch_x.append(np.max(p))
        else:
            pass
    
    if pillar_type == 'pillar2':
        if scalebar == True:
            dist_x_sc = np.asarray(dist_x)*scale
            xdir = pd.DataFrame(list(zip(obj_pairs, dist_x_sc)), columns = ['Pillar pairs', 'C2Cx ('+popup_unit+')'])
        else:
            xdir = pd.DataFrame(list(zip(obj_pairs, dist_x)), columns = ['Pillar pairs', 'C2Cx (px)'])
        namedf = 'c2cx'
    else:      
        dist_x_sc = np.asarray(dist_x)*scale
        pitch_x_sc = np.asarray(pitch_x)*scale
        xdir = pd.DataFrame(list(zip(obj_pairs, dist_x_sc, pitch_x_sc)), columns = ['Pillar pairs', 'D1 distance ('+popup_unit+')', 'D1 pitch ('+popup_unit+')'])
        namedf = 'D1_dir'
        
    dc = 'Pillar pairs'
    return xdir, dc, namedf

def gapCDAnalysis(BB, output_dir, foldername, popup_unit, se, S, additional_data, scalebar, scale, xcheck, ycheck, S2, data):
    
    S2 = np.array(S2)
    A = BB
    yc = np.array(additional_data['yc'])
    xc = np.array(additional_data['xc'])
    d_ave = additional_data['d_ave']
    dil = additional_data['dil']

    RR = S2*1
    
    metrics = ('area', 'centroid', 'bbox', 'coords', 'eccentricity', 'equivalent_diameter', 'major_axis_length', 'minor_axis_length', 'solidity')
    data_g = pd.DataFrame(regionprops_table(label(RR), properties = metrics))
    
    dist_x1 = []
    for circle in range(len(xcheck)):
        pair1 = xcheck['xpair'][circle][0]-1
        pair2 = xcheck['xpair'][circle][1]-1
        c_orig = flood(RR, (int(data['centroid-0'][pair1]), int(data['centroid-1'][pair1])))
        cx = flood(RR, (int(data['centroid-0'][pair2]), int(data['centroid-1'][pair2])))
        pairs = c_orig+cx
        c_labels = label(pairs, background=None, return_num=True)
        if c_labels[1]==2:
            g = find_boundaries(pairs, connectivity=2, mode = 'inner')
            pairs_x_rp = regionprops(label(g))
            d = cdist(pairs_x_rp[0].coords,pairs_x_rp[1].coords)
            dist_x1.append(np.min(d))
        else:
            dist_x1.append(0)
    
    dist_y1 = []
    for circle in range(len(ycheck)):
        pair1 = ycheck['ypair'][circle][0]-1
        pair2 = ycheck['ypair'][circle][1]-1
        c_orig = flood(RR, (int(data['centroid-0'][pair1]), int(data['centroid-1'][pair1])))
        cy = flood(RR, (int(data['centroid-0'][pair2]), int(data['centroid-1'][pair2])))
        pairs = c_orig+cy
        c_labels = label(pairs, background=None, return_num=True)
        if c_labels[1]==2:
            g = find_boundaries(pairs, connectivity=2, mode = 'inner')
            pairs_y_rp = regionprops(label(g))
            d = cdist(pairs_y_rp[0].coords,pairs_y_rp[1].coords)
            dist_y1.append(np.min(d))
        else:
            dist_y1.append(0)
    
            
    xcheck['Gap CDx'] = dist_x1 
    ycheck['Gap CDy'] = dist_y1 
    
    if scalebar == True:
        xcheck['Gap CDx scale'] = abs(xcheck['Gap CDx']*scale)
        gap_x = xcheck[['xpair', 'Gap CDx scale']].copy()
        gap_x.columns = ['Pillar pair', 'Gap CDx ('+popup_unit+')']
        
        ycheck['Gap CDy scale'] = abs(ycheck['Gap CDy']*scale)
        gap_y = ycheck[['ypair', 'Gap CDy scale']].copy()
        gap_y.columns = ['Pillar pair', 'Gap CDy ('+popup_unit+')']
    else:
        gap_x = xcheck[['xpair', 'Gap CDx']].copy()
        gap_x.columns = ['Pillar pair', 'Gap CDx (px)']
        gap_y = ycheck[['ypair', 'Gap CDy']].copy()
        gap_y.columns = ['Pillar pair', 'Gap CDy (px)']
    
    # EXPORT CSV
    gapx = output_dir + foldername+'_gap_cdx.csv'
    gap_x.to_csv(gapx, index=False)
    
    gapy = output_dir + foldername+'_gap_cdy.csv'
    gap_y.to_csv(gapy, index=False)
    
    
#     Gap CD Diagnostic image - include but do not save
#     figg, axx = plt.subplots(figsize=(10,10))
#     axx.imshow(A, cmap='gray')
#     for obj in range(len(xcheck)):
#         axx.arrow(xcheck['x'][obj], xcheck['y'][obj], xcheck['Gap CDx'][obj], 0.1, width = 2, color = 'c', alpha = 1, head_width = 0, head_length = 0)

#     for obj in range(len(ycheck)):
#         axx.arrow(ycheck['x'][obj], ycheck['y'][obj], 0.1, ycheck['Gap CDy'][obj], width = 2, color = 'm', alpha = 1, head_width = 0, head_length = 0)

#     annotateimg = output_dir + foldername+'_annotated_Gap_CD.png'
#     axx.axis('off')       
#     figg.savefig(annotateimg, dpi=100, bbox_inches='tight', pad_inches=0) # save image as ""<img_name>_annotated"
#     plt.close(figg)


    return gapx, gapy

def center2CenterCalculation(yc, xc, d_ave, dil, data, scale, popup_unit, output_dir, foldername, scalebar, G):
    
    
    yc = np.array(yc)
    xc = np.array(xc)

    dy = cdist(yc,yc, lambda u, v: (u-v))
    dx = cdist(xc,xc, lambda u, v: (u-v))
    td = np.arctan(dy/dx) #need to substitute zeros with nan
    srad = (d_ave+dil)
    yd = pd.DataFrame(dy)
    xd = pd.DataFrame(dx)
    
    set_y = []
    set_x = []
    xcoords = []
    ycoords = []
    for ob in range(len(data)):
        pillar_number = ob+1
        Index_yy = []
        Index_xx = []
        Index_xy = []
        Index_yx = []
    
        # ydir 
        Index_yy = yd[(yd[ob] < srad*2.5) & (yd[ob] > srad)].index.tolist()
        Index_yx = xd[(abs(xd[ob]) < d_ave)].index.tolist()
        set_yy = set(Index_yy).intersection(Index_yx)
        if len(set_yy) == 1:
            #add 1 to ob for pillar number
            ypair = list((ob, list(set_yy)[0]))
            ypair_pillar_number = list((pillar_number, list(set_yy)[0]+1))
            set_y.append(ypair)
            coords1y = []
            y_centr = data['centroid-0-float'][ypair[0]]
            x_centr = data['centroid-1-float'][ypair[0]]
            y_dist = data['centroid-0-float'][ypair[1]]-y_centr
            x_dist = data['centroid-1-float'][ypair[1]]-x_centr
            coords1y = list((ypair_pillar_number, y_centr, x_centr, y_dist, x_dist))
            ycoords.append(coords1y)
        
        # xdir
        Index_xx = xd[(xd[ob] < srad*2.5) & (xd[ob] > srad)].index.tolist()
        Index_xy = yd[(abs(yd[ob]) < d_ave)].index.tolist()
        set_xx = set(Index_xx).intersection(Index_xy)
        if len(set_xx) == 1:
            #add 1 to ob for pillar number
            xpair = list((ob, list(set_xx)[0]))
            xpair_pillar_number = list((pillar_number, list(set_xx)[0]+1))
            set_x.append(xpair)
            coords1x = []
            y_centr = data['centroid-0-float'][xpair[0]]
            x_centr = data['centroid-1-float'][xpair[0]]
            y_dist = data['centroid-0-float'][xpair[1]]-y_centr
            x_dist = data['centroid-1-float'][xpair[1]]-x_centr
            coords1x = list((xpair_pillar_number, y_centr, x_centr, y_dist, x_dist))
            xcoords.append(coords1x)
    
    xcheck = pd.DataFrame(list(xcoords))
    ycheck = pd.DataFrame(list(ycoords))
    xcheck.columns =['xpair', 'y', 'x', 'dy', 'dx']
    ycheck.columns =['ypair', 'y', 'x', 'dy', 'dx']
    
    if scalebar == True:
        #xcheck['dy scale'] = abs(xcheck['dy']*scale)
        xcheck['dx scale'] = abs(xcheck['dx']*scale)
        xdir = xcheck[['xpair', 'dx scale']].copy()
        xdir.columns = ['Pillar pair', 'C2Cx ('+popup_unit+')']
        
        #ycheck['dx scale'] = abs(ycheck['dx']*scale)
        ycheck['dy scale'] = abs(ycheck['dy']*scale)
        ydir = ycheck[['ypair', 'dy scale']].copy()
        ydir.columns = ['Pillar pair', 'C2Cy ('+popup_unit+')']
    else:
        xdir = xcheck[['xpair', 'dx']].copy()
        xdir.columns = ['Pillar pair', 'C2Cx (px)']
        ydir = ycheck[['ypair', 'dy']].copy()
        ydir.columns = ['Pillar pair', 'C2Cy (px)']
    
    # EXPORT CSV
    xcsv = output_dir + foldername + '_c2cx.csv' 
    xdir.to_csv(xcsv, index=False)  
    ycsv = output_dir + foldername + '_c2cy.csv' 
    ydir.to_csv(ycsv, index=False)
    
    #diagonostic image
    figg, axx = plt.subplots(figsize=(10,10))
    axx.imshow(G, cmap='gray')
    for obj in range(len(xcheck)):
        axx.arrow(xcheck['x'][obj], xcheck['y'][obj], xcheck['dx'][obj], xcheck['dy'][obj], width = 2, color = 'c', alpha = 1, head_width = 0, head_length = 0)

    for obj in range(len(ycheck)):
        axx.arrow(ycheck['x'][obj], ycheck['y'][obj], ycheck['dx'][obj], ycheck['dy'][obj], width = 2, color = 'm', alpha = 1, head_width = 0, head_length = 0)

    annotateimg = output_dir + foldername+'_annotated_C2Cxy.png'
    axx.axis('off')       
    figg.savefig(annotateimg, dpi=100, bbox_inches='tight', pad_inches=0) # save image as ""<img_name>_annotated"
    plt.close(figg)
    
    return xdir, ydir, xcheck, ycheck, annotateimg, xcsv, ycsv


def center2CenterPlotsref(xdir, ydir, output_dir, foldername, popup_unit, thresh_type, thresh_range, xc):
    # checks
    reference_img_valid = True
    reference_img_current = True
    
    # API inputs
#    thresh_range = 3
#    thresh_type = 'std'
#    thresh_type = 'nm'
    
    imgname = foldername
    if reference_img_valid == True and reference_img_current == True:
    
        # reference image measurements
        xdir.to_pickle(output_dir + imgname +"_c2cx.pkl") #point to output directory
        ydir.to_pickle(output_dir + imgname +"_c2cy.pkl") #point to output directory
        
        # current image
        probx, px = stats.probplot(xdir['C2Cx ('+popup_unit+')'], dist="norm")
        proby, py = stats.probplot(ydir['C2Cy ('+popup_unit+')'], dist="norm")
        datx = probx
        daty = proby
        
        xdir_median = xdir['C2Cx ('+popup_unit+')'].median()
        xdir_mean = xdir['C2Cx ('+popup_unit+')'].mean()
        xdir_std = xdir['C2Cx ('+popup_unit+')'].std()
    
        ydir_median = ydir['C2Cy ('+popup_unit+')'].median()
        ydir_mean = ydir['C2Cy ('+popup_unit+')'].mean()
        ydir_std = ydir['C2Cy ('+popup_unit+')'].std()
        
        #PLOTS
        # SAVE PLOT <image_name> + _C2Cx_plot.png
        # plot 1
        fig, ax = plt.subplots(figsize=(8,8))
        ax.plot(datx[1],datx[0], '.')
        ax.axvline(x=xdir_mean, label='C2Cx mean'.format(xc), c='b', alpha=0.2)
        if thresh_type == 'std':
            #ax.fill_between([xdir_mean - xdir_std*thresh_range, xdir_mean + xdir_std*thresh_range], -4, 4, color='blue', alpha=0.1, transform=ax.get_xaxis_transform())
            ax.legend(['C2Cx', 'C2Cx mean ('+str(np.round(xdir_mean,2))+')'], loc='lower right', framealpha = 1)
        elif thresh_type == 'nm':
            #ax.fill_between([xdir_mean - thresh_range, xdir_mean + thresh_range], -4, 4, color='blue', alpha=0.1, transform=ax.get_xaxis_transform())
            ax.legend(['C2Cx', 'C2Cx mean ('+str(np.round(xdir_mean,2))+')'], loc='lower right', framealpha = 1)
    
        ax.set_title('C2Cx')
        ax.set_ylabel('Theoretical quantiles')
        ax.set_xlabel('Center to Center (C2C) distance ('+popup_unit+')')
        ax.set_ylim([-3.5, 3.5])
        ax.set_xlim([26, 54])
        fig.savefig(output_dir + imgname+'_C2Cx_plot'+'.png', dpi=100, pad_inches=0.2) 
    
    
        # SAVE PLOT <image_name> + _C2Cy_plot.png
        # plot 2
        fig1, ax = plt.subplots(figsize=(8,8))
        ax.plot(daty[1],daty[0], '.r')
        ax.axvline(x=ydir_mean, label='C2Cy mean'.format(xc), c='r', alpha=0.2)
        if thresh_type == 'std':
            #ax.fill_between([ydir_mean - ydir_std*thresh_range, ydir_mean + ydir_std*thresh_range], -4, 4, color='red', alpha=0.1, transform=ax.get_xaxis_transform())
            ax.legend(['C2Cy', 'C2Cy mean ('+str(np.round(ydir_mean,2))+')'], loc='lower right', framealpha = 1)
        elif thresh_type == 'nm':
            #ax.fill_between([ydir_mean - thresh_range, ydir_mean + thresh_range], -4, 4, color='red', alpha=0.1, transform=ax.get_xaxis_transform())
            ax.legend(['C2Cy', 'C2Cy mean ('+str(np.round(ydir_mean,2))+')'], loc='lower right', framealpha = 1)
    
        ax.set_title('C2Cy')
        ax.set_ylabel('Theoretical quantiles')
        ax.set_xlabel('Center to Center (C2C) distance ('+popup_unit+')')
        ax.set_ylim([-3.5, 3.5])
        ax.set_xlim([26, 54])
        fig1.savefig(output_dir + imgname+'_C2Cy_plot'+'.png', dpi=100, pad_inches=0.2) 
    
    
        # SAVE PLOT <image_name> + _C2Cx_C2Cy_plot.png
        # plot 3
        fig2, ax = plt.subplots(figsize=(8,8))
        ax.plot(datx[1],datx[0], '.')
        ax.plot(daty[1],daty[0], '.r')
        ax.axvline(x=xdir_mean, label='C2Cx mean'.format(xc), c='b', alpha=0.2)
        ax.axvline(x=ydir_mean, label='C2Cy mean'.format(xc), c='r', alpha=0.2)
        if thresh_type == 'std':
            #ax.fill_between([xdir_mean - xdir_std*thresh_range, xdir_mean + xdir_std*thresh_range], -4, 4, color='blue', alpha=0.1, transform=ax.get_xaxis_transform())
            #ax.fill_between([ydir_mean - ydir_std*thresh_range, ydir_mean + ydir_std*thresh_range], -4, 4, color='red', alpha=0.1, transform=ax.get_xaxis_transform())
            ax.legend(['C2Cx', 'C2Cy', 'C2Cx mean ('+str(np.round(xdir_mean,2))+')', 'C2Cy mean ('+str(np.round(ydir_mean,2))+')' ], loc='lower right', framealpha = 1)
        elif thresh_type == 'nm':
            #ax.fill_between([xdir_mean - thresh_range, xdir_mean + thresh_range], -4, 4, color='blue', alpha=0.1, transform=ax.get_xaxis_transform())
            #ax.fill_between([ydir_mean - thresh_range, ydir_mean + thresh_range], -4, 4, color='red', alpha=0.1, transform=ax.get_xaxis_transform())
            ax.legend(['C2Cx', 'C2Cy', 'C2Cx mean ('+str(np.round(xdir_mean,2))+')', 'C2Cy mean ('+str(np.round(ydir_mean,2))+')'], loc='lower right', framealpha = 1)
    
        ax.set_title('C2Cx and C2Cy')
        ax.set_ylabel('Theoretical quantiles')
        ax.set_xlabel('Center to Center (C2C) distance ('+popup_unit+')')
        ax.set_ylim([-3.5, 3.5])
        ax.set_xlim([26, 54])
        fig2.savefig(output_dir + imgname+'_C2Cx_C2Cy_plot'+'.png', dpi=100, pad_inches=0.2) 
        
        plot1 = output_dir + imgname+'_C2Cx_plot'+'.png'
        plot2 = output_dir + imgname+'_C2Cy_plot'+'.png'
        plot3 = output_dir + imgname+'_C2Cx_C2Cy_plot'+'.png'
        
        return plot1, plot2, plot3


def center2CenterPlotsRefValidation(xdir, ydir, output_dir, imgname, popup_unit, reference_image, thresh_type, thresh_range, xc):
    
    # checks
    reference_img_valid = True
    reference_img_current = False
    
    # API inputs
#    ref_img_name = 'image1.png' #example reference image name
    _, nameext = os.path.split(reference_image)
    
    ref_img_name, _ = os.path.splitext(nameext)
#    thresh_range = 3
#    thresh_type = 'std'
#    thresh_type = 'nm'
    
    c2cxpath = output_dir + ref_img_name + '_c2cx.pkl'
    c2cypath = output_dir + ref_img_name + '_c2cy.pkl'
    
    if reference_img_valid == True and reference_img_current == False:
        
        # reference image
        
        ref_xdir = pd.read_pickle(c2cxpath)
        ref_xdir = ref_xdir.iloc[:,1]
        ref_xmean = np.mean(ref_xdir)
        ref_xmedian = np.median(ref_xdir)
        ref_xstd = np.std(ref_xdir)

        ref_ydir = pd.read_pickle(c2cypath)
        ref_ydir = ref_ydir.iloc[:,1]
        ref_ymean = np.mean(ref_ydir)
        ref_ymedian = np.median(ref_ydir)
        ref_ystd = np.std(ref_ydir)
    
        # current image
        probx, px = stats.probplot(xdir['C2Cx ('+popup_unit+')'], dist="norm")
        proby, py = stats.probplot(ydir['C2Cy ('+popup_unit+')'], dist="norm")
        datx = probx
        daty = proby
        
        xdir_median = xdir['C2Cx ('+popup_unit+')'].median()
        xdir_mean = xdir['C2Cx ('+popup_unit+')'].mean()
        xdir_std = xdir['C2Cx ('+popup_unit+')'].std()
    
        ydir_median = ydir['C2Cy ('+popup_unit+')'].median()
        ydir_mean = ydir['C2Cy ('+popup_unit+')'].mean()
        ydir_std = ydir['C2Cy ('+popup_unit+')'].std()
        
        # PLOTS 
        x_offset = 1.6
        y_offset = 0
        # SAVE PLOT <image_name> + _C2Cx_plot.png
        # plot 1
        fig, ax = plt.subplots(figsize=(8,8))
        ax.plot(datx[1],datx[0], '.')
        ax.axvline(x=xdir_mean, label='C2Cx mean'.format(xc), c='b', alpha=0.2)
        ax.axvline(x=ref_xmean, label='Reference image C2Cx mean'.format(xc), c='b', alpha=0.2, ls = '--')
        

        if thresh_type == 'std':
            ax.fill_between([ref_xmean - ref_ystd*thresh_range, ref_xmean + ref_ystd*thresh_range], -4, 4, color='blue', alpha=0.1, transform=ax.get_xaxis_transform())
            ax.legend(['C2Cx', 'C2Cx mean ('+str(np.round(xdir_mean,2))+')', 'C2Cx mean ('+str(np.round(ref_xmean,2))+')' + ' (ref. image ' + str(ref_img_name)+')', '+/- ' + str(thresh_range) + ' std' + ' (ref. image ' + str(ref_img_name)+')'], bbox_to_anchor = (x_offset, y_offset), loc='lower right', framealpha = 1)
        elif thresh_type == 'nm':
            ax.fill_between([ref_xmean - thresh_range, ref_xmean + thresh_range], -4, 4, color='blue', alpha=0.1, transform=ax.get_xaxis_transform())
            ax.legend(['C2Cx', 'C2Cx mean ('+str(np.round(xdir_mean,2))+')', 'C2Cx mean ('+str(np.round(ref_xmean,2))+')' + ' (ref. image ' + str(ref_img_name)+')', '+/- ' + str(thresh_range) + ' ' + thresh_type + ' (ref. image ' + str(ref_img_name)+')'], bbox_to_anchor = (x_offset, y_offset), loc='lower right', framealpha = 1)
    
        ax.set_title('C2Cx')
        ax.set_ylabel('Theoretical quantiles')
        ax.set_xlabel('Center to Center (C2C) distance ('+popup_unit+')')
        ax.set_ylim([-3.5, 3.5])
        ax.set_xlim([26, 54])
        fig.savefig(output_dir + imgname+'_C2Cx_plot_'+'ref_comparison'+'.png', dpi=100, pad_inches=0.2, bbox_inches = 'tight') 
    
    
        # SAVE PLOT <image_name> + _C2Cy_plot.png
        # plot 2
        fig1, ax = plt.subplots(figsize=(8,8))
        ax.plot(daty[1],daty[0], '.r')
        ax.axvline(x=ydir_mean, label='C2Cy mean'.format(xc), c='r', alpha=0.2)
        ax.axvline(x=ref_ymean, label='Reference image C2Cy mean'.format(xc), c='r', alpha=0.2, ls = '--')
        if thresh_type == 'std':
            ax.fill_between([ref_ymean - ref_xstd*thresh_range, ref_ymean + ref_xstd*thresh_range], -4, 4, color='red', alpha=0.1, transform=ax.get_xaxis_transform())
            ax.legend(['C2Cy', 'C2Cy mean ('+str(np.round(ydir_mean,2))+')', 'C2Cy mean ('+str(np.round(ref_ymean,2))+')' + ' (ref. image ' + str(ref_img_name)+')', '+/- ' + str(thresh_range) + ' std' + ' (ref. image ' + str(ref_img_name)+')'], bbox_to_anchor = (x_offset, y_offset), loc='lower right', framealpha = 1)
        elif thresh_type == 'nm':
            ax.fill_between([ref_ymean - thresh_range, ref_ymean + thresh_range], -4, 4, color='red', alpha=0.1, transform=ax.get_xaxis_transform())
            ax.legend(['C2Cy', 'C2Cy mean ('+str(np.round(ydir_mean,2))+')', 'C2Cy mean ('+str(np.round(ref_ymean,2))+')' + ' (ref. image ' + str(ref_img_name)+')', '+/- ' + str(thresh_range) + ' ' + thresh_type + ' (ref. image ' + str(ref_img_name)+')'], bbox_to_anchor = (x_offset, y_offset), loc='lower right', framealpha = 1)
    
        ax.set_title('C2Cy')
        ax.set_ylabel('Theoretical quantiles')
        ax.set_xlabel('Center to Center (C2C) distance ('+popup_unit+')')
        ax.set_ylim([-3.5, 3.5])
        ax.set_xlim([26, 54])
        fig1.savefig(output_dir + imgname+'_C2Cy_plot_'+'ref_comparison'+'.png', dpi=100, pad_inches=0.2, bbox_inches = 'tight') 
    
    
        # SAVE PLOT <image_name> + _C2Cx_C2Cy_plot.png
        # plot 3
        fig2, ax = plt.subplots(figsize=(8,8))
        ax.plot(datx[1],datx[0], '.')
        ax.plot(daty[1],daty[0], '.r')
        ax.axvline(x=xdir_mean, label='C2Cx mean'.format(xc), c='b', alpha=0.2)
        ax.axvline(x=ref_xmean, label='Reference image C2Cx mean'.format(xc), c='b', alpha=0.2, ls = '--')
        ax.axvline(x=ydir_mean, label='C2Cy mean'.format(xc), c='r', alpha=0.2)
        ax.axvline(x=ref_ymean, label='Reference image C2Cy mean'.format(xc), c='r', alpha=0.2, ls = '--')
        if thresh_type == 'std':
            ax.fill_between([ref_xmean - ref_ystd*thresh_range, ref_xmean + ref_ystd*thresh_range], -4, 4, color='blue', alpha=0.1, transform=ax.get_xaxis_transform())
            ax.fill_between([ref_ymean - ref_xstd*thresh_range, ref_ymean + ref_xstd*thresh_range], -4, 4, color='red', alpha=0.1, transform=ax.get_xaxis_transform())
            ax.legend(['C2Cx', 'C2Cy', 'C2Cx mean ('+str(np.round(xdir_mean,2))+')', 'C2Cx mean ('+str(np.round(ref_xmean,2))+')' + ' (ref. image ' + str(ref_img_name)+')', 'C2Cy mean ('+str(np.round(ydir_mean,2))+')', 'C2Cy mean ('+str(np.round(ref_ymean,2))+')' + ' (ref. image ' + str(ref_img_name)+')', '+/- ' + str(thresh_range) + ' std C2Cx' + ' (ref. image ' + str(ref_img_name)+')', '+/- ' + str(thresh_range) + ' std C2Cy' + ' (ref. image ' + str(ref_img_name)+')'], bbox_to_anchor = (x_offset, y_offset), loc='lower right', framealpha = 1)
        elif thresh_type == 'nm':
            ax.fill_between([ref_xmean - thresh_range, ref_xmean + thresh_range], -4, 4, color='blue', alpha=0.1, transform=ax.get_xaxis_transform())
            ax.fill_between([ref_ymean - thresh_range, ref_ymean + thresh_range], -4, 4, color='red', alpha=0.1, transform=ax.get_xaxis_transform())
            ax.legend(['C2Cx', 'C2Cy', 'C2Cx mean ('+str(np.round(xdir_mean,2))+')', 'C2Cx mean ('+str(np.round(ref_xmean,2))+')' + ' (ref. image ' + str(ref_img_name)+')', 'C2Cy mean ('+str(np.round(ydir_mean,2))+')', 'C2Cy mean ('+str(np.round(ref_ymean,2))+')' + ' (ref. image ' + str(ref_img_name)+')',  '+/- ' + str(thresh_range) + ' ' + thresh_type + ' C2Cx (ref. image ' + str(ref_img_name)+')', '+/- ' + str(thresh_range) + ' ' + thresh_type + ' C2Cy (ref. image ' + str(ref_img_name)+')'], bbox_to_anchor = (x_offset, y_offset), loc='lower right', framealpha = 1)
    
        ax.set_title('C2Cx and C2Cy')
        ax.set_ylabel('Theoretical quantiles')
        ax.set_xlabel('Center to Center (C2C) distance ('+popup_unit+')')
        ax.set_ylim([-3.5, 3.5])
        ax.set_xlim([26, 54])
        fig2.savefig(output_dir + imgname+'_C2Cx_C2Cy_plot_'+'ref_comparison'+'.png', dpi=100, pad_inches=0.2, bbox_inches = 'tight')
        
        
        
        if reference_img_valid == True and reference_img_current == False:
            
            # reference image
            
            ref_xdir = pd.read_pickle(c2cxpath)
            ref_xdir = ref_xdir.iloc[:,1]
            ref_xmean = np.mean(ref_xdir)
            ref_xmedian = np.median(ref_xdir)
            ref_xstd = np.std(ref_xdir)
    
            ref_ydir = pd.read_pickle(c2cypath)
            ref_ydir = ref_ydir.iloc[:,1]
            ref_ymean = np.mean(ref_ydir)
            ref_ymedian = np.median(ref_ydir)
            ref_ystd = np.std(ref_ydir)
        
            # current image
        #     xx = np.arange(np.min([xdist,ydist])*1.1, np.max([xdist,ydist])*1.1, 0.01) # range of x in spec
            low_lim = np.min([xdir['C2Cx ('+popup_unit+')'].min(), ydir['C2Cy ('+popup_unit+')'].min()])*0.9
            high_lim = np.max([xdir['C2Cx ('+popup_unit+')'].max(), ydir['C2Cy ('+popup_unit+')'].max()])*1.1
            xx = np.arange(low_lim, high_lim, 0.01) # range of x in spec
        
            xdir_median = xdir['C2Cx ('+popup_unit+')'].median()
            xdir_mean = xdir['C2Cx ('+popup_unit+')'].mean()
            xdir_std = xdir['C2Cx ('+popup_unit+')'].std()
        
            ydir_median = ydir['C2Cy ('+popup_unit+')'].median()
            ydir_mean = ydir['C2Cy ('+popup_unit+')'].mean()
            ydir_std = ydir['C2Cy ('+popup_unit+')'].std()
            
            xdist = norm.pdf(xx,xdir_mean, xdir_std)
            ydist = norm.pdf(xx,ydir_mean, ydir_std)
           
            # SAVE PLOT <image_name> + _C2Cx_plot.png
            # plot 1
            fig, ax = plt.subplots(figsize=(8,8))    
            ax.plot(xx,xdist, 'b')
            ax.axvline(x=xdir_mean, label='C2Cx mean'.format(xc), c='b', alpha=0.4)
            ax.axvline(x=ref_xmean, label='Reference image C2Cx mean'.format(xc), c='b', alpha=0.2, ls = '--')
            if thresh_type == 'std':
                ax.fill_between([ref_xmean - ref_ystd*thresh_range, ref_xmean + ref_ystd*thresh_range], -4, 4, color='blue', alpha=0.1, transform=ax.get_xaxis_transform())
                ax.legend(['C2Cx', 'C2Cx mean ('+str(np.round(xdir_mean,2))+')', 'C2Cx mean ('+str(np.round(ref_xmean,2))+')' + ' (ref. image ' + str(ref_img_name)+')', '+/- ' + str(thresh_range) + ' std' + ' (ref. image ' + str(ref_img_name)+')'], bbox_to_anchor = (x_offset, y_offset), loc='lower right', framealpha = 1)
            elif thresh_type == 'nm':
                ax.fill_between([ref_xmean - thresh_range, ref_xmean + thresh_range], -4, 4, color='blue', alpha=0.1, transform=ax.get_xaxis_transform())
                ax.legend(['C2Cx', 'C2Cx mean ('+str(np.round(xdir_mean,2))+')', 'C2Cx mean ('+str(np.round(ref_xmean,2))+')' + ' (ref. image ' + str(ref_img_name)+')', '+/- ' + str(thresh_range) + ' ' + thresh_type + ' (ref. image ' + str(ref_img_name)+')'], bbox_to_anchor = (x_offset, y_offset), loc='lower right', framealpha = 1)
        
            ax.set_title('C2Cx')
            ax.set_ylabel('Probability')
            ax.set_xlabel('Center to Center (C2C) distance ('+popup_unit+')')
            ax.set_ylim([-0.01,np.max([xdist,ydist])*1.1])
            ax.set_xlim([26, 54])
            ax.plot(xdir['C2Cx ('+popup_unit+')'],np.zeros_like(xdir['C2Cx ('+popup_unit+')']), 'ob', alpha = 0.5)
            fig.savefig(output_dir + imgname+'_C2Cx_plot_'+'_normdist_ref_comparison'+'.png', dpi=100, pad_inches=0.2, bbox_inches = 'tight') 
            
            # SAVE PLOT <image_name> + _C2Cx_plot.png
            # plot 2
            fig1, ax = plt.subplots(figsize=(8,8))    
            ax.plot(xx,ydist, 'r')
            ax.axvline(x=ydir_mean, label='C2Cy mean'.format(xc), c='r', alpha=0.4)
            ax.axvline(x=ref_ymean, label='Reference image C2Cy mean'.format(xc), c='r', alpha=0.2, ls = '--')
            if thresh_type == 'std':
                ax.fill_between([ref_ymean - ref_xstd*thresh_range, ref_ymean + ref_xstd*thresh_range], -4, 4, color='red', alpha=0.1, transform=ax.get_xaxis_transform())
                ax.legend(['C2Cy', 'C2Cy mean ('+str(np.round(ydir_mean,2))+')', 'C2Cy mean ('+str(np.round(ref_ymean,2))+')' + ' (ref. image ' + str(ref_img_name)+')', '+/- ' + str(thresh_range) + ' std' + ' (ref. image ' + str(ref_img_name)+')'], bbox_to_anchor = (x_offset, y_offset), loc='lower right', framealpha = 1)
            elif thresh_type == 'nm':
                ax.fill_between([ref_ymean - thresh_range, ref_ymean + thresh_range], -4, 4, color='red', alpha=0.1, transform=ax.get_xaxis_transform())
                ax.legend(['C2Cy', 'C2Cy mean ('+str(np.round(ydir_mean,2))+')', 'C2Cy mean ('+str(np.round(ref_ymean,2))+')' + ' (ref. image ' + str(ref_img_name)+')', '+/- ' + str(thresh_range) + ' ' + thresh_type + ' (ref. image ' + str(ref_img_name)+')'], bbox_to_anchor = (x_offset, y_offset), loc='lower right', framealpha = 1)
        
            ax.set_title('C2Cy')
            ax.set_ylabel('Probability')
            ax.set_xlabel('Center to Center (C2C) distance ('+popup_unit+')')
            ax.set_ylim([-0.01,np.max([xdist,ydist])*1.1])
            ax.set_xlim([26, 54])
            ax.plot(ydir['C2Cy ('+popup_unit+')'],np.zeros_like(ydir['C2Cy ('+popup_unit+')']), 'or', alpha = 0.5)
            fig1.savefig(output_dir + imgname+'_C2Cy_plot_'+'_normdist_ref_comparison'+'.png', dpi=100, pad_inches=0.2, bbox_inches = 'tight') 
        
            # SAVE PLOT <image_name> + _C2Cx_C2Cy_plot.png
            # plot 3
            fig2, ax = plt.subplots(figsize=(8,8))    
            ax.plot(xx,xdist, 'b')
            ax.plot(xx,ydist, 'r')
            ax.axvline(x=xdir_mean, label='C2Cx mean'.format(xc), c='b', alpha=0.4)
            ax.axvline(x=ref_xmean, label='Reference image C2Cx mean'.format(xc), c='b', alpha=0.2, ls = '--')
            ax.axvline(x=ydir_mean, label='C2Cy mean'.format(xc), c='r', alpha=0.4)
            ax.axvline(x=ref_ymean, label='Reference image C2Cy mean'.format(xc), c='r', alpha=0.2, ls = '--')
            if thresh_type == 'std':
                ax.fill_between([ref_xmean - ref_ystd*thresh_range, ref_xmean + ref_ystd*thresh_range], -4, 4, color='blue', alpha=0.1, transform=ax.get_xaxis_transform())
                ax.fill_between([ref_ymean - ref_xstd*thresh_range, ref_ymean + ref_xstd*thresh_range], -4, 4, color='red', alpha=0.1, transform=ax.get_xaxis_transform())
                ax.legend(['C2Cx', 'C2Cy', 'C2Cx mean ('+str(np.round(xdir_mean,2))+')', 'C2Cx mean ('+str(np.round(ref_xmean,2))+')' + ' (ref. image ' + str(ref_img_name)+')', 'C2Cy mean ('+str(np.round(ydir_mean,2))+')', 'C2Cy mean ('+str(np.round(ref_ymean,2))+')' + ' (ref. image ' + str(ref_img_name)+')', '+/- ' + str(thresh_range) + ' std C2Cx' + ' (ref. image ' + str(ref_img_name)+')', '+/- ' + str(thresh_range) + ' std C2Cy' + ' (ref. image ' + str(ref_img_name)+')'], bbox_to_anchor = (x_offset, y_offset), loc='lower right', framealpha = 1)
            elif thresh_type == 'nm':
                ax.fill_between([ref_xmean - thresh_range, ref_xmean + thresh_range], -4, 4, color='blue', alpha=0.1, transform=ax.get_xaxis_transform())
                ax.fill_between([ref_ymean - thresh_range, ref_ymean + thresh_range], -4, 4, color='red', alpha=0.1, transform=ax.get_xaxis_transform())
                ax.legend(['C2Cx', 'C2Cy', 'C2Cx mean ('+str(np.round(xdir_mean,2))+')', 'C2Cx mean ('+str(np.round(ref_xmean,2))+')' + ' (ref. image ' + str(ref_img_name)+')', 'C2Cy mean ('+str(np.round(ydir_mean,2))+')', 'C2Cy mean ('+str(np.round(ref_ymean,2))+')' + ' (ref. image ' + str(ref_img_name)+')',  '+/- ' + str(thresh_range) + ' ' + thresh_type + ' C2Cx (ref. image ' + str(ref_img_name)+')', '+/- ' + str(thresh_range) + ' ' + thresh_type + ' C2Cy (ref. image ' + str(ref_img_name)+')'], bbox_to_anchor = (x_offset, y_offset), loc='lower right', framealpha = 1)
        
            ax.plot(xdir['C2Cx ('+popup_unit+')'],np.zeros_like(xdir['C2Cx ('+popup_unit+')']), 'ob', alpha = 0.5)
            ax.plot(ydir['C2Cy ('+popup_unit+')'],np.zeros_like(ydir['C2Cy ('+popup_unit+')']), 'or', alpha = 0.5)
            ax.set_title('C2Cx and C2Cy')
            ax.set_ylabel('Probability')
            ax.set_xlabel('Center to Center (C2C) distance ('+popup_unit+')')
            ax.set_ylim([-0.01,np.max([xdist,ydist])*1.1])
            ax.set_xlim([26, 54])
            fig2.savefig(output_dir + imgname+'_C2Cx_C2Cy_plot_'+'_normdist_ref_comparison'+'.png', dpi=100, pad_inches=0.2, bbox_inches = 'tight') 
        
            norm_plot1 = output_dir + imgname+'_C2Cx_plot_'+'_normdist_ref_comparison'+'.png'
            norm_plot2 = output_dir + imgname+'_C2Cy_plot_'+'_normdist_ref_comparison'+'.png'
            norm_plot3 = output_dir + imgname+'_C2Cx_C2Cy_plot_'+'_normdist_ref_comparison'+'.png'
            
            norm_success = True
        
        plot1 = output_dir + imgname+'_C2Cx_C2Cy_plot_'+'ref_comparison'+'.png'
        plot2 = output_dir + imgname+'_C2Cx_C2Cy_plot_'+'ref_comparison'+'.png'
        plot3 = output_dir + imgname+'_C2Cx_C2Cy_plot_'+'ref_comparison'+'.png'
        
        if norm_success:
            return plot1, plot2, plot3, norm_plot1, norm_plot2, norm_plot3
        else:
            return plot1, plot2, plot3, None, None, None

def center2CenterPlots(xdir, ydir, output_dir, foldername, popup_unit):

    datx = stats.probplot(xdir['C2Cx ('+popup_unit+')'], dist="norm")
    daty = stats.probplot(ydir['C2Cy ('+popup_unit+')'], dist="norm")
    
    
    # SAVE PLOT <image_name> + _C2Cx_plot.png
    # plot 1
    plt.figure(figsize=(8,8))
    plt.plot(datx[0][1],datx[0][0], '.')
    plt.title('C2Cx')
    plt.ylabel('sigma')
    plt.xlabel('Center to Center (C2C) distance ('+popup_unit+')')
    plt.ylim([-3.5, 3.5])
    plt.legend(['C2Cx'], loc='lower right')
    # plt.grid()
    plot1 = output_dir + foldername + '_C2Cx_plot.png' 
    plt.savefig(plot1, dpi=100, pad_inches=0.2) 
    
    
    # SAVE PLOT <image_name> + _C2Cy_plot.png
    # plot 2
    plt.figure(figsize=(8,8))
    plt.plot(daty[0][1],daty[0][0], '.r')
    plt.title('C2Cy')
    plt.ylabel('sigma')
    plt.xlabel('Center to Center (C2C) distance ('+popup_unit+')')
    plt.ylim([-3.5, 3.5])
    plt.legend(['C2Cy'], loc='lower right')
    plot2 = output_dir + foldername + '_C2Cy_plot.png' 
    plt.savefig(plot2, dpi=100, pad_inches=0.2) 
    
    # SAVE PLOT <image_name> + _C2Cx_C2Cy_plot.png
    # plot 3
    plt.figure(figsize=(8,8))
    plt.plot(datx[0][1],datx[0][0], '.')
    plt.plot(daty[0][1],daty[0][0], '.r')
    plt.title('C2Cx and C2Cy')
    plt.ylabel('sigma')
    plt.xlabel('Center to Center (C2C) distance ('+popup_unit+')')
    plt.ylim([-3.5, 3.5])
    plt.legend(['C2Cx', 'C2Cy'], loc='lower right')
    plot3 = output_dir + foldername + '_C2Cx_C2Cy_plot.png' 
    plt.savefig(plot3, dpi=100, pad_inches=0.2)

    return plot1, plot2, plot3
    
def createPagePdf(num, tmp):
    c = canvas.Canvas(tmp)
    for i in range(1, num + 1):
        c.drawString((210 // 2) * mm, (4) * mm, str(i))
        c.showPage()
    c.save()

def addPageNumberingOnPDF(pdf_path,out):
    """
    Add page numbers to a pdf, save the result as a new pdf
    @param pdf_path: path to pdf
    """
    tmp = "__tmp"+str(int(round(time.time() * 1000)))+".pdf"

    output = PdfFileWriter()
    with open(pdf_path, 'rb') as f:
        pdf = PdfFileReader(f, strict=False)
        n = pdf.getNumPages()

        # create new PDF with page numbers
        createPagePdf(n, tmp)
        with open(tmp, 'rb') as ftmp:
            numberPdf = PdfFileReader(ftmp)
            # iterarte pages
            for p in range(n):
                page = pdf.getPage(p)
                numberLayer = numberPdf.getPage(p)
                # merge number page with actual page
                page.mergePage(numberLayer)
                output.addPage(page)

            # write result
            if output.getNumPages():
                with open(out, 'wb') as f:
                    output.write(f)
        os.remove(tmp)

def encodeImage(img):
    jpg_img = cv2.imencode('.png', skimage.img_as_ubyte(img))
    encoded_str = 'data:image/png;base64,' + base64.b64encode(jpg_img[1]).decode('utf-8')    
    return encoded_str

def createSummaryPDFPage(combined_describe, annotate_img, summarypng, secimag):

    del_col = ['Pillar', 'Hexagon center pillar']
    for i in del_col:
        try:
            combined_describe = combined_describe.drop([i], axis=1)
        except:
            pass

    new_col = ['X-Y parlgrm. packing fraction', 'X-Diag. parlgrm. packing fraction', 'Y-Diag. parlgrm. packing fraction']
    prev_col = ['X-Y parallelogram packing fraction', 'X-Diagonal parallelogram packing fraction', 'Y-Diagonal parallelogram packing fraction']

    for i,j in enumerate(new_col):
        try:
            combined_describe.rename(columns = {prev_col[i]:j}, inplace = True)
        except:
            pass

    #img = io.imread(annotate_img)
    #img = cv2.resize(img, dim, interpolation = cv2.INTER_AREA)
    path,fname = os.path.split(annotate_img)
    fname, _ = os.path.splitext(fname)
    fname = os.path.basename(path)
    encoded = encodeImageUsingPath(annotate_img)
    encoded2 = encodeImage(secimag)
    style = '@media print{.new-page{page-break-before: always}} @page{margin: 1cm; size: A4 landscape;}table thead{display: table-header-group;font-size: 12px}table tbody{page-break-inside: auto !important}table tfoot{display: table-row-group}table tr{font-size: 12px;page-break-inside: auto !important}table td{font-size: 12px;page-break-inside: auto !important}h3{font-size: 12px;font-weight: bold}h2{font-size: 16px;font-weight: bold}table{width: 100%}table tr{cursor: pointer}table th{background: #1d969d;color: #fff;font-weight: 400}img{max-width: 100%;width: 370px; margin-left: 30px;}'

    h2 = 'Pillar CD analysis summary - ' + fname
    Main_Heading = 'Pillar Analysis'
    htmltemp = 'first'+str(int(round(time.time() * 1000)))+'.html'
    with open(htmltemp, 'w') as _file:
        body = '<h2> '+h2+' </h2><hr><img  src="'+encoded+'" /><img  src="'+encoded2+'" /><br>' + combined_describe.to_html(index=True,border=1,justify="center").replace('<tr>','<tr style="text-align: center;">') + '<br><hr>' 
        html = '<!DOCTYPE html><head><meta charset="utf-8"><style>'+style+'</style></head><body><div class="container">'+body+'</div></body></html>';
    
        _file.write(html)

    htmlpdf = 'first'+str(int(round(time.time() * 1000)))+'.pdf'
    HTML(htmltemp).write_pdf(htmlpdf)
    try:
        os.remove(htmltemp)
    except:
        pass


    doc = fitz.open(htmlpdf)
    page = doc.loadPage(0)  # number of page
    pix = page.getPixmap()
    pix.writePNG(summarypng)

#    pages = convert_from_path(htmlpdf, 500)
#    #pages[0].save('out.png', 'png')
#    pages[0].save(summarypng, 'png')
    return htmlpdf  

def createAnalysisPDF(i, annotate_img, cd_describe, cd):
    Main_Heading = i.upper()
    Heading1 = 'All Measurements'
    Heading2 =  'Summary'
    
    encoded = encodeImageUsingPath(annotate_img)
    #@bottom-right{content: counter(page);}
    
    style = '@media print{.new-page{page-break-before: always}} @page{margin: 1cm; size: A4;}table thead{display: table-header-group}table tbody{page-break-inside: auto !important}table tfoot{display: table-row-group}table tr{page-break-inside: auto !important}table td{font-size: 12px;page-break-inside: auto !important}h3{font-size: 12px;font-weight: bold}h2{font-size: 16px;font-weight: bold}table{width: 100%}table tr{cursor: pointer}table th{background: #1d969d;color: #fff;font-weight: 400}img{max-width: 100%;width: 400px}'
    
    htmltemp = i+str(int(round(time.time() * 1000)))+'.html'
    with open(htmltemp, 'w') as _file:
        body = '<h1> '+Main_Heading+' </h1><br><hr><img src="'+encoded+'"><br><h2> '+Heading1+' </h2>' + cd.to_html(index=False,border=1,justify="center").replace('<tr>','<tr style="text-align: center;">')+ '<br><hr>' + '<br><hr><h2 class="new-page"> '+Heading2+' </h2>' + cd_describe.to_html(index=True,border=1,justify="center").replace('<tr>','<tr style="text-align: center;">')+ '<br><hr>' 
        
#        body = '<h1> '+Main_Heading+' </h1><br><hr><img src="'+encoded+'"><br><h2> '+Heading1+' </h2>' + cd_describe.to_html(index=True,border=1,justify="center").replace('<tr>','<tr style="text-align: center;">') + '<br><hr><h2 class="new-page"> '+Heading2+' </h2>' + cd.to_html(index=False,border=1,justify="center").replace('<tr>','<tr style="text-align: center;">')+ '<br><hr>' 
        
        html = '<!DOCTYPE html><head><meta charset="utf-8"><style>'+style+'</style></head><body><div class="container">'+body+'</div></body></html>';

        _file.write(html)

    htmlpdf = i+str(int(round(time.time() * 1000)))+'.pdf'
    HTML(htmltemp).write_pdf(htmlpdf)
    try:
        os.remove(htmltemp)
    except:
        pass
    return htmlpdf


def XYDirectionPilAnalysis(data, S, scale, x0, x1, y0, y1, popup_unit):
    data_y = data.copy()
    data_y['c0-y'] = data_y['centroid-0'] - y0
    data_y['c1-y'] = data_y['centroid-1'] - y1
    data_y.drop(data_y[data_y['c0-y'] >= S.shape[0]].index, inplace = True) 
    data_y.drop(data_y[data_y['c1-y'] >= S.shape[1]].index, inplace = True) 
    data_y.drop(data_y[data_y['c0-y'] < 0].index, inplace = True) 
    data_y.drop(data_y[data_y['c1-y'] < 0].index, inplace = True)
    ##
    data_y.drop(data_y[data_y['c0-x'] >= S.shape[0]].index, inplace = True) 
    data_y.drop(data_y[data_y['c1-x'] >= S.shape[1]].index, inplace = True) 
    data_y.drop(data_y[data_y['c0-x'] < 0].index, inplace = True) 
    data_y.drop(data_y[data_y['c1-x'] < 0].index, inplace = True)
    data_y.drop(data_y[data_y['c0-y']+x0 >= S.shape[0]].index, inplace = True)
    data_y.drop(data_y[data_y['c1-y']+x1 >= S.shape[1]].index, inplace = True)
    data_y.drop(data_y[data_y['c0-y']+x0 < 0].index, inplace = True)
    data_y.drop(data_y[data_y['c1-y']+x1 < 0].index, inplace = True)
    ##
    data_y.index = range(len(data_y))
    
    # data_y
    
    metrics_pg = ('area', 'centroid')
    xypg_pf = np.zeros_like(S)
    xy_pg_packing_fraction = []
    obj_pairs = []
    
    S = S*1
    for circle in range(len(data_y)):
        c_orig = flood(S, (data_y['centroid-0'][circle], data_y['centroid-1'][circle]))
        cy = flood(S, (data_y['c0-y'][circle], data_y['c1-y'][circle]))
        c_orig_xypair = flood(S, (data_y['c0-x'][circle], data_y['c1-x'][circle]))
        cy_xypair = flood(S, (data_y['c0-y'][circle]+int(x0*1.0), data_y['c1-y'][circle]+int(x1*1.0)))
        pairs = c_orig+cy+c_orig_xypair+cy_xypair
        c_labels = label(pairs, background=None, return_num=True)
        if c_labels[1]==4:
            props_pg = regionprops_table(label(pairs), properties = metrics_pg)
        
            temp = []
            for obj in range(len(props_pg['centroid-0'])):
                rr = data.loc[(data['centroid-0'] == int(props_pg['centroid-0'][obj])) & (data['centroid-1'] == int(props_pg['centroid-1'][obj]))]['Object']
                temp.append(rr[:])
            temp1 = list(chain.from_iterable(temp))
            obj_pairs.append(temp1)
            
            ZZ = np.zeros_like(S)
            ZZ[props_pg['centroid-0'].astype(int),props_pg['centroid-1'].astype(int)]=1
            P = convex_hull_image(ZZ, offset_coordinates=False)
            HP = np.zeros_like(S)
            xy_pg_packing_im = pairs*2-P*1
            P_props = regionprops(label(P))
            PC_props = regionprops(label(xy_pg_packing_im==-1))
            packing_fraction = (P_props[0].area-PC_props[0].area)/P_props[0].area
            xy_pg_packing_fraction.append(packing_fraction)   
    #         xypg_pf = np.dstack((xypg_pf, xy_pg_packing_im))
        else:
            pass

    xy_pg_packing = pd.DataFrame(list(zip(obj_pairs, xy_pg_packing_fraction)), columns = ['Pillars in parallelogram D1-D2', 'D1-D2 parallelogram packing fraction'])
    #xy_pg_packing = pd.DataFrame(list(zip(obj_pairs, xy_pg_packing_fraction)), columns = ['Pillars in parallelogram', 'X-Y parallelogram packing fraction'])
    drop_col = 'Pillars in parallelogram D1-D2'
    
    return xy_pg_packing, drop_col


def YDiagonalDirectionPilAnalysis(data, S, scale, x0, x1, z0, z1, popup_unit):

    data_x = data.copy()
    data_x['c0-x'] = data_x['centroid-0'] - x0
    data_x['c1-x'] = data_x['centroid-1'] - x1
    data_x.drop(data_x[data_x['c0-y'] >= S.shape[0]].index, inplace = True) 
    data_x.drop(data_x[data_x['c1-y'] >= S.shape[1]].index, inplace = True) 
    data_x.drop(data_x[data_x['c0-y'] < 0].index, inplace = True) 
    data_x.drop(data_x[data_x['c1-y'] < 0].index, inplace = True)
    ##
    data_x.drop(data_x[data_x['c0-z'] >= S.shape[0]].index, inplace = True) 
    data_x.drop(data_x[data_x['c1-z'] >= S.shape[1]].index, inplace = True) 
    data_x.drop(data_x[data_x['c0-z'] < 0].index, inplace = True) 
    data_x.drop(data_x[data_x['c1-z'] < 0].index, inplace = True)
    data_x.drop(data_x[data_x['c0-y']+z0 >= S.shape[0]].index, inplace = True)
    data_x.drop(data_x[data_x['c1-y']+z1 >= S.shape[1]].index, inplace = True)
    data_x.drop(data_x[data_x['c0-y']+z0 < 0].index, inplace = True)
    data_x.drop(data_x[data_x['c1-y']+z1 < 0].index, inplace = True)
    
    ##
    data_x.index = range(len(data_x))
    
    metrics_pg = ('area', 'centroid')
    ydpg_pf = np.zeros_like(S)
    yd_pg_packing_fraction = []
    obj_pairs = []
    
    S = S*1
    for circle in range(len(data_x)):
        c_orig = flood(S, (data_x['centroid-0'][circle], data_x['centroid-1'][circle]))
        cy = flood(S, (data_x['c0-y'][circle], data_x['c1-y'][circle]))
        c_orig_ydpair = flood(S, (data_x['c0-z'][circle], data_x['c1-z'][circle]))
        cy_ydpair = np.zeros_like(S)
        try:
            cy_ydpair = flood(S, (data_x['c0-y'][circle]+int(z0*1.0), data_x['c1-y'][circle]+int(z1*1.0)))
        except:
            pass
        pairs = c_orig+cy+c_orig_ydpair+cy_ydpair
        c_labels = label(pairs, background=None, return_num=True)
        if c_labels[1]==4:
            props_pg = regionprops_table(label(pairs), properties = metrics_pg)
    
            temp = []
            for obj in range(len(props_pg['centroid-0'])):
                rr = data.loc[(data['centroid-0'] == int(props_pg['centroid-0'][obj])) & (data['centroid-1'] == int(props_pg['centroid-1'][obj]))]['Object']
                temp.append(rr[:])
            temp1 = list(chain.from_iterable(temp))
            obj_pairs.append(temp1)
    
            ZZ = np.zeros_like(S)
            ZZ[props_pg['centroid-0'].astype(int),props_pg['centroid-1'].astype(int)]=1
            P = convex_hull_image(ZZ, offset_coordinates=False)
            HP = np.zeros_like(S)
            yd_pg_packing_im = pairs*2-P*1
            P_props = regionprops(label(P))
            PC_props = regionprops(label(yd_pg_packing_im==-1))
            packing_fraction = (P_props[0].area-PC_props[0].area)/P_props[0].area
            yd_pg_packing_fraction.append(packing_fraction)   
    #             ydpg_pf = np.dstack((ydpg_pf, yd_pg_packing_im))
        else:
            pass          
        
    yd_pg_packing = pd.DataFrame(list(zip(obj_pairs, yd_pg_packing_fraction)), columns = ['Pillars in parallelogram D2-D3', 'D2-D3 parallelogram packing fraction'])
    # yd_pg_packing = pd.DataFrame(list(zip(obj_pairs, yd_pg_packing_fraction)), columns = ['Pillars in parallelogram', 'Y-Diagonal parallelogram packing fraction'])
    
    drop_col = 'Pillars in parallelogram D2-D3'
    return yd_pg_packing, drop_col


def XDiagonalDirectionPilAnalysis(data, S, scale, x0, x1, z0, z1, popup_unit):
    data_x = data.copy()
    data_x['c0-x'] = data_x['centroid-0'] - x0
    data_x['c1-x'] = data_x['centroid-1'] - x1
    data_x.drop(data_x[data_x['c0-x'] >= S.shape[0]].index, inplace = True) 
    data_x.drop(data_x[data_x['c1-x'] >= S.shape[1]].index, inplace = True) 
    data_x.drop(data_x[data_x['c0-x'] < 0].index, inplace = True) 
    data_x.drop(data_x[data_x['c1-x'] < 0].index, inplace = True)
    ##
    data_x.drop(data_x[data_x['c0-z'] >= S.shape[0]].index, inplace = True) 
    data_x.drop(data_x[data_x['c1-z'] >= S.shape[1]].index, inplace = True) 
    data_x.drop(data_x[data_x['c0-z'] < 0].index, inplace = True) 
    data_x.drop(data_x[data_x['c1-z'] < 0].index, inplace = True)
    data_x.drop(data_x[data_x['c0-x']+z0 >= S.shape[0]].index, inplace = True)
    data_x.drop(data_x[data_x['c1-x']+z1 >= S.shape[1]].index, inplace = True)
    data_x.drop(data_x[data_x['c0-x']+z0 < 0].index, inplace = True)
    data_x.drop(data_x[data_x['c1-x']+z1 < 0].index, inplace = True)
    
    ##
    data_x.index = range(len(data_x))
    
    metrics_pg = ('area', 'centroid')
    xdpg_pf = np.zeros_like(S)
    xd_pg_packing_fraction = []
    obj_pairs = []
    
    S = S*1
    for circle in range(len(data_x)):
        c_orig = flood(S, (data_x['centroid-0'][circle], data_x['centroid-1'][circle]))
        cx = flood(S, (data_x['c0-x'][circle], data_x['c1-x'][circle]))
        c_orig_xdpair = flood(S, (data_x['c0-z'][circle], data_x['c1-z'][circle]))
        cx_xdpair = np.zeros_like(S)
        try:
            cx_xdpair = flood(S, (data_x['c0-x'][circle]+int(z0*1.0), data_x['c1-x'][circle]+int(z1*1.0)))
        except:
            pass
        pairs = c_orig+cx+c_orig_xdpair+cx_xdpair
        c_labels = label(pairs, background=None, return_num=True)
        if c_labels[1]==4:
            props_pg = regionprops_table(label(pairs), properties = metrics_pg)
    
            temp = []
            for obj in range(len(props_pg['centroid-0'])):
                rr = data.loc[(data['centroid-0'] == int(props_pg['centroid-0'][obj])) & (data['centroid-1'] == int(props_pg['centroid-1'][obj]))]['Object']
                temp.append(rr[:])
            temp1 = list(chain.from_iterable(temp))
            obj_pairs.append(temp1)
    
            ZZ = np.zeros_like(S)
            ZZ[props_pg['centroid-0'].astype(int),props_pg['centroid-1'].astype(int)]=1
            P = convex_hull_image(ZZ, offset_coordinates=False)
            HP = np.zeros_like(S)
            xd_pg_packing_im = pairs*2-P*1
            P_props = regionprops(label(P))
            PC_props = regionprops(label(xd_pg_packing_im==-1))
            packing_fraction = (P_props[0].area-PC_props[0].area)/P_props[0].area
            xd_pg_packing_fraction.append(packing_fraction)   
    #         xdpg_pf = np.dstack((xdpg_pf, xd_pg_packing_im))
        else:
            pass            
        
    xd_pg_packing = pd.DataFrame(list(zip(obj_pairs, xd_pg_packing_fraction)), columns = ['Pillars in parallelogram D1-D3', 'D1-D3 parallelogram packing fraction'])
    # xd_pg_packing = pd.DataFrame(list(zip(obj_pairs, xd_pg_packing_fraction)), columns = ['Pillars in parallelogram', 'X-Diagonal parallelogram packing fraction'])
    drop_col = 'Pillars in parallelogram D1-D3'    
    return xd_pg_packing, drop_col


def XDirectionPilAnalysis(data, x0, x1, S, scale, popup_unit, dil, pillar_type, scalebar):
    #scale = 100/(67-1)
    data_x = data.copy()
    data_x['c0-x'] = data_x['centroid-0'] - x0
    data_x['c1-x'] = data_x['centroid-1'] - x1
    data_x.drop(data_x[data_x['c0-x'] >= S.shape[0]].index, inplace = True) 
    data_x.drop(data_x[data_x['c1-x'] >= S.shape[1]].index, inplace = True) 
    data_x.drop(data_x[data_x['c0-x'] < 0].index, inplace = True) 
    data_x.drop(data_x[data_x['c1-x'] < 0].index, inplace = True)
    data_x.index = range(len(data_x))
    
    metrics_p = ('area', 'centroid')
    pairs_x = np.empty(S.shape)
    dist_x = []
    pitch_x = []
    obj_pairs = []
    S = S*1
    for circle in range(len(data_x)):
        c_orig = flood(S, (data_x['centroid-0'][circle], data_x['centroid-1'][circle]))
        cx = flood(S, (data_x['c0-x'][circle], data_x['c1-x'][circle]))
        pairs = c_orig+cx
        c_labels = label(pairs, background=None, return_num=True)
        if c_labels[1]==2:
    #         pairs_x = np.dstack((pairs_x, pairs))
    
            pair_rp = regionprops_table(label(pairs),properties = metrics_p)
            temp = []
            for obj in range(len(pair_rp['centroid-0'])):
                rr = data.loc[(data['centroid-0'] == int(pair_rp['centroid-0'][obj])) & (data['centroid-1'] == int(pair_rp['centroid-1'][obj]))]['Object']
                temp.append(rr[:])
            temp1 = list(chain.from_iterable(temp))
            obj_pairs.append(temp1)
            
            if pillar_type == 'pillar2':
                dist = np.linalg.norm(np.array((pair_rp['centroid-0'][0], pair_rp['centroid-1'][0])) - np.array((pair_rp['centroid-0'][1], pair_rp['centroid-1'][1])))
                dist_x.append(dist)
            else:
                g = find_boundaries(pairs, connectivity=2, mode = 'inner')
                pairs_x_rp = regionprops(label(g))
                d = cdist(pairs_x_rp[0].coords,pairs_x_rp[1].coords)
                dist_x.append(np.min(d))
                
                pairs_xmod = binary_closing(g, disk(dil), out=None)
                b = find_boundaries(pairs_xmod, connectivity=2, mode = 'inner')
                pairs_xmod_rp = regionprops(label(b))
                p = cdist(pairs_xmod_rp[0].coords,pairs_xmod_rp[0].coords)
                pitch_x.append(np.max(p))
        else:
            pass
    
    if pillar_type == 'pillar2':
        if scalebar == True:
            dist_x_sc = np.asarray(dist_x)*scale
            xdir = pd.DataFrame(list(zip(obj_pairs, dist_x_sc)), columns = ['Pillar pairs', 'C2Cx ('+popup_unit+')'])
        else:
            xdir = pd.DataFrame(list(zip(obj_pairs, dist_x)), columns = ['Pillar pairs', 'C2Cx (px)'])
        namedf = 'c2cx'
    else:      
        dist_x_sc = np.asarray(dist_x)*scale
        pitch_x_sc = np.asarray(pitch_x)*scale
        xdir = pd.DataFrame(list(zip(obj_pairs, dist_x_sc, pitch_x_sc)), columns = ['Pillar pairs', 'D1 distance ('+popup_unit+')', 'D1 pitch ('+popup_unit+')'])
        namedf = 'D1_dir'
        
    dc = 'Pillar pairs'
    return xdir, dc, namedf


def YDirectionPilAnalysis(data, y0, y1, S, scale, popup_unit, dil, pillar_type, scalebar):
    data_y = data.copy()
    data_y['c0-y'] = data_y['centroid-0'] - y0
    data_y['c1-y'] = data_y['centroid-1'] - y1
    data_y.drop(data_y[data_y['c0-y'] >= S.shape[0]].index, inplace = True) 
    data_y.drop(data_y[data_y['c1-y'] >= S.shape[1]].index, inplace = True) 
    data_y.drop(data_y[data_y['c0-y'] < 0].index, inplace = True) 
    data_y.drop(data_y[data_y['c1-y'] < 0].index, inplace = True)
    data_y.index = range(len(data_y))
    ####
    
    metrics_p = ('area', 'centroid')
    pairs_y = np.empty(S.shape)
    dist_y = []
    pitch_y = []
    obj_pairs = []
    S = S*1
    for circle in range(len(data_y)):
        c_orig = flood(S, (data_y['centroid-0'][circle], data_y['centroid-1'][circle]))
        cy = flood(S, (data_y['c0-y'][circle], data_y['c1-y'][circle]))
        c_orig_pair = flood(S, (data_y['centroid-0'][circle], data_y['centroid-1'][circle]))
        pairs = c_orig+cy
        c_labels = label(pairs, background=None, return_num=True)
        if c_labels[1]==2:
    #         pairs_y = np.dstack((pairs_y, pairs))
    
            pair_rp = regionprops_table(label(pairs),properties = metrics_p)
            temp = []
            for obj in range(len(pair_rp['centroid-0'])):
                rr = data.loc[(data['centroid-0'] == int(pair_rp['centroid-0'][obj])) & (data['centroid-1'] == int(pair_rp['centroid-1'][obj]))]['Object']
                temp.append(rr[:])
            temp1 = list(chain.from_iterable(temp))
            obj_pairs.append(temp1)
            
            
            if pillar_type == 'pillar2':
                dist = np.linalg.norm(np.array((pair_rp['centroid-0'][0], pair_rp['centroid-1'][0])) - np.array((pair_rp['centroid-0'][1], pair_rp['centroid-1'][1])))
                dist_y.append(dist)
            else:
                g = find_boundaries(pairs, connectivity=2, mode = 'inner')
                pairs_y_rp = regionprops(label(g))
                d = cdist(pairs_y_rp[0].coords,pairs_y_rp[1].coords)
                dist_y.append(np.min(d))
                
                pairs_ymod = binary_closing(pairs, disk(dil), out=None)
                b = find_boundaries(pairs_ymod, connectivity=2, mode = 'inner')
                pairs_ymod_rp = regionprops(label(b))
                p = cdist(pairs_ymod_rp[0].coords,pairs_ymod_rp[0].coords)
                pitch_y.append(np.max(p))
        else:
            pass
    
    if pillar_type == 'pillar2':
        if scalebar == True:
            dist_y_sc = np.asarray(dist_y)*scale
            ydir = pd.DataFrame(list(zip(obj_pairs, dist_y_sc)), columns = ['Pillar pairs', 'C2Cy ('+popup_unit+')'])
        else:
            xdir = pd.DataFrame(list(zip(obj_pairs, dist_x)), columns = ['Pillar pairs', 'C2Cx (px)'])
        namedf = 'c2cy'
    else:      
        dist_y_sc = np.asarray(dist_y)*scale
        pitch_y_sc = np.asarray(pitch_y)*scale
        ydir = pd.DataFrame(list(zip(obj_pairs, dist_y_sc, pitch_y_sc)), columns = ['Pillar pairs', 'D2 distance ('+popup_unit+')', 'D2 pitch ('+popup_unit+')'])
        namedf = 'D2_dir'
    
    dc = 'Pillar pairs'
    return ydir, dc, namedf


def ZDirectionPilAnalysis(data, z0, z1, S, scale, popup_unit, dil):
    #scale = 100/(67-1)
    data_z = data.copy()
    data_z['c0-z'] = data_z['centroid-0'] - z0
    data_z['c1-z'] = data_z['centroid-1'] - z1
    data_z.drop(data_z[data_z['c0-z'] >= S.shape[0]].index, inplace = True) 
    data_z.drop(data_z[data_z['c1-z'] >= S.shape[1]].index, inplace = True) 
    data_z.drop(data_z[data_z['c0-z'] < 0].index, inplace = True) 
    data_z.drop(data_z[data_z['c1-z'] < 0].index, inplace = True)
    data_z.index = range(len(data_z))
    
    metrics_p = ('area', 'centroid')
    pairs_z = np.empty(S.shape)
    dist_z = []
    pitch_z = []
    obj_pairs = []
    S = S*1
    for circle in range(len(data_z)):
        c_orig = flood(S, (data_z['centroid-0'][circle], data_z['centroid-1'][circle]))
        cz = flood(S, (data_z['c0-z'][circle], data_z['c1-z'][circle]))
        pairs = c_orig+cz
        c_labels = label(pairs, background=None, return_num=True)
        if c_labels[1]==2:
    #         pairs_z = np.dstack((pairs_z, pairs))
    
            pair_rp = regionprops_table(label(pairs),properties = metrics_p)
            temp = []
            for obj in range(len(pair_rp['centroid-0'])):
                rr = data.loc[(data['centroid-0'] == int(pair_rp['centroid-0'][obj])) & (data['centroid-1'] == int(pair_rp['centroid-1'][obj]))]['Object']
                temp.append(rr[:])
            temp1 = list(chain.from_iterable(temp))
            obj_pairs.append(temp1)
            
            g = find_boundaries(pairs, connectivity=2, mode = 'inner')
            pairs_z_rp = regionprops(label(g))
            d = cdist(pairs_z_rp[0].coords,pairs_z_rp[1].coords)
            dist_z.append(np.min(d))
            
            pairs_zmod = binary_closing(pairs, disk(dil), out=None)
            b = find_boundaries(pairs_zmod, connectivity=2, mode = 'inner')
            pairs_zmod_rp = regionprops(label(b))
            p = cdist(pairs_zmod_rp[0].coords,pairs_zmod_rp[0].coords)
            pitch_z.append(np.max(p))
        else:
            pass
    
    dist_z_sc = np.asarray(dist_z)*scale
    pitch_z_sc = np.asarray(pitch_z)*scale
    zdir = pd.DataFrame(list(zip(obj_pairs, dist_z_sc, pitch_z_sc)), columns = ['Pillar pairs', 'D3 distance ('+popup_unit+')', 'D3 pitch ('+popup_unit+')'])
    dc = 'Pillar pairs'
    return zdir, dc


def withinHexagonPilAnalysis(data, S, d_ave, scale, popup_unit, dil):
    
    hex_packing_fraction = []
    center_object = []
    hpf = np.empty(S.shape)
    
    S = S*1
    search_radius = 2*dil+d_ave*1.1
    for center in range(len(data)):
        ary = cdist(data.loc[[center],['centroid-0','centroid-1']],data[['centroid-0','centroid-1']], metric='euclidean')
        h = np.where(np.ravel(ary) < search_radius)

        if len(h[0])==7:
            h1 = np.delete(h, np.where(h[0] == center))
            ZZ = np.zeros_like(S)
            ZZ[data['centroid-0-round'][h1],data['centroid-1-round'][h1]]=1
            # ZZ = binary_dilation(ZZ,disk(3))
    
            H = convex_hull_image(ZZ, offset_coordinates=False)
            HC = np.zeros_like(H)
            center_object.append(data['Object'][center])
            for pillar in range(len(h[0])):
                HC_temp = flood(S, (data['centroid-0-round'][h[0][pillar]], data['centroid-1-round'][h[0][pillar]] ))
                HC = HC*1+HC_temp
            hex_packing_im = HC*2-H*1
            H_props = regionprops(label(H))
            HC_props = regionprops(label(hex_packing_im==-1))
            hpf = np.dstack((hpf, HC))
            packing_fraction = (H_props[0].area-HC_props[0].area)/H_props[0].area
            hex_packing_fraction.append(packing_fraction)      
        else:
            pass
    hex_packing = pd.DataFrame(list(zip(center_object, hex_packing_fraction)), columns = ['Hexagon center pillar','Hexagon packing fraction'])
    drop_col = 'Hexagon center pillar'
    
    return hex_packing, drop_col
 

def pillarAnalysis(obj):
    output_dir = fetchKeysValue('output_dir', obj)
    if output_dir:
        callfrom = 'backgroundbatch'
    else:
        callfrom = 'normalcall'
        
    analysislist = obj['analysislist']
    titile = obj['title']
        
    # db = establishConnection()
    collection = db.intialanalysisdata
    
    
    path, fname = os.path.split(obj['sampleimg'])
    fname = os.path.basename(path)
    report = collection.find_one({'sample': path})
                
    data = report['data']
    annotate_img = report['annotate_img']
    additional_data = report['additional_data']
    data = pd.read_json(data)
    
    S2 = fetchKeysValue('S2', obj)
    se = fetchKeysValue('se', obj)
    reference_image = fetchKeysValue('reference_image', obj)
    threshold_type = fetchKeysValue('threshold_type', obj)
    threshold_range = fetchKeysValue('threshold_range', obj)
    applying_ref = fetchKeysValue('applying_ref', obj)
    draw_val = obj['draw_val']
    popup_unit = obj['popup_unit']
    popup_val = int(obj['popup_val'])
    
    scale = fetchKeysValue('scale', obj)
    
    if not scale:
        scale = (popup_val/ draw_val) #*unitval
        mu_encode = b'\xce\xbcm'
        units = mu_encode.decode(encoding='UTF-8')
        if popup_unit == units: 
            scale = scale*1000
            popup_unit = 'nm'
    
    scalebar = True
    pillar_type = fetchKeysValue('pillar_type', obj)
    if not pillar_type:
        pillar_type = 'pillar_analysis_combined'
        
    img_path = obj['image_path']
    para1 = {'visualization': 'overlay_segmented', 'color': 'magenta'}
    colurs =  [{'color': 'magenta', 'val': [1, 0, 1]}, {'color': 'red', 'val': [1, 0, 0]}, {'color': 'yellow', 'val': [1, 1, 0]}]
    seg_overlay = callingVisualization('overlay_segmented', para1, rgbToGray(io.imread(img_path)), colurs, rgbToGray(io.imread(obj['sampleimg'])))
    
    foldername, _ = os.path.split(img_path)
    basefoldername = os.path.split(os.path.dirname(img_path))[0]
 
    if callfrom == 'backgroundbatch':
        output_dir = obj['output_dir']
        batchdir = output_dir
    else:
        output_dir = ''
        batchdir = basefoldername + '/batchprocessed/'
        batchdir = checkEnv(batchdir)
        if not os.path.exists(batchdir):
            os.mkdir(batchdir)
        output_dir = batchdir
        

    foldername = os.path.basename(foldername)
    newbatchpathcsv = batchdir + foldername + '_analysis.csv'
    newbatchpathcsvdes = batchdir + foldername + '_summary_analysis.csv'
    pdfpath = batchdir + foldername + '_analysis_report.pdf'
    summarypng = batchdir + foldername + '_summary_analysis.png'

    S = rgbToGray(io.imread(img_path))
    G = rgbToGray(io.imread(obj['sampleimg']))
    data['centroid-0-round'] = data['centroid-0-round'].astype('int')
    data['centroid-1-round'] = data['centroid-1-round'].astype('int')
    data['centroid-0'] = data['centroid-0'].astype('int')
    data['centroid-1'] = data['centroid-1'].astype('int')
    maindata = []
    maindata2 = []
    excel_mode = obj['excel_mode']   
    pdflist = []
    merger = PdfFileMerger()
    combined_describe = pd.DataFrame()
    collection = db.describe_analysis            
    csvslists = []
    space = ' '
    merged = pd.DataFrame()
    xdir, ydir = [], []
    csvnames = []
    for ind,i in enumerate(analysislist):
        if i == 'cd':
            if pillar_type == 'pillar2':   
                cd = data[['Object']].copy()
                cd.rename(columns={'Object':'Pillar'}, inplace = True)
                cd['Pillar'] = range(1, len(cd) + 1)
                if scalebar == True:
                    cd['Pillar CDx ('+popup_unit +')'] = (data['bbox-3']-data['bbox-1'])*scale
                    cd['Pillar CDy ('+popup_unit +')'] = (data['bbox-2']-data['bbox-0'])*scale
                else:
                    cd['Pillar CDx (px)'] = data['bbox-3']-data['bbox-1']
                    cd['Pillar CDy (px)'] = data['bbox-2']-data['bbox-0']
                drop_col = ''
            else:
                cd = data[['Object', 'CD_'+popup_unit, 'flattening']].copy()
                cd.rename(columns={'Object':'Pillar'}, inplace = True)
                cd['Pillar'] = range(1, len(cd) + 1)
                cd.rename(columns={'CD_'+popup_unit: 'Equivalent diameter ('+popup_unit+')', 'flattening': 'Ellipticity'}, inplace=True)
                cd = cd[['Pillar', 'Equivalent diameter ('+popup_unit+')', 'Ellipticity']]
                drop_col = 'Pillar'
            namedf = i     
                      
        elif i == 'xdir':
            x0,x1 = additional_data['x0'], additional_data['x1']
            cd, drop_col, namedf = XDirectionPilAnalysis(data, x0, x1, S, scale, popup_unit, additional_data['dil'], pillar_type, scalebar)
            xdir = cd
        elif i == 'ydir':
            cd, drop_col, namedf = YDirectionPilAnalysis(data, additional_data['y0'], additional_data['y1'], S, scale, popup_unit, additional_data['dil'], pillar_type, scalebar)
            ydir = cd
        elif i == 'zdir':
            cd, drop_col = ZDirectionPilAnalysis(data, additional_data['z0'], additional_data['z1'], S, scale, popup_unit, additional_data['dil'])
            namedf = 'D3_dir'
        elif i == 'xy_pg_packing':
            x0,x1 = additional_data['x0'], additional_data['x1']
            y0,y1 = additional_data['y0'], additional_data['y1']
            cd, drop_col = XYDirectionPilAnalysis(data, S, scale, x0, x1, y0, y1, popup_unit)
            namedf = 'D1D2_pg_packing'
        elif i == 'xd_pg_packing':
            x0,x1 = additional_data['x0'], additional_data['x1']
            z0,z1 = additional_data['z0'], additional_data['z1']
            cd, drop_col = XDiagonalDirectionPilAnalysis(data, S, scale, x0, x1, z0, z1, popup_unit)
            namedf = 'D1D3_pg_packing'
        elif i == 'yd_pg_packing':
            x0,x1 = additional_data['x0'], additional_data['x1']
            z0,z1 = additional_data['z0'], additional_data['z1']
            cd, drop_col = YDiagonalDirectionPilAnalysis(data, S, scale, x0, x1, z0, z1, popup_unit)
            namedf = 'D2D3_pg_packing'
            
        else:
            d_ave = additional_data['d_ave'] 
            cd, drop_col = withinHexagonPilAnalysis(data, S, d_ave, scale, popup_unit, additional_data['dil'])
            namedf = i
        if  cd.shape[0] > 0:
            cd = cd.fillna(0)
            table2 = cd.round(3)   
            if i =='cda':
                tt = cd[['Equivalent diameter ('+popup_unit+')', 'Ellipticity']]
                table1 = tt.drop(columns=[drop_col]).describe().round(3)
                table1.loc["range"] = table1.loc['max'] - table1.loc['min']
    
            else:
                if pillar_type != 'pillar2':
                    table1 = cd.drop(columns=[drop_col]).describe().round(3)
                    table1.loc["range"] = table1.loc['max'] - table1.loc['min']
                    cd_describe = table1
                else:
                    cd_describe = cd.describe().round(3)
                    table1 = cd_describe
                    
            pdflist.append(createAnalysisPDF(namedf, annotate_img, cd_describe, cd)) 
            table1 = table1.fillna(0)
            if excel_mode =='new':
                report = collection.delete_one({'sample': path})
                if os.path.exists(pdfpath):
                    os.remove(pdfpath)
                
            else:
                report = collection.find_one({'sample': path})
                if report:
                    a = pd.read_json(report['combined_describe'])
                    comb_desc = a
                    combined_describe = pd.concat([combined_describe, a], axis=1)
                    report = collection.delete_one({'sample': path})
                    try:
                        pages_to_delete = [0] # page numbering starts from 0
                        infile = PdfFileReader(pdfpath, 'rb')
                        output = PdfFileWriter()
                        
                        for k in range(infile.getNumPages()):
                            if k not in pages_to_delete:
                                p = infile.getPage(k)
                                output.addPage(p)
                        os.remove(pdfpath)
                        with open(pdfpath, 'wb') as f:
                            output.write(f)
                    except:
                        pass
            
            allmeasurementcsv = batchdir + foldername + '_' + namedf + '.csv'
            csvnames.append(i)
            cd.to_csv(allmeasurementcsv, mode= 'w', index=False)
            csvslists.append(allmeasurementcsv)
            combined_describe = pd.concat([cd_describe[cd_describe.columns[::-1]], combined_describe], axis=1)
            excel_mode = 'append'
            head = list(table1.columns)
            head2 = list(table2.columns)
            table1 = table1.to_dict()
            table2 = table2.to_dict()
            
            temp = {'heading': head, 'value': json.dumps(table1), 'heading2': head2, 'value2': json.dumps(table2) , 'analysis_type': i}
            maindata.append(temp)
        else:
            pass
            
    combined_describe = combined_describe[combined_describe.columns[::-1]]
    try:
        collection.insert_one({'sample': path, 'combined_describe': combined_describe.to_json()})
    except:
        pass
        
    pdflist.insert(0, createSummaryPDFPage(combined_describe, annotate_img, summarypng, seg_overlay))
    for i in pdflist:
        merger.append(i)
    
    if os.path.exists(pdfpath):
        merger.append(pdfpath)
        os.remove(pdfpath)
        
    temppdf= 'temp'+str(int(round(time.time() * 1000)))+'.pdf'
    merger.write(temppdf)
    merger.close()
    addPageNumberingOnPDF(temppdf, pdfpath)
    os.remove(temppdf)
       
    try: 
        [os.remove(i) for i in pdflist]
    except:
        pass
    
    if pillar_type == 'pillar2':
        xdir, ydir, xcheck, ycheck, annotateimg, c2cx_csv, c2cy_csv = center2CenterCalculation(additional_data['yc'], additional_data['xc'], additional_data['d_ave'], additional_data['dil'], data, scale, popup_unit, output_dir, foldername, scalebar, G)
        
        if reference_image:
            
            fullpath , _ = os.path.splitext(reference_image)
            refname = os.path.basename(fullpath)
            
#             fullpath , _ = os.path.splitext(reference_image)
#             refname = os.path.basename(fullpath)
            c2cxpath = output_dir + refname + '_c2cx.pkl'
            c2cypath = output_dir + refname + '_c2cy.pkl'
            if os.path.isfile(c2cxpath) and os.path.isfile(c2cypath):
                pass
            else:
                dd = [{'path': reference_image}]
                for p,i in enumerate(dd):
#                     fullpath , _ = os.path.splitext(reference_image)
#                     refname = os.path.basename(fullpath)
                    
                    if not threshold_type: 
                        threshold_type = 'std'
                    
                    if not threshold_range:
                        threshold_range = 3
                    
                    c2cx_plot, c2cy_plot, C2Cx_C2Cy_plot = center2CenterPlotsref(xdir, ydir, output_dir, refname, popup_unit, threshold_type, threshold_range, additional_data['xc'])
                        
            
            c2cx_plot, c2cy_plot, C2Cx_C2Cy_plot, c2cx_plot_norm, c2cy_plot_norm, C2Cx_C2Cy_plot_norm = center2CenterPlotsRefValidation(xdir, ydir, output_dir, foldername, popup_unit, reference_image, threshold_type, threshold_range, additional_data['xc'])
        
        else:
#             print('no reference image found')
            c2cx_plot, c2cy_plot, C2Cx_C2Cy_plot = center2CenterPlots(xdir, ydir, output_dir, foldername, popup_unit)
            
        gap_cdx_csv, gap_cdy_csv = gapCDAnalysis(G, output_dir, foldername, popup_unit, se, S, additional_data, scalebar, scale, xcheck, ycheck, S2, data)            
            
#         if reference_image:
#             if applying_ref:
#                 c2cx_plot, c2cy_plot, C2Cx_C2Cy_plot = center2CenterPlotsref(xdir, ydir, output_dir, foldername, popup_unit, threshold_type, threshold_range, additional_data['xc'])
# #                 center2CenterPlotsref(xdir, ydir, output_dir, foldername, popup_unit, threshold_type, threshold_range, additional_data['xc'])
#             else:
#                 c2cx_plot, c2cy_plot, C2Cx_C2Cy_plot, c2cx_plot_norm, c2cy_plot_norm, C2Cx_C2Cy_plot_norm = center2CenterPlotsRefValidation(xdir, ydir, output_dir, foldername, popup_unit, reference_image, threshold_type, threshold_range, additional_data['xc'])
#         else:    
#             c2cx_plot, c2cy_plot, C2Cx_C2Cy_plot = center2CenterPlots(xdir, ydir, output_dir, foldername, popup_unit)
#         gap_cdx_csv, gap_cdy_csv = gapCDAnalysis(G, output_dir, foldername, popup_unit, se, S, additional_data, scalebar, scale, xcheck, ycheck, S2, data)
        
    else:
        combined_describe.to_csv(newbatchpathcsvdes, mode= 'w', index=True)
    
    cmpltdata = {}
    othercsvs = {}
    if callfrom == 'backgroundbatch' or output_dir:
        for ind,csv in enumerate(csvslists):
#             copyFile(csv, output_dir)
            othercsvs[csvnames[ind]] = csv
        if pillar_type != 'pillar2':
#             copyFile(pdfpath, output_dir)
#             copyFile(summarypng, output_dir)
#             copyFile(newbatchpathcsvdes, output_dir)
            cmpltdata['othercsvs'] = othercsvs
    
    
    if pillar_type == 'pillar2':
        cmpltdata['pillarc2c_annotate'] = annotateimg
        cmpltdata['c2cx_csv'] = c2cx_csv
        cmpltdata['c2cy_csv'] = c2cy_csv
        cmpltdata['c2cx_plot'] = c2cx_plot
        cmpltdata['c2cy_plot'] = c2cy_plot
        cmpltdata['C2Cx_C2Cy_plot'] = C2Cx_C2Cy_plot
        cmpltdata['gap_cdx_csv'] = gap_cdx_csv
        cmpltdata['gap_cdy_csv'] = gap_cdy_csv
        try:
            os.remove(pdfpath)
        except:
            pass
        cmpltdata['excel_path'] = othercsvs['cd']
        cmpltdata['pdf_path'] = ''
    else:
        cmpltdata['excel_path'] = newbatchpathcsvdes
        cmpltdata['pdf_path'] = pdfpath

    cmpltdata ['Analysis'] = maindata
    
    return cmpltdata

def encodeImageUsingPath(newbatchpath):
    with open(newbatchpath, 'rb') as f:
        encoded_str = base64.b64encode(f.read())
        #encoded_str = 'data:image/png;base64,' + encoded_str.decode("utf-8")
    encoded_str = 'data:image/png;base64,'+encoded_str.decode('ascii')
    
    return encoded_str 

def getPillarAnalysisData(data, popup_unit, draw_val, popup_val, user_id, callfrom, output_dir):
    t_flip = fetchKeysValue('t_flip', data)
    pillar_type = fetchKeysValue('pillar_type', data)
    S2 = fetchKeysValue('S2', data)
    scale = fetchKeysValue('scale', data)
    
    
    mu_encode = b'\xce\xbcm'
    units = mu_encode.decode(encoding='UTF-8')
    if popup_unit == units: 
        scale = scale*1000
        popup_unit = 'nm'
    
    orignalpath = fetchKeysValue('orignalpath', data)
    analysislist = fetchKeysValue('analysislist', data)
    if not analysislist:
        analysislist = ['cd', 'xdir', 'ydir', 'zdir', 'hex_packing', 'xy_pg_packing', 'xd_pg_packing', 'yd_pg_packing']
    if not pillar_type:
        pillar_type = 'pillar1'
    if not scale:
        calldata = {'callfrom': callfrom, 'sample_image': data['cropimg'],
                     'image_path': data['segmented_img'],
                       'popup_unit': popup_unit, 'draw_val': draw_val, 
                       'popup_val': popup_val, 'userId': user_id, 
                       'call': 'calling from batch class', 
                       'pillar_analysis':True, 'output_dir': output_dir,
                         't_flip': t_flip, 'pillar_type':pillar_type, 
                         'orignalpath': orignalpath}
    else:
        calldata = {'callfrom': callfrom, 'sample_image': data['cropimg'],
                    'image_path': data['segmented_img'], 
                    'popup_unit': popup_unit, 'draw_val': draw_val, 
                    'popup_val': popup_val, 'userId': user_id, 
                    'call': 'calling from batch class', 
                    'pillar_analysis':True, 'output_dir': output_dir, 
                    't_flip': t_flip, 'pillar_type':pillar_type, 
                    'scale': scale, 'orignalpath': orignalpath}
        
    a_data = calculateDataforAnalysis(calldata)
    
    if pillar_type == 'pillar2':
        reference_image = fetchKeysValue('reference_image', data)
        threshold_type = fetchKeysValue('threshold_type', data)
        threshold_range = fetchKeysValue('threshold_range', data)
        applying_ref = fetchKeysValue('applying_ref', data)
        if not scale:
            calldata2 = {'callfrom': callfrom, 'data': 'calling from batch class  ', 
                         'seg_overlay': data['seg_overlay'], 
                         'sampleimg': data['cropimg'], 
                         'image_path': data['segmented_img'],
                         'excel_mode': 'new', 'analysislist': ['cd'], 
                         'draw_val': draw_val, 'popup_val': popup_val, 
                         'userId': user_id, 'popup_unit': popup_unit, 
                         'title': '', 'userId': user_id, 'output_dir': output_dir, 
                         'pillar_type':pillar_type, 'se':data['se'], 
                         'S2': S2, 'reference_image': reference_image, 
                         'threshold_type': threshold_type, 
                         'threshold_range': threshold_range, 
                         'applying_ref': applying_ref, 'orignalpath': orignalpath, 
                         'output_dir': output_dir}
        else:
            calldata2 = {'callfrom': callfrom, 'data': 'calling from batch class  ', 
                         'seg_overlay': data['seg_overlay'], 'sampleimg': data['cropimg'], 
                         'image_path': data['segmented_img'],'excel_mode': 'new', 
                         'analysislist': ['cd'], 'draw_val': draw_val, 
                         'popup_val': popup_val, 'userId': user_id, 
                         'popup_unit': popup_unit, 'title': '', 'userId': user_id, 
                         'output_dir': output_dir, 'pillar_type':pillar_type, 
                         'se':data['se'], 'scale': scale, 'S2': S2, 
                         'reference_image': reference_image, 'threshold_type': threshold_type, 
                         'threshold_range': threshold_range, 'applying_ref': applying_ref, 
                         'orignalpath': orignalpath, 'output_dir': output_dir}
    else:
        if not scale:
            calldata2 = {'callfrom': callfrom, 'data': 'calling from batch class  ', 
                         'seg_overlay': data['seg_overlay'], 
                         'sampleimg': data['cropimg'], 'image_path': data['segmented_img'],
                         'excel_mode': 'new', 'analysislist': analysislist, 
                         'draw_val': draw_val, 'popup_val': popup_val, 
                         'userId': user_id, 'popup_unit': popup_unit, 
                         'title': '', 'userId': user_id, 'output_dir': output_dir, 
                         'pillar_type':pillar_type, 'orignalpath': orignalpath}
        else:
            calldata2 = {'callfrom': callfrom, 'data': 'calling from batch class  ', 
                         'seg_overlay': data['seg_overlay'], 
                         'sampleimg': data['cropimg'], 
                         'image_path': data['segmented_img'],'excel_mode': 'new', 
                         'analysislist': analysislist, 'draw_val': draw_val, 
                         'popup_val': popup_val, 'userId': user_id, 
                         'popup_unit': popup_unit, 'title': '', 'userId': user_id, 
                         'output_dir': output_dir, 'pillar_type':pillar_type, 'scale': scale
            ,'orignalpath': orignalpath}
    

    objanalysis = pillarAnalysis(calldata2)
    analysis = objanalysis["Analysis"]                 
    annotate = encodeImageUsingPath(a_data['annotate_img'])
    excel_path = objanalysis['excel_path']
    annotated = a_data['annotate_img']
    pdf_path = objanalysis['pdf_path']
    
    if pillar_type == 'pillar2':
        c2cdata = {'c2cx_csv': objanalysis['c2cx_csv'],
                    'c2cy_csv': objanalysis['c2cy_csv'],
                    'c2cx_plot': objanalysis['c2cx_plot'], 
                    'c2cy_plot': objanalysis['c2cy_plot'],
                    'C2Cx_C2Cy_plot': objanalysis['C2Cx_C2Cy_plot'], 
                    'gap_cdx_csv': objanalysis['gap_cdx_csv'], 
                    'gap_cdy_csv': objanalysis['gap_cdy_csv']}
        return annotate, excel_path, annotated, analysis, objanalysis['pillarc2c_annotate'], c2cdata
    else:
        
        return annotate, excel_path, annotated, analysis, pdf_path, objanalysis['othercsvs']



def pillarCombined(obj):
    
    analysislist = obj['analysislist']
    title = obj['title']

    output_dir = fetchKeysValue('output_dir', obj)
    
    if output_dir:
        callfrom = 'backgroundbatch'
    else:
        callfrom = 'normalcall'
        
    
    
    popup_unit = obj['popup_unit']
    userId = obj['userId']
    scale = fetchKeysValue('scale', obj)
    draw_val = obj['draw_val']
    popup_val = float(obj['popup_val']) 
    
    if not scale:    
        scale = (popup_val/ draw_val) #*unitval
        mu_encode = b'\xce\xbcm'
        units = mu_encode.decode(encoding='UTF-8')
        if popup_unit == units: 
            scale = scale*1000
            popup_unit = 'nm'
    
    scalebar = True
        
    img_path = obj['image_path']
    
    sampleimg = obj['sampleimg']
    image_crop = io.imread(sampleimg)
    
    orignalpath = obj['orignalpath']
    junk_folder, _  = os.path.splitext(orignalpath)
    basefoldername, image_name = os.path.split(junk_folder)
    
    if not os.path.exists(junk_folder):
        os.mkdir(junk_folder)
    
    
    
    if callfrom == 'backgroundbatch':
        output_dir = obj['output_dir']
        batchdir = basefoldername + '/processed_api/'
        batchdir = checkEnv(batchdir)
        if not os.path.exists(batchdir):
            os.mkdir(batchdir)
            
        output_dir = addSlashonLastIndex(output_dir)
    else:
        
        batchdir = basefoldername + '/batchprocessed/'
        batchdir = checkEnv(batchdir)
        if not os.path.exists(batchdir):
            os.mkdir(batchdir)
            
        output_dir = batchdir
    
    prepprocesspath, seg_path, seg_overlay, t_flip = applyingPillarcombinedWf(image_crop, output_dir, image_name, junk_folder, scale, popup_unit)
    data = {'cropimg': prepprocesspath, 'segmented_img': seg_path, 
            'seg_overlay': seg_overlay, 't_flip': t_flip, 'scale': scale, 
    'analysislist':analysislist, 'title':title}
    annotate, excel_path, annotated, analysis, pdf_path, othercsvs = getPillarAnalysisData(data,
                                                                                            popup_unit, 
                                                                                            float(draw_val), 
                                                                                            float(popup_val), 
                                                                                            userId, 'pillarcombined', 
                                                                                            output_dir)
    
    
    
    temp = {"Analysis":analysis, 'annotate_img': annotated, 
            'excel_path': excel_path, 'analysis_type': 'pillar_analysis', 
            'pdf_path': pdf_path, 'othercsvs': othercsvs, 
            'prepprocesspath': prepprocesspath, 'seg_path': seg_path, 
            'seg_overlay': seg_overlay, 't_flip': t_flip}
    
    return temp

def batchpillaranalysis(data, output_dir, image_name, 
                        junk_folder, scale, popup_unit, 
                        draw_val, popup_val, orignalpath, 
                        userId, scalebarextarction):
    
    try:
        
        inputdata = {'orignalpath': orignalpath,
                      'annotate_img': '', 
                      'sampleimg': data['cropimg'], 
                      'image_path': data['segmented_img'], 
                      'analysislist': ['cd', 'xdir', 'ydir', 'zdir', 'hex_packing', 'xy_pg_packing', 'xd_pg_packing', 'yd_pg_packing'], 
                      'title': ['Critical dimensions', 'Distance and pitch between the pillars(X-dir)', 'Distance and pitch between the pillars(Y-dir)', 'Distance and pitch between the pillars (z-dir)', 'Pillar packing fraction (within hexagon)', 'Pillar packing fraction within parallelogram (X-Y dir)', 'Pillar packing fraction within parallelogram (X-Diagonal dir)', None], 
                      'draw_val': draw_val, 'popup_val': popup_val, 
                      'popup_unit': popup_unit, 'excel_mode': 'new', 
                      'pillar_analysis': True, 'output_dir': output_dir, 'userId': output_dir, 'scale': scale}
        data = pillarCombined(inputdata)
        excel_path, annotated, analysis, pdf_path, othercsvs = data['excel_path'], data['annotate_img'], data['Analysis'], data['pdf_path'], data['othercsvs']
        
        
        error = False
    except:
        excel_path, annotated, analysis, pdf_path, othercsvs = '', '', '', '', ''
        error = True
    
    notification_data = [{'ImageName': image_name, 
                          'Analysis': 'Pillar Analysis', 
                          'Applicable': True, 'Failed': error,
                            'Scale bar': scalebarextarction}]
    return notification_data


def pillarAnomalypredefinewf(image_crop, output_dir, image_name, 
                             junk_folder, pixel_size, popup_unit, 
                             ellipticity_threshold, sigma_threshold):
    
    scale = pixel_size
    if popup_unit == MICRONM: 
        scale = scale*1000
        pixel_size = scale
        popup_unit = 'nm'
    
    c_magenta = [1,0,1]
    c_yellow = [1,1,0]
    BB = shadowRemoval(image_crop) # apply shadow removal
    B1 = BB[0]
    C = image_crop
    t = threshold_otsu(B1)
    S1 = B1 >= t

    ## check if pillar intensity flip
    ST = clear_border(S1)
    metrics = ('area', 'eccentricity', 'equivalent_diameter', 'solidity')
    props = regionprops_table(label(remove_small_objects(ST, 100)), properties = metrics)
    data_prem = pd.DataFrame(props)

    t_flip = False
    if len(data_prem.loc[data_prem['eccentricity']<0.7])<5:
        S1 = S1==0
        t_flip = True

    metrics = ('area', 'centroid', 'coords', 'eccentricity', 'equivalent_diameter', 'major_axis_length', 'minor_axis_length', 'solidity')
    props = regionprops_table(label(S1), properties = metrics)
    data_prem = pd.DataFrame(props)

    #keep pillars with 'holes' by closing
    if scale>1.8:
        m = 0.5
    else:
        m = 1

    #remove holes and unnecessary small objects
    S1 = remove_small_holes(S1,np.pi*((120/scale)**2)*m)
    S1 = remove_small_objects(S1,np.pi*((100/scale)**2)/8*m)


    SC = binary_closing(S1,disk(radius=int(scale*4*m)))
    SC = remove_small_holes(SC,np.pi*((140/scale)**2)*m)
    SC = binary_opening(SC,disk(radius=int(scale*4)*m))
    SC = remove_small_objects(SC,np.pi*((100/scale)**2)/8)
    SC = clear_border(SC)
    SC = SC*1
    propsc = pd.DataFrame(regionprops_table(label(SC), properties = metrics))
    Index_label = propsc[propsc['eccentricity'] > 0.7].index.tolist()
    for rem in Index_label:
        SC = flood_fill(SC, (propsc['coords'][rem][0][0], propsc['coords'][rem][0][1]), 0, connectivity =2 )

    #smooth seg results
    S1 = binary_opening(S1,disk(radius=int(scale*8)*m)) #7 all; #3
    S1 = clear_border(S1)

    #filter pillars by eccentricity
    S2 = S1
    props = regionprops_table(label(S1), properties = metrics)
    data = pd.DataFrame(props)

    ecc_label = data[data['eccentricity'] > 0.7].index.tolist()
    for rem in ecc_label:
        S2 = S2*1
        S2 = flood_fill(S2, (data['coords'][rem][0][0], data['coords'][rem][0][1]), 0)
    data.drop(ecc_label, inplace=True)
    data.reset_index(inplace=True, drop=True)

    #filter pillars by solidity
    sol_label = data[data['solidity'] < 0.9].index.tolist()
    for rem in sol_label:
        S2 = S2*1
        S2 = flood_fill(S2, (data['coords'][rem][0][0], data['coords'][rem][0][1]), 0)
    data.drop(sol_label, inplace=True)
    data.reset_index(inplace=True, drop=True)

    # if pillar intensity flip
    if t_flip==True:    
        E = feature.canny(B1, sigma=3)
        metrics = ('area', 'centroid', 'coords', 'eccentricity', 'equivalent_diameter', 'solidity')
        props = regionprops_table(label(E), properties = metrics)
        data_prem = pd.DataFrame(props)

        Index_label = data_prem[data_prem['eccentricity'] > 0.7].index.tolist()
        E1 = E
        E1 = E1*1
        for rem in Index_label:
            E1 = flood_fill(E1, (data_prem['coords'][rem][0][0], data_prem['coords'][rem][0][1]), 0, connectivity =2 )

        data_prem.drop(Index_label, inplace=True)
        data_prem.reset_index(inplace=True, drop=True)

        E1 = clear_border(E1)
        E1 = remove_small_holes(E1,np.pi*((140/scale)**2))
        E1 = remove_small_objects(E1,np.pi*((100/scale)**2)/6)

        #combine the edge and threshold results
        props_E = regionprops_table(label(E1), properties = metrics)
        d_ave = np.mean(props_E['equivalent_diameter'])

    #     SE = S2+E1*1
    #     SE1 = binary_opening(SE==1, disk(int(d_ave/3)))
        SE1 = binary_opening(S2, disk(int(d_ave/4)))
        SE = SE1+E1
    #     SE = SE==2
    #     SE = SE+SE1

        ME = label2rgb(SE, C, colors=list([c_magenta]), alpha=0.3, bg_label=0, bg_color=None, image_alpha=1, kind='overlay')
        S2 = SE


    if t_flip == False:
        SC2 = S2
        # check if any incomplete pillars still remain and can be filled
        data = pd.DataFrame(regionprops_table(label(SC2), properties = metrics))
        data['area dev'] = abs(data['area']-data['area'].median())
        area_th = data['area'].std()*3
        Index_label = data[(data['eccentricity'] > 0.4) & (data['area dev']>area_th)].index.tolist()
        if Index_label !=[]:
            SC = SC*1
            ZC = np.zeros_like(S1)
            for rem in Index_label:
                FC = flood(SC, (data['coords'][rem][0][0], data['coords'][rem][0][1]))
                ZC = ZC + FC
            SC2 = SC2 + ZC    
            SC2 = SC2>0
        else:
            print('incomplete pillars not found')

        if np.sum(SC2*1)>len(np.ravel(SC2))*0.5:
        #     raise ValueError('Incomplete pillar segmentation.')
            propsc = pd.DataFrame(regionprops_table(label(S2), properties = metrics))
            propsc['ell'] = propsc['major_axis_length']/propsc['minor_axis_length']
            Index_label = propsc[propsc['ell'] > 1.15].index.tolist()
            for rem in Index_label:
                S2 = flood_fill(S2, (propsc['coords'][rem][0][0], propsc['coords'][rem][0][1]), 0, connectivity =2 )
        else:
            S2 = SC2
            propsc = pd.DataFrame(regionprops_table(label(S2), properties = metrics))
            propsc['ell'] = propsc['major_axis_length']/propsc['minor_axis_length']
            Index_label = propsc[propsc['eccentricity'] > 0.7].index.tolist()
            for rem in Index_label:
                S2 = flood_fill(S2, (propsc['coords'][rem][0][0], propsc['coords'][rem][0][1]), 0, connectivity =2 )

    
    imgg = img_as_ubyte(B1)
    imgg = gray2rgb(imgg)
    imgg = Image.fromarray(imgg)
    prepprocesspath = junk_folder + '/'+image_name+ '_preprocessed.png'
    imgg.save(prepprocesspath)  
    
    
    seg_path = junk_folder + '/'+image_name+ '_segmented.png'
    plt.imsave(seg_path, S2, cmap='gray')
    
    
    anomalydata = pillarAnomalyAnalysis(B1, S2, junk_folder, output_dir, image_name, pixel_size, ellipticity_threshold, sigma_threshold)
    
    return anomalydata

def get_props_rotation(box,theta_range=range(0,360,1)):

    chord_length_theta = [0]*len(theta_range)

    index = 0

    x_c1 = sum(np.where(box)[1])/len(box[box==True])
    y_c1 = sum(np.where(box)[0])/len(box[box==True])

    # rounded to nearest integer
    x_c_r1 = round(x_c1)
    y_c_r1 = round(y_c1)
    
    ellipticity = [];
        
    for theta in theta_range:
        
        box_r = rotate(box,angle=theta,resize=True,center=(y_c_r1,x_c_r1),order=0)
        
        metrics=('major_axis_length',
                 'minor_axis_length',
                 'area')
        
        props = regionprops_table(label(box_r),properties=metrics)
        
        df = pd.DataFrame(props)
        
#         ellipticity.append(df['major_axis_length'].iloc[0]/df['minor_axis_length'].iloc[0])
        
        # centroids
        x_c = sum(np.where(box_r)[1])/len(box_r[box_r==True])
        y_c = sum(np.where(box_r)[0])/len(box_r[box_r==True])

        # rounded to nearest integer
        x_c_r = round(x_c)
        y_c_r = round(y_c)
        
        line = box_r[y_c_r,x_c_r:]
        
        chord_length_theta[index] = sum(line)

        index += 1
        
    return chord_length_theta, theta_range#, ellipticity

def pillarAnomalyAnalysis(B1, S2, junk_folder, output_dir, image_name, pixel_size, ellipticity_threshold, sigma_threshold):
    
    if not ellipticity_threshold: ellipticity_threshold = 0
    if not sigma_threshold: sigma_threshold = 0
    
    if ellipticity_threshold == 0 and sigma_threshold == 0:
        ellipticity_threshold, sigma_threshold = np.inf, np.inf
    elif ellipticity_threshold == 0 and sigma_threshold != 0:
        ellipticity_threshold = np.inf
    elif ellipticity_threshold != 0 and sigma_threshold == 0:
        sigma_threshold = np.inf
    
    ## Hyung's code addition for measuring pillar anomaly
    scale = pixel_size
    
    imgg = img_as_ubyte(B1)
    imgg = gray2rgb(imgg)
    
    # make a copy of the original grayscale image for anomaly analysis
    G = imgg.copy()
    
    ## Column names for building dataframe
    column_names = ['Image #',
                    'Pillar #',
                    'bbox-0',
                    'bbox-1',
                    'bbox-2',
                    'bbox-3',
                    'centroid-0',
                    'centroid-1',
                    'area',
                    'eccentricity',
                    'major_axis_length',
                    'minor_axis_length',
                    'orientation',
                    'Ellipticity',
                    'Sigma']
    
    # Initiate dataframe with above columns
    df_master = pd.DataFrame(columns=column_names)

    ## Reassign the segmented image
    S = S2

    ## Metrics to be measured using regionprops
    metrics=('bbox',
             'centroid',
             'area',
             'eccentricity',
             'orientation',
             'major_axis_length',
             'minor_axis_length')

    props = regionprops_table(label(S),properties=metrics)

    df = pd.DataFrame(props)   

    ## Create empty variables that will be measured
    ellipticity_mean = [];
    sigma = [];
    
    for index2 in range(0,len(df)):

        ## Isolate bounding boxes of each pillar object
        box = S[df['bbox-0'].iloc[index2]:df['bbox-2'].iloc[index2],
                df['bbox-1'].iloc[index2]:df['bbox-3'].iloc[index2]]

        box = pad(box,pad_width=1,
                  mode='constant',
                  constant_values=0)

        ## Find the largest object to get rid of neighboring pillars
        rp = regionprops(label(box))
        size = max([i.area for i in rp])

        ## Remove the neighboring pillars
        box = remove_small_objects(label(box), min_size=size-1)
        box = box>0

        ## Call function to calculate sigma values for each pillar
        chord_length_theta, theta_range = get_props_rotation(box)

#         ellipticity_mean.append(np.mean(ellipticity))   

        props = regionprops(label(box))
        props = props[0]

        a = (props.major_axis_length*scale*0.5)
        b = (props.minor_axis_length*scale*0.5)

        ## Calculate radial distance of the ideal ellipse fit
        analytical_CLD = [np.sqrt (((a**2)*(b**2)) / ((b**2)*((np.sin(np.radians(x)))**2) + (a**2)*((np.cos(np.radians(x)))**2))) for x in range(0,360)+np.degrees(props.orientation)]

        ## Calculate deviance of actual object to idealfit ellipse
        actual = [i*scale for i in chord_length_theta]
        diff = [actual[i]-analytical_CLD[i] for i in range(0,len(actual))]

        ## Store the standard deviation of deviance as sigma
        sigma.append(np.std(diff))
        
        del actual
        del diff
        
    ## Save measurements in .csv file
    df['Image #'] = [image_name]*len(df)
    df['Pillar #'] = list(range(1,len(df)+1))
    df['Sigma'] = sigma
    df['Ellipticity'] = df['major_axis_length']/df['minor_axis_length']
    df_save = df[['Image #', 'Pillar #','Ellipticity','Sigma']]
    full_dataframe = output_dir+'/'+image_name+'_full_dataframe.csv'
    df_save.to_csv(full_dataframe,index=False)

    ## Save annotated image with numbered pillars
    fig, ax = plt.subplots(figsize=(10, 10)); 
    ax.imshow(S, cmap='gray'); 
    ax.axis('off')
    for index1 in range(len(df)):
        ax.text(df['centroid-1'][index1],df['centroid-0'][index1], str(index1+1), color='k')
    
    
    annotated_img = output_dir+'/'+image_name+'_pillars_numbers.png'
    fig.savefig( annotated_img ,bbox_inches="tight")
    plt.close(fig)
    
    ## Plot and save ellipticity histogram
    fig,ax=plt.subplots(figsize=(5,5));
    ax.hist(df['Ellipticity'],bins=25,edgecolor='black');
    ax.set_xlabel('Ellipticity', fontsize=20);
    ax.set_ylabel('# of Pillars', fontsize=20);
    ax.tick_params(axis='both', which='major', labelsize=12)
    
    ellipticity_hist = output_dir+'/'+image_name+'_ellipticity_hist.png'
    fig.savefig( ellipticity_hist, bbox_inches="tight")
    plt.close(fig)

    ## Plot and save sigma histogram
    fig,ax=plt.subplots(figsize=(5,5));
    ax.hist(df['Sigma'],bins=25,edgecolor='black');
    ax.set_xlabel('Sigma', fontsize=20);
    ax.set_ylabel('# of Pillars', fontsize=20);
    ax.tick_params(axis='both', which='major', labelsize=12)
    
    
    sigma_hist = output_dir+'/'+image_name+'_sigma_hist.png'
    fig.savefig(sigma_hist, bbox_inches="tight")
    plt.close(fig)

    ## Plt and save ellipticity vs. sigma scatter plot
    fig,ax=plt.subplots(figsize=(5,5));
    ax.scatter(df['Ellipticity'],df['Sigma'])
    ax.set_xlabel('Ellipticity', fontsize=20);
    ax.set_ylabel('Sigma (nm)', fontsize=20);
    ax.tick_params(axis='both', which='major', labelsize=12)
    
    
    ellipticity_sigma_scatter = output_dir+'/'+image_name+'_ellipticity_sigma_scatter.png'
    fig.savefig( ellipticity_sigma_scatter,bbox_inches="tight")
    plt.close(fig)
    
    ## Plotting and saving annotated image of identified anomalies
    MA = label2rgb(S, G,
                   colors=list([(1, 0 ,1)]),
                   alpha=0.3, bg_label=0,
                   bg_color=None, image_alpha=1,
                   kind='overlay')

    fig, ax = plt.subplots(frameon=False,figsize=(10,10))
    ax.imshow(MA, cmap = 'gray')

    ## Annotate each of the pillars with ellipticity and sigma values
    for index3 in range(0,len(df)):
        
        if len(df)<=20:
            fontsize='large'
        elif len(df)>20 and len(df)<=100:
            fontsize='small'
        elif len(df)>100:
            fontsize='x-small'
        
        ax.text(df['centroid-1'][index3],
                df['centroid-0'][index3],
                'e=' + str(np.round(df['Ellipticity'][index3],2)),
                horizontalalignment='center',
                verticalalignment='bottom',
                color = 'w',
                fontsize=fontsize,
                fontweight='bold')

        ax.text(df['centroid-1'][index3],
                df['centroid-0'][index3],
                's=' + str(np.round(df['Sigma'][index3],2)),
                horizontalalignment='center',
                verticalalignment='top',
                color = 'w',
                fontsize=fontsize,
                fontweight='bold')
        
        if isinstance(ellipticity_threshold,float)==False:
            ellipticity_threshold=float(ellipticity_threshold)
        
        if isinstance(sigma_threshold,float)==False:
            sigma_threshold=float(sigma_threshold)
        
        if (df['Ellipticity'].iloc[index3] >= ellipticity_threshold) or (df['Sigma'].iloc[index3] >= sigma_threshold): 
            rect = mpatches.Rectangle((df['bbox-1'].iloc[index3],df['bbox-0'].iloc[index3]),
                              df['bbox-3'].iloc[index3]-df['bbox-1'].iloc[index3],
                              df['bbox-2'].iloc[index3]-df['bbox-0'].iloc[index3],
                              edgecolor='r',
                              linewidth=1,
                              facecolor="none")
            ax.add_patch(rect)

    ax.axis('off')
    
    identify_anomalies = output_dir+'/'+image_name+'_identify_anomalies.png'
    fig.savefig( identify_anomalies,bbox_inches="tight")
    plt.close(fig)
    
    ## Saving original and segmented images of pillar anomalies
    ## Separate the dataframes and save them also
    columns = ['Image #',
               'Pillar #',
               'area',
               'bbox-0',
               'bbox-1',
               'bbox-2',
               'bbox-3',
               'centroid-0',
               'centroid-1',
               'eccentricity',
               'major_axis_length',
               'minor_axis_length',
               'orientation',
               'Ellipticity',
               'Sigma']
    
    df_normal = pd.DataFrame(columns=columns)
    df_anomaly = pd.DataFrame(columns=columns)
    
    for index4 in range(len(df)):

        if (df['Ellipticity'].iloc[index4] >= ellipticity_threshold) or (df['Sigma'].iloc[index4] >= sigma_threshold): 

            box = S[df['bbox-0'].iloc[index4]:df['bbox-2'].iloc[index4],
                  df['bbox-1'].iloc[index4]:df['bbox-3'].iloc[index4]]

            box = pad(box,pad_width=1,
                      mode='constant',
                      constant_values=0)

            # labelled = measure.label(box)
            rp = regionprops(label(box))

            # get size of largest cluster
            size = max([i.area for i in rp])

            # remove everything smaller than largest
            box = remove_small_objects(label(box), min_size=size-1)

            box_raw = G[df['bbox-0'].iloc[index4]:df['bbox-2'].iloc[index4],
                          df['bbox-1'].iloc[index4]:df['bbox-3'].iloc[index4]]

            fig, ax = plt.subplots(1,2,figsize=(10,5))
            ax[0].imshow(box_raw,cmap='gray');
            ax[0].axis('off');
            ax[1].imshow(box,cmap='gray');
            ax[1].axis('off');

            fig.savefig(output_dir+'/'+image_name+'_'+str(df['Pillar #'].iloc[index4])+'_individual_anomaly.png',
                        bbox_inches="tight")
            plt.close(fig)
            
            df_anomaly = df_anomaly.append(df.iloc[index4])
    
    df_anomaly = df_anomaly[columns]
    
    pillar_anomalies_dataframe = output_dir+'/'+image_name+'_pillar_anomalies_dataframe.csv'
    df_anomaly.to_csv(pillar_anomalies_dataframe, index=False)
    
    df_normal = df.append(df_anomaly)
    df_normal.drop_duplicates(keep=False,inplace=True)
    
    df_normal = df_normal[columns]
    
    normal_pillars_dataframe = output_dir+'/'+image_name+'_normal_pillars_dataframe.csv'
    df_normal.to_csv(normal_pillars_dataframe, index=False)
    
    data = {
    'full_dataframe': full_dataframe,
    'annotate_img': annotated_img,
    'ellipticity_hist': ellipticity_hist,
    'sigma_hist': sigma_hist,
    'ellipticity_sigma_scatter': ellipticity_sigma_scatter,
    'identify_anomalies': identify_anomalies,
    'pillar_anomalies_dataframe': pillar_anomalies_dataframe,
    'normal_pillars_dataframe': normal_pillars_dataframe
    }
    
    return data   

def batchpillaranomalyanalysis(image_crop, output_dir, image_name, junk_folder, 
                               scale, popup_unit, ellipticity_threshold,
                               sigma_threshold, scalebarextarction):
    error = False
    try:
        data = pillarAnomalypredefinewf(image_crop, output_dir, image_name, 
                                        junk_folder, scale, popup_unit, ellipticity_threshold,
                                        sigma_threshold)
        anomaly = [{'analysis_type': 'pillar_anomaly', 'annotate_img': data['annotate_img']}]
    except:
        error = True
        anomaly = []
    # notification_data = [{'ImageName': image_name, 'Analysis': 'Pillar Anomaly', 'Applicable': True, 'Failed': error, 'Scale bar': scalebarextarction}]
    notification_data = [{'ImageName': image_name, 
                          'Analysis': 'Pillar Anomaly', 
                          'Failed': error, 'Scale bar': scalebarextarction}]

    return anomaly, notification_data

def profileOutlineAnalysis(S, path, batchdir, foldername, output_dir, scale, G, callfrom):
    B = find_boundaries(label(S), connectivity=1, mode='thin', background=0)
    # export backend
    i,j = np.nonzero(B)
    df2 = pd.DataFrame(j, columns=["x_img"])
    df2['y_img'] = i
    y_dim = S.shape[0]-1
    df2['x'] = df2['x_img']
    df2['y'] = y_dim-df2['y_img']
    df2['x_normalized'] = (df2['x']-np.min(df2['x']))/np.max(df2['x'])
    df2['y_normalized'] = (df2['y']-np.min(df2['y']))/np.max(df2['y'])
    df2['x_scale'] = df2['x']*scale
    df2['y_scale'] = df2['y']*scale
    df2['x_scale_zeroed'] = df2['x_scale']-np.min(df2['x_scale'])
    df2['y_scale_zeroed'] = df2['y_scale']-np.min(df2['y_scale'])
    annotateimg = path + '/outline'+'_'+str(int(round(time.time() * 1000)))+'.png' 
    binaryimg = img_as_ubyte(B)
    binaryimg = gray2rgb(binaryimg)
    binaryimg = Image.fromarray(binaryimg)
    binaryimg.save(annotateimg)
    
    S1 = S==0
    S1 = binary_opening(S1,disk(5))
    metrics = ('area', 'centroid', 'coords', 'bbox', 'equivalent_diameter', 'major_axis_length', 'minor_axis_length', 'solidity')
    props = regionprops_table(label(S1, connectivity=2), properties = metrics)
    ds = pd.DataFrame(props)
    yc = ds.loc[0,'bbox-2']
    S1[0:int(yc*0.8),:] = 0
    
    D = np.zeros_like(S)
    props_d = regionprops_table(label(S1, connectivity=2), properties = metrics)
    dv = pd.DataFrame(props_d)
    dv['centroid-0'] = dv['centroid-0'].astype(int)
    dv['centroid-1'] = dv['centroid-1'].astype(int)
    D[:,dv['centroid-1']] = 1
    
    SD = S-D*1
    SD = (SD>0)*1
    MS = np.zeros_like(S)
    MS[:,1:-1] = 1
    SD = clear_border(SD, mask=MS.astype(bool))
    
    props_x = regionprops_table(label(SD, connectivity=2), properties = metrics)
    data_x = pd.DataFrame(props_x)
    data_x['centroid-0'] = data_x['centroid-0'].astype(int)
    data_x['centroid-1'] = data_x['centroid-1'].astype(int)
    #data_x.drop(data_x[data_x['area'] < np.mean(data_x['area'])-np.std(data_x['area'])*1].index, inplace = True) 
    data_x.drop(data_x[data_x['area'] < np.mean(data_x['area'])/2].index, inplace = True)
    data_x.index = range(len(data_x))
    data_x.sort_values(by=['bbox-1'], ignore_index=True, inplace=True)
    data_x['Object'] = range(1, len(data_x) + 1)
    
    x_spacing = []
    for feat in range(len(data_x)):
        clx = np.count_nonzero(np.asarray(SD[data_x['bbox-0'][feat]:data_x['bbox-2'][feat],data_x['bbox-1'][feat]:data_x['bbox-3'][feat]]), axis=1)
        x_spacing.append(list(clx))

    
    df_t = pd.DataFrame(x_spacing)
    df_t.index = np.arange(1, len(df_t) + 1)
    df_t.index.names = ['height']
    df_t = df_t.T
    df_scale = df_t.multiply(scale)
    df_scale.index = np.arange(1, len(df_scale) + 1)*scale
    #df_scale = df_scale.columns.name = 'height '
    #df_t = df_t.columns.name = 'height '

#    newbatchpath = batchdir + foldername + 'feature_outline_output.xlsx'
#    with pd.ExcelWriter(newbatchpath, engine="xlsxwriter") as writer:  # doctest: +SKIP
#        df2[['x','y','x_normalized','y_normalized','x_scale','y_scale','x_scale_zeroed','y_scale_zeroed']].to_excel(writer, sheet_name='outline_coords') 
#        df_scale.to_excel(writer, sheet_name='Feature thickness scaled')
#        df_t.to_excel(writer, sheet_name='Feature thickness pixels')
     
    thickness_csv =  batchdir + foldername + '_feature_thickness.csv'
    with open(thickness_csv,'w') as fd:
        fd.write('Feature thickness scaled \n')
    df_scale.to_csv(thickness_csv, mode='a', index=True, header=True)
    table2 = df_scale.to_dict()
    with open(thickness_csv,'a') as fd:
        fd.write('Feature thickness pixels \n')
    df_t.to_csv(thickness_csv, mode='a', index=True, header=True)
        
    outline_csv = batchdir + foldername + '_feature_outline.csv'
    df2[['x','y','x_normalized','y_normalized','x_scale','y_scale','x_scale_zeroed','y_scale_zeroed']].to_csv(outline_csv, index=False, header=True)  
                            
    table1 = df_t.to_dict() #df[['x','y','x_normalized','y_normalized','x_scale','y_scale','x_scale_zeroed','y_scale_zeroed']].to_dict()
    
    annotateimg2 = path + '/outline_annotated'+'_'+str(int(round(time.time() * 1000)))+'.png' 
    
    c_magenta = [1,0,1]
    M2 = label2rgb(SD, image=G, colors=list([c_magenta]), alpha=0.3, bg_label=0, bg_color=None, image_alpha=1, kind='overlay')
    
    fig, ax = plt.subplots(figsize=(10,10))
    ax.imshow(M2, cmap='gray')
    for obj in range(len(data_x)):
        ax.text(data_x['centroid-1'][obj], data_x['centroid-0'][obj], str(data_x['Object'][obj]), horizontalalignment='center', verticalalignment='center', color = 'y', fontsize='large', fontweight='bold')      
        
    ax.axis('off') 
    fig.savefig(annotateimg2, dpi=100, bbox_inches='tight', pad_inches=0) # save image as ""<img_name>_annotated"
    plt.close(fig)

    newbatchpath1 = batchdir + foldername + '_feature_outline.png'
    newbatchpath2 = batchdir + foldername + '_feature_outline_annotated.png'
    
    if callfrom == 'backgroundbatch' and output_dir:
        shutil.copyfile(annotateimg2, newbatchpath2)
        shutil.copyfile(annotateimg, newbatchpath1)
        outbatchpath1 = output_dir + foldername + '_feature_outline.png'
        shutil.copyfile(annotateimg, outbatchpath1)
        outbatchpath1 = output_dir + foldername + '_feature_outline_annotated.png'
        shutil.copyfile(annotateimg2, outbatchpath1)
        outbatchpath3 = output_dir + foldername +  '_feature_thickness.csv'
        shutil.copyfile(thickness_csv, outbatchpath3)
        outbatchpath4 = output_dir + foldername +  '_feature_outline.csv'
        shutil.copyfile(outline_csv, outbatchpath4)                   
    else:
        shutil.copyfile(annotateimg2, newbatchpath2)
        shutil.copyfile(annotateimg, newbatchpath1)   
        
    return table1, thickness_csv, outline_csv, annotateimg2, annotateimg, table2

def profileThicknessAnalysis(additional_data, data, S, batchdir, foldername, G, path, output_dir, scale, callfrom):
    xc = np.array(additional_data['xc'])
    x0 = additional_data['x0']
    ddx = cdist(xc,xc)
    ddx = ddx[np.triu_indices(ddx.shape[0], k = 1)]+1e-9
    (n, binedges) = np.histogram(ddx, bins=np.arange(ddx.min(), ddx.max(), 5))
    bincenters = np.mean(np.vstack([binedges[0:-1],binedges[1:]]), axis=0)
    # counts = np.vstack((n,bincenters))
    counts = np.column_stack((n,bincenters))
    counts[0,0] = counts[0,0] + counts[-1,0]
    counts_order = counts[np.argsort(counts[:, 0])]
    counts_order = counts_order[::-1][:counts_order.shape[0]]
    spac = counts_order[:,1]
    x1 = int(spac[0])
    data['centroid-0'] = data['centroid-0'].astype(int)
    data['centroid-1'] = data['centroid-1'].astype(int)
    
    data_x = data.copy()
    
    data_x['c0-x'] = data_x['centroid-0'] - x0
    data_x['c1-x'] = data_x['centroid-1'] - x1
    data_x.drop(data_x[data_x['c0-x'] >= S.shape[0]].index, inplace = True) 
    data_x.drop(data_x[data_x['c1-x'] >= S.shape[1]].index, inplace = True) 
    data_x.drop(data_x[data_x['c0-x'] < 0].index, inplace = True) 
    data_x.drop(data_x[data_x['c1-x'] < 0].index, inplace = True)
    data_x.index = range(len(data_x))
    
    
    metrics_p = ('area', 'centroid', 'bbox')
    pairs_x = np.empty(S.shape)
    pairs_neg = np.empty(S.shape)
    features = np.zeros_like(S)
    dist_x = []
    pitch_x = []
    obj_pairs = []
    x_spacing = []
    data_x['c0-x'] = data_x['c0-x'].astype(int)
    data_x['c1-x'] = data_x['c1-x'].astype(int)
    for circle in range(len(data_x)):       
        c_orig = flood(S, (data_x['centroid-0'][circle], data_x['centroid-1'][circle]))
        cx = flood(S, (data_x['c0-x'][circle], data_x['c1-x'][circle]))
        pairs = c_orig+cx
        c_labels = label(pairs, background=None, return_num=True)
        if c_labels[1]==2:
            pair_rp = regionprops_table(label(pairs),properties = metrics_p)
            pair_rp['centroid-0'] = pair_rp['centroid-0'].astype(int)
            pair_rp['centroid-1'] = pair_rp['centroid-1'].astype(int)
            ZR = np.zeros_like(S)
            ZR[pair_rp['bbox-0'].max():pair_rp['bbox-2'].min(),pair_rp['centroid-1'].astype(int).min():pair_rp['centroid-1'].astype(int).max()] = 1
            DFF = ZR-pairs*1
            neg_s = DFF == 1
            neg_s = remove_small_objects(neg_s,20)
    #         pairs_neg = np.dstack((pairs_neg, neg_s))
            features = features + neg_s*1
            
            clx = np.count_nonzero(np.asarray(neg_s[pair_rp['bbox-0'].max():pair_rp['bbox-2'].min(),pair_rp['centroid-1'].astype(int).min():pair_rp['centroid-1'].astype(int).max()]), axis=1)
            x_spacing.append(list(clx)) 
        else:
            pass
    
    df = pd.DataFrame(x_spacing)
    df = df.T
    df.index = np.arange(1, len(df) + 1)
    df.index.names = ['height']
    df_scale = df.multiply(scale)
    df_scale.index = np.arange(1, len(df_scale) + 1)*scale
    
    table1 = df.to_dict()
    table2 = df_scale.to_dict()
    
    metrics = ('area', 'bbox', 'centroid', 'coords', 'eccentricity', 'equivalent_diameter', 'major_axis_length', 'minor_axis_length', 'solidity')
    features_props = regionprops_table(label(features, connectivity=2), properties = metrics)
    features_data = pd.DataFrame(features_props)
    # sort from left to right
    features_data.sort_values(by=['bbox-1'], axis=0, ascending=True, inplace=True, kind='quicksort', na_position='last', ignore_index=True)
    features_data['Object'] = range(1, len(features_data) + 1)
    c_magenta = [1,0,1]
    M1 = mark_boundaries(G, features, color=c_magenta, outline_color=None, mode='thick', background_label=0)
    M2 = label2rgb(features, image=G, colors=list([c_magenta]), alpha=0.3, bg_label=0, bg_color=None, image_alpha=1, kind='overlay')
    
    annotateimg = path + '/annotate'+'_'+str(int(round(time.time() * 1000)))+'.png'
    len_mod = 1.5
    len_mod_ax = len_mod*0.8
    fig, ax = plt.subplots(figsize=(10,10))
    ax.imshow(M2, cmap='gray')
    
    for obj in range(len(features_data)):
        ax.text(features_data['centroid-1'][obj], features_data['centroid-0'][obj], str(features_data['Object'][obj]), horizontalalignment='center', verticalalignment='center', color = 'y', fontsize='large', fontweight='bold')
    
    ax.axis('off') 
    fig.savefig(annotateimg, dpi=100, bbox_inches='tight', pad_inches=0) # save image as ""<img_name>_annotated"
    plt.close(fig)
    
    # results from Trace boundaries
    B = find_boundaries(label(features), connectivity=1, mode='thin', background=0)
    # export backend
    i,j = np.nonzero(B)
    # i = np.unravel_index(nz*1,S.shape)
    df2 = pd.DataFrame(j, columns=["x_img"])
    df2['y_img'] = i
    y_dim = S.shape[0]-1
    df2['x'] = df2['x_img']
    df2['y'] = y_dim-df2['y_img']
    df2['x_normalized'] = (df2['x']-np.min(df2['x']))/np.max(df2['x'])
    df2['y_normalized'] = (df2['y']-np.min(df2['y']))/np.max(df2['y'])
    df2['x_scale'] = df2['x']*scale
    df2['y_scale'] = df2['y']*scale
    df2['x_scale_zeroed'] = df2['x_scale']-np.min(df2['x_scale'])
    df2['y_scale_zeroed'] = df2['y_scale']-np.min(df2['y_scale'])
    
    
    
    #df_scale.columns.name = 'height '
    #df.columns.name = 'height'
    thickness_csv =  batchdir + foldername + '_feature_thickness.csv'
    with open(thickness_csv,'w') as fd:
        fd.write('Feature thickness scaled \n')
    df_scale.to_csv(thickness_csv, mode='a', index=True, header=True)
    
    with open(thickness_csv,'a') as fd:
        fd.write('Feature thickness pixels \n')
    df.to_csv(thickness_csv, mode='a', index=True, header=True)
        
    outline_csv = batchdir + foldername + '_feature_outline.csv'
    df2[['x','y','x_normalized','y_normalized','x_scale','y_scale','x_scale_zeroed','y_scale_zeroed']].to_csv(outline_csv, index=False, header=True)
    
    
    annotateimg2 = path + '/thick_outline'+'_'+str(int(round(time.time() * 1000)))+'.png'
    plt.imsave(annotateimg2,B, cmap ='gray')
    newbatchpath1 = batchdir + foldername + '_feature_thickness_annotated.png'
    newbatchpath2 = batchdir + foldername + '_feature_thickness_outline.png'
    if callfrom == 'backgroundbatch' and output_dir:
        shutil.copyfile(annotateimg, newbatchpath1)
        outbatchpath1 = output_dir + foldername + '_feature_thickness_annotated.png'
        shutil.copyfile(annotateimg, outbatchpath1)
        outbatchpath2 = output_dir + foldername + '_feature_thickness_outline.png'
        shutil.copyfile(annotateimg2, outbatchpath2)
        outbatchpath3 = output_dir + foldername +  '_feature_thickness.csv'
        shutil.copyfile(thickness_csv, outbatchpath3)
        outbatchpath4 = output_dir + foldername +  '_feature_outline.csv'
        shutil.copyfile(outline_csv, outbatchpath4)
            
    else:
        shutil.copyfile(annotateimg, newbatchpath1)
        shutil.copyfile(annotateimg2, newbatchpath2) 
                           
    df_scale.index = df_scale.index.to_series().apply(lambda x: np.round(x,2))
    df = df.round(2)
    df_scale = df_scale.round(2)
    
    return table1, thickness_csv, outline_csv, annotateimg, annotateimg2, table2

def featureProfileAnalysis(obj):
    analysislist = obj['analysislist']
    try:
        callfrom = obj['callfrom']
        batch = obj['batch']

    except:
        callfrom = 'normalcall'
        batch = False
        
    # db = establishConnection()
    collection = db.intialanalysisdata
    
    path, fname = os.path.split(obj['sampleimg'])
    #fname, _ = os.path.splitext(fname)
    fname = os.path.basename(path)
    report = collection.find_one(
                {'sample': path},
                sort=[( '_id', pymongo.DESCENDING )]
                )
          
    data_key = 'data'
    path, fname = os.path.split(obj['image_path'])
    data = report['profile_data']
    additional_data = report['additional_data']
    data = pd.read_json(data)
    draw_val = obj['draw_val']
    popup_val = int(obj['popup_val'])
    scale = (popup_val/ draw_val)  #*unitval
    
    img_path = obj['image_path']
    
    foldername, _ = os.path.split(img_path)
    #basefoldername = os.path.basename(os.path.basename(foldername))
    
    basefoldername = os.path.split(os.path.dirname(img_path))[0]

    if callfrom == 'backgroundbatch':
        output_dir = obj['output_dir']
        batchdir = basefoldername + '/processed_api/'
        batchdir = checkEnv(batchdir)
        if not os.path.exists(batchdir):
            os.mkdir(batchdir)
    else:
        output_dir = ''
        batchdir = basefoldername + '/batchprocessed/'
        batchdir = checkEnv(batchdir)
        if not os.path.exists(batchdir):
            os.mkdir(batchdir)

    foldername = os.path.basename(foldername)
    cmpltdata = []
    S = rgb2gray(io.imread(img_path))
    G = rgb2gray(io.imread(obj['sampleimg']))
    
    metrics = ('area', 'centroid', 'coords', 'eccentricity', 'equivalent_diameter', 'major_axis_length', 'minor_axis_length', 'solidity')
    error = False
    for ind in  analysislist:
        try:
            
            if ind == 'fpt':
                table1, thickpath, outline_path, thickimg, outlineimg, table2 = profileThicknessAnalysis(additional_data, data, S, batchdir, foldername, G, path,output_dir, scale, callfrom)
            else:
                table1, thickpath, outline_path, thickimg, outlineimg, table2 = profileOutlineAnalysis(S, path, batchdir, foldername, output_dir, scale, G, callfrom) 
                thickimg = outlineimg
            
            if batch:
                data = {'Feature_thickness_pixels': json.dumps(table1), 'analysis_type': ind, 'Feature_thickness_scaled': json.dumps(table2),'Analysis': ind, 'csv_thickness':thickpath, 'csv_outline': outline_path, 'annotate_img':thickimg}
            else:
                data = { 'analysis_type': ind, 'csv_thickness':thickpath, 'csv_outline': outline_path, 'annotate_img':thickimg}
                
            cmpltdata.append(data)
        except:
            error = True
            traceback.print_exc()
            
        
    fulldata = {'Analysis': cmpltdata,  'error': error}
    return fulldata

def getProfileAnalysisData(data, popup_unit, draw_val, popup_val, user_id, both, callfrom, feature_profile_type, output_dir, error, scalebarextarction, image_name):
    
    error = False
    try:
        if not both:
            calldata = {'callfrom': callfrom, 'sample_image': data['cropimg'], 
                        'image_path': data['segmented_img'], 
                        'popup_unit': popup_unit, 'draw_val': draw_val,
                          'popup_val': popup_val, 'userId': user_id, 
                          'call': 'calling from batch class', 
                          'pillar_analysis': False, 'output_dir': output_dir, 
                          'orignalpath': data['orignalpath']}

        a_data = calculateDataforAnalysis(calldata)

        calldata2 = {'callfrom': callfrom, 'batch': True, 
                     'sampleimg': data['cropimg'], 
                     'image_path': data['segmented_img'], 
                     'analysislist': feature_profile_type, 
                     'title': ['Thickness', 'Outline'], 
                     'draw_val': draw_val, 'popup_val': popup_val, 
                     'popup_unit': popup_unit, 'excel_mode': 'new',
                       'pillar_analysis': False, 'userId': user_id, 
                       'output_dir': output_dir, 'orignalpath': data['orignalpath']}


        object = featureProfileAnalysis(calldata2)
        error = object['error']
#         objanalysis = object
    except:
#         traceback.print_exc()
        error = True
    
    # notification_data = [{'ImageName': image_name, 'Analysis': 'Feature Profile', 'Applicable': True, 'Failed': error, 'Scale bar': scalebarextarction}]
    notification_data = [{'ImageName': image_name, 'Analysis': 'Feature Profile', 'Failed': error, 'Scale bar': scalebarextarction}]

#     objanalysis = objanalysis['Analysis']
    return None, None, None, None, notification_data 

def flood_overlap(obj, img):
    V = obj*1 + img*1
    R = obj*1
    overlap = V==2
    metrics = ('area', 'centroid', 'coords')
    props = pd.DataFrame(regionprops_table(label(overlap), properties = metrics))
    for feat in range(len(props)):
        R = flood_fill(R, (props['coords'][feat][0][0], props['coords'][feat][0][1]), 2)
    return R

def check_threshold_tier(img, scale, popup_unit):
    global APPLICABLE

    f = int(2/scale)
    if f<0:
        f=0
    t = threshold_otsu(img)
    S1 = img>t
    S2 = S1==0
    if f>=20:
        f = 12
    S1 = binary_opening(S1,disk(f))
    S2 = binary_opening(S2,disk(f))
    # S1 = clear_border(S1)
    target_w = 250/scale
    metrics = ('area', 'bbox', 'coords', 'solidity', 'centroid')
    prop_s1 = pd.DataFrame(regionprops_table(label(S1),properties = metrics))
    prop_s1['width'] = prop_s1['bbox-3']-prop_s1['bbox-1']
    s1_ind = prop_s1[(prop_s1['solidity'] > 0.9) & (prop_s1['width']>target_w*0.6)].index.tolist()

    prop_s2 = pd.DataFrame(regionprops_table(label(S2),properties = metrics))
    prop_s2['width'] = prop_s2['bbox-3']-prop_s2['bbox-1']
    s2_ind = prop_s2[(prop_s2['solidity'] > 0.9) & (prop_s2['width']>target_w*0.6)].index.tolist()

    
    
    if len(s1_ind)>len(s2_ind):
        SS = S1
        tiers_dark = False
        if len(s1_ind)==0:
            APPLICABLE = False
            raise Exception
#             raise ValueError('Incorrect segmentation S1')
        
    else:
        SS = S2
        tiers_dark = True
        if len(s2_ind)==0 and popup_unit == 'px':
            MS = np.zeros_like(SS)
            MS[1:-1,:] = 1
            SS = clear_border(SS, mask=MS.astype(bool))
#             raise ValueError('Incorrect segmentation S2')
    
    return SS, tiers_dark

def tierVoidChechking(G, S, img_path, batchdir, foldername, scale, popup_unit, callfrom, output_dir):
    f = int(4/scale)
    if f<0:
        f=0
    
    if scale:
        scalebar = True
    else:
        scalebar = False
        
    #G = gaussian(G,0.5)
    B = S
    
    f = int(4/scale)
    if f>=20:
        f = 12
    S, tiers_dark = check_threshold_tier(S, scale, 'nm')
    
    MK = np.zeros_like(S)
    MK[1:-1,:] = 1
    
    # remove objects touching upper and lower frames
    S = clear_border(S, mask=MK.astype(bool))
    S = remove_small_objects(S, min_size=100, connectivity=1)
    
    metrics = ('area', 'centroid', 'coords', 'eccentricity', 'equivalent_diameter', 'major_axis_length', 'minor_axis_length', 'solidity')
    data = pd.DataFrame(regionprops_table(label(S), properties = metrics))
    block_sz = np.mean(data['area'])/10
    
    S = remove_small_holes(S==1,block_sz*4) # relate to image, condition
    S = remove_small_objects(S==1,block_sz) # relate to image, condition
    
    # #check uniformity of segmented objects
    SC2 = binary_dilation(S>0, disk(f+1))
    metrics = ('area', 'bbox', 'coords', 'solidity', 'centroid')
    prop_s = pd.DataFrame(regionprops_table(label(SC2),properties = metrics))
    prop_s['width'] = prop_s['bbox-3']-prop_s['bbox-1']
    prop_s['height'] = prop_s['bbox-2']-prop_s['bbox-0']
    prop_s['width dev'] = abs(prop_s['width']-prop_s['width'].median())
    prop_s['height dev'] = abs(prop_s['height']-prop_s['height'].median())
    width_th = prop_s['width'].std()*2
    height_th = prop_s['height'].std()*3
    s_ind = prop_s[(prop_s['solidity'] < 0.9) | (prop_s['width dev'] > width_th) | (prop_s['height dev'] > height_th)].index.tolist()
    
    c_magenta = [1,0,1] 
    
    if tiers_dark==False:
        
    
        # Calculate dimensions of each column
        Z = np.zeros_like(S)
        
              
        D1 = binary_closing(S>0,rectangle(int(prop_s['height'].median()*1),int(prop_s['width'].median()*0.25)))
        D1 = binary_dilation(D1,rectangle(int(prop_s['height'].median()*0.1),int(prop_s['width'].median()*0.5)))
    
        L = label(D1, connectivity=2)
        data = pd.DataFrame(regionprops_table(L, properties = metrics))
        data['width'] = data['bbox-3']-data['bbox-1']
        data['height'] = data['bbox-2']-data['bbox-0']
        labels = np.unique(L)
        data.sort_values(by=['bbox-1'], axis=0, ascending=True, inplace=True, kind='quicksort', na_position='last', ignore_index=True)
        only_pillars = D1*(G)
        labelled_columns = L*S*1
        
        R1 = np.ravel(only_pillars)
        R1 = np.sort(R1)
        R2 = np.where(R1>0)
        R1 = R1[R2[0][0]:]
        Rt2 = threshold_otsu(R1, nbins = 256)
        mt2 = threshold_multiotsu(R1, 4)
        ty = threshold_yen(R1)
        tm = threshold_minimum(R1)
    #     SR2 = G<mt2[0]*0.75
        SR2 = only_pillars<mt2[0]*0.5
        #SR2 = G<ty*0.75
        #SR2 = G<tm
        #VD = G>t*0.75
        DD = SR2*binary_erosion(S*1,disk(1))*1
        voids = SR2*D1
        voids = remove_small_objects(voids==1, prop_s['area'].median()*0.05)-S*1
        voids = binary_dilation(voids>0, disk(f))
        voids = flood_overlap(voids, SC2)
        voids = (voids == 2)*1

    
    if tiers_dark==True:

        if len(s_ind)>0:
            for rem in s_ind:
                SC2 = SC2*1
                SC2 = flood_fill(SC2, (prop_s['coords'][rem][0][0], prop_s['coords'][rem][0][1]), 2)

            t = threshold_otsu(G)
            G1 = rescale_intensity(G)
            R = G1 < t*0.35
            R = binary_dilation(R, disk(np.ceil(block_sz/100)+1))
    
    #         SR = (1*S-R)>0
    #         # S = binary_opening(S,disk(3))
            SR = SC2==2
            SR = remove_small_objects(SR,block_sz*5)  # relate to image size/tier size; 100, 400
            if np.sum(SR)==0:
                S = S
                S = remove_small_objects(S==1,block_sz*5)  # relate to image size/tier size; 100, 400
            else:
                S = SR
        else:
            print('skip checking for voids')
    #     S2 = (SC2==2)*1
#         S2 = SR
        S2 = S
        
        D1 = binary_dilation(S2,rectangle(int(prop_s['height'].median()*1),int(prop_s['width'].median()*0.5)))
        # D1 = binary_closing(S>0,rectangle(int(prop_s['height'].median()*6),20))
    
        L = label(D1, connectivity=2)
        data = pd.DataFrame(regionprops_table(L, properties = metrics))
        data['width'] = data['bbox-3']-data['bbox-1']
        data['height'] = data['bbox-2']-data['bbox-0']
        labels = np.unique(L)
        data.sort_values(by=['bbox-1'], axis=0, ascending=True, inplace=True, kind='quicksort', na_position='last', ignore_index=True)    
        only_pillars = (S2)*G
        labelled_columns = L*S*1
        
        R1 = np.ravel(only_pillars)
        R1 = np.sort(R1)
        R2 = np.where(R1>0)
        R1 = R1[R2[0][0]:]
        Rt2 = threshold_otsu(R1, nbins = 256)
        mt2 = threshold_multiotsu(R1, 4)
        ty = threshold_yen(R1)
        tm = threshold_minimum(R1)
        SR2 = G<mt2[0]*0.75
    #     SR2 = G<ty*0.75
        # SR2 = G<tm
    #     VD = G>t*0.75
        DD = SR2*binary_erosion(S2*1,disk(1))*1
        voids = R
    #     voids = SR2*S2
        voids = remove_small_objects(voids==1, prop_s['area'].median()*0.1)
    #     voids = binary_dilation(voids, disk(f))
    #     voids = flood_overlap(voids, SC2)
        voids = flood_overlap(voids, SC2>0)
        voids = (voids == 2)*1
    
        c_magenta = [1,0,1]
        M2 = mark_boundaries(G, voids, color=c_magenta, outline_color=None, mode='thick', background_label=0)
        MR = mark_boundaries(G, R, color=c_magenta, outline_color=None, mode='thick', background_label=0)
    
#        plt.figure(figsize=(15,15))
#        plt.imshow(M2)

    metrics = ('area', 'centroid', 'bbox', 'coords', 'eccentricity', 'equivalent_diameter', 'major_axis_length', 'minor_axis_length', 'solidity')
    void_props = pd.DataFrame(regionprops_table(label(voids), properties = metrics))
    void_props['Void Width (px)'] = void_props['bbox-3']-void_props['bbox-1']
    void_props['Void Height (px)'] = void_props['bbox-2']-void_props['bbox-0']
    void_props['Void Area (px)'] = void_props['area']
    void_props['Void Number'] = range(1, len(void_props) + 1)
    void_props
    
    p, _ = os.path.split(img_path) 
    excelpath = p + '/tier_voids.csv'
    # EXPORT CSV
    if scalebar == True:
        void_props['Void Height ('+popup_unit+')'] = void_props['Void Height (px)']*scale
        void_props['Void Width ('+popup_unit+')'] = void_props['Void Width (px)']*scale
        void_props['Void Area ('+popup_unit+'^2)'] = void_props['Void Area (px)']*scale*scale
        void_props[['Void Number', 'Void Height ('+popup_unit+')', 'Void Height (px)', 'Void Width ('+popup_unit+')', 'Void Width (px)', 'Void Area ('+popup_unit+'^2)', 'Void Area (px)']].to_csv(excelpath, index = False)
    else:
        void_props[['Void Number', 'Void Height (px)', 'Void Width (px)', 'Void Area (px)']].to_csv(excelpath, index = False)
        pass
    
    
    # SAVE figure imgname+'_voids_annotated'+'.png'
    ZZ = np.zeros_like(S)
    for feat in range(len(void_props)):
        ZZ[void_props['bbox-0'][feat]:void_props['bbox-2'][feat],void_props['bbox-1'][feat]:void_props['bbox-3'][feat]] = 1
    
    MZ = mark_boundaries(G, ZZ, color=c_magenta, outline_color=None, mode='thick', background_label=0)
    
    annotateimg = p + '/annotated_tier_check_'+str(int(round(time.time() * 1000)))+'.png'
    
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.imshow(MZ,cmap='gray')
    ax.axis('off')
    for voidd in range(len(void_props)):
        ax.text(void_props['centroid-1'][voidd], void_props['bbox-0'][voidd]-5, str(void_props['Void Number'][voidd]), horizontalalignment='center', verticalalignment='bottom', color = 'm', fontsize='large', fontweight='bold')
    fig.savefig(annotateimg, dpi=100, bbox_inches='tight', pad_inches=0.2) # save image as ""<img_name>_annotated"
    plt.close(fig)
    
    
    if callfrom == 'backgroundbatch' and output_dir:
        newbatchpath = output_dir + foldername + '_void_annot.png'
        copyFile(annotateimg, newbatchpath)
        excelout = output_dir + foldername + '_tier_voids.csv'
        copyFile(excelpath, excelout)
        
        
    else:
        newbatchpath = batchdir + foldername + '_void_annot.png'
        copyFile(annotateimg, newbatchpath)
        excelout = batchdir + foldername + '_tier_voids.csv'
        copyFile(excelpath, excelout)
   
    df1 = pd.DataFrame({'key':['1','2','3']})
    
    
    return annotateimg, df1, excelpath



def tierThicknessAnalysis(G, S, img_path, batchdir, foldername,
                           scale, popup_unit, callfrom, output_dir):
    
    f = int(2/scale)
    if f<0:
        f=0
    
    if f>=20:
        f = 12
    B = gaussian(S, 1)
    S = B
    S, tiers_dark = check_threshold_tier(S, scale, popup_unit)
    S = remove_small_objects(S,min_size=200, connectivity=1)
    
    
    # keep small objects
    L = remove_small_objects(S,len(np.ravel(S))/40) # relate to image size; 80, 40
    S = S*1-L
    
    # remove objects touching upper and lower frames
    MS = np.zeros_like(S)
    MS[1:-1,:] = 1
    #S = clear_border(S, mask=MS.astype(bool))
    S = clear_border(S)
    
    metrics = ('area', 'centroid', 'coords', 'eccentricity', 'equivalent_diameter', 'major_axis_length', 'minor_axis_length', 'solidity')
    data = pd.DataFrame(regionprops_table(label(S), properties = metrics))
    block_sz = np.mean(data['area'])/10/2
    
    S = remove_small_holes(S==1,300) # relate to image, condition
    S = remove_small_objects(S==1,block_sz) # relate to image, condition
    SC = remove_small_holes(S==1, block_sz*5)-S*1
    S = S+SC*2

    SC2 = binary_dilation(S>0, disk(f+1))
    metrics = ('area', 'bbox', 'coords', 'solidity', 'centroid')
    prop_s = pd.DataFrame(regionprops_table(label(SC2),properties = metrics))
    prop_s['width'] = prop_s['bbox-3']-prop_s['bbox-1']
    prop_s['height'] = prop_s['bbox-2']-prop_s['bbox-0']
    prop_s['width dev'] = abs(prop_s['width']-prop_s['width'].median())
    prop_s['height dev'] = abs(prop_s['height']-prop_s['height'].median())
    width_th = prop_s['width'].std()*2
#     height_th = prop_s['height'].std()*3
    height_th = abs(prop_s['height'].median()-prop_s['height'].max())*2
    s_ind = prop_s[(prop_s['solidity'] < 0.9) | (prop_s['width dev'] > width_th) | (prop_s['height dev'] > height_th)].index.tolist()
#     s_ind = prop_s[ (prop_s['width dev'] > width_th) | (prop_s['height dev'] > height_th)].index.tolist()


    if len(s_ind)>0 :
        for rem in s_ind:
            SC2 = SC2*1
            SC2 = flood_fill(SC2, (prop_s['coords'][rem][0][0], prop_s['coords'][rem][0][1]), 0)
    #         data.drop(ecc_label, inplace=True)
    #         data.reset_index(inplace=True, drop=True)
        CH = (S-SC2)>0
        # void checking
        t = threshold_otsu(B)
        G1 = rescale_intensity(B)
        R = G1 < t*0.35
        R = binary_dilation(R, disk(np.ceil(block_sz/100)+1))
        
        SR = (1*S-R)>0
        # S = binary_opening(S,disk(3))
        SR = remove_small_objects(SR,block_sz*5)  # relate to image size/tier size; 100, 400
        if np.sum(SR)==0:
            S = S
            S = remove_small_objects(S==1,block_sz*5)  # relate to image size/tier size; 100, 400
        else:
            S = SR
    else:
        print('Skip checking for voids')
   
    
    # Calculate dimensions of each column
    Z = np.zeros_like(S)
    D1 = binary_dilation(S,rectangle(int(prop_s['height'].median()*6),20))
    
    L = label(D1, connectivity=2)
    data = pd.DataFrame(regionprops_table(L, properties = metrics))
    data['width'] = data['bbox-3']-data['bbox-1']
    data['height'] = data['bbox-2']-data['bbox-0']
    labels = np.unique(L)
    data.sort_values(by=['bbox-1'], axis=0, ascending=True, inplace=True, kind='quicksort', na_position='last', ignore_index=True)
    
    
    tiers = pd.DataFrame()
    CL = np.zeros_like(S)
    for cluster in range(len(data)):
        C = (S>0)*(L==(cluster+1))
        C = remove_small_objects(C,20)
        CL = CL + C*(cluster+1)
        #CT = (1*C - voids)>0
        #CT_props = regionprops_table(label(CT, connectivity=2), properties = ('area', 'bbox'))
    
        data_temp = pd.DataFrame(regionprops_table(label(C, connectivity=2), properties = metrics))
        data_temp['Column'] = cluster+1
        #data_temp['void_area'] = CT_props['area']
        clust_tiers = len(data_temp)
        tiers=tiers.append(data_temp)
    
    tiers['Tier'] = tiers.index+1
    tiers['Width'] = tiers['bbox-3']-tiers['bbox-1']
    tiers['height'] = tiers['bbox-2']-tiers['bbox-0']
    tiers.reset_index(inplace=True)
    tiers['Void Area'] = np.nan
    
    # get tier void area fraction
    V = (S == 2)*CL
    defect = []
    for voidcol in np.unique(V)[1:]:
        vprops = regionprops(label(V==voidcol))
        for void in range(len(vprops)):
            p = cdist(np.array(vprops[void].centroid).reshape([1,2]),np.array(tiers.loc[tiers['Column']==voidcol][['centroid-0','centroid-1']]))
            defect.append([voidcol, np.argmin(p)])
    
    tier_voids = pd.DataFrame(columns=['Measure', 'Quantity'])    
    tier_voids.loc[0] = ['Identified tier columns', len(data)]
    tier_voids.loc[1] = ['Identified tiers',  len(tiers)]
    tier_voids.loc[2] = ['Identified tiers voids', len(defect)]
    
    for void in defect:
        mask = tiers.loc[(tiers['Column'] == void[0]) & (tiers['Tier'] == void[1])]
        pos = mask.index[0]
#         tiers.loc[tiers.index[pos],['Void Area']] = mask['area'][pos] - np.sum(np.ravel(DV[mask['bbox-0'][pos]:mask['bbox-2'][pos], mask['bbox-1'][pos]:mask['bbox-3'][pos]]))
    
    # find tier mid heigt
    for tier in range(len(tiers)):
        tiers.loc[tier,'Mid Height'] = np.sum(tiers['coords'][tier][:,1]==int(tiers['centroid-1'][tier]))
        
    # SAVE ANNOTATED IMAGE
    c_magenta = [1,0,1]
    tiers.set_index('index', inplace = True)
    MS = mark_boundaries(G, S, color=c_magenta, outline_color=None, mode='thick', background_label=0)
    fig, ax = plt.subplots(figsize=(15, 15))
    ax.imshow(MS, cmap='gray')
    for cluster in range(len(data)):
        rect = mpatches.Rectangle((data['bbox-1'][cluster],  data['bbox-0'][cluster]),  data['width'][cluster],  data['height'][cluster], fill=False, edgecolor='magenta', linewidth=2, alpha = 0.5)
        ax.add_patch(rect)
        ax.text(data['bbox-1'][cluster],  data['bbox-0'][cluster], 'Col. ' + str(cluster+1), horizontalalignment='right', verticalalignment='top', color = 'k', fontsize='x-large', fontweight='bold')
        ind = cluster+1
        for obj in range(len(tiers[tiers["Column"] == ind])):
            ax.text(tiers[tiers["Column"] == ind]['centroid-1'][obj], tiers[tiers["Column"] == ind]['centroid-0'][obj], str(tiers[tiers["Column"] == ind]['Tier'][obj]), horizontalalignment='center', verticalalignment='center', color = 'w', fontsize='large', fontweight='bold')
    ax.axis('off')
    
    p, _ = os.path.split(img_path) 

    annotateimg = p + '/annotated_tier_thk_'+str(int(round(time.time() * 1000)))+'.png' 

    fig.savefig(annotateimg, dpi=100, bbox_inches='tight', pad_inches=0) # save image as
    plt.close(fig)
    
    tiers['Tier Width ('+popup_unit+')'] = tiers['Width']*scale
    tiers['Tier Mid Height ('+popup_unit+')'] = tiers['Mid Height']*scale
#     tiers['Tier Void Area (px)'] = tiers['Void Area']#*(scale**2)
#     tiers['Tier Void Area Fraction'] = tiers['Void Area']/tiers['area']
    # tiers.set_index('Tier', inplace=True)
    
    # EXPORT CSV
#     tier_thickness = tiers[['Column', 'Tier', 'Tier Width ('+popup_unit+')', 'Tier Mid Height ('+popup_unit+')', 'Tier Void Area Fraction']].copy()
    tier_thickness = tiers[['Column', 'Tier', 'Tier Width ('+popup_unit+')', 'Tier Mid Height ('+popup_unit+')']].copy()
    outbatch = output_dir + foldername + '_tier_thickness.csv'
    tier_thickness.to_csv(outbatch, index=False)

        
    newbatchpath = batchdir + foldername + '_annotated_tier_thk.png'
    
    if callfrom == 'backgroundbatch' and output_dir:
        copyFile(annotateimg, newbatchpath)
        copyFile(newbatchpath, output_dir)
        
    else:
        copyFile(annotateimg, newbatchpath)
        
                    
    plt.close('all')
    return annotateimg, tier_thickness, outbatch

def tierAnalysis(obj):
    try:
        callfrom = obj['callfrom']
        batch = obj['batch']
    except:
        batch = False
        callfrom = 'normalcall'
    G = obj['sampleimg']
    img_path = obj['image_path']
    G = io.imread(G)
    G = rgb2gray(G)
    S = io.imread(img_path)
    S = rgb2gray(S)
    
    draw_val = obj['draw_val']
    popup_val = float(obj['popup_val'])
            
    scale = (popup_val/ draw_val)  #*unitval
    
    excel_mode = obj['excel_mode']
    anatype = obj['analysislist']#'void'
    cmpltdata = []
    
    output_dir = fetchKeysValue('output_dir', obj)
    if output_dir:
        callfrom = 'backgroundbatch'
    else:
        callfrom = 'normalcall'
    
    
    orignalpath = obj['orignalpath']
    fpath, _  = os.path.splitext(orignalpath)
    basefoldername, foldername = os.path.split(fpath)
    img_path = fpath + '/abc.png'
    
    if not os.path.exists(fpath):
        os.mkdir(fpath)
    
    
    if callfrom == 'backgroundbatch':
        output_dir = obj['output_dir']
        batchdir = basefoldername + '/processed_api/'
        batchdir = checkEnv(batchdir)
        if not os.path.exists(batchdir):
            os.mkdir(batchdir)
        output_dir = addSlashonLastIndex(output_dir)
    else:
        output_dir = ''
        batchdir = basefoldername + '/batchprocessed/'
        batchdir = checkEnv(batchdir)
        if not os.path.exists(batchdir):
            os.mkdir(batchdir)
    notification_data = []
    global APPLICABLE
    excelfile = batchdir + foldername + 'tier_analysis.xlsx'
    for j,i in enumerate(anatype):
        APPLICABLE = True
        error = False
        try:
            if i == 'tva':
                funcname = 'Tier Void'
                annotateimg, tier_ana, excelfile = tierVoidChechking(G, S, img_path, batchdir, foldername, scale, obj['popup_unit'], callfrom, output_dir)
                
                
            elif i == 'tvc':
                funcname = 'Tier Void'
                annotateimg, tier_ana, excelfile = tierVoidChechking(G, S, img_path, batchdir, foldername, scale, obj['popup_unit'], callfrom, output_dir)
                
            else:
                funcname = 'Tier Thickness'
                annotateimg, tier_ana, excelfile = tierThicknessAnalysis(G, S, img_path, batchdir, foldername, scale, obj['popup_unit'], callfrom, output_dir)
               
                
            head = list(tier_ana.columns)
            table1 = tier_ana.to_dict()
            data = {'analysis_type': i, 'annotate_img': annotateimg, 'heading': head, 'value': json.dumps(table1), 'excel_path': excelfile}
            cmpltdata.append(data)
        except Exception:
#             traceback.print_exc()
            error = True
            
        # notification_data.append({'ImageName': foldername, 'Analysis': funcname, 'Applicable': APPLICABLE, 'Failed': error})
        notification_data.append({'ImageName': foldername, 'Analysis': funcname, 'Failed': error})

    fulldata = {'error': notification_data, 'data': cmpltdata}            
    return fulldata

def getTierAnalysisData(data, user_id, callfrom, tier_type, popup_unit, 
                        draw_val, popup_val, output_dir, error, scalebarextarction):
    tier_ana = []
    calldata = {'batch': True, 'callfrom': callfrom, 
                'sampleimg': data['cropimg'], 
                'image_path': data['segmented_img'], 
                'excel_mode': 'new', 'analysislist': tier_type,
                  'draw_val': draw_val, 'popup_val': popup_val,
                    'popup_unit': popup_unit, 'output_dir': output_dir,
               'orignalpath': data['orignalpath']}
        

    object = tierAnalysis(calldata)
    error = object['error']
    a_data = object['data']
    
    error = [{**item, 'Scale bar':scalebarextarction} for item in error]
    
    return a_data, error


def metalrecessv2(B, S, img_path, batchdir, foldername, scale, popup_unit, 
                  callfrom, output_dir, scalebar, APPLICABLE):
    csv_metal_recess, annotate_img, annotate_img2 = '', '', ''
    msg = ''
    mr_featparam = 17
    dl = int(np.ceil(mr_featparam/scale))

    G = gaussian(B,0.5)
    t = threshold_otsu(G)
    tm = threshold_multiotsu(G)
    # S = G < tm[1]
    S = G <= t 
    M = np.digitize(B, tm)
    MS = np.zeros_like(S)
    MS[:,1:-1] = 1
    S = remove_small_objects(S,len(np.ravel(S))/40) # relate to image size; ~ # dl**2*20

    c_magenta = [1,0,1]
    c_cyan = [0,1,1]
    
    # get props of S
    SL, labels = label(S, return_num=True, connectivity=2)
    metrics = ('area', 'bbox', 'centroid', 'coords', 'eccentricity', 'equivalent_diameter', 'major_axis_length', 'minor_axis_length', 'solidity')
    data_temp = pd.DataFrame(regionprops_table(SL, properties = metrics))

    # filtering params
    recess_gap = [190, 340] #nm
    recess_gap_px = [x / scale for x in recess_gap]
    xpad = int(121/scale) # relate to feature size; 121 nm
    ypad = int(25/scale) # relate to feature size; 25 nm
    ypad_lower = int(17/scale) # relate to feature size; 17 nm

    # crop_amount = []
    recess_features = {}
    for n in range(labels):
        clx = []
        labl = n+1

        # get  CL of label
        SS = (SL==labl)*1
        SS = remove_small_holes(SS==1, 500)
        clx = np.count_nonzero(np.asarray(SS[data_temp['bbox-0'][n]:data_temp['bbox-2'][n],data_temp['bbox-1'][n]:data_temp['bbox-3'][n]]), axis=1)
        clx_inv = clx*(-1)

        # get peak/valleys
        peaks, _ = find_peaks(clx, distance = int(41/scale)) #41 nm
        valleys, _ = find_peaks(clx_inv, distance = int(41/scale)) #41 nm

        # crop based on peak/valley recess gap
        df = pd.DataFrame([clx[peaks]]).T
        df.columns = ['clx']
        c_valleys = c_peaks = np.zeros_like(clx[peaks])
        df['peak'] = peaks
        Index_label = df[(df['clx'] > recess_gap_px[0]) & (df['clx'] < recess_gap_px[1])].index.tolist()
        if Index_label !=[]:
            y_bounds = [df['peak'][Index_label[0]], df['peak'][Index_label[-1]]]
            if y_bounds[0]>ypad and S.shape[0]-y_bounds[1]>ypad_lower:
                y_bounds = [y_bounds[0]-ypad, y_bounds[1]+ypad_lower]

            #NI = (SL==labl)[y_bounds[0]:y_bounds[1], :]
            NI = (SS)[y_bounds[0]:y_bounds[1], :]
            props_temp = pd.DataFrame(regionprops_table(NI*1))
            if props_temp['bbox-1'][0]>xpad and S.shape[1]-props_temp['bbox-3'][0]>xpad:
                x_bounds = [props_temp['bbox-1'][0]-xpad, props_temp['bbox-3'][0]+xpad]
            else:
                x_bounds = [props_temp['bbox-1'][0], props_temp['bbox-3'][0]]          
            #CI = (SL==labl)[y_bounds[0]-20:y_bounds[1]+20, x_bounds[0]-20:x_bounds[1]+20]
            #CI = (SL==labl)[y_bounds[0]:y_bounds[1], x_bounds[0]:x_bounds[1]]
            CI = (SS)[y_bounds[0]:y_bounds[1], x_bounds[0]:x_bounds[1]]
            crop_amount= [ y_bounds[0], y_bounds[1], x_bounds[0], x_bounds[1]]
            #clx = clx[y_bounds[0]:y_bounds[1]]
            #peaks = peaks + y_bounds[0]-1
            #valleys = valleys + y_bounds[0]-1
            recess_features[len(recess_features)] = {'label': labl, 'clx': clx, 
                                                     'peaks': peaks, 'valleys': valleys,
                                                       'bounds':crop_amount, 'feat': CI} 

            #diagnostic image
            plt.figure()
            plt.imshow(CI)

            #clx = np.count_nonzero(np.asarray(CI), axis=1)
            #dl = np.max(clx)-np.mean(clx)

        else:
            #raise ValueError('Could not identify metal recess features.')
            pass
    
    # check the features in dict if they are MR

    recess_depth = [200, 290] #240 290 nm
    recess_depth_px = [x / scale for x in recess_depth]

    recess_feat_real = []
    for ii in range(len(recess_features)):
        clx = recess_features[ii]['clx']
        peaks = recess_features[ii]['peaks']
        valleys = recess_features[ii]['valleys']

        df_temp = pd.DataFrame(clx[recess_features[ii]['peaks']])
        df_temp.columns = ['clx']
        df_temp['peak'] = peaks
        df_temp['valley'] = np.nan
        df_temp['clx_valley'] = np.nan
        for r in range(len(df_temp)):
            try:
                val = np.where(valleys > df_temp['peak'][r])[0][0]
                df_temp.loc[r,'clx_valley'] = clx[valleys[val]]
                df_temp.loc[r,'valley'] = valleys[val]
            except:
                pass
        df_temp['clx diff'] = df_temp['clx']-df_temp['clx_valley']
        df_temp['clx diff pu'] = df_temp['clx diff']*scale
        df_temp['p_v diff'] = df_temp['valley']-df_temp['peak']
        df_temp['p_v diff pu'] = df_temp['p_v diff']*scale
        #recess_spacing_check = df.dropna(subset=['p_v diff'])

        #check first peak/valley matching reqs
        df_temp.dropna(inplace=True)
        first_depth_check = df_temp[(df_temp['clx diff pu'] > 10) & (df_temp['clx diff pu'] < 70)].index.tolist() # limts in p.u., physical units
        first_spacing_check = df_temp[(df_temp['p_v diff pu'] > 10) & (df_temp['p_v diff pu'] < 40)].index.tolist() # limts in p.u., physical units
        idx_match = [x for x in first_depth_check if x in first_spacing_check]
        df_temp = df_temp.iloc[idx_match]

        recess_depth_check = df_temp.dropna(subset=['clx diff'])[(df_temp['clx diff pu'] < 10) | (df_temp['clx diff pu'] > 70)].index.tolist() # limts in p.u., physical units
        recess_spacing_check = df_temp.dropna(subset=['p_v diff'])[(df_temp['p_v diff pu'] < 10) | (df_temp['p_v diff pu'] > 40)].index.tolist() # limts in p.u., physical units
        if recess_spacing_check or recess_depth_check:
            if len(recess_spacing_check) < 3 and len(recess_spacing_check) >= len(recess_depth_check):
                #raise ValueError('Recess spacing outside of expected bounds')
                bad_recesses = len(df_temp)-recess_spacing_check[0]
                new_ybound = df_temp['valley'][recess_spacing_check[0]-1].astype(int)
                recess_features[ii]['bounds'][1] = new_ybound
                recess_feat_real.append(ii) # the label that has the recess features
            else:
                print('Recess spacing outside of expected bounds: '+str(ii))
            if len(recess_depth_check) < 3 and len(recess_depth_check) >= len(recess_spacing_check):
                #raise ValueError('Recess depth outside of expected bounds')
                bad_recesses = len(df_temp)-recess_depth_check[0]
                new_ybound = df_temp['valley'][recess_depth_check[0]-1].astype(int)
                recess_features[ii]['bounds'][1] = new_ybound
                recess_feat_real.append(ii) # the label that has the recess features
            else:
                print('Recess depth outside of expected bounds: '+str(ii))
        else:
            recess_feat_real.append(ii)

    c_yellow = [1,1,0]
    
    spearhead_output = False
    for jj, feat in enumerate(recess_feat_real):
        mr_feat = recess_features[feat]

        # crop the MR features from original image and segment
        GI = G[mr_feat['bounds'][0]:mr_feat['bounds'][1],mr_feat['bounds'][2]:mr_feat['bounds'][3]]
        tt = threshold_multiotsu(GI)
        GM = np.digitize(GI, tt)
        SG = GM<2
        MK = np.zeros_like(SG)
        MK[:,1:-1] = 1
        SG_edges = SG
        SG = binary_opening(SG,disk(int(dl/8)+1)) # relate to feature size; 3
        SG_edges = (SG+SG_edges*2)==2
        SG = clear_border(SG, mask=MK.astype(bool))
        SG = SG + SG_edges
        SG = remove_small_objects(SG==1, int(dl*100)) #relate to feature sizes; 1000
        SG = remove_small_holes(SG, int(dl*100)) #relate to feature sizes
        MS = mark_boundaries(GI, SG, color=c_magenta, outline_color=None, mode='thick', background_label=0)
        io.imsave('SG.png', SG*1)
        props_SG = pd.DataFrame(regionprops_table(label(SG),properties=metrics))
        if len(props_SG)>0 and props_SG['solidity'][0]<0.82:
            msg = 'Recess object too large for feat ' + str(feat)
            raise Exception #('Recess object too large for feat ' + str(feat))

        S2 = SG
        S0 = SG==0
        S0 = binary_dilation(S0, rectangle(int(dl*2.5),1)) #relate to feature sizes; 40
        PP = S0+S2*2
        CC = PP==3
        CC = clear_border(CC)

        try:
            if (mr_feat['bounds'][3]-mr_feat['bounds'][2])/S.shape[1]>0.75:
                msg = 'Recess object too large for feat ' + str(feat)
                raise Exception #('Recess object too large for feat ' + str(feat))
            # divide into left and right MR features
            divider = int(np.floor(CC.shape[1]/2))
            if CC.shape[1] % 2 != 0:
                divider_L = divider+1
            else:
                divider_L = divider
            LC = CC[:,0:divider_L]
            RC = CC[:,CC.shape[1]-divider:]
            if scale>2:
                dl_recess = int(dl/2)
            else:
                dl_recess = dl

            ## METAL RECESS
            # left recesses
            LC1 = binary_opening(LC, rectangle(int(np.ceil(dl_recess/2.0)),int(np.ceil(dl_recess/1.5))))
            LC1 = remove_small_objects(LC1, (dl_recess**2)/8)
            LC_pad = np.pad(LC1, ((0, 0), (0, divider)), 'constant', constant_values=(0,0)) 

            data_recess_L = pd.DataFrame(regionprops_table(label(LC_pad, connectivity=2), properties = metrics))
            data_recess_L['width'] = data_recess_L['bbox-3']-data_recess_L['bbox-1']
            data_recess_L['width ('+popup_unit+')'] = data_recess_L['width']*scale

            MRL = np.zeros_like(LC_pad)

            for recess in range(len(data_recess_L)):
                data_recess_L.loc[recess,'Recess Depth (px)'] = np.sum((data_recess_L['coords'][recess][:,0])==int(data_recess_L['centroid-0'][recess]))
                MRL[int(data_recess_L['centroid-0'][recess]), :] = 1
            MRL = MRL*LC_pad

            # right recesses
            RC1 = binary_opening(RC, rectangle(int(np.ceil(dl_recess/2.0)),int(np.ceil(dl_recess/1.5))))
            RC1 = remove_small_objects(RC1, (dl_recess**2)/8)
            RC_pad = np.pad(RC1, ((0, 0), (divider_L, 0)), 'constant', constant_values=(0,0)) 

            data_recess_R = pd.DataFrame(regionprops_table(label(RC_pad, connectivity=2), properties = metrics))
            data_recess_R['width'] = data_recess_R['bbox-3']-data_recess_R['bbox-1']
            data_recess_R['width ('+popup_unit+')'] = data_recess_R['width']*scale    

            MRR = np.zeros_like(RC_pad)
            for recess in range(len(data_recess_R)):
                data_recess_R.loc[recess,'Recess Depth (px)'] = np.sum((data_recess_R['coords'][recess][:,0])==int(data_recess_R['centroid-0'][recess]))
                MRR[int(data_recess_R['centroid-0'][recess]), :] = 1
            MRR = MRR*RC_pad
                       
            try:
                ## MR SPEARHEAD V2
                SPL = np.zeros_like(LC)
                SPR = np.zeros_like(RC)

                # left side spearhead
                LF = remove_small_objects(LC, int(dl*5)) # relate to feature size; 100
                # LF = binary_opening(LF, rectangle(2,2))

                LF_props = regionprops_table(label(LF, connectivity=2), properties = metrics)
                data_LF = pd.DataFrame(LF_props)
                data_LF.drop(data_LF[LF_props['area'] < np.mean(data_LF['area'])-np.std(data_LF['area'])*1].index, inplace = True) 
                data_LF.reset_index(inplace=True)
                data_LF['width'] = data_LF['bbox-3'] - data_LF['bbox-1']
                data_LF['height'] = data_LF['bbox-2'] - data_LF['bbox-0'] #metal height

                for obj in range(len(data_LF)):
                    yy = list(data_LF['coords'][obj][:,0])
                    xx = list(data_LF['coords'][obj][:,1])
                    x1 = np.min(xx)
                    y1 = yy[xx.index(x1)]
                    indices = (np.where(yy == y1)[0].flatten().astype(int))
                    selected_elements = [xx[index] for index in indices]
                    x2 = np.max(selected_elements)
#                     spear_L = x2-x1
                    x2_adjusted = x2 - data_recess_L.loc[obj,'Recess Depth (px)'].astype(int)
                    spear_L = x2_adjusted-x1
                    if spear_L<3 and scale<1:
                        spear_L = 0
                    if spear_L<0:
                        spear_L = 0
                    SPL[y1,x1:x1+spear_L]=1
#                     SPL[y1,x1:x2]=1
                    data_LF.loc[data_LF['index'][obj],'Spearhead (px)'] = spear_L
                    data_LF.replace(0, np.nan)

                LF_pad = np.pad(SPL, ((0, 0), (0, divider)), 'constant', constant_values=(0,0)) 

                # right side spearhead
                RF = remove_small_objects(RC, int(dl*5))
                # RF = binary_opening(RF, rectangle(2,2))

                RF_props = regionprops_table(label(RF, connectivity=2), properties = metrics)
                data_RF = pd.DataFrame(RF_props)
                data_RF.drop(data_RF[RF_props['area'] < np.mean(data_RF['area'])-np.std(data_RF['area'])*1].index, inplace = True) 
                data_RF.reset_index(inplace=True)  
                data_RF['width'] = data_RF['bbox-3'] - data_RF['bbox-1']
                data_RF['height'] = data_RF['bbox-2'] - data_RF['bbox-0'] #metal height

                for obj in range(len(data_RF)):
                    yy = list(data_RF['coords'][obj][:,0])
                    xx = list(data_RF['coords'][obj][:,1])
                    x2 = np.max(xx)
                    y1 = yy[xx.index(x2)]
                    indices = (np.where(yy == y1)[0].flatten().astype(int))
                    selected_elements = [xx[index] for index in indices]
                    x1 = np.min(selected_elements)
#                     spear_R = x2-x1
                    x1_adjusted = x1 + data_recess_R.loc[obj,'Recess Depth (px)'].astype(int)
                    spear_R = x2-x1_adjusted
                    if spear_R<3 and scale<1:
                        spear_R = 0
                    if spear_R<0:
                        spear_R = 0
#                     SPR[y1,x1:x2]=1
                    SPR[y1,x1_adjusted:x1_adjusted+spear_R]=1
                    data_RF.loc[data_RF['index'][obj],'Spearhead (px)'] = spear_R
                    data_RF.replace(0, np.nan)

                RF_pad = np.pad(SPR, ((0, 0), (divider_L,0)), 'constant', constant_values=(0,0)) 
            
                ML = mark_boundaries(GI, LF_pad, color=c_cyan, outline_color=None, mode='thick', background_label=0) #spearhead visualization
                MR = mark_boundaries(ML, RF_pad, color=c_cyan, outline_color=None, mode='thick', background_label=0)
                spearhead_output = True
            except:
                traceback.print_exc()
                spearhead_output = False
                pass

            data_recess_L['Recess'] = range(1, len(data_recess_L) + 1)
            data_recess_R['Recess'] = range(1, len(data_recess_R) + 1)
            data_recess_L['Recess location'] = 'L'+ data_recess_L['Recess'].astype(str)
            data_recess_R['Recess location'] = 'R'+ data_recess_R['Recess'].astype(str)
        #     data_recess_L['Recess location'] = (range(1, len(data_recess_L) + 1)
        #     data_recess_R['Recess location'] = (range(1, len(data_recess_R) + 1)

           ## OUTPUT
            csv_metal_recess = batchdir + foldername + '_metal_recess.csv'
            if scalebar == True:
                data_recess_L['Recess Depth ('+popup_unit+')'] = data_recess_L['Recess Depth (px)']*scale
                data_recess_R['Recess Depth ('+popup_unit+')'] = data_recess_R['Recess Depth (px)']*scale
                if spearhead_output == True:
                    data_LF['Spearhead ('+popup_unit+')'] = data_LF['Spearhead (px)']*scale #+ data_recess_L['Recess Depth ('+popup_unit+')']
                    data_RF['Spearhead ('+popup_unit+')'] = data_RF['Spearhead (px)']*scale #+ data_recess_R['Recess Depth ('+popup_unit+')']
                    dfl = pd.concat([data_recess_L['Recess location'], data_recess_L['Recess Depth ('+popup_unit+')'], data_LF['Spearhead ('+popup_unit+')']], axis=1)        
                    dfr = pd.concat([data_recess_R['Recess location'], data_recess_R['Recess Depth ('+popup_unit+')'], data_RF['Spearhead ('+popup_unit+')']], axis=1)
                else:
                    dfl = pd.concat([data_recess_L['Recess location'], data_recess_L['Recess Depth ('+popup_unit+')']], axis=1)        
                    dfr = pd.concat([data_recess_R['Recess location'], data_recess_R['Recess Depth ('+popup_unit+')']], axis=1)
                #dfl = pd.concat([data_recess_L['Recess location'], data_recess_L['Recess Depth ('+popup_unit+')'], data_recess_L['width ('+popup_unit+')'], data_LF['Spearhead ('+popup_unit+')']], axis=1)        
                #dfr = pd.concat([data_recess_R['Recess location'], data_recess_R['Recess Depth ('+popup_unit+')'], data_recess_R['width ('+popup_unit+')'], data_RF['Spearhead ('+popup_unit+')']], axis=1)
                dff = pd.concat([dfl, dfr], axis=0)        
                dff.round(2).to_csv(csv_metal_recess, index=False)
            else:
                if spearhead_output == True: 
                    dfl = pd.concat([data_recess_L['Recess location'], data_recess_L['Recess Depth (px)'], data_LF['Spearhead (px)']], axis=1)        
                    dfr = pd.concat([data_recess_R['Recess location'], data_recess_R['Recess Depth (px)'], data_RF['Spearhead (px)']], axis=1)
                else:
                    dfl = pd.concat([data_recess_L['Recess location'], data_recess_L['Recess Depth (px)']], axis=1)        
                    dfr = pd.concat([data_recess_R['Recess location'], data_recess_R['Recess Depth (px)']], axis=1)
                #dfl = pd.concat([data_recess_L['Recess location'], data_recess_L['Recess Depth (px)'], data_recess_L['width (px)'], data_LF['Spearhead (px)']], axis=1)        
                #dfr = pd.concat([data_recess_R['Recess location'], data_recess_R['Recess Depth (px)'], data_recess_R['width (px)'], data_RF['Spearhead (px)']], axis=1)
                dff = pd.concat([dfl, dfr], axis=0)            
                dff.round(2).to_csv(csv_metal_recess, index=False)

    #         SP = SPL+SPR
    #         MP = mark_boundaries(GI, SP, color=c_cyan, outline_color=None, mode='thick', background_label=0) #spearhead visualization
#             ML = mark_boundaries(GI, LF_pad, color=c_cyan, outline_color=None, mode='thick', background_label=0) #spearhead visualization
#             MR = mark_boundaries(ML, RF_pad, color=c_cyan, outline_color=None, mode='thick', background_label=0)

    #         LC_pad2 = binary_opening(LC_pad, rectangle(int(np.ceil(dl/1.0)),int(np.ceil(dl/3))))
    #         RC_pad2 = binary_opening(RC_pad, rectangle(int(np.ceil(dl/1.0)),int(np.ceil(dl/3))))
    #         MC = mark_boundaries(GI, LC_pad2, color=c_magenta, outline_color=None, mode='thick', background_label=0)
    #         MC = mark_boundaries(MC, RC_pad2, color=c_magenta, outline_color=None, mode='thick', background_label=0)
            MC = mark_boundaries(GI, MRL, color=c_yellow, outline_color=None, mode='thick', background_label=0)
            MC = mark_boundaries(MC, MRR, color=c_yellow, outline_color=None, mode='thick', background_label=0)

            # MC = mark_boundaries(GI, LC_pad, color=c_magenta, outline_color=None, mode='thick', background_label=0)
            # MC = mark_boundaries(MC, RC_pad, color=c_magenta, outline_color=None, mode='thick', background_label=0)
            # MC = mark_boundaries(MC, MRL, color=c_yellow, outline_color=None, mode='thick', background_label=0)
            # MC = mark_boundaries(MC, MRR, color=c_yellow, outline_color=None, mode='thick', background_label=0)
            
            annotate_img = batchdir + foldername + '_recess_depth.png'
            fig, ax = plt.subplots(figsize=(12,12))
            ax.imshow(MC)
            ax.axis('off')
            for rec in range(len(data_recess_L)):
                ax.text(data_recess_L['bbox-3'][rec], data_recess_L['centroid-0'][rec], str(data_recess_L['Recess location'][rec]), horizontalalignment='left', verticalalignment='center', color = 'w', fontsize='medium', fontweight='bold')
            
            for rec in range(len(data_recess_R)):
                ax.text(data_recess_R['bbox-1'][rec], data_recess_R['centroid-0'][rec], str(data_recess_R['Recess location'][rec]), horizontalalignment='right', verticalalignment='center', color = 'w', fontsize='medium', fontweight='bold')
            
            fig.savefig(annotate_img, bbox_inches='tight', pad_inches=0)
            plt.close(fig)
            
            if spearhead_output == True:
                annotate_img2 = batchdir + foldername + '_spearhead.png'
                fig, ax = plt.subplots(figsize=(12,12))
                ax.imshow(MR)
                ax.axis('off')
                for rec in range(len(data_recess_L)):
                    ax.text(data_recess_L['bbox-3'][rec], data_recess_L['centroid-0'][rec], str(data_recess_L['Recess location'][rec]), horizontalalignment='left', verticalalignment='center', color = 'w', fontsize='medium', fontweight='bold')
                    
                for rec in range(len(data_recess_R)):
                    ax.text(data_recess_R['bbox-1'][rec], data_recess_R['centroid-0'][rec], str(data_recess_R['Recess location'][rec]), horizontalalignment='right', verticalalignment='center', color = 'w', fontsize='medium', fontweight='bold')
                
                fig.savefig(annotate_img2, bbox_inches='tight', pad_inches=0)
                plt.close(fig)
            
        except:
            print('Second except')
            traceback.print_exc()
    return annotate_img, annotate_img2, csv_metal_recess, msg   


def MRAnalysis(obj):
    
    G = obj['sampleimg']
    img_path = obj['image_path']
    G = io.imread(G)
    G = rgb2gray(G)
    S = io.imread(img_path)
    S = rgb2gray(S)
    try:
        callfrom = obj['callfrom']
        batch = obj['batch'] 
    except:
        batch = False
        callfrom = 'normalcall'
        
    draw_val = obj['draw_val']
    popup_val = int(obj['popup_val'])
            
    scale = (popup_val/ draw_val)  #*unitval
    scalebar = True
    anatype = obj['analysislist']#'void'
    cmpltdata = []
    foldername, _ = os.path.split(img_path)
    basefoldername = os.path.split(os.path.dirname(img_path))[0]
    output_dir = fetchKeysValue('output_dir', obj)
    
    if output_dir:
        callfrom = 'backgroundbatch'
    else:
        callfrom = 'normalcall'
        
        
    orignalpath = obj['orignalpath']
    fpath, _  = os.path.splitext(orignalpath)
    basefoldername, foldername = os.path.split(fpath)
    img_path = fpath + '/abc.png'
    
    if not os.path.exists(fpath):
        os.mkdir(fpath)    
    
    if output_dir:
        callfrom = 'backgroundbatch'
    else:
        callfrom = 'normalcall'
    
    if callfrom == 'backgroundbatch':
        output_dir = obj['output_dir']
        batchdir = output_dir
        output_dir = addSlashonLastIndex(output_dir)
        batchdir = output_dir
    else:
        output_dir = ''
        batchdir = basefoldername + '/batchprocessed/'
        batchdir = checkEnv(batchdir)
        if not os.path.exists(batchdir):
            os.mkdir(batchdir)
        output_dir = batchdir

    notification_data = []
    global APPLICABLE
    for i in anatype:
        error = False
        APPLICABLE = True
        try:
            extraannotated = []
            if i == 'metal_recess':
                funcname = 'Metal Recess'
#                 annotateimg, annotateimg2, anapath, recess = metalRecessAnalysis(G, S, img_path, batchdir, foldername, scale, obj['popup_unit'], callfrom, output_dir, scalebar, APPLICABLE)
                
                annotateimg, annotateimg2, anapath, msg = metalrecessv2(G, S, img_path, batchdir, foldername, scale, obj['popup_unit'], callfrom, output_dir, scalebar, APPLICABLE)
                
                if not annotateimg:
                    error = True         
                else:
                    extraannotated = [ {'recess_depth': annotateimg}, {'spearhead': annotateimg2}]
                    
#                 annotateimg, annotateimg2, anapath, recess = orignalpath, '32', '14', '52'
#             elif i == 'metal_recess_sec_t': #
                
#                 funcname = 'Metal Recess Second Tier'
#                 annotateimg, anapath = MRSecTierAnalysis(G, S, img_path, batchdir, foldername, scale, obj['popup_unit'], callfrom, output_dir, scalebar, APPLICABLE)
# #                 annotateimg = orignalpath
#             elif i == 'metal_recess_tier_thick':
#                 funcname = 'Metal Recess Tier Thickness'
#                 annotateimg, anapath = MRTierThicknessAnalysis(G, S, img_path, batchdir, foldername, scale, obj['popup_unit'], callfrom, output_dir, scalebar, APPLICABLE)
# #                 annotateimg = orignalpath   
            
            #df = pd.read_csv(anapath)
            df = pd.DataFrame({'heigh': [1,3,5,6]})
            head = list(df.columns)
            table1 = df.to_dict()  

            data = {'analysis_type': i,'annotate_img': annotateimg, 'heading': head, 'value': json.dumps(table1), 'excel_path':anapath,
                   'otherannotated': extraannotated}
            cmpltdata.append(data)
                                    
        except:
            traceback.print_exc()
            error = True
            
        notification_data.append({'ImageName': foldername, 'Analysis': funcname, 'Applicable': APPLICABLE, 'Failed': error})
    
    fulldata = {'error': notification_data, 'data': cmpltdata}
    return fulldata

def getMetalRecessAnalysisData(data, user_id, callfrom, popup_unit, 
                               draw_val, popup_val, output_dir, 
                               metal_recess_type, error, scalebarextarction):
    tier_ana = []
    calldata = {'batch': True, 'callfrom': callfrom, 
                'sampleimg': data['cropimg'], 
                'image_path': data['segmented_img'], 
                'excel_mode': 'new', 'analysislist': metal_recess_type,
                  'draw_val': draw_val, 'popup_val': popup_val, 
                  'popup_unit': popup_unit, 'output_dir': output_dir, 
                  'orignalpath': data['orignalpath']}
        
    
    api_data = MRAnalysis(calldata)
    error = api_data['error']
    data = api_data['data']
    for i in data:
        i['value'] = json.loads(i['value'])
    error = [{**item, 'Scale bar':scalebarextarction} for item in error]
    return data, error 

def clean_by(img, clear_img_border = False, **kwargs):
    
    area = kwargs.get('area', None)
    area_std = kwargs.get('area_std', None)
    solidity = kwargs.get('solidity', None)
    aspect_hw = kwargs.get('aspect_hw', None)
    aspect_wh = kwargs.get('aspect_wh', None)
    
    if clear_img_border == True:
        img = clear_border(img)
    
    metrics = ('area', 'bbox', 'centroid', 'coords', 'eccentricity', 'equivalent_diameter', 'major_axis_length', 'minor_axis_length', 'solidity')
    prop_temp = pd.DataFrame(regionprops_table(label(img), properties = metrics))
    prop_temp['area dev'] = abs(prop_temp['area']-prop_temp['area'].median())
    prop_temp['width'] = prop_temp['bbox-3']-prop_temp['bbox-1']
    prop_temp['height'] = prop_temp['bbox-2']-prop_temp['bbox-0']
    prop_temp['aspect'] = prop_temp['height']/prop_temp['width']
    prop_temp['aspect_wh'] = prop_temp['width']/prop_temp['height']

    if area_std:
        area_th = prop_temp['area'].std()*area_std
        Index_label = prop_temp[(prop_temp['area dev'] > area_th)].index.tolist()
        img = img*1
        if Index_label !=[]:
            for rem in Index_label:
                img = flood_fill(img, (prop_temp['coords'][rem][0][0], prop_temp['coords'][rem][0][1]), 2)

    if solidity:
        Index_label = prop_temp[(prop_temp['solidity'] < solidity)].index.tolist()
        img = img*1
        if Index_label !=[]:
            for rem in Index_label:
                img = flood_fill(img, (prop_temp['coords'][rem][0][0], prop_temp['coords'][rem][0][1]), 2)
    if aspect_hw:
        Index_label = prop_temp[(prop_temp['aspect'] > aspect_hw)].index.tolist()
        img = img*1
        if Index_label !=[]:
            for rem in Index_label:
                img = flood_fill(img, (prop_temp['coords'][rem][0][0], prop_temp['coords'][rem][0][1]), 2)
                
    if aspect_wh:
        Index_label = prop_temp[(prop_temp['aspect_wh'] > aspect_wh)].index.tolist()
        img = img*1
        if Index_label !=[]:
            for rem in Index_label:
                img = flood_fill(img, (prop_temp['coords'][rem][0][0], prop_temp['coords'][rem][0][1]), 2)


    return img

def bubbleAnalysis(obj):  
    G = obj['sampleimg']
    img_path = obj['image_path']
    G = io.imread(G)
    G = rgb2gray(G)
    S = io.imread(img_path)
    S = rgb2gray(S)
    c_magenta = [1,0,1]
    try:
        callfrom = obj['callfrom']
        batch = obj['batch'] 
    except:
        batch = False
        callfrom = 'normalcall'

    draw_val = obj['draw_val']
    popup_val = float(obj['popup_val'])
    scale = (popup_val/ draw_val)  #*unitval
    popup_unit = obj['popup_unit']
    mu_encode = b'\xce\xbcm'
    units = mu_encode.decode(encoding='UTF-8')
    if popup_unit == 'px':
        scale = 1
        popup_unit = 'px'
        scalebar = False
    else:
        scalebar = True
    
    if popup_unit == units: 
        scale = scale*1000
        popup_unit = 'nm'
    #excel_mode = obj['excel_mode']
    anatype = obj['analysislist']#'void'
    cmpltdata = []
    
    orignalpath = obj['orignalpath']
    fpath, _  = os.path.splitext(orignalpath)
    basefoldername, foldername = os.path.split(fpath)
    
    if not os.path.exists(fpath):
        os.mkdir(fpath)
    
#     foldername, _ = os.path.split(img_path)
#     basefoldername = os.path.split(os.path.dirname(img_path))[0]
    output_dir = fetchKeysValue('output_dir', obj)
    if output_dir:
        callfrom = 'backgroundbatch'
    else:
        callfrom = 'normalcall'
        
    if callfrom == 'backgroundbatch':

        output_dir = obj['output_dir']
        batchdir = output_dir
        output_dir = addSlashonLastIndex(output_dir)
        batchdir = output_dir
        

    else:
        output_dir = ''
        batchdir = basefoldername + '/batchprocessed/'
        batchdir = checkEnv(batchdir)
        if not os.path.exists(batchdir):
            os.mkdir(batchdir)
        output_dir = batchdir
    cmpltdata = []
    error = False
    try:
        
        #try segmenting for stage 2
        B = gaussian(G, 1)
        #B = S
        thresholds = threshold_multiotsu(B,classes=3)
        regions = np.digitize(B, bins=thresholds)
        S = regions>0
        S = remove_small_objects(S, min_size=1000, connectivity=2)
        S = remove_small_holes(S, 20, connectivity=2)
        S = binary_opening(S,disk(3))
        
        MK = np.zeros_like(S)
        MK[:,1:-1] = 1
        S = clear_border(S, mask=MK.astype(bool))
        
        S1 = binary_opening(S,disk(int(S.shape[1]/100)))
        if len(np.unique(label(S)))==len(np.unique(label(S1))):
            S = S1
        else:
            pass
        
        
        #decide class of bubble features
        S0 = S==0
        S0 = clear_border(S0, mask=MK.astype(bool))
        L0 = label(S0, connectivity = 2)
        L = label(S, connectivity = 2)
        metrics = ('area', 'bbox', 'centroid', 'coords', 'eccentricity', 'solidity')
        data = pd.DataFrame(regionprops_table(L, properties = metrics))
        feature_clx_light = []
        feature_clx_dark = []
        SC = np.zeros_like(S)
        SC0 = np.zeros_like(S)
        for feat in range(len(data)):
        #     LL = flood(S, (int(data['centroid-0'][obj]), int(data['centroid-1'][obj])))
        #     CL = CL + LL*(obj+1)
            C = (L==feat+1)*1
            C = remove_small_holes(C==1, area_threshold=int(S.size/20), connectivity=2)
            SC = SC+C
            data_temp = pd.DataFrame(regionprops_table(label(C, connectivity=2), properties = metrics))
            clx_light = np.count_nonzero(np.asarray(C[data_temp['bbox-0'][0]:data_temp['bbox-2'][0],data_temp['bbox-1'][0]:data_temp['bbox-3'][0]]), axis=1)
            feature_clx_light.append(clx_light)
            
            C0 = (L0==feat+1)*1
            C0 = remove_small_holes(C0==1, area_threshold=int(S.size/20), connectivity=2)
            C0 = binary_opening(C0==1, disk(3))
            if np.sum(C0) != 0:
                SC0 = SC0+C0
                data_temp0 = pd.DataFrame(regionprops_table(label(C0, connectivity=2), properties = metrics))
                clx_dark = np.count_nonzero(np.asarray(C0[data_temp0['bbox-0'][0]:data_temp0['bbox-2'][0],data_temp0['bbox-1'][0]:data_temp0['bbox-3'][0]]), axis=1)
                feature_clx_dark.append(clx_dark)
            else:
                pass
        #     plt.imshow(C)
        
        feature_data_light = pd.DataFrame(feature_clx_light).T
        width_ratio_light = feature_data_light.std()/feature_data_light.mean()
        # width_ratio_light
        feature_data_dark = pd.DataFrame(feature_clx_dark).T
        width_ratio_dark = feature_data_dark.std()/feature_data_dark.mean()
        # width_ratio_dark
        
        stage1 = False
        stage2 = False
        stage3 = False
        if any(x > 0.1 for x in width_ratio_light):
            stage2 = True
            S = SC
            if np.mean(width_ratio_dark) < 0.1: 
                S = regions>0
                S = remove_small_objects(S, min_size=1000, connectivity=2)
                S = binary_opening(S ,disk(3))
                S = clear_border(S==0, mask=MK.astype(bool))
                S = binary_opening(S ,disk(4))
                S = remove_small_holes(S, 50, connectivity=2)
        else:
            stage1 = True
            t = threshold_otsu(B)
            S = B <= t
            S = S==0
            S = remove_small_objects(S, min_size=1000, connectivity=2)
            S = remove_small_holes(S, 20, connectivity=2)
            S = binary_opening(S,disk(3))
            S1 = binary_opening(S,disk(int(S.shape[1]/100)))
            if len(np.unique(label(S)))==len(np.unique(label(S1))):
                S = S1
            else:
                pass
        
        #clean features not in full height of image
        S = binary_closing(S*1, disk(4))
        S = remove_small_holes(S==1, 50)
        data_S = pd.DataFrame(regionprops_table(label(S), properties = metrics))
        data_S['feature height'] = data_S['bbox-2']-data_S['bbox-0']
        idx = data_S[data_S['feature height'] < S.shape[0]].index.tolist()
        S = S*1
        for rem in idx:
            S = flood_fill(S, (data_S['coords'][rem][0][0], data_S['coords'][rem][0][1]), 0, connectivity = 2)
        
        
        seg_img = fpath + '/segmented'+str(int(round(time.time() * 1000)))+'.png'
        c_magenta = [1,0,1]
        M1 = mark_boundaries(G, S, color=c_magenta, outline_color=None, mode='thick', background_label=0)
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.imshow(M1,cmap='gray')
        ax.axis('off')
        fig.savefig(seg_img, dpi=100, bbox_inches='tight', pad_inches=0) # save image as ""<img_name>_annotated"
        plt.close(fig)
        
        
        #guess peak/valley distance
        feat_S = label(S)
        FS = feat_S == 2
        props_F = pd.DataFrame(regionprops_table(label(FS)))
        FZ = np.zeros_like(S)
        FZ[props_F['bbox-0'][0]:props_F['bbox-2'][0],props_F['bbox-1'][0]:props_F['bbox-3'][0]] = 1
        FZ = FZ - FS*1
        FZ = binary_opening(FZ,disk(4))
        FZ = remove_small_objects(FZ,200)
        FZ = clear_border(FZ)
        FZ = clean_by(FZ, area_std=2)
        props_FZ = pd.DataFrame(regionprops_table(label(FZ==1)))
        props_FZ['height'] = props_FZ['bbox-2']-props_FZ['bbox-0']
        if props_FZ['height'].max()/props_FZ['height'].min() >1.75:
            sp = int(props_FZ['height'].min()*1.2)    
        else:
            sp = int(props_FZ['height'].mean()*1.2)
        
        metrics = ('area', 'bbox', 'centroid', 'coords', 'eccentricity', 'equivalent_diameter', 'major_axis_length', 'minor_axis_length', 'solidity')
        props = regionprops_table(label(S, connectivity=2), properties = metrics)
        
        data = pd.DataFrame(props)
        data['centroid-0'] = data['centroid-0'].astype(int)
        data['centroid-1'] = data['centroid-1'].astype(int)
        data['centroid-0-round'] = np.round(data['centroid-0'])
        data['centroid-1-round'] = np.round(data['centroid-1'])
        data['Object'] = range(1, len(data) + 1)
        data.sort_values(by=['bbox-1'], axis=0, ascending=True, inplace=True, kind='quicksort', na_position='last', ignore_index=True)
        d_ave = np.mean(data['equivalent_diameter'])*1
        
        metrics_p = ('area', 'centroid', 'bbox', 'coords')
        pairs_x = np.empty(S.shape)
        pairs_neg = np.empty(S.shape)
        pairs_agg = np.zeros_like(S)
        features = np.zeros_like(S)
        vals = np.zeros_like(S)
        pks = np.zeros_like(S)
        dist_x = []
        pitch_x = []
        obj_pairs = []
        x_spacing = []
        nb = 0
        S = S*1
        for circle in range(len(data)):
        
          S = S*1
          c_orig = flood(S, (data['coords'][circle][0][0], data['coords'][circle][0][1]))
          if circle<len(data)-1:
              cx = flood(S, (data['coords'][circle+1][0][0], data['coords'][circle+1][0][1]))
              pairs = c_orig+cx
          else:
              pairs = c_orig
          
          c_labels = label(pairs, background=None, return_num=True)
          if c_labels[1]==2:
              pair_rp = regionprops_table(label(pairs),properties = metrics_p)       
              ZR = np.zeros_like(S)
        #         ZR[pair_rp['bbox-0'].max():pair_rp['bbox-2'].min(),pair_rp['centroid-1'].astype(int).min():pair_rp['centroid-1'].astype(int).max()] = 1
              ZR[pair_rp['bbox-0'].max():pair_rp['bbox-2'].min(),pair_rp['centroid-1'].astype(int).min():pair_rp['centroid-1'].astype(int).max()] = 1
        
              DFF = ZR-pairs*1      
              neg_s = DFF == 1
              neg_s = remove_small_objects(neg_s,20)
              #pairs_neg = np.dstack((pairs_neg, neg_s))
              
              pairs_agg = np.dstack((pairs_agg, pairs))
              features = features + neg_s*1
              
              clx = np.count_nonzero(np.asarray(neg_s[pair_rp['bbox-0'].max():pair_rp['bbox-2'].min(),pair_rp['centroid-1'].astype(int).min():pair_rp['centroid-1'].astype(int).max()]), axis=1)
              x_spacing.append(list(clx)) 
              nb = nb+1 # number of features
        
          else:
              pass
        
        # M2 = label2rgb(features, B, colors=list([c_magenta]), alpha=0.3, bg_label=0, bg_color=None, image_alpha=1, kind='overlay')
        # plt.imshow(M2)
        
        # sp = 175 #spock 125
        SL = label(features)
        measures_bcd = pd.DataFrame()
        measures_lcd = pd.DataFrame()
        LL = np.zeros_like(S)
        BL = np.zeros_like(S)
        for feat in range(nb):
          S1 = SL==(feat+1)
          x = np.sum(S1*1,axis=1)
          x_inv = x*(-1)
          
          peaks, _ = find_peaks(x, distance=sp)
          valleys, _ = find_peaks(x_inv, distance=sp)
          results_half = peak_widths(x_inv, valleys, rel_height=0.5, wlen=sp)
          results_full = peak_widths(x, peaks, rel_height=1)
        
          axx_y = []
          axx_x = []
          axxmin = []
          axxmaj = []
          data_temp = pd.DataFrame()
          ds = cdist(peaks.reshape(-1,1),results_half[2].reshape(-1,1))
          for p in range(len(peaks)):
              #axmin = np.count_nonzero(S1[peaks[p],:]) #minor axis
              nz = np.nonzero(S1[peaks[p],:])[0]
              axmin = len(nz) #minor axis
              axmaj = np.min(ds[p,:])*2 #major axis
              if axmaj > axmin*2 and p>0:
                  axmaj = np.min(ds[p-1,:])*2 #major axis
              else:
                  pass 
              
              axx_y.append(peaks[p])
              axx_x.append(np.min(nz)+(np.max(nz) - np.min(nz))/2)
              axxmin.append(axmin)
              axxmaj.append(axmaj)
          
          lcd_y = []
          lcd_x = []
          l_cd = []
          for v in range(len(valleys)):
              nl = np.nonzero(S1[valleys[v],:])[0]
              lcd = len(nl) #minor axis
              lcd_y.append(valleys[v])
              lcd_x.append(np.min(nl)+(np.max(nl) - np.min(nl))/2)
              l_cd.append(lcd)
          
          temp_line = pd.DataFrame()
          temp_line['linecd'] = l_cd
          temp_line['lcd_x'] = lcd_x
          temp_line['lcd_y'] = lcd_y
          temp_line['feat'] = feat
          measures_lcd = measures_lcd.append(temp_line)
          
          temp_data = pd.DataFrame()
          temp_data['axmaj'] = axxmaj
          temp_data['axmin'] = axxmin
          temp_data['el_x'] = axx_x
          temp_data['el_y'] = axx_y
          temp_data['feat'] = feat
          measures_bcd = measures_bcd.append(temp_data)
          
          #draw Line CDs
          ZL = np.zeros_like(S)
          ZL[valleys,:] = 1
          L1 = (SL==feat+1)*ZL
          LL = LL + L1*(feat+1)
          vals = np.dstack((vals, ZL))
          
          #draw Bubble CDs
          ZL = np.zeros_like(S)
          ZL[peaks,:] = 1
          L1 = (SL==feat+1)*ZL
          BL = BL + L1*(feat+1)
          pks = np.dstack((pks, ZL))
          
          SL1 = S1
          SL1[peaks,:] = 0
          SL1[valleys,:] = 0
          SL1[(results_half[1:][1]).astype(int),:] = 0
          ML = mark_boundaries(G, SL1, color=c_magenta, outline_color=None, mode='thick', background_label=0)
        #     plt.figure(figsize=(10,10))
        #     plt.imshow(ML)
        vals = vals[:,:,1:]
        pks = pks[:,:,1:]
        
        if scalebar == True:
          measures_bcd['axmin_scale'] = measures_bcd['axmin']*scale
          measures_lcd['linecd_scale'] = measures_lcd['linecd']*scale
          bubblecd = measures_bcd[['axmin_scale', 'axmin', 'el_x', 'el_y', 'feat']].copy()
          linecd = measures_lcd[['linecd_scale', 'linecd', 'lcd_x', 'lcd_y', 'feat']].copy()
          bubblecd.columns = ['Bubble CD ('+popup_unit+')', 'Bubble CD  (px)', 'bcd_x', 'bcd_y', 'feat']
          linecd.columns = ['Line CD ('+popup_unit+')', 'Line CD  (px)', 'lcd_x', 'lcd_y', 'feat']
        else:
          bubblecd = measures_bcd[['axmin', 'el_x', 'el_y', 'feat']].copy()
          linecd = measures_lcd[['linecd', 'lcd_x', 'lcd_y', 'feat']].copy()
          bubblecd.columns = ['Bubble CD  (px)', 'bcd_x', 'bcd_y', 'feat']
          linecd.columns = ['Line CD  (px)', 'lcd_x', 'lcd_y', 'feat']
        
        
        
        # plot Line CD
        annotateimg2 = fpath + '/line_cd_'+str(int(round(time.time() * 1000)))+'.png'
        c_blue = [0,0,1]
        MLL = mark_boundaries(G, LL, color=c_blue, outline_color=None, mode='thick', background_label=0)
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.imshow(MLL,cmap='gray')

        label_ind = []
        for n in range(nb):
            for nl in range(len(linecd.loc[linecd['feat']==n])):
                ax.text(linecd.loc[linecd['feat']==n]['lcd_x'][nl], linecd.loc[linecd['feat']==n]['lcd_y'][nl], 'LCD'+'-'+str(+n+1)+'-'+str(nl), horizontalalignment='left', verticalalignment='top', color = c_blue, fontsize='large', fontweight='bold')
                label_ind.append('LCD'+'-'+str(+n+1)+'-'+str(nl))
        
        ax.axis('off')
        fig.savefig(annotateimg2, dpi=100, bbox_inches='tight', pad_inches=0) # save image as ""<img_name>_annotated"
        plt.close(fig)
        
        linecd['label'] = label_ind
        linecd.set_index('label', drop=True, append=False, inplace=True, verify_integrity=False)
        linecd.loc['mean'] = linecd.mean()
        linecd.loc['std'] = linecd[:-1].std()
        linecd.loc[['mean', 'std'],['lcd_x','lcd_y']] = np.nan
        
        #EXPORT CSV
        line_cd_csv = batchdir + foldername + '_line_cd.csv'
        linecd.round(2).drop(columns=['feat']).rename(columns={"lcd_x": "x-position (px)", "lcd_y": "y-position (px)"}).to_csv(line_cd_csv, index = True)
        
        
        # plot Bubble CD
        c_green = [0,1,0]
        annotateimg3 = fpath + '/bubble_cd'+str(int(round(time.time() * 1000)))+'.png' 
        BLL = mark_boundaries(G, BL, color=c_green, outline_color=None, mode='thick', background_label=0)
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.imshow(BLL,cmap='gray')
        
        label_ind = []
        for n in range(nb):
            for bl in range(len(bubblecd.loc[bubblecd['feat']==n])):
                ax.text(bubblecd.loc[bubblecd['feat']==n]['bcd_x'][bl], bubblecd.loc[bubblecd['feat']==n]['bcd_y'][bl], 'BCD'+'-'+str(+n+1)+'-'+str(bl), horizontalalignment='left', verticalalignment='top', color = c_green, fontsize='large', fontweight='bold')
                label_ind.append('BCD'+'-'+str(+n+1)+'-'+str(bl))
        
        ax.axis('off')
        fig.savefig(annotateimg3, dpi=100, bbox_inches='tight', pad_inches=0) # save image as ""<img_name>_annotated"
        plt.close(fig)
        
        bubblecd['label'] = label_ind
        bubblecd.set_index('label', drop=True, append=False, inplace=True, verify_integrity=False)
        bubblecd.loc['mean'] = bubblecd.mean()
        bubblecd.loc['std'] = bubblecd[:-1].std()
        bubblecd.loc[['mean', 'std'],['bcd_x','bcd_y']] = np.nan
        
        #Calculate bubble cd continuously
        pvals = np.zeros_like(S)
        ppks = np.zeros_like(S)
        bubble = np.zeros_like(S)
        sr = len(np.unique(LL))-1
        bbcd = []
        key = []
        LB = LL+BL
        for ft in range(sr):
            #get and store whole profile of features
        #     FF = (LL==ft+1 + BL==ft+1)
            FF = (SL==ft+1)*1
            LF = LB==ft+1
            LF = (LF*1)*FF
            fprops = pd.DataFrame(regionprops_table(label(FF),properties = metrics))
            props_temp = pd.DataFrame(regionprops_table(label(LF),properties = metrics))
            clx = np.count_nonzero(np.asarray(FF[fprops['bbox-0'][0]:fprops['bbox-2'][0],fprops['bbox-1'][0]:fprops['bbox-3'][0]]), axis=1)
            pv = np.zeros_like(clx)
            #pv[props_temp['centroid-0'].astype(int)] = 1
            V = (LL==ft+1)
            Z = (BL==ft+1)
            temp_v = V
            temp_p = Z
            props_temp_v = pd.DataFrame(regionprops_table(label(temp_v), properties = ('area', 'centroid', 'bbox')))
            props_temp_p = pd.DataFrame(regionprops_table(label(temp_p), properties = ('area', 'centroid', 'bbox')))
            pv[props_temp_v['centroid-0'].astype(int)] = 1
            pv[props_temp_p['centroid-0'].astype(int)] = 2   
            
            if scalebar == True:
                bbcd.append(list(clx*scale))
                key.append('Feature ' + str(ft+1) + ' ('+popup_unit+')')
            
            bbcd.append(list(clx))
            bbcd.append(list(pv))
            key.append('Feature ' + str(ft+1) + ' (px)')
            key.append('Feature ' + str(ft+1) + ' Peak/Valley')
        
        bb_cd = pd.DataFrame(bbcd)
        bb_cd['key'] = key
        bb_cd.set_index(['key'],inplace=True)
        bb_cd = bb_cd.T
        bb_cd.loc['mean'] = bb_cd.mean()
        bb_cd.loc['std'] = bb_cd[:-1].std()
        bb_cd.loc['area'] = bb_cd[:-2].sum()
        bb_cd.loc[['mean', 'std', 'area'],'Peak/Valley'] = np.nan
        if scalebar == True:
            bb_cd.loc['area', bb_cd.columns.str.endswith('('+popup_unit+')')] = bb_cd.loc['area', bb_cd.columns.str.endswith('('+popup_unit+')')]*scale
        
        #EXPORT CSV
        bubble_cd_csv = batchdir + foldername + '_bubble_cd.csv'
        bubblecd.drop(columns=['feat']).rename(columns={"bcd_x": "x-position (px)", "bcd_y": "y-position (px)"}).to_csv(bubble_cd_csv, index = True)
        
        #EXPORT CSV
        bubble_cd_cont_csv = batchdir + foldername + '_bubble_cd_cont.csv'
        bb_cd['label'] =  range(len(bb_cd))
        bb_cd.set_index('label',inplace=True)
        bb_cd.round(2).to_csv(bubble_cd_cont_csv, index = True)
        
        
        pvals = np.zeros_like(S)
        ppks = np.zeros_like(S)
        spacingcd = pd.DataFrame()
        spacing = np.zeros_like(S)
        sr = len(np.unique(feat_S))-1
        spcd = []
        key = []
        for ft in range(sr):
            V = np.zeros_like(S)
            Z = np.zeros_like(S)
            if ft==0:
                V = (feat_S==ft+1) + vals[:,:,0]*1
                Z = (feat_S==ft+1) + pks[:,:,0]*1
            else:
                V = (feat_S==ft+1) + vals[:,:,ft-1]*1
                Z = (feat_S==ft+1) + pks[:,:,ft-1]*1
            pvals = pvals + (V>1)*(ft+1)
            ppks = ppks + (Z>1)*(ft+1)
            temp = (V>1)*(ft+1) + (Z>1)*(ft+1)
            spacing = spacing + temp
            props_temp = pd.DataFrame(regionprops_table(label(temp>0), properties = ('area', 'centroid', 'bbox')))
            props_temp['feat'] = ft
            spacingcd = spacingcd.append(props_temp)
            
            #get and store whole profile of features
            FF = feat_S==ft+1
            FF=FF*1
            fprops = pd.DataFrame(regionprops_table(label(FF),properties = metrics))
            clx = np.count_nonzero(np.asarray(FF[fprops['bbox-0'][0]:fprops['bbox-2'][0],fprops['bbox-1'][0]:fprops['bbox-3'][0]]), axis=1)
            pv = np.zeros_like(clx)
            pv[props_temp['centroid-0'].astype(int)] = 1
            
            if scalebar == True:
                spcd.append(list(clx*scale))
                key.append('Feature ' + str(ft+1) + ' ('+popup_unit+')')
            
            spcd.append(list(clx))
            spcd.append(list(pv))
            key.append('Feature ' + str(ft+1) + ' (px)')
            key.append('Feature ' + str(ft+1) + ' Peak/Valley')
        
        sp_cd = pd.DataFrame(spcd)
        sp_cd['key'] = key
        sp_cd.set_index(['key'],inplace=True)
        sp_cd = sp_cd.T
        sp_cd.loc['mean'] = sp_cd.mean()
        sp_cd.loc['std'] = sp_cd[:-1].std()
        sp_cd.loc['area'] = sp_cd[:-2].sum()
        sp_cd.loc[['mean', 'std', 'area'],'Peak/Valley'] = np.nan
        if scalebar == True:
            sp_cd.loc['area', sp_cd.columns.str.endswith('('+popup_unit+')')] = sp_cd.loc['area', sp_cd.columns.str.endswith('('+popup_unit+')')]*scale
        # sp_cd.round(2)
        
        annotateimg4 = fpath + '/bubble_annotated'+str(int(round(time.time() * 1000)))+'.png' 
        c_magenta = [1,0,1]
        PL = spacing        
        if scalebar == True:
            spacingcd['Spacer CD ('+popup_unit+')'] = (spacingcd['bbox-3']-spacingcd['bbox-1'])*scale
        spacingcd['Spacer CD (px)'] = spacingcd['bbox-3']-spacingcd['bbox-1']

        PLL = mark_boundaries(G, PL>0, color=c_magenta, outline_color=None, mode='thick', background_label=0)
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.imshow(PLL,cmap='gray')
        label_ind = []
        for n in range(sr):
            for pl in range(len(spacingcd.loc[spacingcd['feat']==n])):
                ax.text(spacingcd.loc[spacingcd['feat']==n]['centroid-1'][pl], spacingcd.loc[spacingcd['feat']==n]['centroid-0'][pl], 'SCD'+'-'+str(+n+1)+'-'+str(pl), horizontalalignment='left', verticalalignment='top', color = c_magenta, fontsize='large', fontweight='bold')
                label_ind.append('SCD'+'-'+str(+n+1)+'-'+str(pl))
        
        ax.axis('off')
        fig.savefig(annotateimg4, dpi=100, bbox_inches='tight', pad_inches=0) # save image as ""<img_name>_annotated"
        plt.close(fig)
        
        
        
        spacingcd['label'] = label_ind
        spacingcd['scd_x'] = spacingcd['centroid-1']
        spacingcd['scd_y'] = spacingcd['centroid-0']
        spacingcd.set_index('label', drop=True, append=False, inplace=True, verify_integrity=False)
        spacingcd.loc['mean'] = spacingcd.mean()
        spacingcd.loc['std'] = spacingcd[:-1].std()
        spacingcd.loc[['mean', 'std'],['scd_x', 'scd_y']] = np.nan
               
        #EXPORT CSV
        spacing_cd_csv = batchdir + foldername + '_spacer_cd.csv'
        
        spacingcd.drop(columns=['feat', 'area', 'centroid-0', 'centroid-1', 'bbox-0', 'bbox-1', 'bbox-2', 'bbox-3']).rename(columns={"scd_x": "x-position (px)", "scd_y": "y-position (px)"}).to_csv(spacing_cd_csv, index = True)
        #EXPORT CSV
        spacing_cd_cont_csv = batchdir + foldername + '_spacer_cd_cont.csv'
        sp_cd['label'] =  range(len(sp_cd))
        sp_cd.set_index('label',inplace=True)
        sp_cd.round(2).to_csv(spacing_cd_cont_csv, index = True)
        
        
        c_orange = [1,0.66,0]
        metrics = ('area', 'bbox', 'centroid')
        
        amp_vl = pd.DataFrame()
        amp_pk = pd.DataFrame()
        sr = len(np.unique(feat_S))-1
        MS_h = np.zeros_like(S)
        MS_h[1:-1,:] = 1
        for ft in range(sr):
            pk_amp = (feat_S==ft+1)*1 - (ppks==ft+1)*1
            vl_amp = (feat_S==ft+1)*1 - (pvals==ft+1)*1
            pk_amp = clear_border(pk_amp, mask=MS_h.astype(bool))
            vl_amp = clear_border(vl_amp, mask=MS_h.astype(bool))
            props_vl = pd.DataFrame(regionprops_table(label(vl_amp>0), properties = metrics))
            props_pk = pd.DataFrame(regionprops_table(label(pk_amp>0), properties = metrics))
            props_vl['feat'] = ft
            props_pk['feat'] = ft
            amp_vl = amp_vl.append(props_vl)
            amp_pk = amp_pk.append(props_pk)
        
        amp_pk['width'] = amp_pk['bbox-3']-amp_pk['bbox-1']
        amp_vl['width'] = amp_vl['bbox-3']-amp_vl['bbox-1']
        amp_pk['height'] = amp_pk['bbox-2']-amp_pk['bbox-0']
        amp_vl['height'] = amp_vl['bbox-2']-amp_vl['bbox-0']
        
        # EXPORT IMAGE "image"_bubble_amp_ABP.png
        bubble_amp_ABP = batchdir + foldername + '_bubble_amp_ABP.png'
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.imshow(G,cmap='gray')
        label_v = []
        for n in range(sr):
            dfplot = amp_vl.loc[amp_vl['feat']==n]
            for pl in range(len(dfplot)):
                #rect = mpatches.Rectangle((amp_vl['bbox-1'][pl], amp_vl['bbox-0'][pl]), amp_vl['width'][pl], amp_vl['height'][pl], fill=False, edgecolor=c_orange, linewidth=2, alpha = 0.5)
                rect = mpatches.Rectangle((dfplot['bbox-1'][pl], dfplot['bbox-0'][pl]), dfplot['width'][pl], dfplot['height'][pl], fill=False, edgecolor=c_orange, linewidth=2, alpha = 0.5)
                ax.add_patch(rect)
                ax.text(amp_vl.loc[amp_vl['feat']==n]['centroid-1'][pl], amp_vl.loc[amp_vl['feat']==n]['centroid-0'][pl], 'ABV'+'-'+str(+n+1)+'-'+str(pl), horizontalalignment='left', verticalalignment='top', color = c_orange, fontsize='large', fontweight='bold')
                label_v.append('ABV'+'-'+str(+n+1)+'-'+str(pl))
        
        ax.axis('off')
        fig.savefig(bubble_amp_ABP, dpi=100, bbox_inches='tight', pad_inches=0) # save image as ""<img_name>_annotated"
        plt.close(fig)
        
        # EXPORT IMAGE "image"_bubble_amp_ABV.png
        bubble_amp_ABV = batchdir + foldername + '_bubble_amp_ABV.png'
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.imshow(G,cmap='gray')
        label_p = []
        for n in range(sr):
            dfplot = amp_pk.loc[amp_pk['feat']==n]
            for pl in range(len(dfplot)):
                rect = mpatches.Rectangle((dfplot['bbox-1'][pl], dfplot['bbox-0'][pl]), dfplot['width'][pl], dfplot['height'][pl], fill=False, edgecolor=c_orange, linewidth=2, alpha = 0.5)
                ax.add_patch(rect)
                ax.text(amp_pk.loc[amp_pk['feat']==n]['centroid-1'][pl], amp_pk.loc[amp_pk['feat']==n]['centroid-0'][pl], 'ABP'+'-'+str(+n+1)+'-'+str(pl), horizontalalignment='left', verticalalignment='top', color = c_orange, fontsize='large', fontweight='bold')
                label_p.append('ABP'+'-'+str(+n+1)+'-'+str(pl))
        
        ax.axis('off')
        fig.savefig(bubble_amp_ABV, dpi=100, bbox_inches='tight', pad_inches=0) # save image as ""<img_name>_annotated"
        plt.close(fig)
        
        amp_vl['label'] = label_v
        amp_pk['label'] = label_p
        
        bubbleamp = amp_vl.copy()
        bubbleamp = bubbleamp.append(amp_pk)
        if scalebar == True:
            bubbleamp['Amplitude ('+popup_unit+')'] = bubbleamp['width']*scale
        bubbleamp['Amplitude (px)'] = bubbleamp['width']
        bubbleamp['amp_x'] = bubbleamp['centroid-1']
        bubbleamp['amp_y'] = bubbleamp['centroid-0']
        # bubbleamp.sort_values(by=['label','feat'], inplace = True)
        bubbleamp.set_index('label', drop=True, append=False, inplace=True, verify_integrity=False)
        bubbleamp.loc['mean'] = bubbleamp.mean()
        bubbleamp.loc['std'] = bubbleamp[:-1].std()
        bubbleamp.loc[['mean', 'std'],['amp_x','amp_y']] = np.nan
            
        #EXPORT CSV
        bubble_amp_csv = batchdir + foldername + '_bubble_amp.csv'
        bubbleamp.round(2).drop(columns=['feat', 'area', 'centroid-0', 'centroid-1', 'bbox-0', 'bbox-1', 'bbox-2', 'bbox-3', 'height', 'width']).rename(columns={"amp_x": "x-position (px)", "amp_y": "y-position (px)"}).to_csv(bubble_amp_csv, index = True)
        
        newbatchpath2 = batchdir + foldername + '_line_cd_.png'
        newbatchpath3 = batchdir + foldername + '_bubble_cd.png'
        newbatchpath = batchdir + foldername + '_spacer_cd.png'
        outbatch2, outputannotated = '', ''

        if callfrom == 'backgroundbatch' or output_dir:
            outbatch = output_dir + foldername + '_segmented.png'
            outbatch2 = output_dir + foldername + '_line_cd_.png'
            outbatch3 = output_dir + foldername + '_bubble_cd.png'
            outputannotated = output_dir + foldername + '_spacer_cd.png'
            copyFile(seg_img, outbatch)
            copyFile(annotateimg2, outbatch2)
            copyFile(annotateimg3, outbatch3)
            copyFile(annotateimg4, outputannotated)
            
        else:
            copyFile(annotateimg4, newbatchpath) 
            copyFile(annotateimg2, newbatchpath2) 
            copyFile(annotateimg3, newbatchpath3) 
        
        
        extraannotated = [ {'line_cd': outbatch2}, {'spacer_cd': outputannotated}, {'bubble_amp_ABP': bubble_amp_ABP}, {'bubble_amp_ABV': bubble_amp_ABV}, {'bubble_cd': annotateimg3}]
        extracsv = [{'line_cd_csv': line_cd_csv}, {'bubble_cd_csv': bubble_cd_csv}, {'bubble_cd_cont_csv': bubble_cd_cont_csv}, {'spacing_cd_csv': spacing_cd_csv},
        {'bubble_amp_csv': bubble_amp_csv}]
        data = {'analysis_type': 'bubble_analysis',
                'annotate_img': annotateimg3, 
                'otherannotated': extraannotated, 'othercsvs': extracsv}
        
        cmpltdata.append(data)
    except:
        traceback.print_exc()
        error = True
    
    # notification_data = [{'ImageName': foldername, 'Analysis':'Bubble Analysis', 'Applicable': True, 'Failed': error}]
    notification_data = [{'ImageName': foldername, 'Analysis':'Bubble Analysis', 'Failed': error}]

    data = {'Analysis': cmpltdata, 'error': notification_data}
    return data

def getBubbleAnalysisData(data, user_id, callfrom, popup_unit, 
                          draw_val, popup_val, output_dir,
                            error, orignalpath, scalebarextarction):

    calldata = {'batch': True, 'callfrom': callfrom, 
                'sampleimg': data['cropimg'], 
                'image_path': data['segmented_img'], 
                'excel_mode': 'new', 'analysislist': ['bubble_analysis'], 
                'draw_val': draw_val, 'popup_val': popup_val, 
                'popup_unit': popup_unit, 'output_dir': output_dir, 
                'orignalpath': orignalpath}
            
    data = bubbleAnalysis(calldata)
    
    error = data['error']
    
    error = [{**item, 'Scale bar':scalebarextarction} for item in error]
    b_analysis = data['Analysis']

    return b_analysis, error

def cropLargeAnnotationMetalVoid(image,threshold=240,crop=True):
    
    # convert to grayscale 8bit
    G = rgb2gray(image)
    G = img_as_ubyte(G)
    
    # Make an original copy for later
    G_original = G.copy()

    # Assumes a relatively white annotate box with default value = 240
    G = G > threshold
    
    # Cleaning up noise that might have been picked up
    G = binary_erosion(G,square(2))
    G = binary_dilation(G,square(3))
    G = binary_closing(G,square(2))
    
    # Additional noise removal
    G = remove_small_objects(G,G.shape[0]*G.shape[1]*0.0005)
    
    # All pixels below halfway point of image is 0 (we expect annotations to be at the top)
    G[round(G.shape[0]*0.5):,:]=0
    
    # Fill in holes within the annotation boxes
    G = ndimage.binary_fill_holes(G)

    # Measure bounding boxes and areas of each object
    df = regionprops_table(label(G), properties=('bbox','area'))

    # Convert measurements table to DataFrame
    df = pd.DataFrame(df)

    # We expect 4 annotation boxes. If there are more than 5, it is most likely noise
    # If more than 5 objects are identified, filter them by solidity
    # Else, pass the DataFrame as it is
    if len(df) > 5:
        df['solidity']=df['area']/((df['bbox-2']-df['bbox-0'])*(df['bbox-3']-df['bbox-1']))
        sorted_df = df.sort_values(by='solidity',ascending=False)
        filtered_df = sorted_df[sorted_df['solidity']>0.9]
    else:
        filtered_df = df
    
    filtered_df = filtered_df[(filtered_df['area']>2000)]
    
    # Reset the indices
    filtered_df.reset_index(inplace=True)
    
    # Create an empty black image
    seg = np.zeros_like(G)
    
    if len(filtered_df)>0:
        pass
    else:
        return G_original, seg
    
    bottom_most_bound = []
    # Cycle through all of the annotations, and then remove their info from original image
    for i in range(len(filtered_df)):
        
        topbound = filtered_df['bbox-0'].iloc[i]
        botbound = filtered_df['bbox-2'].iloc[i]
        leftbound = filtered_df['bbox-1'].iloc[i]
        rightbound = filtered_df['bbox-3'].iloc[i]

        seg[topbound:botbound,leftbound:rightbound]=1
        G_original[topbound:botbound,leftbound:rightbound]=255
        
        bottom_most_bound.append(botbound)
        bottom_most_bound = [max(bottom_most_bound)]
    
    if crop == True:
        # Instead of filtering, return cropped image
        filtered_image = G_original[bottom_most_bound[0]:,:]
    else:
        # Image has been filtered
        filtered_image = G_original

    return filtered_image, seg


def cropLargeAnnotationMetalVoid(image,threshold=240,crop=True):
    
    # convert to grayscale 8bit
    G = rgb2gray(image)
    G = img_as_ubyte(G)
    
    # Make an original copy for later
    G_original = G.copy()

    # Assumes a relatively white annotate box with default value = 240
    G = G > threshold
    
    # Cleaning up noise that might have been picked up
    G = binary_erosion(G,square(2))
    G = binary_dilation(G,square(3))
    G = binary_closing(G,square(2))
    
    # Additional noise removal
    G = remove_small_objects(G,G.shape[0]*G.shape[1]*0.0005)
    
    # All pixels below halfway point of image is 0 (we expect annotations to be at the top)
    G[round(G.shape[0]*0.5):,:]=0
    
    # Fill in holes within the annotation boxes
    G = ndimage.binary_fill_holes(G)

    # Measure bounding boxes and areas of each object
    df = regionprops_table(label(G), properties=('bbox','area'))

    # Convert measurements table to DataFrame
    df = pd.DataFrame(df)

    # We expect 4 annotation boxes. If there are more than 5, it is most likely noise
    # If more than 5 objects are identified, filter them by solidity
    # Else, pass the DataFrame as it is
    if len(df) > 5:
        df['solidity']=df['area']/((df['bbox-2']-df['bbox-0'])*(df['bbox-3']-df['bbox-1']))
        sorted_df = df.sort_values(by='solidity',ascending=False)
        filtered_df = sorted_df[sorted_df['solidity']>0.9]
    else:
        filtered_df = df
    
    filtered_df = filtered_df[(filtered_df['area']>2000)]
    
    # Reset the indices
    filtered_df.reset_index(inplace=True)
    
    # Create an empty black image
    seg = np.zeros_like(G)
    
    if len(filtered_df)>0:
        pass
    else:
        return G_original, seg
    
    bottom_most_bound = []
    # Cycle through all of the annotations, and then remove their info from original image
    for i in range(len(filtered_df)):
        
        topbound = filtered_df['bbox-0'].iloc[i]
        botbound = filtered_df['bbox-2'].iloc[i]
        leftbound = filtered_df['bbox-1'].iloc[i]
        rightbound = filtered_df['bbox-3'].iloc[i]

        seg[topbound:botbound,leftbound:rightbound]=1
        G_original[topbound:botbound,leftbound:rightbound]=255
        
        bottom_most_bound.append(botbound)
        bottom_most_bound = [max(bottom_most_bound)]
    
    if crop == True:
        # Instead of filtering, return cropped image
        filtered_image = G_original[bottom_most_bound[0]:,:]
    else:
        # Image has been filtered
        filtered_image = G_original

    return filtered_image, seg


def removeAnnotateFromMetalVoidImg(img,thresh=200,hpad=10, vpad=30,area_thresh=100):
    G = rgb2gray(img)
    G = img_as_ubyte(G)
    seg = G > thresh
    seg = clear_border(seg)
    seg = np.invert(seg)
    seg = clear_border(seg)
    seg = np.invert(seg)
    
    strings = pytesseract.image_to_data(seg,
                                        config = r'tessedit_char_whitelist=0123456789\
                                        abcdefghijklmnopqrstuvwxyz\
                                        ABCDEFGHIJKLMNOPQRSTUVWXYZ \
                                        tessedit_char_blacklist=- \
                                        --psm 6 --oem 3',
                                        output_type='data.frame')  
    strings.dropna(inplace=True)
    
#     if len(strings)<1:
#         return None, None
    
#     strings = strings[strings['text'].str.isalnum()]

    if len(strings)>0:
        strings = strings[strings['text'].str.isalnum()]
    
    if len(strings)<1:
        seg = np.zeros_like(G)
        return seg, (0,1,0,1)
    
    topbound = strings['top'].iloc[0]-vpad
    botbound = strings['top'].iloc[0]+strings['height'].iloc[0]+vpad
    leftbound = strings['left'].iloc[0]-hpad
    rightbound = strings['left'].iloc[0]+strings['width'].iloc[0]+hpad

    seg[topbound:botbound,leftbound:rightbound]=0
    
    seg = np.invert(seg)
    seg = remove_small_objects(seg,area_thresh)
    
    return seg, (topbound,botbound,leftbound,rightbound)


def cropLargeAnnotationMetalVoid(image,threshold=240,crop=True):
    
    # convert to grayscale 8bit
    G = rgb2gray(image)
    G = img_as_ubyte(G)
    
    # Make an original copy for later
    G_original = G.copy()

    # Assumes a relatively white annotate box with default value = 240
    G = G > threshold
    
    # Cleaning up noise that might have been picked up
    G = binary_erosion(G,square(2))
    G = binary_dilation(G,square(3))
    G = binary_closing(G,square(2))
    
    # Additional noise removal
    G = remove_small_objects(G,G.shape[0]*G.shape[1]*0.0005)
    
    # All pixels below halfway point of image is 0 (we expect annotations to be at the top)
    G[round(G.shape[0]*0.5):,:]=0
    
    # Fill in holes within the annotation boxes
    G = ndimage.binary_fill_holes(G)

    # Measure bounding boxes and areas of each object
    df = regionprops_table(label(G), properties=('bbox','area'))

    # Convert measurements table to DataFrame
    df = pd.DataFrame(df)

    # We expect 4 annotation boxes. If there are more than 5, it is most likely noise
    # If more than 5 objects are identified, filter them by solidity
    # Else, pass the DataFrame as it is
    if len(df) > 5:
        df['solidity']=df['area']/((df['bbox-2']-df['bbox-0'])*(df['bbox-3']-df['bbox-1']))
        sorted_df = df.sort_values(by='solidity',ascending=False)
        filtered_df = sorted_df[sorted_df['solidity']>0.9]
    else:
        filtered_df = df
    
    filtered_df = filtered_df[(filtered_df['area']>2000)]
    
    # Reset the indices
    filtered_df.reset_index(inplace=True)
    
    # Create an empty black image
    seg = np.zeros_like(G)
    
    if len(filtered_df)>0:
        pass
    else:
        return G_original, seg
    
    bottom_most_bound = []
    # Cycle through all of the annotations, and then remove their info from original image
    for i in range(len(filtered_df)):
        
        topbound = filtered_df['bbox-0'].iloc[i]
        botbound = filtered_df['bbox-2'].iloc[i]
        leftbound = filtered_df['bbox-1'].iloc[i]
        rightbound = filtered_df['bbox-3'].iloc[i]

        seg[topbound:botbound,leftbound:rightbound]=1
        G_original[topbound:botbound,leftbound:rightbound]=255
        
        bottom_most_bound.append(botbound)
        bottom_most_bound = [max(bottom_most_bound)]
    
    if crop == True:
        # Instead of filtering, return cropped image
        filtered_image = G_original[bottom_most_bound[0]:,:]
    else:
        # Image has been filtered
        filtered_image = G_original

    return filtered_image, seg


def MVAnalysis(obj):  
    G = obj['sampleimg']
    img_path = obj['image_path']
    try:
        G = io.imread(G)
    except:
        G = Image.open(G)
        G = np.asarray(G)
    G = rgb2gray(G)
    try:
        S = io.imread(img_path)
    except:
        S = Image.open(img_path)
        S = np.asarray(S)

    S = rgb2gray(S)
    c_magenta = [1,0,1]
    
    try:
        callfrom = obj['callfrom']
        batch = obj['batch'] 
    except:
        batch = False
        callfrom = 'normalcall'

    draw_val = obj['draw_val']
    popup_val = float(obj['popup_val'])
    scale = fetchKeysValue('scale', obj)
    if not scale:
        scale = (popup_val/ draw_val)  #*unitval
    
    popup_unit = obj['popup_unit']
    mu_encode = b'\xce\xbcm'
    units = mu_encode.decode(encoding='UTF-8')
    
    spacing = fetchKeysValue('spacing', obj)
    if not spacing:
        spacing = 5 #  m #spacing for measurements in popup_unit

    scalebar = True
    
    if popup_unit == units: 
        scale = scale*1000
        popup_unit = 'nm'
        spacing = spacing/1000
    elif popup_unit == 'px':
        scale = 1
        scalebar = False
    
    
    #excel_mode = obj['excel_mode']
    # anatype = obj['analysislist']#'void'
    cmpltdata = []
    
    orignalpath = obj['orignalpath']
    fpath, _  = os.path.splitext(orignalpath)
    basefoldername, foldername = os.path.split(fpath)
    
    if not os.path.exists(fpath):
        os.mkdir(fpath)
    
    output_dir = fetchKeysValue('output_dir', obj)
    if output_dir:
        callfrom = 'backgroundbatch'
    else:
        callfrom = 'normalcall'
        
    if callfrom == 'backgroundbatch':

        output_dir = obj['output_dir']
        batchdir = output_dir
        output_dir = addSlashonLastIndex(output_dir)
        batchdir = output_dir
        

    else:
        output_dir = ''
        batchdir = basefoldername + '/batchprocessed/'
        batchdir = checkEnv(batchdir)
        if not os.path.exists(batchdir):
            os.mkdir(batchdir)
        output_dir = batchdir
    cmpltdata = []
    notification_data = []
    error = False
    imgname = foldername
    try:
        G, _ = cropLargeAnnotationMetalVoid(G)
        SM, bounds = removeAnnotateFromMetalVoidImg(G)
        G = gaussian(G,0.5)
        B = gaussian(G,0)
        
        preprocess_p = fpath + '/preprocess'+str(int(round(time.time() * 1000)))+'.png'
        io.imsave(preprocess_p, B)


        mt = threshold_multiotsu(B, 4)
        M = np.digitize(B, mt)
        S1 = M<2
        S1 = binary_opening(S1, disk(2))
        S1 = binary_closing(S1, disk(12))
        S1 = remove_small_objects(S1==1,S1.shape[1]*10)

        ST = S1
        # ZZ = np.zeros_like(S1)
        MK = np.zeros_like(S1)
        MK_left = np.zeros_like(S1)
        MK_right = np.zeros_like(S1)
        MK_left_only = np.zeros_like(S1)
        MK_right_only = np.zeros_like(S1)
        MK_left_only[:,1:] = 1
        MK_right_only[:,:-1] = 1
        MK[1:-1,:] = 1
        MK_left[1:-1,1:] = 1
        MK_right[1:-1,:-1] = 1
        S1 = clear_border(S1, mask=MK.astype(bool))
        metrics = ('area', 'centroid', 'bbox', 'coords')
        props_S1 = pd.DataFrame(regionprops_table(label(S1), properties = metrics))
        if len(props_S1) == 0:
            S1 = ST

        S_otsu = G<threshold_otsu(G)
        S_otsu = binary_opening(S_otsu, disk(5))
        S_otsu = remove_small_holes(S_otsu == 1,S1.shape[1]*2)
        #S1 = S1*S_otsu

        seg_img = fpath + '/segmented'+str(int(round(time.time() * 1000)))+'.png'
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.imshow(S1,cmap='gray')
        ax.axis('off')
        fig.savefig(seg_img, dpi=100, bbox_inches='tight', pad_inches=0) # save image as ""<img_name>_annotated"
        plt.close(fig)


        metrics = ('area', 'centroid', 'bbox', 'coords', 'orientation')
        data = pd.DataFrame(regionprops_table(label(S1), properties = metrics))
        data_inv = pd.DataFrame(regionprops_table(label(S1==0), properties = metrics))
        data['width'] = data['bbox-3']-data['bbox-1']
        data['height'] = data['bbox-2']-data['bbox-0']
        data_inv['height'] = data_inv['bbox-2']-data_inv['bbox-0']
        data_inv['width'] = data_inv['bbox-3']-data_inv['bbox-1']
        
        try:
            #use bottom metal tier as reference for rotation
            L1_temp, nn_temp = label(S1, return_num=True)
            L1_temp = abs(L1_temp-np.max(L1_temp)-1)*(L1_temp>0)
            RT = L1_temp==(1+np.min(L1_temp))
            props_RT = pd.DataFrame(regionprops_table(label(RT), properties = metrics))
            RT1 = np.zeros_like(RT)
            RT1[:,np.arange(0,RT.shape[1],20)] = 1
            RT1 = (RT1-RT*1)>0
            MK_bot_only = np.zeros_like(RT1)
            MK_bot_only[1:,:] = 1
            RT1 = clear_border(RT1, mask=MK_bot_only.astype(bool))
            RT1 = binary_dilation(RT1, rectangle(2,1))
            SR = RT1*RT
            props_SR = pd.DataFrame(regionprops_table(label(SR), properties = metrics))



            xl = np.array(props_SR['centroid-1']).reshape(-1, 1)
            yl = np.array(props_SR['centroid-0']).reshape(-1, 1)
            model_SR = LinearRegression().fit(xl, yl)
            pred_SR = model_SR.predict(xl)
            mean_rot = np.arctan(model_SR.coef_)[0][0]

        except:
            #use average rotation of all metal tiers as reference for rotation
            #Index_label = data[(data['width'] < S1.shape[1])].index.tolist()
            #Index_right_edge = data[(data['bbox-3'] < S1.shape[1])].index.tolist()
            mean_rot = np.pi/2+data['orientation'].mean()

            if len(data)<2:
                #Index_label = data_inv[(data_inv['width'] < S1.shape[1])].index.tolist()
                #Index_right_edge = data_inv[(data_inv['bbox-3'] < S1.shape[1])].index.tolist()
                mean_rot = np.pi/2+data_inv['orientation'].mean()

        #check shape
        Index_label = data[(data['width'] < S1.shape[1])].index.tolist()
        Index_right_edge = data[(data['bbox-3'] < S1.shape[1])].index.tolist()

        if len(data)<2:
            Index_label = data_inv[(data_inv['width'] < S1.shape[1])].index.tolist()
            Index_right_edge = data_inv[(data_inv['bbox-3'] < S1.shape[1])].index.tolist()

        #Index_label = data[(data['width'] < S1.shape[1])].index.tolist()
        #Index_right_edge = data[(data['bbox-3'] < S1.shape[1])].index.tolist()
        
        middle_image = []
        edge_image = []
        right_edge_image = []
        left_edge_image = []
        if len(Index_label)!=0:
            edge_image = True
            #if len(Index_right_edge)!=0:
            if len(Index_right_edge)>1:
                right_edge_image = True
            else:
                left_edge_image = True
            S1 = M<1
            S1 = binary_opening(S1, disk(1)) #small erosion due to text box
#             io.imsave('S1.png', S1*1)

            S1 = binary_closing(S1, disk(12))
            S1 = clear_border(S1, mask=MK.astype(bool))
            S1 = remove_small_objects(S1==1,S1.shape[1]*10)   
            S1 = S1*S_otsu
            props_S1 = pd.DataFrame(regionprops_table(label(S1), properties = metrics))
            if len(props_S1) == 0:
                SE = ST==0
                if left_edge_image == True:
                    SE = clear_border(SE, mask=MK_left_only.astype(bool))   
                if right_edge_image == True:
                    SE = clear_border(SE, mask=MK_right_only.astype(bool))   
                SE1 = binary_closing(SE, rectangle(int(data_inv['height'].median()*1.2),2))
                SE1 = SE1-SE*1
                SE1 = binary_opening(SE1, disk(5))
                SE1 = remove_small_objects(SE1 == 1,S1.shape[1]*2)
                SE2 = SE1 # without removing top/bottom metal tiers
                SE1 = clear_border(SE1, mask=MK.astype(bool)) ### this removes edge images with no recess
                S1 = SE1
                S1 = S1*binary_closing(S_otsu, disk(12))
        else:
            S1 = S1*binary_closing(S_otsu, disk(12))
            middle_image = True


        #2
        if edge_image == True:
            GG = unsharp_mask(G, radius=1, amount=1)
            # T = G<threshold_otsu(GG)
            local_thresh = threshold_local(B, 201)
            GL = B < local_thresh
            # CC = GL*1+(M==2)*2 #switch b/w 1,2

            # CC = GL*1+(M<2)*2 #4
            CC = GL*1+(M<2)*2 #4b if inadequate
            #io.imsave('CC.png', CC*1)
            CC = remove_small_objects(CC, 50)
            # CC = binary_closing(CC, disk(5)) # 4a
            CC = remove_small_objects(CC==0,500)
            CC = remove_small_holes(CC,500)
            CC = binary_opening(CC, disk(5))
            CC1 = CC

            if left_edge_image==True:
                CC = clear_border(CC, mask=MK_left.astype(bool))
            if right_edge_image==True:
                CC = clear_border(CC, mask=MK_right.astype(bool))

            CC = remove_small_objects(CC==1, 20000)
            CC = binary_closing(CC, rectangle(5,5))

            if np.sum(CC) < 500 or len(np.unique(label(CC))) < len(data):
                CC = GL*1+(M<3)*2 #4b if inadequate
                #io.imsave('CC.png', CC*1)
                CC = remove_small_objects(CC, 50)
                CC = binary_closing(CC, disk(5)) # 4a
                CC = remove_small_objects(CC==0,500)
                CC = remove_small_holes(CC,500)
                CC = binary_opening(CC, disk(5))
                if left_edge_image==True:
                    CC = clear_border(CC, mask=MK_left.astype(bool))
                if right_edge_image==True:
                    CC = clear_border(CC, mask=MK_right.astype(bool))

                CC1 = CC
                CC = remove_small_objects(CC==1, 20000)
                CC = binary_closing(CC, rectangle(5,5))
                CC = remove_small_holes(CC==1, 100)
            c_magenta = [1,0,1]
            c_cyan = [0,1,1]
            MG = mark_boundaries(G, CC, color=c_magenta, outline_color=None, mode='thick', background_label=0)    
            MG = mark_boundaries(MG, S1, color=c_cyan, outline_color=None, mode='thick', background_label=0)

            fig, ax = plt.subplots(figsize=(10, 10))
            ax.imshow(MG,cmap='gray')
            ax.axis('off')
            image_name = batchdir + imgname + '_edge_tiers.png'
            fig.savefig(image_name, dpi=100, bbox_inches='tight', pad_inches=0)
            plt.close(fig)
        
            
            if np.sum(CC) < 500 or len(np.unique(label(CC))) < len(data)-1: ###
                SS1 = binary_closing(S1, rectangle(2,20))
                SS1_hole = SS1-S1*1
                try:
                    dil_amount = 40 #relate to feature_size
                    CS = binary_dilation(SS1,rectangle(dil_amount,1))
                    labels_CS = len(np.unique(label(CS)))
                    while (labels_CS>2):
                        dil_amount = dil_amount + 5
                        CS = binary_dilation(CS,rectangle(dil_amount,1))
                        labels_CS = len(np.unique(label(CS)))
                        if (labels_CS==2):
                            break
                    DT = CS*1+SS1*2
                    DT = DT==1
                    DT = binary_opening(DT, square(10))
                    DT_label = label(DT)
                    MK_top_only = np.zeros_like(DT)
                    MK_top_only[:-1,:] = 1
                    DT = clear_border(DT, mask=MK_top_only.astype(bool))
                    #DT_bottom = DT_label==1 #remove bottom diel. tiers
                    DT_top = DT_label==np.max(DT_label) # remove top tier only if touching
                    DT = DT - DT_top*1 #- DT_bottom*1
                    S_cut = binary_dilation(SS1, rectangle(1,dil_amount))
                    DT = DT-S_cut
                    DT = DT>0
                    DT = binary_opening(DT, rectangle(25,dil_amount))
                    CC = DT #assing to dielectric tie
                except:
                    raise Exception('Error identifying dielectric tiers.')
        
        #visualization
        c_magenta = [1,0,1]
        c_cyan = [0,1,1]
        if edge_image == True:
            MG = mark_boundaries(G, CC, color=c_magenta, outline_color=None, mode='thick', background_label=0)
            MG = mark_boundaries(MG, S1, color=c_cyan, outline_color=None, mode='thick', background_label=0)
        else:
            MG = mark_boundaries(G, S1, color=c_cyan, outline_color=None, mode='thick', background_label=0)

#         fig, ax = plt.subplots(figsize=(10, 10))
#         ax.imshow(MG,cmap='gray')
#         ax.axis('off')
#         image_name = batchdir + imgname + '_edge_tiers.png'
#         fig.savefig(image_name, dpi=100, bbox_inches='tight', pad_inches=0)
#         plt.close(fig)

        feature_clx_light = []
        clx_light_columns = []
        if edge_image==True:
            #Z1 = np.ones_like(S1)-S1*1
            #Z1 = clear_border(Z1, mask=MK.astype(bool))
            ZL, nz = label(CC, return_num=True)
            ZL = abs(ZL-np.max(ZL)-1)*(ZL>0)

            props_z = pd.DataFrame(regionprops_table(ZL, properties = metrics))
            
            feature_clx_light = []
            for tier in range(nz):
                C = (ZL == tier+1)*1
                data_temp = pd.DataFrame(regionprops_table(label(C, connectivity=2), properties = metrics))
                #clx_light = np.count_nonzero(np.asarray(C[data_temp['bbox-0'][0]:data_temp['bbox-2'][0],data_temp['bbox-1'][0]:data_temp['bbox-3'][0]]), axis=0)
                clx_light = np.count_nonzero(np.asarray(C[data_temp['bbox-0'][0]:data_temp['bbox-2'][0],0:C.shape[1]]), axis=0)
                feature_clx_light.append(clx_light)
                clx_light_columns.append('Dielectric tier ' + str(tier+1))
            
            feature_data_light = pd.DataFrame(feature_clx_light).T
            max_dielectric_width = len(feature_data_light)
            left_most_tier = props_z['bbox-1'].min()
            right_most_tier = props_z['bbox-3'].max()

#         # first pass at dielectric
        GG = adjust_gamma(G,0.55)
        GG = unsharp_mask(GG, radius=2, amount=1.5)

        SS1 = binary_closing(S1, rectangle(4,20))
        L1, nn = label(SS1, return_num=True)
        L1 = abs(L1-np.max(L1)-1)*(L1>0)
        L1 = L1*S1
        c_magenta = [1,0,1]
        c_cyan = [0,1,1]
        MS = mark_boundaries(G, S1, color=c_magenta, outline_color=None, mode='thick', background_label=0)
        # plt.figure(figsize=(15,15))
        # plt.imshow(MS)

        #get voids
        MV = np.zeros_like(S1)
        if edge_image == True:
            nsizes = list(np.arange(67,103,6))
            nsizes.reverse()    
        elif middle_image == True:
            nsizes = list(np.arange(43,99,6))
            nsizes.reverse()

        
        for i, block_size in enumerate(nsizes):
            local_thresh = threshold_local(B, block_size)
            V = B > local_thresh

            # V = B<t*1.25
            # V = M>0
            SC = binary_erosion(S1, disk(4)) # have to do this bc of text in metal tier
            S2 = V*SC
            #io.imsave('S2.png', S2*1)
            S2 = remove_small_objects(S2, 100)
            LS2 = L1*S2
            top_row_rem = LS2==1
            top_row_rem = remove_small_objects(top_row_rem==1, 200)
            LS2 = (top_row_rem*LS2+LS2>1)*LS2
            LM = L1-LS2
            
#             if SM.any()!=None:
#                 LM = (SM<1)*LM
#                 LS2 = (SM<1)*LS2
#             else:
#                 LM = LM
                
            if SM.any() and SM.any()==1:
                LM = (SM<1)*LM
                LS2 = (SM<1)*LS2*SC
            else:
                LM = LM*SC
                
            MS2 = mark_boundaries(GG, LS2, color=c_cyan, outline_color=None, mode='thin', background_label=0)
            #MS2 = mark_boundaries(adjust_gamma(G,0.55), ((LS2*1-SM*1)>0)*1, color=c_cyan, outline_color=None, mode='thin', background_label=0)
            #MS2 = mark_boundaries(G, LS2, color=c_cyan, outline_color=None, mode='thin', background_label=0)

            # SAVE IMAGES FOR EVERY ITERATION IN THIS LOOP
            io.imsave(batchdir + 'sweep_'+imgname+'_sensitivity_'+str(i+1)+'.png',MS2)

            MV = np.dstack((MV, LS2))


        MV = MV[:,:,1:]

        # metal tier properties

        metrics = ('area', 'centroid', 'bbox', 'coords')
        tiers = pd.DataFrame(regionprops_table(LM, properties = metrics))
        tiers_metal_consistent = pd.DataFrame(regionprops_table(L1, properties = metrics))
        # tiers.sort_values(['centroid-0', 'centroid-1'], ascending = [False, True], ignore_index = True, inplace = True)

        # take each metal void data and compare to metal data
        dfs = []
        df_labels = []

        tv = []
        for i in range(len(nsizes)):
            props = pd.DataFrame()
            #props['Metal area (px)'] = tiers['area']
            props['Metal area (px)'] = tiers_metal_consistent['area'].astype(int)
            props['Void area (px)'] = np.nan

            for tier in range(len(tiers)):
                props.at[tier,'Void area (px)'] = np.sum(MV[:,:,i]==tier+1)
            props['Void area (px)']=props['Void area (px)'].astype(int)
            
            props['Metal void area ('+popup_unit+')^2'] = props['Void area (px)']*scale
            props['Metal void area ('+popup_unit+')^2'] = props['Metal void area ('+popup_unit+')^2'].astype(int)
  

            #props['V+M area (px)'] = (props['Metal area (px)']+props['Void area (px)']).astype(int)
            props['V+M area (px)'] = (tiers_metal_consistent['area']).astype(int)
            props['Metal void area %'] = np.round(props['Void area (px)']/props['V+M area (px)']*100,2)
            total_void_perc = np.round(props['Void area (px)'].sum()/props['Metal area (px)'].sum()*100,2)
            tv.append(total_void_perc)
            #props.at[0,'Total void %'] = total_void_perc
            dfs.append(props)
            df_labels.append('sensitivity ' + str(i+1))

        total_void_percentage = df2=pd.concat(dfs, keys=df_labels, axis=1)

        df2=pd.concat(dfs, keys=df_labels, axis=1, names=['Option', 'Measures'])
        df2.drop(['Void area (px)', 'Metal area (px)', 'V+M area (px)'], axis=1, level=1, inplace=True)


        df3 = df2.iloc[:, df2.columns.get_level_values(1)=='Metal void area %']
        df3 = df3.loc[~(df3==0).all(axis=1)]
        df3loc = df3.iloc[:, df3.columns.get_level_values(1)=='Measures'] # the rows that have voids

        df3['Metal void % slope'] = np.nan
        for i in df3loc.index:
            x = np.arange(1,len(nsizes)+1,1).reshape((-1, 1))
            y = np.array(df3.loc[i][:-1])
            model = LinearRegression().fit(x, y)
            df3.loc[i, 'Metal void % slope'] = model.coef_

        df2.replace(0, np.nan, inplace=True)
        if scalebar == True:
            df2['Metal tier area ('+popup_unit+')^2'] = props['Metal area (px)']*scale
        df2['Metal tier area ('+popup_unit+')^2'] = df2['Metal tier area ('+popup_unit+')^2'].astype(int)
        
        df2['Metal void % mean'] = df2.mean(axis=1, skipna=True, level=1).round(2).iloc[:,1]
        df2['Metal void % std'] = df2.std(axis=1, skipna=True, level=1).round(2).iloc[:,1]
        #df2['Metal void % std'] = df2.iloc[:,:-1].std(axis=1, skipna=True).round(2).iloc[:,1]
        df2['Metal void % slope'] = df3['Metal void % slope'].round(2)
        df2.at[len(df2)-1, 'Tilt angle (deg.)'] = np.degrees(mean_rot).round(2)
        df2.insert(0, column='Metal tier', value=range(1, len(props) + 1))

        ## EXPORT CSV #1
        df2 = df2[::-1]
        mvsensitivities = batchdir + imgname+ '_metal_void_sensitivities.csv'
        df2.to_csv(mvsensitivities, index = False)

        ## EXPORT CSV #2

        props_v = df2[['Metal tier', 'Metal void % mean', 'Metal void % std', 'Metal void % slope']].droplevel('Measures', axis=1).copy()
        props_v['Total void % mean'] = np.nan
        props_v['Total void % std'] = np.nan
        props_v['Total void % mean'][len(props_v)-1] = np.mean(tv).round(2)
        props_v['Total void % std'][len(props_v)-1] = np.std(tv).round(2)
        metal_voids = output_dir +  imgname + '_metal_voids.csv'
        props_v.to_csv(metal_voids, index = False)


        if middle_image==True:
            Z1 = np.ones_like(S1)-S1*1
            Z1 = clear_border(Z1, mask=MK.astype(bool))
            ZL, nz = label(Z1, return_num=True)
            ZL = abs(ZL-np.max(ZL)-1)*(ZL>0)

            feature_clx_light = []
            for tier in range(nz):
                C = (ZL == tier+1)*1
                data_temp = pd.DataFrame(regionprops_table(label(C, connectivity=2), properties = metrics))
                #clx_light = np.count_nonzero(np.asarray(C[data_temp['bbox-0'][0]:data_temp['bbox-2'][0],data_temp['bbox-1'][0]:data_temp['bbox-3'][0]]), axis=0)
                clx_light = np.count_nonzero(np.asarray(C[data_temp['bbox-0'][0]:data_temp['bbox-2'][0],:]), axis=0)
                feature_clx_light.append(clx_light)
                clx_light_columns.append('Dielectric tier ' + str(tier+1))
            
            feature_data_light = pd.DataFrame(feature_clx_light).T
            max_dielectric_width = len(feature_data_light)
            #feature_data_light


        #measure metal tier height
        feature_clx_dark = []
        clx_dark_columns = []
        for tier in range(nn):
            #measures = int(S1.size[0]/spacing_px)
            C = (L1 == tier+1)*1
            data_temp = pd.DataFrame(regionprops_table(label(C, connectivity=2), properties = metrics))
            #clx_dark = np.count_nonzero(np.asarray(C[data_temp['bbox-0'][0]:data_temp['bbox-2'][0],data_temp['bbox-1'][0]:data_temp['bbox-3'][0]]), axis=0)
            clx_dark = np.count_nonzero(np.asarray(C[data_temp['bbox-0'][0]:data_temp['bbox-2'][0],:]), axis=0)
            feature_clx_dark.append(clx_dark)
            clx_dark_columns.append('Metal tier ' + str(tier+1))

        feature_data_dark = pd.DataFrame(feature_clx_dark).T
        max_metal_width = len(feature_data_dark)
        
        
        D_seg = ZL>0
        M_seg = L1>0

        #SPACING VARIABLE
        spacing_px = int(spacing/scale)
        # measures = np.floor(max_width/spacing_px)
        if right_edge_image == True:
            measures_dielectric = np.arange(0,right_most_tier, spacing_px)
            measures_metal = measures_dielectric
        if left_edge_image == True:
            measures_dielectric = np.arange(left_most_tier,right_most_tier, spacing_px)
            measures_metal = measures_dielectric
        if middle_image == True:
            measures_dielectric = np.arange(0,max_dielectric_width, spacing_px)
            measures_metal = np.arange(0,max_metal_width, spacing_px)

        dielectric_thickness = feature_data_light.iloc[[measures_dielectric][0]]
        metal_thickness = feature_data_dark.iloc[[measures_metal][0]]

        dielectric_thickness.columns = clx_light_columns
        # dielectric_thickness.reset_index(level=None, drop=False, inplace=True, col_level=0)
        # dielectric_thickness.rename(columns={"index": "Location (px)"}, inplace=True)
        metal_thickness.columns = clx_dark_columns
        # metal_thickness.reset_index(level=None, drop=False, inplace=True, col_level=0)
        # metal_thickness.rename(columns={"index": "Location (px)"}, inplace=True)


        if scalebar == True:
            if mean_rot:
                metal_thickness = (metal_thickness*scale/np.cos(mean_rot)).round(2)    
            else:
                metal_thickness = (metal_thickness*scale).round(2)
            metal_thickness[metal_thickness.eq(0)] = ''
            metal_thickness['Location #'] = range(1, len(metal_thickness) + 1)
            metal_thickness['Location #'] = 'loc. ' + metal_thickness['Location #'].astype(str) #

            metal_thickness['Location (' + popup_unit + ')'] = np.round(measures_metal*scale,2)
            metal_thickness['Location (px)'] = measures_metal
            
            if mean_rot:
                dielectric_thickness = (dielectric_thickness*scale/np.cos(mean_rot)).round(2)
            else:
                dielectric_thickness = (dielectric_thickness*scale).round(2)
            dielectric_thickness[dielectric_thickness.eq(0)] = ''
            dielectric_thickness['Location #'] = range(1, len(dielectric_thickness) + 1)
            dielectric_thickness['Location #'] = 'loc. ' + dielectric_thickness['Location #'].astype(str) #

            dielectric_thickness['Location (' + popup_unit + ')'] = np.round(measures_dielectric*scale,2)
            dielectric_thickness['Location (px)'] = measures_dielectric           
            dielectric_thickness = dielectric_thickness.T[::-1]
            metal_thickness = metal_thickness.T[::-1]

        else:              
            if mean_rot:
                metal_thickness = metal_thickness/np.cos(mean_rot)
                dielectric_thickness = dielectric_thickness/np.cos(mean_rot)  
            else:
                metal_thickness = metal_thickness
                dielectric_thickness = dielectric_thickness  
            metal_thickness[metal_thickness.eq(0)] = ''
            dielectric_thickness[dielectric_thickness.eq(0)] = ''
            
            metal_thickness['Location #'] = range(1, len(metal_thickness) + 1)
            metal_thickness['Location #'] = 'loc. ' + metal_thickness['Location #'].astype(str) #
            metal_thickness['Location (px)'] = measures_metal
            dielectric_thickness['Location #'] = range(1, len(dielectric_thickness) + 1)
            dielectric_thickness['Location #'] = 'loc. ' + dielectric_thickness['Location #'].astype(str) #
            dielectric_thickness['Location (px)'] = measures_dielectric           

            dielectric_thickness = dielectric_thickness.T[::-1]
            metal_thickness = metal_thickness.T[::-1]
        
        metal_thickness.columns = metal_thickness.loc['Location #'].astype(str)
        dielectric_thickness.columns = dielectric_thickness.loc['Location #'].astype(str)
        
        dielectric_thickness.reset_index(inplace=True)
        metal_thickness.reset_index(inplace=True)
        
        di_tiers = pd.DataFrame(regionprops_table(ZL, properties = metrics)) #dielectric tiers
                    

        #EXPORT CSV #1 & #2
        dielectric_thickness_csv = output_dir + imgname+ '_dielectric_thickness.csv'
        dielectric_thickness.to_csv(dielectric_thickness_csv, index=False, header=True)  
        metal_thickness_csv = output_dir + imgname+ '_metal_thickness.csv'
        metal_thickness.to_csv(metal_thickness_csv, index=False, header=True) 



        ## SAVE IMAGE
        fig, axarr = plt.subplots(1,2, figsize=(15,15))
        axarr[0].imshow(G, cmap='gray')
        axarr[0].set_title('Original')
        #text for metal tiers
        for tier in range(len(tiers)):
            axarr[0].text(tiers['centroid-1'][tier],  tiers['centroid-0'][tier]-0, 'Metal tier ' + str(tier+1), horizontalalignment='left', verticalalignment='top', color = 'w', fontsize='small', fontweight='bold')
        #text for dielectric tiers
        for tier in range(len(di_tiers)):
            axarr[0].text(di_tiers['centroid-1'][tier],  di_tiers['centroid-0'][tier]-0, 'Dielectric tier ' + str(tier+1), horizontalalignment='left', verticalalignment='top', color = 'k', fontsize='small', fontweight='bold')

        axarr[1].imshow(GG, cmap='gray')
        axarr[1].set_title('Enhanced')
        axarr[0].axis('off')
        axarr[1].axis('off')
        comparisonimg = batchdir + imgname + '_comparison.png' 
        fig.savefig(comparisonimg, bbox_inches='tight', dpi = 200)
        plt.close(fig)


        ## SAVE IMAGE
        # full annotation plot
        c_yellow = [1,1,0]
        VZ = np.zeros_like(S1)
        VZ = VZ+D_seg*2+M_seg*1
        VF = label2rgb(VZ, rescale_intensity(G), colors=list([c_magenta, c_yellow]), alpha=0.3, bg_label=0, bg_color=(0, 0, 0), image_alpha=1, kind='overlay')


        annotated = fpath + '/annotated' + str(int(round(time.time() * 1000)))+'.png'
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.imshow(G,cmap='gray')
        ax.axis('off')

        if middle_image==True:
            for i, xc in enumerate(measures_metal):
                plt.axvline(x=xc, color='m', linestyle='--', alpha = 0.8)
#                 ax.text(xc, VF.shape[0]-10, 'Loc. # ' + str(i+1), horizontalalignment='center', verticalalignment='center', color = 'm', fontsize='small')
                
        if edge_image==True:
            for i, xc in enumerate(measures_dielectric):
                plt.axvline(x=xc, color='m', linestyle='--', alpha = 0.8)

        for tier in range(len(tiers)):
            ax.text(tiers['centroid-1'][tier]+0,  tiers['centroid-0'][tier]-0, 'Metal tier ' + str(tier+1), horizontalalignment='left', verticalalignment='top', color = 'w', fontsize='large', fontweight='bold')
        #text for dielectric tiers
        for tier in range(len(di_tiers)):
            ax.text(di_tiers['centroid-1'][tier]+0,  di_tiers['centroid-0'][tier]-0, 'Dielectric tier ' + str(tier+1), horizontalalignment='left', verticalalignment='top', color = 'k', fontsize='large', fontweight='bold')
        
        fig.savefig(annotated, dpi=100, bbox_inches='tight', pad_inches=0)
        plt.close(fig)

        othercsvs = [{'metal_voids': metal_voids}, {'dielectric_thickness': dielectric_thickness_csv}, {'metal_thickness': metal_thickness_csv}, 
        {'metal_voids_sitivities': mvsensitivities}]
        data = {'analysis_type': 'metal_voids','annotate_img': annotated, 'othercsvs': othercsvs}
        cmpltdata.append(data)

       
        outbatch = output_dir + foldername + '_tier_thickness.png'
        copyFile(annotated, outbatch)

    except:
        traceback.print_exc()
        error = True
        
    # notification_data = [{'ImageName': foldername, 'Analysis':'Metal Voids', 'Applicable': True, 'Failed': error}]
    notification_data = [{'ImageName': foldername, 'Analysis':'Metal Voids', 'Failed': error}]

    data = {'Analysis': cmpltdata, 'error': notification_data}
    return data

def batch_mv(data, user_id, callfrom, popup_unit, draw_val, 
             popup_val, output_dir, error, orignalpath, 
             spacing, scale, scalebarextarction):

    calldata = {'batch': True, 'callfrom': callfrom, 
                'sampleimg': data['cropimg'], 
                'image_path': data['segmented_img'], 
                'analysislist': ['metal_voids'], 
                'draw_val': draw_val, 'popup_val': popup_val, 
                'popup_unit': popup_unit, 'output_dir': output_dir, 
                'orignalpath': orignalpath, 'spacing': spacing, 'scale':scale}
            
    data = MVAnalysis(calldata)
    error = data['error']
    error = [{**item, 'Scale bar':scalebarextarction} for item in error]

    return data['Analysis'], error

def cropAndSegAnalysis(Analysis_info, folderdata, p, img, output_dir, fullname,
                        newpath, user_id, obj, data, callfrom=''):
    analysis, excel_path, annotated, p_analysis, pdf_path, tier_voids_analysis, metalrecess_analysis, bubble_analysis, pillar_c2c_analysis, pillar_anomaly_analysis, metal_voids_analysis = '', '', '', '', '', '', '', '', '', '', '',
    error = False

    if Analysis_info['carryanalysis'] and Analysis_info['analysis_type']:   
        for ana in Analysis_info['analysis_type']:
            scalebarextarction = fetchKeysValue('scalebarextarction', folderdata[p])
            draw_val = int(folderdata[p]['draw_val'])
            
            if float(folderdata[p]['popup_val']) < 1 and folderdata[p]['popup_unit'] == MICRONM:
                popup_val = float(float(folderdata[p]['popup_val'])*1000)
                popup_unit = 'nm'
            else:
                popup_val = float(folderdata[p]['popup_val'])
                popup_unit = folderdata[p]['popup_unit']
                
            scale = float(popup_val)/float(folderdata[p]['draw_val'])

            try:
                if ana == 'pillar_c2c_analysis' or ana == 'pillar2':
                    
                    pillar_c2c_analysis, error = batchpillarc2c(img, output_dir, os.path.splitext(fullname)[0], newpath, scale,
                                            folderdata[p]['popup_unit'], int(folderdata[p]['draw_val']),
                                            int(folderdata[p]['popup_val']), data['orignalpath'], user_id, obj, scalebarextarction)
                
                elif ana == 'pillar_analysis' or ana == 'pillar_analysis_combined':

                    analysis, excel_path, annotated, pdf_path, error = batchpillaranalysis(data, output_dir, os.path.splitext(fullname)[0], newpath, scale, popup_unit,
                                    draw_val, popup_val, data['orignalpath'], user_id, scalebarextarction)
                
                elif ana == 'pillar_anomaly_analysis' or ana == 'pillar_anomaly':
                    
                    ellipticity_threshold = fetchKeysValue('ellipticity_threshold', obj)
                    sigma_threshold = fetchKeysValue('sigma_threshold', obj)
                    
                    pillar_anomaly_analysis, error = batchpillaranomalyanalysis(img, output_dir, os.path.splitext(fullname)[0], newpath, scale, popup_unit,
                                                        ellipticity_threshold, sigma_threshold, scalebarextarction)

                elif ana == 'profile_analysis':
                    both = False
                    p_analysis, profileanalysis, outlineanalysis, scaled_data, error = getProfileAnalysisData(data,
                                                                                                               popup_unit, 
                                                                                                               draw_val, 
                                                                                                               popup_val, 
                                                                                                               user_id, 
                                                                                                               both,
                                                                                                                 callfrom,
                                                                                                                   Analysis_info['feature_profile_type'], 
                                                                                                                   output_dir, error, scalebarextarction,
                                                                                                                     os.path.splitext(fullname)[0])

                elif ana == 'tier_analysis':
                    tier_voids_analysis, error = getTierAnalysisData(data, user_id,
                                                                      callfrom, 
                                                                      Analysis_info['tier_type'],
                                                                        popup_unit, draw_val, 
                                                                        popup_val, output_dir, 
                                                                        error, scalebarextarction) 

                elif ana == 'metal_recess_analysis':
                    metalrecess_analysis, error = getMetalRecessAnalysisData(data, user_id, 
                                                                             callfrom, popup_unit, 
                                                                             draw_val, popup_val, 
                                                                             output_dir, Analysis_info[ 'metal_recess_type'], 
                                                                             error, scalebarextarction)
                elif ana == 'bubble_analysis':
                    bubble_analysis, error = getBubbleAnalysisData(data, user_id, callfrom, 
                                                                   popup_unit, draw_val, 
                                                                   popup_val, output_dir, 
                                                                   error, data['orignalpath'], 
                                                                   scalebarextarction)
                    
                elif ana == 'metal_voids_analysis':
                    spacing = fetchKeysValue('spacing', folderdata[p])
                    scale = fetchKeysValue('scale', folderdata[p])
                    metal_voids_analysis, error = batch_mv(data, user_id, 
                                                           callfrom, popup_unit, 
                                                           draw_val, popup_val, 
                                                           output_dir, error, data['orignalpath'], 
                                                           spacing, scale, scalebarextarction)

            except:
                traceback.print_exc()

    else:
        pass   

    response = {'analysis': analysis, 'excel_path': excel_path, 
                'annotate_img': annotated,'pdf_path': pdf_path, 
                'profile_analysis': p_analysis, 
                'tier_analysis': tier_voids_analysis, 
                'metal_recess_analysis': metalrecess_analysis, 
                'bubble_analysis': bubble_analysis,  
                'pillar_c2c_analysis': pillar_c2c_analysis, 
                'pillar_anomaly_analysis': pillar_anomaly_analysis, 
                'metal_voids_analysis':metal_voids_analysis}    
    return response



async def cropAndSegmentationwWf(obj, image_analysis_dao):
    global db 
    db = image_analysis_dao
    images_path = obj['image']
    original_path = obj['orignalpath']
    user_id = obj['user_id']
    pixelX = obj['PixleX']
    pixelY = obj['PixleY']
    sample_image = obj['sample_image']
    images_names = obj['images_names']
    retrieve = obj['workflow'][0]["retrieve"]
    default = checkWorkflowMode(obj['workflow'][0]["_id"],image_analysis_dao)
    newpath = createImageNamefolder(original_path)
    _, fullname = os.path.split(original_path)
    filt = list(filter(lambda val: val['Value'] == 'feature.match_template', obj['workflow'][0]['features']))
    if filt:
        if not filt[0]['Params']['template_cord']:
            dat = {"cropimg": sample_image, "segmented_img":images_path,
                   "preprocessedlayers": '', "segmentationlayers": '', 
                   "postprocessedlayers": '', "user_id":user_id,'progressbar':0}
            data = {'imagedata': dat, 'analysis':[]}
            return data
          
    # db = establishConnection()
    if retrieve:
        p, _  = os.path.splitext(original_path)
          
        collection = db.workflowimagespath
        report = collection.find_one({'sample_name': p},
                                    sort=[( '_id', pymongo.DESCENDING )])
        
        # bubble_analysis = fetchKeysValue('bubble_analysis', report)
        # tier_voids_analysis = fetchKeysValue('tier_analysis', report)
        # metal_recess_analysis = fetchKeysValue('metal_recess_analysis', report)
        # P_analysis = fetchKeysValue('profile_analysis', report)
        # pillar_c2c_analysis = fetchKeysValue('pillar_c2c_analysis', report)
        # pillar_anomaly_analysis = fetchKeysValue('pillar_anomaly_analysis', report)
        # metal_voids_analysis = fetchKeysValue('metal_voids_analysis', report)
        # data = {'imagedata': report['data'], 'analysis': report['analysis'], 'annotate_img': report['annotate_img'], 'excel_path': report['excel_path'], 'profile_analysis': P_analysis, 'pdf_path': report['pdf_path'],  'tier_analysis': tier_voids_analysis, 'metal_recess_analysis': metal_recess_analysis, 'bubble_analysis': bubble_analysis, 'pillar_c2c_analysis': pillar_c2c_analysis,
        #        'pillar_anomaly_analysis': pillar_anomaly_analysis, 'metal_voids_analysis':metal_voids_analysis}
        data = {"imagedata":report["data"]}   
    else:
        images_names = [x.replace('.png', '') for x in images_names]
    
        newpath, filename = os.path.split(original_path)
        newpath = createImageNamefolder( original_path)
        
        workflow = obj['workflow']
        applied = obj['applied']
        pathh = images_path
        pathhh_data = cv2.imread(pathh)
        img = rgbToGray(cv2.imread(pathh))

        # sample_imagep, sample_image , img = do_masking(original_path=original_path, newpath=newpath,images_path=images_path)
        if applied: #and modification['applyCropping']:
            try:
            
                collection = db.sampleworkflows
                wid = obj['workflow'][0]["_id"]
                report = collection.find_one(
                          {'_id': ObjectId(wid)})
    
                modification = report['modification']
                img = cropAndSegimageMasking(img, modification)
                newpathh = newpath + '/'+'image_masking'+'_'+str(int(round(time.time() * 1000)))+'.png'
                img = img_as_ubyte(img)
                cv2.imwrite(newpathh, img)
                sample_imagep = newpathh
                sample_image = img
                img = rgbToGray(img)
            except:
                traceback.print_exc()
                sample_image = img
                sample_imagep = images_path
        else:
            sample_imagep = sample_image
            sample_image = rgbToGray(io.imread(sample_image))
            sample_image = img
        
        img = skimage.util.img_as_float(img)
        
        callfrom='segmentationapi'
        mainwf = workflow[0]['features']
        post_visu = workflow[0]['post_visualization']
        scale = 1.5151
        if obj.get('popup_val') and obj.get('draw_val'):
            scale = int(obj['popup_val'])/ obj['draw_val']
        # else:
        #     scale = None
        popup_unit = obj.get('popup_unit') if (obj.get('popup_unit') and obj.get('popup_unit') != '' and scale) else None
        if mainwf:
            dat = await filtersToBeApllied(mainwf, post_visu, img, pixelX, 
                                     pixelY, newpath, user_id, sample_image, 
                                     default, callfrom, sample_imagep, scale, popup_unit)
            if 'annotation_data_df' in dat:
                del dat['annotation_data_df']
        else:
            h, w = img.shape[:2]
            dat = {"cropimg": sample_imagep, "cropimg_shape":[h,w],
                   "segmented_img":sample_imagep,"preprocessedlayers": [], 
                   "segmentationlayers": [], "postprocessedlayers": [], "user_id":user_id}

        
        collection = db.sampleworkflows
        wid = obj['workflow'][0]["_id"]
        if wid:         
            dat['orignalpath'] = original_path
            temp = {'path': original_path, 'PixelSizeX': pixelX,
                     'PixelSizeY': pixelY, 'workflowid': wid, 'appliedid':1,
                    'popup_val': obj['popup_val'], 'draw_val': obj['draw_val'], 
                    'popup_unit':  obj['popup_unit'], 'autocrop': True, 
                    'image': sample_imagep, 'orignalpath': original_path,
                    'scale': scale, 'scalebarextarction': 'undefined'}
            inputdata = [temp]
            mainwf, modification, post_visu, Analysis_info, outputdir_info = getWfFromDB(wid)

            # data = cropAndSegAnalysis(Analysis_info, inputdata, 0, img, None, fullname, newpath, user_id, inputdata, dat, 'crop&segfunc')
        else:
            data = {}
        data = {"imagedata" :dat}
            
    return data
