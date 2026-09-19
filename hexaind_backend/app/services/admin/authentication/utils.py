from fastapi.responses import JSONResponse
from fastapi import status
from bson.objectid import ObjectId

def http_err_unauthorized(error_descr):
    return JSONResponse(status_code = status.HTTP_401_UNAUTHORIZED , content={'reason': error_descr})

def http_err_forbidden(error_descr):
    return JSONResponse(status_code = status.HTTP_403_FORBIDDEN , content={'reason': error_descr})

def http_err_meth_not_allowed(error_descr):
    return JSONResponse(status_code = status.HTTP_405_METHOD_NOT_ALLOWED, content={'reason': error_descr})

def http_err_conflict(error_descr):
    return JSONResponse(status_code = status.HTTP_409_CONFLICT, content={'reason': error_descr})

async def mongo_list_json_async(objList: list):
    retList = []
    if objList is not None:
        async for obj in objList:
            if '_id' in obj:
                obj['_id'] = str(obj['_id'])
            retList.append(obj)
    return retList

async def get_object_id(id):
    if ObjectId.is_valid(id):
        return ObjectId(id)
    else:
        return None
    
def get_object_id_sync(id):
    if ObjectId.is_valid(id):
        return ObjectId(id)
    else:
        return None