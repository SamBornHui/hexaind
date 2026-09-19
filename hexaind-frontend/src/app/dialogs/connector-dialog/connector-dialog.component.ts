import { Component, ViewChild, Input, Inject } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { BigQueryServiceAccountData } from './big-query-service-account-data';
import { NewConnectorService } from './services/new-connector.service';
import { ActivatedRoute, Router } from '@angular/router';
import {
  BigQueryAuthType,
  BigQueryBrowserAuthConfig,
  BigQueryConnectorConfiguration,
  BigQueryServiceAccountConfig,
  BigQueryUserAuthConfig,
  Connector,
  ConnectorType,
  RescaleConnectorConfiguration,
  SnowflakeAuthType,
  SnowFlakeConnectorConfiguration,
  SnowFlakeUserAuthConfig,
  ThermoCalcConnectorConfiguration,
  CouchbaseConnectorConfiguration,
  ElasticConnectorConfiguration,
  MysqlConnectorConfiguration,
  HiveConnectorConfiguration,
  PostgresqlConnectorConfiguration,
  RedshiftConnectorConfiguration
} from 'src/app/models/connector-models';

@Component({
  selector: 'app-connector-dialog',
  templateUrl: './connector-dialog.component.html',
  styleUrls: ['./connector-dialog.component.less'],
})
export class ConnectorDialogComponent {
  selectedConnector: string | null = null;
  currentStep = 1;
  totalSteps = 3;
  connectionType = 'Service Account';
  connectionType1 = 'Snowflake Authentication';
  bigQueryServiceAccountData: BigQueryServiceAccountData | undefined = undefined;
  newConnectorName: string = '';
  //newConnectorDescription: string = '';
  clientId: string = '';
  sf_password: string = '';
  sf_account: string = '';
  sf_warehouse: string = '';
  sf_database: string = '';
  sf_schema: string = '';
  sf_role: string = '';
  clientSecret: string = '';
  refreshToken: string = '';
  passwordVisible: boolean = false;
  connectorType = ''
  authMethod = 'service_account_file'
  fileName = ''
  showContinue: boolean = false;
  showContinue2: boolean = false;
  projectId: string = '1'
  userAuthProjectId: string = '';
  browserAuthProjectId: string = '';
  spinner: boolean = false;
  isJsonAuthenticationSuccessful: boolean = false;
  isJsonAuthenticationFailed: boolean = false;
  isUserAuthenticatedSuccessful: boolean = false;
  isUserAuthenticatedFailed: boolean = false;
  isBrowserAuthenticated: boolean = false;
  gcp_project_id: string = '';
  sf_user: string = '';
  siteId: string = '1';
  token: string = '';
  connection_str: string = '';
  skipStep = false;
  themoCalcAuthMethod = 'server_ip_address';
  serverName = '';
  applicationPath = '';
  isLoading = false;

  connectors = [
    { value: 'BIGQUERY', label: 'BigQuery', icon: 'assets/icon-bigquery.svg' },
    { value: 'SNOWFLAKE', label: 'Snowflake', icon: 'assets/icon-snowflake.svg' },
    { value: 'RESCALE', label: 'Rescale', icon: 'assets/icon-rescale.svg' },
    { value: 'THERMOCALC', label: 'ThermoCalc', icon: 'assets/icon-thermocalc.svg' },    
    { value: 'MYSQL', label: 'Mysql', icon: 'assets/icon-mysql.svg' },
    { value: 'HIVE', label: 'Hive', icon: 'assets/icon-hive.svg' },
    { value: 'REDSHIFT', label: 'Redshift', icon: 'assets/icon-redshift.svg' },
    { value: 'POSTGRESQL', label: 'Postgresql', icon: 'assets/icon-postgresql.svg' },
    { value: 'COUCHBASE', label: 'Couchbase', icon: 'assets/icon-couchbase.svg' },
    { value: 'ELASTICSEARCH', label: 'ElasticSearch', icon: 'assets/icon-elasticsearch.svg' },
  ];

  
  searchTerm: string = '';
  filteredConnectors = [...this.connectors];
  gcsBucketName: string = "";

