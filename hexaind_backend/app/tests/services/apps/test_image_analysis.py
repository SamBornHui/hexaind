from app.services.apps.image_analysis.service import ImageAnalysisService
import pytest
from app.services.apps.image_analysis.schema import *
from app.core.dao.dao_base import get_db_async,get_db_sync
from unittest.mock import AsyncMock, patch


a = {"image_masking":[{"coordinates":{"x1":2,"y1":16,"x2":20,"y2":37,"w":18,"h":20},
                     "color":"#1A7A7F","ymax":0,"path":True,"mask_name":"Mask-4","apply":False}],
                     "dataset_id":"66ed1d8cd7461e4cd52f6975","category":"NA",
                     "image":"/Users/msacbook/desktop/hexaind-data/datasets/image_datasets_2_0/sep201726815630304/1000C_3602h_a1z3/modifiedimages//a1z3-thread-08.png",
                     "base_image":"/Users/msacbook/desktop/hexaind-data/datasets/image_datasets_2_0/sep201726815630304/1000C_3602h_a1z3/processedimg/a1z3-thread-08.png",
                     "apply_all":False}

b = {"dataset_id":"66ed1d8cd7461e4cd52f6975",
    "image":"/Users/msacbook/desktop/hexaind-data/datasets/image_datasets_2_0/sep201726815630304/1000C_3602h_a1z3/modifiedimages//a1z3-thread-08.png",
    "category":"NA","coordinates":{"x1":21,"y1":31,"x2":74,"y2":75,"w":52,"h":41}}

c = {"dataset_id":"66ed1d8cd7461e4cd52f6975","image":"/Users/msacbook/desktop/hexaind-data/datasets/image_datasets_2_0/sep201726815630304/1000C_3602h_a1z3/modifiedimages//a1z3-thread-08.png",
    "category":"NA","old_coordinates":{"x1":2,"y1":16,"x2":20,"y2":37,"w":18,"h":20},
    "new_coordinates":{"x1":21,"y1":31,"x2":74,"y2":75,"w":52,"h":41},"apply_change":True,
    "mask_name":"Mask-2"}

d = {"dataset_id":"66ed1d8cd7461e4cd52f6975",
     "image":"/Users/msacbook/desktop/hexaind-data/datasets/image_datasets_2_0/sep201726815630304/1000C_3602h_a1z3/modifiedimages//a1z3-thread-08.png",
     "category":"NA"}





# @pytest.fixture
def create_required_obj(obj_create):

    client  = get_db_sync()
    db = client['Hexaind']["categorizeddata"]
    categorized_data_doc = db.find_one()
    dataset_id  = categorized_data_doc['dataset_id']
    all_data = categorized_data_doc['data']['NA'] + categorized_data_doc['data']['SEM'] + categorized_data_doc['data']['OM']
    manual_image = all_data[0]['manual_image']
    processed_image = all_data[0]['image']

    print(dataset_id)
    print("manual_image:",manual_image)
    print("processed_image",processed_image)

    if obj_create == 'save_mask':
        mask_obj = Masks(**a)
        mask_obj.dataset_id = dataset_id
        mask_obj.base_image = processed_image
        mask_obj.image = manual_image
        return  mask_obj
    elif obj_create == 'delete_mask':
        mask_obj = DeleteMaskObjects(**b)
        mask_obj.dataset_id = dataset_id
        mask_obj.image = manual_image
        return  mask_obj
    elif obj_create == 'update_mask':
        mask_obj = UpdateMaskConfig(**c)
        mask_obj.dataset_id = dataset_id
        mask_obj.image = manual_image
        return  mask_obj
    elif obj_create == 'get_mask':
        mask_obj = MaskedObjRequest(**d)
        mask_obj.dataset_id = dataset_id
        mask_obj.image = manual_image
        return  mask_obj

@pytest.mark.fixme
@pytest.mark.asyncio
async def test_save_masks():
    mock_db_client = AsyncMock()
    db_client_async = get_db_async()
    new_mask = create_required_obj('save_mask')
    # Initialize your service class
    image_analysis_obj = ImageAnalysisService(db_sync_client=get_db_sync(), db_async_client=db_client_async)

    result = await image_analysis_obj.save_mask(new_mask)

    assert result is not None, "mask is not saved"

@pytest.mark.fixme
@pytest.mark.asyncio
async def test_get_masks():
    db_client_async = get_db_async()
    new_mask = create_required_obj('get_mask')
    # Initialize your service class
    image_analysis_obj = ImageAnalysisService(db_sync_client=get_db_sync(), db_async_client=db_client_async)
    # Print the new mask to debug the object creation
    result = await image_analysis_obj.get_masked_objs(new_mask)
    print(result)
    assert result is not None, "mask is not deleted"


@pytest.mark.fixme
@pytest.mark.asyncio
async def test_update_masks():
    db_client_async = get_db_async()
    new_mask = create_required_obj('update_mask')
    # Initialize your service class
    image_analysis_obj = ImageAnalysisService(db_sync_client=get_db_sync(), db_async_client=db_client_async)

    # Print the new mask to debug the object creation
    print(new_mask)

    result = await image_analysis_obj.update_mask(new_mask)

    assert result is not None, "mask is not updated"


@pytest.mark.fixme
@pytest.mark.asyncio
async def test_delete_masks():
    db_client_async = get_db_async()
    new_mask = create_required_obj('delete_mask')
    # Initialize your service class
    image_analysis_obj = ImageAnalysisService(db_sync_client=get_db_sync(), db_async_client=db_client_async)

    # Print the new mask to debug the object creation
    print(new_mask)

    result = await image_analysis_obj.delete_masked_obj(new_mask)

    assert result is not None, "mask is not deleted"
