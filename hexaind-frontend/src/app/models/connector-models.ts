abstract class BaseConnectorModel { }

export class CreateConnectorResponse implements BaseConnectorModel {
  connector_id: string | undefined;
}

export class ConnectorListResponse implements BaseConnectorModel {
  connectors: Connector[] = [];
  total_count: number | undefined = undefined;
}

class UpdateConnectorResponse implements BaseConnectorModel {
  success: boolean | undefined = undefined;
}

class DeleteConnectorResponse implements BaseConnectorModel {
  success: boolean | undefined = undefined;
}

export enum ConnectorType {
  BIGQUERY = 'BIGQUERY',
  RESCALE = 'RESCALE',
  THERMOCALC='THERMOCALC',
  SNOWFLAKE='SNOWFLAKE',
  COUCHBASE='COUCHBASE',
  ELASTICSEARCH='ELASTICSEARCH',
  MYSQL='MYSQL',
  HIVE='HIVE',
  REDSHIFT='REDSHIFT',
  POSTGRESQL='POSTGRESQL'
}

export enum BigQueryAuthType {
  USER_AUTH = 'USER_AUTH',
  SERVICE_ACCOUNT = 'SERVICE_ACCOUNT',
  BROWSER_AUTH = 'BROWSER_AUTH'
}

export enum SnowflakeAuthType {
  USER_AUTH = 'USER_AUTH'
}

export class BigQueryUserAuthConfig implements BaseConnectorModel {
  client_id: string | undefined;
  client_secret: string | undefined;
  refresh_token: string | undefined;
  project_id: string | undefined;
}

export class BigQueryBrowserAuthConfig implements BaseConnectorModel {
  project_id: string | undefined;
}

export class BigQueryServiceAccountConfig implements BaseConnectorModel {
  type: string | undefined;
  project_id: string | undefined;
  private_key_id: string | undefined;
  private_key: string | undefined;
  client_email: string | undefined;
  client_id: string | undefined;
  auth_uri: string | undefined;
  token_uri: string | undefined;
  auth_provider_x509_cert_url: string | undefined;
  client_x509_cert_url: string | undefined;
}



export class BigQueryConnectorConfiguration implements BaseConnectorModel {
  connector_type: string; // Add connector_type
  gcs_bucket_name: string = ""; 
  authentication_type: BigQueryAuthType | undefined;
  authentication_details:
    | BigQueryUserAuthConfig
    | BigQueryServiceAccountConfig
    | BigQueryBrowserAuthConfig
    | undefined;

  constructor() {
    this.connector_type = "BIGQUERY"; // Default value for connector_type
  }
}


export class SnowFlakeConnectorConfiguration implements BaseConnectorModel {
  connector_type: string;  // Add connector_type
  authentication_type: SnowflakeAuthType | undefined;
  //authentication_details: SnowFlakeUserAuthConfig | undefined; 
  authentication: SnowFlakeUserAuthConfig | undefined;

  constructor() {
    this.connector_type = "SNOWFLAKE"; // Default value for connector_type
    this.authentication = new SnowFlakeUserAuthConfig();  // Initialize authentication
    //this.authentication_details = new SnowFlakeUserAuthConfig();  // Initialize authentication details
  }
}

export class SnowFlakeUserAuthConfig implements BaseConnectorModel {
  sf_user: string | undefined;
  sf_account: string | undefined;
  sf_password: string | undefined;
  sf_database: string | undefined;
  sf_warehouse: string | undefined;
  sf_schema: string | undefined;
  sf_role: string | undefined;
  authentication_type: string | undefined;
}

export class RescaleConnTemplate implements BaseConnectorModel {
  name: string;
  test_mode: boolean;
  run_job: boolean;
  files: string[] | undefined;
  software: SoftwareConfig;