  constructor(
    public dialogRef: MatDialogRef<ConnectorDialogComponent>,
    private connectorService: NewConnectorService,
    private route: ActivatedRoute,
    private router: Router,
    @Inject(MAT_DIALOG_DATA) public data: any
  ) {
    let currentUser = JSON.parse(localStorage.getItem("currentUser")!);

    let url = this.router.url.split('/');
    this.projectId = url[4];
    this.siteId = url[2];

    if (this.data) {
      this.selectedConnector = this.data.selectedConnector;
      this.showContinue = true;
      if (this.data.skipStep) {
        this.skipStep = true;
        this.currentStep = 2;
      }
    }
  }

  isShowingUserAuthentication() {
    return this.connectionType === 'User Authentication';
  }

  onRadioChange(event: any) {
    const selectedValue = event.value;
    if (selectedValue != "") {
      this.selectedConnector = selectedValue;
      this.showContinue = true;
    }
  }

  // filteredConnectors() {
  //   if (!this.searchTerm) {
  //     return this.connectors; // Return all connectors if no search term
  //   }
  //   return this.connectors.filter(connector =>
  //     connector.label.toLowerCase().includes(this.searchTerm.toLowerCase())
  //   );
  // }

  filterConnectors() {
    this.filteredConnectors = this.connectors.filter(connector =>
      connector.label.toLowerCase().includes(this.searchTerm.toLowerCase())
    );
  }

 

  onConnectorChange(event: any) {
    console.log('Selected connector:', event.value);
    this.selectedConnector = event.value;
    this.showContinue = true;
    // Perform additional logic if needed (e.g., advance to the next step)
  }

  displayBackButton() {
    if (this.currentStep == 2 && this.skipStep) {
      return false;
    } else if (this.currentStep == 2 && !this.skipStep) {
      return true;
    } else if (this.currentStep == 3) {
      return true;
    } else {
      return false;
    }

  }

  checkContinueButton() {
    if (this.currentStep === 2) {
      this.showContinue = this.newConnectorName.trim() !== ''; //  && this.newConnectorDescription.trim() !== ''
    } else if (this.currentStep === 3 && this.connectionType === 'User Authentication') {
      this.showContinue = this.clientId.trim() !== '' && this.clientSecret.trim() !== '' && this.refreshToken.trim() !== '';
    } else {
      this.showContinue = true;
    }
  }

  next() {
    this.currentStep = this.currentStep + 1;

    if (this.currentStep === 2) {
      this.showContinue = this.newConnectorName.trim().length > 0; //&& this.newConnectorDescription.trim().length > 0
    }
  }

  previous() {
    this.currentStep = this.currentStep - 1;
    if (this.currentStep === 1) {
      this.showContinue = true;
    }
    if (this.currentStep === 2) {
      this.showContinue = this.newConnectorName.trim().length > 0; //&& this.newConnectorDescription.trim().length > 0
    }
  }

