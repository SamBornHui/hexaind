from datetime import datetime, timezone
import json
import logging
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from .dao import NotificationDao
from .schema import NotificationModel
import redis
import os
logger = logging.getLogger(__name__)

from app.config.env_vars import celery_environment


class Notification:
    def __init__(self,db_sync_client:MongoClient = None, db_async_client:AsyncIOMotorClient = None):
        self.notificationDao = NotificationDao(db_sync_client = db_sync_client,
                                                   db_async_client = db_async_client)
        self.redis_client = redis.Redis.from_url(str(celery_environment.celery_result_backend_url))

    async def add_configuration(self, userId, notificationsubscription):
        notification_subscription = dict(notificationsubscription)
        if notification_subscription['teams_channel_url'] == '':
            notification_subscription.pop('teams_channel_url')
        if notification_subscription['slack']['token'] == '' or notification_subscription['slack']['channel_name'] == '':
            notification_subscription.pop('slack')
        if notification_subscription['email']  == '':
            notification_subscription.pop('email')
        if notification_subscription['sms_number'] is None:
            notification_subscription.pop('sms_number')
        await self.notificationDao.update_subscription_document_async({'user_id':userId},notification_subscription)




    def create_notification_sync(self,notification_message: NotificationModel):
        try:
            logger.info("create notification function")
            notification_message_dict = notification_message.model_dump()
            notification_message_dict['created_at'] = datetime.now(timezone.utc).isoformat()
            notification_message_dict['last_updated'] = datetime.now(timezone.utc).isoformat()

            response = self.redis_client.ping()
            # Check if response is PONG
            if response:
                logger.info("Redis is up and running.")
                message = json.dumps(notification_message_dict)
                aa = self.redis_client.publish("notifications", message)
                logger.info(f"notifications {message} published to redis")
                return aa
            else:
                logger.error("Redis is not responding properly.")
                raise "Redis is not responding properly."

        except Exception as e:
            logger.error(f"Failed to publish notification due to exception: {str(e)}")
            raise Exception


    async def create_notification(self,notification_message: NotificationModel):
        try:

            logger.info("create notification function")
            notification_message_dict = notification_message.model_dump()
            notification_message_dict['created_at'] = datetime.now(timezone.utc).isoformat()
            notification_message_dict['last_updated'] = datetime.now(timezone.utc).isoformat()
            logger.info(f"inside create notification service :{notification_message_dict}")

            response = self.redis_client.ping()
                # Check if response is PONG
            if response:

                logger.info("Redis is up and running.")
                message = json.dumps(notification_message_dict)
                aa = self.redis_client.publish("notifications", message)
                logger.info(f"notifications {message} published to redis")
                return aa
            else:
                logger.error("Redis is not responding properly.")
                raise "Redis is not responding properly."

        except Exception as e:
            logger.error(f"Failed to publish notification due to exception: {str(e)}")
            raise Exception
        
    def create_notification_sync(self,notification_message: NotificationModel):
        try:

            logger.info("create notification function")
            notification_message_dict = notification_message.model_dump()
            notification_message_dict['created_at'] = datetime.now(timezone.utc).isoformat()
            notification_message_dict['last_updated'] = datetime.now(timezone.utc).isoformat()
            logger.info(f"inside create notification service :{notification_message_dict}")

            response = self.redis_client.ping()
                # Check if response is PONG
            if response:

                logger.info("Redis is up and running.")
                message = json.dumps(notification_message_dict)
                aa = self.redis_client.publish("notifications", message)
                logger.info(f"notifications {message} published to redis")
                return aa
            else:
                logger.error("Redis is not responding properly.")
                raise "Redis is not responding properly."

        except Exception as e:
            logger.error(f"Failed to publish notification due to exception: {str(e)}")
            raise Exception

    def __del__(self):
        self.redis_client.close()





