import { Component, Inject } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { ToastrService } from 'ngx-toastr';
import { ConnectorType } from 'src/app/models/connector-models';
import { ConnectorsService } from 'src/app/pages/connectors/services/connectors.service';
import { ConfigService } from 'src/app/services/config.service';
import { NewConnectorService } from '../connector-dialog/services/new-connector.service';

@Component({
  selector: 'app-connectors-update',
  templateUrl: './connectors-update.component.html',
  styleUrls: ['./connectors-update.component.less']
})
export class ConnectorsUpdateComponent {

  descriptionError: any;
  nameError: any;
  isCreatingConnectors: boolean = false;
  spinner: boolean = false;
  isJsonAuthenticationSuccessful: boolean = false;
  isJsonAuthenticationFailed: boolean = false;
  isUserAuthenticatedSuccessful: boolean = false;
  isUserAuthenticatedFailed: boolean = false;

  constructor(
    private dialogRef: MatDialogRef<ConnectorsUpdateComponent>,
    @Inject(MAT_DIALOG_DATA)
    public data: {
      connectors: any;
    },
    private connectorsService: ConnectorsService,
    public toaster: ToastrService,
    private configService: ConfigService,
    private connectorService: NewConnectorService,
  ) { }
  connectorName: any = this.data.connectors.name;
  connectorDescription: any = this.data.connectors.description;
  ngOnInit(): void {
    //this.getAllConnectors();
  }

  handleInputChange(event: Event) {
    this.connectorName = this.connectorName.trim()
    this.connectorDescription = this.connectorDescription.trim()

    if (this.connectorName === '') {
      this.nameError = 'Name is required.'
      this.isCreatingConnectors = true;
    }
    else if (this.connectorDescription === '') {
      this.descriptionError = 'Name is required.'
      this.isCreatingConnectors = true;
    }
    else if (this.data.connectors.type === ConnectorType.THERMOCALC && !this.checkValidation()) {
      this.isCreatingConnectors = true
    }
    else {
      this.isCreatingConnectors = false;
      this.nameError = '';
      this.descriptionError = '';
    }
  }

  async onUpdateProject() {
    this.data.connectors.name = this.connectorName;
    this.data.connectors.description = this.connectorDescription;
    if (this.data.connectors.type === ConnectorType.THERMOCALC) {
      var config = this.data.connectors.configuration;
      if (!config.host) {
        this.toaster.error('Server name is required.'); return;
      }

      if (!config.path) {
        this.toaster.error('Application path is required.'); return;
      }
    }

    this.connectorsService.ConnectorsUpdate(this.data.connectors).subscribe((res) => {
    });
    this.dialogRef.close();
  }

  checkValidation() {
    return (this.data.connectors.configuration.host !== '' && this.data.connectors.configuration.path !== '')
  }
  authentication() {
    this.spinner = true;
    if (this.data.connectors.type === ConnectorType.THERMOCALC) {
      this.thermoCalcAuthentication();
    }
  }

  thermoCalcAuthentication() {
    // this.onchange();
    let authObj = {
      "host": this.data.connectors.configuration.host,
      "path": this.data.connectors.configuration.path,
      "method": this.data.connectors.configuration.method
    };
    this.connectorService.thermoCalcAuthenticate(this.configService.SelectedSiteId, this.configService.SelectedProjectId ?? '', authObj).subscribe({
      next: (response: any) => {
        this.spinner = false;
        this.isJsonAuthenticationFailed = false
        this.isJsonAuthenticationSuccessful = true;
        // this.showContinue = true;
      },
      error: (error: any) => {
        this.spinner = false;
        this.isJsonAuthenticationSuccessful = false;
        this.isJsonAuthenticationFailed = true
      }
    });
  }

}


