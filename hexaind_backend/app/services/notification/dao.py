from app.core.dao.dao_base import *
from datetime import datetime, timezone
from bson import ObjectId


class NotificationDao(DaoBase):


    async def add_record_async(self,notification):
        notification['created_at'] = datetime.fromisoformat(notification['created_at'])
        notification['last_updated'] = datetime.fromisoformat(notification['last_updated'])

        filter ={
            'created_at':notification['created_at'],
            'last_updated':notification['last_updated']
        }

        document = await self.db_async.notification.find_one(filter)
        if not document:
            await self.db_async.notification.insert_one(notification)


    def add_record(self,notification):
        notification['created_at'] = datetime.fromisoformat(notification['created_at'])
        notification['last_updated'] = datetime.fromisoformat(notification['last_updated'])
        filter ={
            'created_at':notification['created_at'],
            'last_updated':notification['last_updated']
        }
        document = self.db_sync.notification.find_one(filter)
        if not document:
            self.db_sync.notification.insert_one(notification)



    def get_name(self, category_id:str, notification_category:str):
        print(category_id)
        print(notification_category)

        if notification_category == "WORKFLOWS":
            document = self.db_sync.workflows.find_one({"_id":ObjectId(category_id)})
            return document["name"]
            # return document
        elif notification_category == "DATA":
            document = self.db_sync.datasets.find_one({"_id":ObjectId(category_id)})
            return document["name"]


    def find_user(self,filter):
        document = self.db_sync.users.find_one(filter)
        return document



    def find_notification_report(self):
        document = self.db_sync.notification_interaction_report.find_one()
        return document

    def update_notification_report(self,filter,update):
        document_count = self.db_sync.notification_frequency_report.count_documents({})
        if not document_count:
            self.db_sync.notification_frequency_report.insert_one({})
        self.db_sync.notification_frequency_report.update_one(filter,update)


    def find_subscription_document(self,filter:dict):

        document = self.db_sync.notification_configuration.find_one(filter)
        if not document:
            self.db_sync.notification_configuration.insert_one({
                                          "user_id": filter['user_id'],
                                          "in_app_notification": True,
                                          "slack": {
                                            "token": "",
                                            "channel_name": ""
                                          },
                                          "teams_channel_url": "",
                                          "email": "",
                                          "sms_number": 0
                                        })
            document = self.db_sync.notification_configuration.find_one(filter)


        return document

    def update_subscription_document(self,filter,update_value):
        document = self.db_sync.notification_configuration.find_one(filter)
        if document:
            self.db_sync.notification_configuration.update_one(filter,{'$set':update_value})
        else:
            self.db_sync.notification_configuration.insert_one(update_value)


    async def update_subscription_document_async(self, filter,update_value):
        document = await self.db_async.notification_configuration.find_one(filter)
        if document:
            await self.db_async.notification_configuration.update_one(filter,{'$set':update_value})
        else:
            await self.db_async.notification_configuration.insert_one(update_value)
