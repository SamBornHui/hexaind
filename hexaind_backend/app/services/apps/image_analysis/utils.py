def fetchKeysValue(keyname, obj, defaultname=''):
    # extracting key value from object
    if keyname in obj:
        keyvalue = obj[keyname]
        del obj[keyname]
    else:
        keyvalue = defaultname
    
    return keyvalue