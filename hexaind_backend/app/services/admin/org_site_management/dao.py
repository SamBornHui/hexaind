from app.core.dao.dao_base import DaoBase
from datetime import datetime,timezone
from bson.objectid import ObjectId

from app.services.admin.authentication.dao import get_utc_date_time
from app.services.admin.org_site_management.schemas import Site
from app.services.admin.authentication.utils import http_err_unauthorized, mongo_list_json_async, get_object_id

org_data = {
    '_id': '1001',
    'name': 'Databrick',
    'description': 'Databrick Technologies',
    'date_created': '2023-09-08'
}

class OrgSiteManagementDao(DaoBase):
    async def create_site(self, siteObj: Site):
        site = siteObj.dict()
        site.pop('id')

        site_found = await self.db_async.Site.find_one({'name': site['name']})
        if site_found is not None:
            return http_err_unauthorized('Site Already exists.')

        site_adm_ids = site['admin_users']
        # site['users_roles'] = [{'role_id': 'R2', 'user_id': site_adm_ids}]
        site.pop('admin_users', None)
        site.pop('users_roles', None)
        site['date_created'] = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        site['is_active'] = 1

        org = self.get_organization()
        site['organization_id'] = org['_id']

        inserted_obj = await self.db_async.Site.insert_one(site)
        if inserted_obj is None:
            return http_err_unauthorized('Unknown issue while trying to Create Site.')

        if site_adm_ids is not None and len(site_adm_ids) > 0:
            self.create_or_modify_site_admin_roles(site_adm_ids, str(inserted_obj.inserted_id))

        site_created = await self.db_async.Site.find_one({'_id': ObjectId(inserted_obj.inserted_id)})
        site_created['_id'] = str(site_created['_id'])

        return site_created

    async def create_or_modify_site_admin_roles(self, adm_role_user_ids: list, site_id: str):
        time_stamp = await get_utc_date_time()
        for user_id in adm_role_user_ids:
            user_acc_role_in_db = await self.db_async.user_access_roles.find_one({'user_id': user_id, 'site_id': site_id})
            if user_acc_role_in_db is None:
                ins_rec_data = {'user_id': user_id, 'site_id': site_id, 'role_id': 'R2', 'created_date': time_stamp, 'updated_date': time_stamp}
                await self.db_async.user_access_roles.insert_one(ins_rec_data)
            else:
                await self.db_async.user_access_roles.update_one({'user_id': user_id, 'site_id': site_id}, {'$set': {'role_id': 'R2', 'updated_date': time_stamp}})

    async def get_organization(self):
        try:
            org_rec = await self.db_async.Organization.find_one()
            if org_rec is None:
                org_data['date_created'] = datetime.now(timezone.utc).strftime('%Y-%m-%d')
                await self.db_async.Organization.insert_one(org_data)
                org_rec = await self.db_async.Organization.find_one({})
            org_rec['_id'] = str(org_rec['_id'])
            return org_rec
        except Exception as e:
            return http_err_unauthorized('Unknown Error while trying to get Organization.')

    async def get_roles_list(self):
        roles_cursor = self.db_async.roles.find({'_id': {'$ne': 'R1'}})
        return await mongo_list_json_async(roles_cursor)

    async def get_sites_list(self):
        sites_cursor = self.db_async.Site.find({'is_active': 1})
        return await mongo_list_json_async(sites_cursor)

    async def get_user_sites_list(self, email):
        user = await self.db_async.users.find_one({'email': email})
        if not user:
            return []

        user_id = str(user['_id'])
        user_sites_cursor = self.db_async.user_access_roles.find({'user_id': user_id}, {'_id': 0, 'site_id': 1})
        user_sites = await mongo_list_json_async(user_sites_cursor)
        site_ids_list = []
        for site in user_sites:
            site_id_ob_id = await get_object_id(site['site_id'])
            if site_id_ob_id:
                site_ids_list.append(site_id_ob_id)

        sites_cursor = self.db_async.Site.find({'_id': {'$in': site_ids_list}, 'is_active': 1})
        return await mongo_list_json_async(sites_cursor)
