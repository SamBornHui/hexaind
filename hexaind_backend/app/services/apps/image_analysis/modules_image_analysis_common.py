from pymongo import MongoClient
from bson import ObjectId
from app.services.apps.image_analysis.configurations import *
from datetime import datetime
import cv2
from skimage import io, data
import pymongo
import shutil
from skimage.color import rgb2gray, gray2rgb, label2rgb


def establishConnection():
    
    db=None
    client = MongoClient(configurations["db_address"],
                         username=configurations["db_username"],
                         password=configurations["db_password"],
                         authSource=configurations["db_name"])

    db = client[configurations["db_name"]]

    return db


def retrieveWfId(path):
    db = establishConnection()
    collection = db.multiplyimagesworkflow
    
    report = collection.find_one({'image_path': path},
              sort=[( '_id', pymongo.DESCENDING )])
    if report:   
        return report['w_id']
    else:
        return 0
        
        
        
def retrieveProcessedWfId(path):
    db = establishConnection()
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


def rgbToGray(img):
    if len(img.shape)>=3:
        img = rgb2gray(img)
        return img
    else:
        return img

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
    

def deleteRemainingData(image, db):
    collection = db.multiplyimagesworkflow
    report = collection.delete_one(
                    {'image_path': image})
    
    path, fname = os.path.split(image)
    fname, _ = os.path.splitext(fname)
    
    removedir = path + '/' + fname
    
    if os.path.exists(removedir):
        shutil.rmtree(removedir)

    fname, _ = os.path.splitext(image)
    collection = db.workflowimagespath
    report = collection.delete_many({'sample_name': fname})
    
    
def fetchKeysValue(keyname, obj):
    if keyname in obj:
        value = obj[keyname]
    else:
        value = None
        
    return value
    

def removeSlashonLastIndex(path):
    if path[-1]=='/':
        path, _ = os.path.split(path)
        return path
    else:
        return path   
        
        

    







        
