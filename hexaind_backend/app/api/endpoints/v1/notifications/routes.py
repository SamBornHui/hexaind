from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import JSONResponse
from bson import ObjectId
from motor.motor_asyncio import  AsyncIOMotorClient
from datetime import datetime, timezone
import traceback
import logging
from app.core.db.db_utils import get_db_async
from app.services.notification.schema import NotificationModel,NotificationConfiguration,NotificationStatus
from app.services.notification.service import Notification
import json
from pymongo import MongoClient
from app.config.env_vars import environment
from app.api.rbac.end_points_v1_access_control import CheckNameRoute



logger = logging.getLogger(__package__)
notifications_router = APIRouter(tags=['Notifications'], route_class = CheckNameRoute)

class NotificationsAPIRouter:

    def __init__(self):
        pass

    # Create a new notification.
    @notifications_router.post('/v1/sites/{siteId}/notification')
    async def create_notificiation(siteId: str,
                        notification: NotificationModel ,
                        client: MongoClient = Depends(get_db_async)) -> JSONResponse:

        try:
            logger.info("Inside create notification.")
            # Insert the notification into the database
            notification.created_at = datetime.now(timezone.utc)
            notification.last_updated = datetime.now(timezone.utc)
            notification.read.clear()
            notification.deleted_by_users.clear()
            notification_service_obj = Notification(db_async_client=client)
            create_notificication_response = await notification_service_obj.create_notification(notification)
            return JSONResponse(content={"message": create_notificication_response},status_code=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code = status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "notification_creation_error",
                    "message": str(e)
                }
            )


    # Get all notification for a given project
    @notifications_router.get('/v1/sites/{siteId}/projects/{projectId}/notification')
    async def get_notifications_by_project(
                        siteId: str,
                        projectId: str,
                        page_limit:int = Query(default=10),
                        page_number:int = Query(default=1),
                        client: AsyncIOMotorClient = Depends(get_db_async)) -> JSONResponse:
        try:
            logger.info("inside get all notification.")
            db = client[environment.hexaind3_database_name]
            offset = (page_number - 1) * page_limit
            query = {"project_id": projectId }
            notifications_cursor = db.notification.aggregate([{"$match": query},
                                                       {"$addFields": {"_id": {"$toString": "$_id"},
                                                                       "created_at": {"$dateToString": {"format": "%Y-%m-%dT%H:%M:%S.%LZ", "date": "$created_at"}},
                                                                       "last_updated": {"$dateToString": {"format": "%Y-%m-%dT%H:%M:%S.%LZ", "date": "$last_updated"}}
                                                                      }},
                                                        {"$sort": {"created_at": -1}},
                                                       {"$skip": offset},
                                                       {"$limit": page_limit}
                                                       ])
            notifications = [notification async for notification in notifications_cursor]


            total_count = await db.notification.count_documents(query)
            logger.info(f"retrieved all the notification from the db with total count: {total_count}")
            return JSONResponse(content={"notification": notifications,
                                         "notifications_count": total_count,
                                         "page_number": page_number,
                                         "page_limit": page_limit
                                         })
        except Exception as e:
            logger.error(f"{str(e)}", exc_info = True)
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code = status.HTTP_400_BAD_REQUEST,
                detail={
                        "code": "while fetching notification",
                        "message": str(e)
                        }
                        )



    # Update an existing notification.
    @notifications_router.put('/v1/sites/{siteId}/notification/{notificationId}/updateNotification')
    async def update_notification(siteId: str,
                              notificationId: str,
                              read: NotificationStatus,
                              client: AsyncIOMotorClient = Depends(get_db_async)) -> JSONResponse:
        try:

            logger.info("inside update notification.")

            db = client[environment.hexaind3_database_name]
            if read.status == True:
                update_data = {
                    "$addToSet": {"read": read.user_id},
                    "$set": {"last_updated": datetime.now(timezone.utc)}
                }
            else:
                update_data = {
                    "$pull": {"read": read.user_id},
                    "$set": {"last_updated": datetime.now(timezone.utc)}
                }

            result = await db.notification.find_one_and_update(
                {"_id": ObjectId(notificationId) },
                update_data,
                return_document = True
                )
            if result:
                result['_id'] = str(result['_id'])
                result['created_at']=str(result['created_at'])
                result['last_updated']=str(result['last_updated'])
                response_content = {"notification": result}
                response_json = json.dumps(response_content)
                logger.info("updated the notification.")
                return JSONResponse(content = response_json, status_code = status.HTTP_200_OK)
            else:
                logger.exception("Notification not found or user not authorized to update this notification.", exc_info=True)
                raise HTTPException(
                    status_code = status.HTTP_404_NOT_FOUND,
                    detail = "Notification not found or user not authorized to update this notification."
                    )
        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code = status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "notification_update_error",
                    "message": str(e)
                }
            )

    @notifications_router.put('/v1/sites/{siteId}/userid/{userId}')
    async def mark_all_notification_true(
                                userId: str,
                                client: MongoClient = Depends(get_db_async)) -> JSONResponse:
        try:
            logger.info("inside update notification status.")

            db = client[environment.hexaind3_database_name]
            update_data = {
                    "$addToSet": {"read": userId},
                    "$set": {"last_updated": datetime.now(timezone.utc)}
                }
            await db.notification.update_many(
                {},
                update_data,
            )
            return JSONResponse(content = 'response_json', status_code = status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code = status.HTTP_400_BAD_REQUEST,
                detail = {
                    "code": "notification_update_error",
                    "message": str(e)
                }
            )

    @notifications_router.post('/v1/sites/{siteId}/notificationConfiguration')
    async def create_notification_configuration(siteId: str,
                                                userId: str,
                            notificationsubscription: NotificationConfiguration ,
                            client: AsyncIOMotorClient = Depends(get_db_async)) -> JSONResponse:

        try:
            logger.info("Inside notification configuration.")

            if notificationsubscription.slack:
                notificationsubscription.slack = dict(notificationsubscription.slack)

            notification_service_obj = Notification(db_async_client = client)
            await notification_service_obj.add_configuration(userId,notificationsubscription)

            logger.info(f"Created notification with notification id ")

            return JSONResponse(content = {"configuration": "configuration_added"},
                                status_code = status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"{str(e)}", exc_info = True)
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code = status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "notification_configuration_creation_error",
                    "message": str(e)
                }
            )



    @notifications_router.get('/v1/sites/{siteId}/workflow/{workflow_id}/get_session')
    async def get_session_id(siteId: str,
                             workflow_id: str,
                             client: AsyncIOMotorClient = Depends(get_db_async)) -> JSONResponse:
        try:
            db = client[environment.hexaind3_database_name]
            document = await db.workflow_sessions.find_one({"$or": [{"workflow_id":workflow_id}, {"saved_workflows.workflow_id":workflow_id}]})
            if document:
                document.update({"_id": str(document['_id']),
                                 "created_at": str(document['created_at']),
                                 "last_modified_at": str(document['last_modified_at'])})
                response = json.dumps(document)
                return JSONResponse(content = response, status_code = status.HTTP_200_OK)
            else:
                return JSONResponse(content = "no session found", status_code = status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code = status.HTTP_400_BAD_REQUEST,
                detail = {
                    "code": "workflow_session",
                    "message": str(e)
                }
            )

     # Delete an existing notification.
    @notifications_router.delete('/v1/sites/{siteId}/users/{userId}/notification/{notificationId}')
    async def delete_notification(siteId: str,
                                  userId: str,
                          notificationId: str,
                            client: AsyncIOMotorClient = Depends(get_db_async)) -> JSONResponse:
        try:
            logger.info("Inside delete notification method.")
            db = client[environment.hexaind3_database_name]
            update_data = {
                    "$addToSet": {"deleted_by_users": userId},
                    "$set": {"last_updated": datetime.now(timezone.utc)}
                }
            result = await db.notification.find_one_and_update(
                {"_id": ObjectId(notificationId) },
                update_data,
                return_document = True
                )

            return JSONResponse(content = {"message": "Notification deleted successfully"}, status_code=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"{str(e)}", exc_info = True)
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code = status.HTTP_400_BAD_REQUEST,
                detail = {
                    "code": "notification_delete_error",
                    "message": str(e)
                }
            )

    #
    # @staticmethod
    # @notifications_router.websocket("/ws")
    # async def websocket_endpoint(websocket: WebSocket):
    #     await websocket.accept()
    #     redis = aioredis.Redis.from_url(
    #         os.environ.get('CELERY_RESULT_BACKEND_URL')
    #     )
    #
    #     # redis.Redis.from_url(os.environ.get('CELERY_RESULT_BACKEND_URL'))
    #     try:
    #         pubsub = redis.pubsub()
    #         await pubsub.subscribe('notifications')
    #         async for message in pubsub.listen():
    #             if message['type'] == 'message':
    #                 # print(message['data'])
    #                 await websocket.send_text(message['data'].decode())
    #                 notification_obj = Notification(db_sync_client=get_db_sync())
    #                 await notification_obj.process_notification(message['data'])
    #
    #     except WebSocketDisconnect:
    #         print("Client disconnected")
    #     finally:
    #         await pubsub.unsubscribe('notifications')
    #         await redis.close()
    #         await websocket.close()




notifications_router_obj = NotificationsAPIRouter()
