import os
import json
import logging
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from .dao import NotificationDao
import redis
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import slack
import pymsteams

from app.config.env_vars import celery_environment


redis_client = redis.Redis.from_url(str(celery_environment.celery_result_backend_url))



logger = logging.getLogger(__name__)

class Notification:
    def __init__(self,db_sync_client:MongoClient = None, db_async_client:AsyncIOMotorClient = None):
        self.notificationDao = NotificationDao(db_sync_client = db_sync_client,
                                                   db_async_client = db_async_client)


    async def send_email_notification(self,notification:dict):
        ''' this function will be abled in future'''

        sender_email = os.environ.get("SENDER_EMAIL",'email')
        sender_password = os.environ.get("SENDER_PASSWORD",'password')
        smtp_server = os.environ.get("SMTP_SERVER","smtp.office365.com")
        smtp_port = os.environ.get("SMTP_PORT",587)

        logger.info("Inside send email notification function")
        try:
            document = self.notificationDao.find_subscription_document({"user_id":notification['user_id']})
            recipient_email = document['email']
            subject = 'Databrick Hexaind Notification'
            message = notification['message']

            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = recipient_email
            msg['Subject'] = subject
            msg.attach(MIMEText(message, 'plain'))
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
            server.quit()
            logger.info("email notification sent successfully")
        except Exception as e:
            logger.error(f"failed to send email notification due to the exception:{str(e)}")



    async def send_teams_notification(self,notification:dict):
        logger.info("inside send teams notification function")
        try:
            document = self.notificationDao.find_subscription_document({"user_id":notification['user_id']})
            team_url = document['teams_channel_url']
            card = pymsteams.connectorcard(team_url)
            message = notification['message']
            card.text(message)
            assert card.send()
            logger.info(f"team notification send successfully")
        except Exception as e:
            logger.error(f"failed to send team notification due to the exception :{str(e)}")




    async def send_slack_notification(self,notification:dict):
        logger.info("inside slack notification")
        try:
            document=self.notificationDao.find_subscription_document({"user_id":notification['user_id']})
            token = document['slack']['token']
            channel_name = document['slack']['channel_name']
            slack_client = slack.WebClient(token = token)
            message = notification['message']
            slack_client.chat_postMessage(channel = f"#{channel_name}",text = message )
            logger.info("slack message sent successfully")
        except Exception as e:
            logger.error(f"failed to send notification to slack due to the exception: {str(e)}")

    async def tracking_notification(self,notification:dict):
        try:
            logger.info("inside tracking notification")
            update_query = {'$inc': {notification['notification_type']: 1}}
            filter = {}
            self.notificationDao.update_notification_report(filter,update_query)
        except Exception as e:
            raise Exception


    async def check_channel_subscription(self,notification,notification_channel:str)->bool:
        try:
            document = self.notificationDao.find_subscription_document({"user_id":notification['user_id']})
            subscription_channel_list = []
            if document['slack']['token'] and document['slack']['channel_name']:
                subscription_channel_list.append('slack')
            if document['teams_channel_url']:
                subscription_channel_list.append('teams')
            if document['email']:
                subscription_channel_list.append('email')

            return subscription_channel_list


        except Exception as e:
            logger.error(f"failed to get channel subscription due to exception: {str(e)}")
            raise Exception






    async def create_message(self,notification:dict):
        logger.info("Inside create_message function")
        name = self.notificationDao.get_name(notification["category_id"],notification["notification_category"])
        # logger.info(f"Workflow_name:{name}")
        # print(f"Workflow_name:{name}")
        if notification['notification_type'] == 'SUCCESS' and notification['notification_category'] == "WORKFLOWS":
            message = f"Workflow {name} has successfully completed"
        elif notification['notification_type'] == 'ERROR' and notification['notification_category'] == "WORKFLOWS":
            message = f"Workflow {name} has failed"
        elif notification['notification_type'] == 'INFO' and notification['notification_category'] == "WORKFLOWS":
            message = f"Workflow {name}  has published"
        elif notification['notification_type'] == 'SUCCESS' and notification['notification_category'] == "DATA":
            message = f"Dataset {name} has been created"
        elif notification['notification_type'] == 'INFO' and notification['notification_category'] == "DATA":
            message = f"Dataset has been renamed to {name} "
        notification.update({"message":message})

        return notification

    async def process_notification(self,notification:bytes):
        logger.info('inside process_notification function')
        try:
            if type(notification) != int:
                decoded_notification = notification.decode('utf-8')
                notification_dict:dict = json.loads(decoded_notification)
                self.notificationDao.add_record(notification_dict)
                await self.tracking_notification(notification_dict)

                #this function will be uncommented in the future to send the notification to others channel

                # subscription_channel_list = await self.check_channel_subscription(notification_dict,'email')
                # if 'email' in subscription_channel_list:
                #     await self.send_email_notification(notification_dict)
                # if 'slack' in subscription_channel_list:
                #     await self.send_slack_notification(notification_dict)
                # if 'teams' in subscription_channel_list:
                #     await self.send_teams_notification(notification_dict)
        except Exception as e:
            logger.error(f"failed to process notification due to the exception: {str(e)}")
            raise Exception

    async def receive_notification(self):
        try:
            pubsub = redis_client.pubsub()
            pubsub.subscribe(['notifications'])
            for message in pubsub.listen():
                print(message['data'])
                logger.info(message)
                await self.process_notification(message['data'])
                logger.info('notification processed')
        except Exception as e:
            logger.error(f"failed to recieve notification due to exception {str(e)}")



def async_wrapper(async_func):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(async_func())
    loop.close()
