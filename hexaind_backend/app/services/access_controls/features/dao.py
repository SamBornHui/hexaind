from app.core.dao.dao_base import DaoBase
from typing import List
from app.services.admin.authentication.utils import mongo_list_json_async
from app.services.access_controls.features.schemas import (
    EndPointsFeatureMappings,
    HTTPEndPointMethodType
)


class EndPointsFeatureMappingsDao(DaoBase):

    async def insert_mapping(self, payload: EndPointsFeatureMappings) -> str:
        await self.db_async.endpoints_feature_mappings.delete_many(
            {"endpoint": payload.endpoint, "method": payload.method})
        result = await self.db_async.endpoints_feature_mappings.insert_one(payload.model_dump(exclude={'id'}))
        if not result:
            raise Exception("Unable to create EndPointsFeatureMappings record")
        return str(result.inserted_id)

    async def get_mapping_by_endpoint_and_method(self, end_point: str,
                                                 method: HTTPEndPointMethodType) -> EndPointsFeatureMappings:
        document = await self.db_async.endpoints_feature_mappings.find_one({"endpoint": end_point, "method": method})
        if document:
            document['_id'] = str(document['_id'])
            return EndPointsFeatureMappings(**document)
        else:
            raise Exception(
                f"No mapping found for endpoint {end_point} with method {method.value}")
        
    def get_token_excluded_endpoint_method_list(self) -> List[str]:
        excluded_end_points_list = []
        excluded_enpoints_cursor = self.db_sync.endpoints_feature_mappings.find({"exclude": True}, {'_id':0,'endpoint':1,'method':1})
        excluded_end_points_dict_list = list(excluded_enpoints_cursor)
        
        if excluded_end_points_dict_list:
            for endpoint_dict in excluded_end_points_dict_list:
                excluded_end_points_list.append(endpoint_dict['endpoint']+"_"+endpoint_dict['method'])

        return excluded_end_points_list

    def get_all_endpoint_method_details(self):
        docs_cursor = self.db_sync.endpoints_feature_mappings.find({'exclude': False})
        endpoint_method_features_dict = {}

        for features in docs_cursor:
            features.pop("_id")
            endpoint_feat_maps: EndPointsFeatureMappings =  EndPointsFeatureMappings(**features)
            key = features['endpoint']+'_'+features['method']
            endpoint_method_features_dict[key] = endpoint_feat_maps
        
        return endpoint_method_features_dict
