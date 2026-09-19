import { APP_INITIALIZER, NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { SharedModule } from './shared.module';
import { DragDropModule } from '@angular/cdk/drag-drop';
import { AppRoutingModule } from './app-routing.module';
import { ToastrModule } from 'ngx-toastr';
import { AppComponent } from './app.component';
import { ContextMenuComponent } from './controls/context-menu/context-menu.component';
import { LoginComponent } from './pages/login/login.component';
import { LicenseAgreementComponent } from './dialogs/license-agreement/license-agreement.component';
import { PrivacyPolicyComponent } from './dialogs/privacy-policy/privacy-policy.component';
import { RoutinesComponent } from './pages/routines/routines.component';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { ChangePasswordComponent } from './dialogs/change-password/change-password.component';
import { ColorPickerModule } from 'ngx-color-picker';
import { HTTP_INTERCEPTORS } from '@angular/common/http';
import { ColumnPickerComponent } from './controls/column-picker/column-picker.component';
import { ColumnPickerPanelComponent } from './dialogs/column-picker-panel/column-picker-panel.component';
import { ManageAccountComponent } from './controls/manage-account/manage-account.component';
import { BigQueryPreviewComponent } from './dialogs/big-query-preview/big-query-preview.component';
import { NotificationDailogComponent } from './controls/notification-dailog/notification-dailog.component';
import { ComponentsComponent } from './components/components.component';
import { AuthGuard } from './pages/guards/index';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { ShowPagesService } from './services/show-pages.service';
import { RegisterAccountComponent } from './pages/register-account/register-account.component';
import { TokenInterceptor } from './services/token.interceptor';
import { FileEditorDialogComponent } from './dialogs/file-editor-view/file-editor-view-dialog.component';
import { OAuthModule } from 'angular-oauth2-oidc';
import * as PlotlyJS from 'plotly.js-dist-min';
import { PlotlyModule } from 'angular-plotly.js';
import { PromptSaveComponent } from './dialogs/prompt-save/prompt-save.component';
import { ResetPasswordComponent } from './pages/reset-password/reset-password.component';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatGridListModule } from '@angular/material/grid-list';
import { MatListModule } from '@angular/material/list';
import { MatSortModule } from '@angular/material/sort';
import { WebSocketService } from './services/web-sockets.service';
import { BigQueryResultPreviewComponent } from './dialogs/big-query-result-preview/big-query-result-preview.component';
import { BigQueryLoadSavedQueryComponent } from './dialogs/big-query-load-saved-query/big-query-load-saved-query.component';
import { NgMultiSelectDropDownModule } from 'ng-multiselect-dropdown';
import { DatePipe } from '@angular/common';
import { ConfirmationPrompComponent } from './dialogs/confirmation-promp/confirmation-promp.component';
import { ConfirmationImagePrompComponent } from './dialogs/confirmation-image-promp/confirmation-image-promp.component';
import { FeatureFlagService } from './services/feature-flag.service';
import { lastValueFrom } from 'rxjs';
import { JoinSelectColumnComponent } from './dialogs/join-select-columns/join-select-columns.component';
import { JupyterModalComponent } from './dialogs/jupyter-modal/jupyter-modal.component';
import { MatDialogModule } from '@angular/material/dialog';
import { CodeMirrorEditorComponent } from './monaco-editor/codemirror-editor.component';
import { CodemirrorModule } from '@ctrl/ngx-codemirror';
import { NgChartsModule } from 'ng2-charts';

export function loadFeatureFlags(featureFlagService: FeatureFlagService) {
  return () => lastValueFrom(featureFlagService.loadFeatureFlags()).catch((error: any) => {
    return {}
  });
}
PlotlyModule.plotlyjs = PlotlyJS;
@NgModule({
  declarations: [
    AppComponent,
    ContextMenuComponent,
    LoginComponent,
    LicenseAgreementComponent,
    PrivacyPolicyComponent,
    RoutinesComponent,
    ChangePasswordComponent,
    ColumnPickerComponent,
    ColumnPickerPanelComponent,
    ManageAccountComponent,
    BigQueryPreviewComponent,
    BigQueryResultPreviewComponent,
    BigQueryLoadSavedQueryComponent,
    RegisterAccountComponent,
    FileEditorDialogComponent,
    PromptSaveComponent,
    ResetPasswordComponent,
    ConfirmationPrompComponent,
    JoinSelectColumnComponent,
    JupyterModalComponent,
    CodeMirrorEditorComponent,
    ConfirmationImagePrompComponent,
    JoinSelectColumnComponent
  ],
  imports: [
    MatListModule,
    MatDialogModule,
    MatGridListModule,
    MatExpansionModule,
    MatProgressSpinnerModule,
    BrowserModule,
    AppRoutingModule,
    DragDropModule,
    ColorPickerModule,
    SharedModule,
    BrowserAnimationsModule,
    ComponentsComponent,
    PlotlyModule,
    OAuthModule.forRoot(),
    ToastrModule.forRoot({
      closeButton: false,
      timeOut: 2000,
      progressBar: true,
    }),
    PlotlyModule,
    MatSortModule,
    NgMultiSelectDropDownModule,
    CodemirrorModule
  ],
  providers: [
    AuthGuard,
    ShowPagesService,
    WebSocketService,
    DatePipe,
    {
      provide: HTTP_INTERCEPTORS,
      useClass: TokenInterceptor,
      multi: true,
    },
    {
      provide: APP_INITIALIZER,
      useFactory: loadFeatureFlags,
      deps: [FeatureFlagService],
      multi: true,
    },
  ],
  bootstrap: [AppComponent],
})
export class AppModule { }
