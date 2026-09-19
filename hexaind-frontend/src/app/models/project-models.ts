abstract class BaseProjectModel {}

export class Project implements BaseProjectModel {
  _id: string | undefined = undefined;
  project_id: any | undefined = undefined
  name: string;
  description: string;
  site_id: string;
  owner_name: string;
  owner_id: string;
  role_id: any | undefined = undefined;
  role_name: string | undefined;
  created_at: any | undefined = undefined;
  last_modified_by_id: string | undefined = undefined;
  last_modified_at: any | undefined = undefined;
  last_accessed_at: any | undefined = undefined; 
  version: string | undefined = undefined;
  favourited_by: string[] = [];
  project_name: any;
  project_administrator_id: string | undefined;
  project_administrator_name: string | undefined;
  users_roles_mappings: any;
  project_owner_name: any;
  project_owner_id: any;
  role_info: any;

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
