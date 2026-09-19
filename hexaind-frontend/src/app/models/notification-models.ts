abstract class BaseNotificationsModel {}

export class Notification implements BaseNotificationsModel {
  _id: string | undefined = undefined;
  name: string;
  description: string;
  site_id: string;
  owner_name: string;
  owner_id: string;
  created_at: any | undefined = undefined;
  last_modified_by_id: string | undefined = undefined;
  last_modified_at: any | undefined = undefined;

  constructor(
    name: string,
    description: string,
    ownerName: string,
    ownerId: string,
    siteId: string,
  ) {
    this.name = name;
    this.description = description;
    this.owner_name = ownerName;
    this.owner_id = ownerId;
    this.site_id = siteId;
  }
}

export enum NotificationType {
    SUCCESS = 'SUCCESS',
    ERROR = 'ERROR',
    INFO = 'INFO',
    WARNING = 'WARNING',
    SYSTEM = 'SYSTEM'
}

export enum NotificationResponseMessages {
  FETCH_SUCCESS = "Notifications fetched successfully",
  FETCH_FAILURE = "Error while fetching notifications",
  UPDATE_SUCCESS = "Notifications updated successfully",
  UPDATE_FAILURE = "Notifications update failed",
  UPDATE_ERROR = "An error occurred during notifications update"
}