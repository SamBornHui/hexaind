abstract class BaseUserModel {}

export enum UserRole {
  USER = 'USER',
  ADMIN = 'ADMIN',
}

export class UserForProjectsResponse implements BaseUserModel {
  succeeded: boolean = false;
  message: string | undefined = undefined;
  results: UserForProjects[] = [];
  results_count: number = 0;
}

export class CreateNewPassword implements BaseUserModel {
  email: string | undefined;
  reason: string | undefined = undefined;
}

export class UserForProjects implements BaseUserModel {
  id: string | undefined = undefined;
  name: string | undefined = undefined;
  user_id: string | undefined = undefined;
  user_name: string | undefined = undefined;
  email: string | undefined = undefined;
  invited_by: string | undefined = undefined;
  server_role_value: number = 0;
  server_role: string | undefined = undefined;
  role_updated_at: Date | undefined = undefined;
  role_updated_by_id: string | undefined = undefined;
  role_updated_by_name: string | undefined = undefined;
}

export class UserProjectMapping implements BaseUserModel {
  version: string | undefined = undefined;
  _id: string | undefined = undefined;
  user_id: string | undefined = undefined;
  project_id: string | undefined = undefined;
  role_id: string | undefined = undefined;
  is_activate: boolean | undefined = undefined;
  created_at: Date | undefined = undefined;
  created_by: string | undefined = undefined;
  last_modified_at: Date | undefined = undefined;
  last_modified_by: string | undefined = undefined;
  user_name: string | undefined = undefined;
  project_name: string | undefined = undefined;
  project_owner_id: string | undefined = undefined;
  project_owner_name: string | undefined = undefined;
  last_modified_by_name: string | undefined = undefined;
  description: string | undefined = undefined;
  role_name: string | undefined = undefined;
}

export class User implements BaseUserModel {
  _id: string | null = null;
  name: string;
  email: string;
  role: UserRole;
  created_at: any;

  constructor(name: string, email: string, role: UserRole) {
    this.name = name;
    this.email = email;
    this.role = role;
  }
}