  constructor(rescaleConnTemplate: RescaleConnTemplate) {
    this.name = rescaleConnTemplate.name;
    this.test_mode = rescaleConnTemplate.test_mode;
    this.run_job = rescaleConnTemplate.run_job;
    this.files = rescaleConnTemplate.files;
    this.software = new SoftwareConfig(rescaleConnTemplate.software);
  }
}
export class SoftwareConfig {
  analysis: {
    code: string;
    version: string;
  };
  hardware: {
    coresPerSlot: number;
    slots: number;
    coreType: string;
    walltime: number;
    type?: string
  };
  command: string;
  output_file: string;
  visualize_files?: string[];
  envVars: { [key: string]: string };
  onDemandLicenseSeller?: string | null;
  software_type: string | undefined;

  constructor(softwareConfig: SoftwareConfig) {
    this.analysis = softwareConfig.analysis;
    this.hardware = softwareConfig.hardware;
    this.command = softwareConfig.command;
    this.output_file = softwareConfig.output_file;
    this.visualize_files = softwareConfig.visualize_files;
    this.envVars = softwareConfig.envVars;
    this.onDemandLicenseSeller = softwareConfig.onDemandLicenseSeller;
    this.software_type = softwareConfig.software_type;
  }
}
export class RescaleConnectorConfiguration implements BaseConnectorModel {
  connector_type: string; // Add connector_type
  token: string | undefined;
  rescale_settings: RescaleConnTemplate | string = '';

  constructor() {
    this.connector_type = "RESCALE"; // Default value for connector_type
  }
}

export class CouchbaseConnectorConfiguration implements BaseConnectorModel {
  connector_type: string; // Add connector_type
  connection_str: string | undefined;

  constructor() {
    this.connector_type = "COUCHBASE"; // Default value for connector_type
  }
}

export class MysqlConnectorConfiguration implements BaseConnectorModel {
  connector_type: string; // Add connector_type
  connection_str: string | undefined;

  constructor() {
    this.connector_type = "MYSQL"; // Default value for connector_type
  }
}

export class HiveConnectorConfiguration implements BaseConnectorModel {
  connector_type: string; // Add connector_type
  connection_str: string | undefined;

  constructor() {
    this.connector_type = "HIVE"; // Default value for connector_type
  }
}

export class PostgresqlConnectorConfiguration implements BaseConnectorModel {
  connector_type: string; // Add connector_type
  connection_str: string | undefined;

  constructor() {
    this.connector_type = "HIVE"; // Default value for connector_type
  }
}

export class RedshiftConnectorConfiguration implements BaseConnectorModel {
  connector_type: string; // Add connector_type
  connection_str: string | undefined;

  constructor() {
    this.connector_type = "HIVE"; // Default value for connector_type
  }
}
export class ElasticConnectorConfiguration implements BaseConnectorModel {
  connector_type: string; // Add connector_type
  connection_str: string | undefined;

  constructor() {
    this.connector_type = "ELASTICSEARCH"; // Default value for connector_type
  }
}

export class ThermoCalcConnectorConfiguration implements BaseConnectorModel {
  connector_type: string; // Add connector_type
  host: string | undefined;
  path: string | undefined;
  method: string | undefined;

  constructor() {
    this.connector_type = "THERMOCALC"; // Default value for connector_type
  }
}

export class Connector implements BaseConnectorModel {
  _id: string | undefined = undefined;
  name: string | undefined = undefined;
  description: string | undefined = undefined;
  type: ConnectorType | undefined = undefined;
  configuration: BigQueryConnectorConfiguration 
  | RescaleConnectorConfiguration 
  | ThermoCalcConnectorConfiguration
  | SnowFlakeConnectorConfiguration
  | CouchbaseConnectorConfiguration
  | MysqlConnectorConfiguration
  | RedshiftConnectorConfiguration
  | HiveConnectorConfiguration
  | ElasticConnectorConfiguration
  | undefined;
  owner_id: string | undefined = undefined;
  owner_name: string | undefined = undefined;
  created_at: string | undefined = undefined;
  last_modified_by_id: string | undefined = undefined;
  last_modified_at: string | undefined = undefined;
  project_id: string | undefined = undefined;
  site_id: string | undefined = undefined;
  version: string | undefined = undefined;
}
