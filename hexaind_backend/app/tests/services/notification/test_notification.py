# from app.services.notification.service import Notification
# from app.services.notification.schema import (
#     NotificationModel,
#     NotificationMessages,
#     NotificationType,
#     NotificationCategory,
#     NotificationImportance)
# from app.core.db.db_utils import  get_db_sync
#
# def test_notifcation():
#     dataset_id = "datasetId"
#     projectId = "projectId"
#
#     notification_obj = {"message":NotificationMessages.DATASET_CREATED,
#                               'category_id':dataset_id,
#                               'project_id':projectId,
#                               'notification_type':NotificationType.SUCCESS,
#                               'importance':NotificationImportance.MEDIUM,
#                               'notification_category':NotificationCategory.DATA}
#     verified_notfication_obj = NotificationModel(**notification_obj)
#     notification_service_obj = Notification(db_async_client = get_db_sync())
#     await notification_service_obj.create_notification(verified_notfication_obj)
#