  async finish() {
    if (!this.isCreated()) { 
      return;
    }

    this.isLoading = true; // Show spinner
    let connector: Connector = new Connector();
    connector.name = this.newConnectorName;
    //connector.description = this.newConnectorDescription;
    if (this.selectedConnector == ConnectorType.BIGQUERY) {
      connector.type = ConnectorType.BIGQUERY;
      connector.configuration = new BigQueryConnectorConfiguration();

      if (this.connectionType === 'User Authentication') {
        connector.configuration.authentication_type = BigQueryAuthType.USER_AUTH;
        let bigQueryUserAuthConfig: BigQueryUserAuthConfig = new BigQueryUserAuthConfig();
        bigQueryUserAuthConfig.client_id = this.clientId;
        bigQueryUserAuthConfig.client_secret = this.clientSecret;
        bigQueryUserAuthConfig.refresh_token = this.clientId;
        connector.configuration.authentication_details = bigQueryUserAuthConfig;
      }

      if (this.connectionType === 'Service Account') {
        connector.configuration.authentication_type = BigQueryAuthType.SERVICE_ACCOUNT;
        connector.configuration.authentication_details = this.bigQueryServiceAccountData;
        connector.configuration.gcs_bucket_name = this.gcsBucketName;
      }
    } else if (this.selectedConnector == ConnectorType.RESCALE) {
      connector.type = ConnectorType.RESCALE;
      let config = new RescaleConnectorConfiguration();
      config.token = this.token;
      config.rescale_settings = ''
      connector.configuration = config;
    } else if (this.selectedConnector == ConnectorType.COUCHBASE) {
      connector.type = ConnectorType.COUCHBASE;
      let config = new CouchbaseConnectorConfiguration();
      config.connection_str = this.connection_str;
      connector.configuration = config;
    } else if (this.selectedConnector == ConnectorType.ELASTICSEARCH) {
      connector.type = ConnectorType.ELASTICSEARCH;
      let config = new ElasticConnectorConfiguration();
      config.connection_str = this.connection_str;
      connector.configuration = config;
    } else if (this.selectedConnector == ConnectorType.MYSQL) {
      connector.type = ConnectorType.MYSQL;
      let config = new MysqlConnectorConfiguration();
      config.connection_str = this.connection_str;
      connector.configuration = config;
    } else if (this.selectedConnector == ConnectorType.HIVE) {
      connector.type = ConnectorType.HIVE;
      let config = new HiveConnectorConfiguration();
      config.connection_str = this.connection_str;
      connector.configuration = config;
    } else if (this.selectedConnector == ConnectorType.REDSHIFT) {
      connector.type = ConnectorType.REDSHIFT;
      let config = new RedshiftConnectorConfiguration();
      config.connection_str = this.connection_str;
      connector.configuration = config;
    } else if (this.selectedConnector == ConnectorType.POSTGRESQL) {
      connector.type = ConnectorType.POSTGRESQL;
      let config = new PostgresqlConnectorConfiguration();
      config.connection_str = this.connection_str;
      connector.configuration = config;
    } else if (this.selectedConnector == ConnectorType.THERMOCALC) {
      connector.type = ConnectorType.THERMOCALC;
      let config = new ThermoCalcConnectorConfiguration();
      config.host = this.serverName;
      config.path = this.applicationPath,
      config.method = this.themoCalcAuthMethod
      connector.configuration = config;
    } else if (this.selectedConnector === ConnectorType.SNOWFLAKE) {
      // Create a new instance of SnowFlakeConnectorConfiguration
      connector.type = ConnectorType.SNOWFLAKE;
      let snowflakeConfig = new SnowFlakeConnectorConfiguration();
      
      // Set the connector_type property to "SNOWFLAKE"
      snowflakeConfig.connector_type = "SNOWFLAKE";
    
      // Set the authentication details
      snowflakeConfig.authentication = new SnowFlakeUserAuthConfig();
      snowflakeConfig.authentication.authentication_type = "DEFAULT";  // Set default value
      snowflakeConfig.authentication.sf_user = this.sf_user || "example_user";  // User input or default value
      snowflakeConfig.authentication.sf_password = this.sf_password || "example_password";  // User input or default value
      snowflakeConfig.authentication.sf_account = this.sf_account || "example_account";  // User input or default value
      snowflakeConfig.authentication.sf_warehouse = this.sf_warehouse || "example_warehouse";  // User input or default value
      snowflakeConfig.authentication.sf_database = this.sf_database || "example_database";  // User input or default value
      snowflakeConfig.authentication.sf_schema = this.sf_schema || "example_schema";  // User input or default value
      snowflakeConfig.authentication.sf_role = this.sf_role || "example_role";  // User input or default value
    
      // Assign the Snowflake configuration to the connector
      connector.configuration = snowflakeConfig;
    }
    
    


    /**
      * The following code is commented out as it may be needed in the 
      * future for Browser Authentication with the BigQuery connector.
      */

    // if (this.connectionType === 'Browser Authentication') {
    //   let bigQueryBrowserAuthConfig: BigQueryBrowserAuthConfig = new BigQueryBrowserAuthConfig();
    //   connector.configuration.authentication_type = BigQueryAuthType.BROWSER_AUTH;
    //   bigQueryBrowserAuthConfig.project_id = this.browserAuthProjectId;
    //   connector.configuration.authentication_details = bigQueryBrowserAuthConfig;
    // }
    let currentUser = JSON.parse(localStorage.getItem("currentUser")!);
    connector.owner_id = currentUser._id;
    connector.owner_name = currentUser.first_name + " " + currentUser.last_name;
    connector.last_modified_by_id = currentUser._id;
    connector.project_id = this.projectId;
    connector.site_id = this.siteId;
    connector.version = '1.0';
    connector.created_at = new Date().toISOString();
    connector.last_modified_at = new Date().toISOString();
    try {
      let connectorId: string | null = await this.connectorService.CreateConnector(this.siteId, this.projectId, connector);
      if (connectorId) {
          this.dialogRef.close({ success: true });
      }
      } catch (error) {
          console.error("Error creating connector:", error);
      } finally {
          this.isLoading = false; // Stop the spinner
      }
  }

  onFileSelected(event: any) {
    const input = event.target as HTMLInputElement;
    if (!input.files?.length) {
      return;
    }
    this.isJsonAuthenticationSuccessful = false;
    this.isJsonAuthenticationFailed = false;
    const file = input.files[0];
    this.fileName = file.name
    const reader = new FileReader();
    reader.onload = (e) => {
      const content = reader.result as string;
      try {
        const jsonContent = JSON.parse(content);
        const obj = new BigQueryServiceAccountData();
        this.bigQueryServiceAccountData = Object.assign(obj, jsonContent);
      } catch (error) {
        console.error('Error parsing JSON', error);
      }
    };
    reader.readAsText(file);
  }

  authentication() {
    this.spinner = true;
    if (this.selectedConnector === ConnectorType.RESCALE) {
      this.rescaleAuthentication();
    } else if (this.selectedConnector === ConnectorType.BIGQUERY) {
      this.bigQueryAuthentication();
    } else if (this.selectedConnector === ConnectorType.SNOWFLAKE) {
      this.snowFlakeAuthentication();  
    } else if (this.selectedConnector === ConnectorType.THERMOCALC) {
      this.thermoCalcAuthentication();
    }
  }
  onchange() {
    this.isJsonAuthenticationFailed = false;
    this.isJsonAuthenticationSuccessful = false;
  }

  onchangestring() {
    this.isJsonAuthenticationFailed = false;
    this.isJsonAuthenticationSuccessful = true;
  }

  bigQueryAuthentication() {
    
    if (this.connectionType === 'Service Account') {
      this.isJsonAuthenticationSuccessful = false;
      this.isJsonAuthenticationFailed = false;
      let obj = {
        "auth_object": this.bigQueryServiceAccountData,
        "auth_type": "SERVICE_ACCOUNT_FILE"
      };

      this.connectorService.authenticateConnector(this.siteId, this.projectId, obj).subscribe({
        next: (response: any) => {
          this.spinner = false;
          this.isJsonAuthenticationFailed = false
          this.isJsonAuthenticationSuccessful = true;
        },
        error: (error: any) => {
          this.spinner = false;
          this.isJsonAuthenticationSuccessful = false;
          this.isJsonAuthenticationFailed = true
        }
      });
    } else if (this.connectionType === "User Authentication") {
      this.isUserAuthenticatedFailed = false;
      this.isUserAuthenticatedSuccessful = false;
      let obj = {
        auth_type: "GOOGLE_DEFAULT_LOGIN",
        gcp_project_id: this.gcp_project_id,
        client_id: this.clientId,
        client_secret: this.clientSecret,
        refresh_token: this.refreshToken,
      };
      this.connectorService.authenticateConnector(this.siteId, this.projectId, obj).subscribe({
        next: (response: any) => {
          this.spinner = false;
          this.isUserAuthenticatedFailed = false;
          this.isUserAuthenticatedSuccessful = true;
        },
        error: (error: any) => {
          this.spinner = false;
          this.isUserAuthenticatedSuccessful = false;
          this.isUserAuthenticatedFailed = true;
        }
      });
    }
    else { }
  }
  snowFlakeAuthentication() {
    
    if (this.connectionType1 === "Snowflake Authentication") {
      this.isUserAuthenticatedFailed = false;
      this.isUserAuthenticatedSuccessful = false;
      let obj = {
        authentication_type: "DEFAULT",
        sf_user: this.sf_user,
        sf_account: this.sf_account,
        sf_password: this.sf_password,
        sf_database: this.sf_database,
        sf_warehouse: this.sf_warehouse,
        sf_schema: this.sf_schema,
        sf_role: this.sf_role
      };
      this.connectorService.SnowflakeauthenticateConnector(this.siteId, this.projectId, obj).subscribe({
        next: (response: any) => {
          this.spinner = false;
          if(response.status != false){
            this.isUserAuthenticatedFailed = false;
            this.isUserAuthenticatedSuccessful = true;
          }else{
            this.isUserAuthenticatedFailed = true;
            this.isUserAuthenticatedSuccessful = false;
          }
        },
        error: (error: any) => {
          this.spinner = false;
          this.isUserAuthenticatedSuccessful = false;
          this.isUserAuthenticatedFailed = true;
        }
      });
    }
    else { }
  }
  rescaleAuthentication() {
    this.onchange();
    this.connectorService.rescaleAuthenticate(this.siteId, this.projectId, { token: this.token }).subscribe({
      next: (response: any) => {
        this.spinner = false;
        this.isJsonAuthenticationFailed = false
        this.isJsonAuthenticationSuccessful = true;
        this.showContinue = true;
      },
      error: (error: any) => {
        this.spinner = false;
        this.isJsonAuthenticationSuccessful = false;
        this.isJsonAuthenticationFailed = true
      }
    });
  }
  thermoCalcAuthentication() {
    this.onchange();
    let authObj = {
      "host": this.serverName,
      "path": this.applicationPath,
      "method": this.themoCalcAuthMethod,
      "connector_type": 'THERMOCALC'
    };
    this.connectorService.thermoCalcAuthenticate(this.siteId, this.projectId, authObj).subscribe({
      next: (response: any) => {
        this.spinner = false;
        this.isJsonAuthenticationFailed = false
        this.isJsonAuthenticationSuccessful = true;
        this.showContinue = true;
      },
      error: (error: any) => {
        this.spinner = false;
        this.isJsonAuthenticationSuccessful = false;
        this.isJsonAuthenticationFailed = true
      }
    });
  }
  isThermCalcConnection() {
    return (this.selectedConnector == 'THERMOCALC') ? true : false;
  }
  isRescaleConnection() {
    return (this.selectedConnector == 'RESCALE') ? true : false;
  }
  isBigQueryConnection() {
    return (this.selectedConnector == 'BIGQUERY') ? true : false;
  }
  isSnowFlakeConnection() {
    return (this.selectedConnector == 'SNOWFLAKE') ? true : false;
  }
  isCouchbaseConnection() {
    return (this.selectedConnector == 'COUCHBASE') ? true : false;
  }
  isElasticConnection() {
    return (this.selectedConnector == 'ELASTICSEARCH') ? true : false;
  }
  isMysqlConnection() {
    return (this.selectedConnector == 'MYSQL') ? true : false;
  }
  isHiveConnection() {
    return (this.selectedConnector == 'HIVE') ? true : false;
  }
  isRedshiftConnection() {
    return (this.selectedConnector == 'REDSHIFT') ? true : false;
  }
  isPostgresqlConnection() {
    return (this.selectedConnector == 'POSTGRESQL') ? true : false;
  }
  isCreated(): any { 
    if (this.selectedConnector == ConnectorType.RESCALE) {
      return this.isCreatedRescale();
    } else if (this.selectedConnector == ConnectorType.BIGQUERY) {
      return this.isCreatedBigQuery();
    } else if (this.selectedConnector == ConnectorType.SNOWFLAKE) {
      return this.isCreatedSnowFlake();  
    } else if (this.selectedConnector == ConnectorType.THERMOCALC) {
      return this.isCreatedThermoCalc();
    } else if (this.selectedConnector == ConnectorType.COUCHBASE) {
      return this.isCreatedCouchbase();
    } else if (this.selectedConnector == ConnectorType.ELASTICSEARCH) {
      return this.isCreatedElastic();
    } else if (this.selectedConnector == ConnectorType.MYSQL) {
      return this.isCreatedMysql();
    } else if (this.selectedConnector == ConnectorType.HIVE) {
      return this.isCreatedHive();
    } else if (this.selectedConnector == ConnectorType.REDSHIFT) {
      return this.isCreatedRedshift();
    } else if (this.selectedConnector == ConnectorType.POSTGRESQL) {
      return this.isCreatedPostgresql();
    }
  }
  isCreatedBigQuery(): boolean {
    if (this.connectionType === 'Service Account') {
      return this.fileName !== '';
    } else if (this.connectionType === 'User Authentication') {
      return this.checkRequiredFields();
    } else {
      return false;
    }
  }
  isCreatedSnowFlake(): boolean {
    if (this.connectionType1 === 'Snowflake Authentication') {
      return this.checkSnowflakeRequiredFields();
    } else {
      return false;
    }
  }
  isCreatedCouchbase(): boolean {
    return (
      this.connection_str !== ''  &&
      this.isJsonAuthenticationSuccessful
    );
  }
  isCreatedElastic(): boolean {
    return (
      this.connection_str !== ''  &&
      this.isJsonAuthenticationSuccessful
    );
  }
  isCreatedMysql(): boolean {
    return (
      this.connection_str !== ''  &&
      this.isJsonAuthenticationSuccessful
    );
  }
  isCreatedHive(): boolean {
    return (
      this.connection_str !== ''  &&
      this.isJsonAuthenticationSuccessful
    );
  }
  isCreatedRedshift(): boolean {
    return (
      this.connection_str !== ''  &&
      this.isJsonAuthenticationSuccessful
    );
  }
  isCreatedPostgresql(): boolean {
    return (
      this.connection_str !== ''  &&
      this.isJsonAuthenticationSuccessful
    );
  }
  isCreatedRescale(): boolean {
    return (
      this.token !== '' &&
      this.newConnectorName !== '' &&
      this.isJsonAuthenticationSuccessful
    );
  }
  isCreatedThermoCalc(): boolean {
    return (
      this.serverName !== '' &&
      this.applicationPath !== '' &&
      this.newConnectorName !== '' &&
      this.isJsonAuthenticationSuccessful
    );
  }
  enableThermoCalcAuthButton(): boolean {
    return (
      this.serverName !== '' &&
      this.applicationPath !== ''
    );
  }

  checkRequiredFields(): boolean {
    return (
      this.gcp_project_id !== '' &&
      this.clientId !== '' &&
      this.clientSecret !== '' &&
      this.refreshToken !== ''
    );
  }
  enableAuthenticateButton(): boolean {
    return (
      this.gcp_project_id !== '' &&
      this.clientId !== '' &&
      this.clientSecret !== '' &&
      this.refreshToken !== ''
    );
  }

  checkSnowflakeRequiredFields(): boolean {
    return (
      this.sf_user !== '' &&
      this.sf_password !== '' &&
      this.sf_account !== '' &&
      this.sf_warehouse !== '' &&
      this.sf_database !== '' &&
      this.sf_schema !== '' &&
      this.sf_role !== ''
    );
  }
  enableSnowflakeAuthenticateButton(): boolean {
    return (
      this.sf_user !== '' &&
      this.sf_password !== '' &&
      this.sf_account !== '' &&
      this.sf_warehouse !== '' &&
      this.sf_database !== '' &&
      this.sf_schema !== '' &&
      this.sf_role !== ''
    );
  }

  togglePasswordVisibility() {
    this.passwordVisible = !this.passwordVisible;
  }

}
