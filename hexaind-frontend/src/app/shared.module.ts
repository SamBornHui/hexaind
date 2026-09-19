// shared.module.ts
import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TooltipModule } from 'ngx-bootstrap/tooltip';
import { FlexLayoutModule } from '@angular/flex-layout';
import { MatTableModule } from '@angular/material/table';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MatDialogModule } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatSelectModule } from '@angular/material/select';
import { ToastrModule } from 'ngx-toastr';
import {
  MatFormFieldModule,
  MAT_FORM_FIELD_DEFAULT_OPTIONS,
} from '@angular/material/form-field';
import { MatGridListModule } from '@angular/material/grid-list';
import { MatMenuModule } from '@angular/material/menu';
import { MatChipsModule } from '@angular/material/chips';
import { MatCardModule } from '@angular/material/card';
import { HttpClientModule } from '@angular/common/http';
import { NotificationComponent } from './controls/notification/notification.component';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { HeaderComponent } from './controls/header/header.component';
import { LeftNavComponent } from './controls/left-nav/left-nav.component';
import { MatTabsModule } from '@angular/material/tabs';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatButtonToggleModule } from '@angular/material/button-toggle';
import { MatRadioModule } from '@angular/material/radio';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatBadgeModule } from '@angular/material/badge';
import { MatTreeModule } from '@angular/material/tree';
import { MatSliderModule } from '@angular/material/slider';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatNativeDateModule } from '@angular/material/core';
import { ColorPickerModule } from 'ngx-color-picker';
import { MatAutocompleteModule } from '@angular/material/autocomplete';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { WorkflowDesignerHeaderComponent } from './controls/workflow-designer-header/workflow-designer-header.component';
import { MatSortModule } from '@angular/material/sort';
import { TreeTableModule } from 'primeng/treetable';
import { TimeAgoPipe } from './time-ago.pipe';
import { MatListModule } from '@angular/material/list';
import { RoundFigurePipe } from './pipes/round-figure.pipe';
import { ModelsSummaryComponent } from './dialogs/model-preview-dialog-box/models-summary/models-summary.component';
import { ScientificNumberPipe } from './pipes/scientific-number.pipe';
import { ReplaceAndCapitalizePipe } from './pipes/text-replace-transform.pipe';
import { CustomTooltipComponent } from './pages/custom-tooltip/custom-tooltip.component';

import { FeatureNameSearchPipe } from './pipes/filter-input-name.pipe';
import { EnlargedTextEditorComponent } from './util-components/enlarged-text-editor/enlarged-text-editor.component';
import { ColumnDropDownComponent } from './util-components/column-drop-down/column-drop-down.component';
import { ScrollingModule } from '@angular/cdk/scrolling';
import { PieChartComponent } from './util-components/pie-chart/pie-chart.component';
import { NgChartsModule } from 'ng2-charts';
import { FeaturesListCommonComponent } from './util-components/features-list-common/features-list-common.component';
import { CpwCodeEditorComponent } from './util-components/cpw-code-editor/cpw-code-editor.component';
import { CodemirrorModule } from '@ctrl/ngx-codemirror';
import { CodeEditorComponent } from './util-components/code-editor/code-editor.component';
import { SpcChartComponent } from './util-components/spc-chart/spc-chart/spc-chart.component';


@NgModule({
  declarations: [
    NotificationComponent,
    HeaderComponent,
    LeftNavComponent,
    WorkflowDesignerHeaderComponent,
    RoundFigurePipe,
    ReplaceAndCapitalizePipe,
    ModelsSummaryComponent,
    ScientificNumberPipe,
    CustomTooltipComponent,
    FeatureNameSearchPipe,
    EnlargedTextEditorComponent,
    CpwCodeEditorComponent,
    PieChartComponent,
    SpcChartComponent,
    ColumnDropDownComponent,
    FeaturesListCommonComponent,
    CodeEditorComponent
  ],
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    TooltipModule.forRoot(),
    HttpClientModule,
    FlexLayoutModule,
    MatTableModule,
    MatDialogModule,
    MatSelectModule,
    MatButtonModule,
    MatFormFieldModule,
    MatGridListModule,
    MatCardModule,
    MatTabsModule,
    MatMenuModule,
    MatIconModule,
    MatInputModule,
    MatToolbarModule,
    MatSnackBarModule,
    MatTooltipModule,
    MatButtonToggleModule,
    MatRadioModule,
    MatCheckboxModule,
    NgChartsModule,
    MatBadgeModule,
    MatExpansionModule,
    MatSlideToggleModule,
    MatTreeModule,
    ScrollingModule,
    MatSliderModule,
    MatExpansionModule,
    MatSlideToggleModule,
    MatProgressSpinnerModule,
    MatDatepickerModule,
    MatNativeDateModule,
    MatAutocompleteModule,
    MatChipsModule,
    ColorPickerModule,
    MatProgressBarModule,
    TreeTableModule,
    MatListModule,
    CodemirrorModule
  ],
  exports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    TooltipModule,
    HttpClientModule,
    MatTableModule,
    MatDialogModule,
    MatSelectModule,
    PieChartComponent,
    SpcChartComponent,
    FeaturesListCommonComponent,
    MatButtonModule,
    MatFormFieldModule,
    MatGridListModule,
    MatCardModule,
    MatTabsModule,
    ColumnDropDownComponent,
    MatMenuModule,
    MatIconModule,
    FlexLayoutModule,
    HeaderComponent,
    WorkflowDesignerHeaderComponent,
    LeftNavComponent,
    NotificationComponent,
    MatInputModule,
    MatToolbarModule,
    MatSnackBarModule,
    MatTooltipModule,
    MatButtonToggleModule,
    MatRadioModule,
    MatCheckboxModule,
    MatBadgeModule,
    MatExpansionModule,
    MatSlideToggleModule,
    MatTreeModule,
    MatSliderModule,
    MatBadgeModule,
    MatExpansionModule,
    MatSlideToggleModule,
    MatDatepickerModule,
    MatAutocompleteModule,
    MatChipsModule,
    MatProgressSpinnerModule,
    ColorPickerModule,
    MatProgressBarModule,
    MatSortModule,
    TreeTableModule,
    MatListModule,
    RoundFigurePipe,
    ReplaceAndCapitalizePipe,
    ModelsSummaryComponent,
    ScientificNumberPipe,
    CustomTooltipComponent,
    FeatureNameSearchPipe,
    ScrollingModule,
    CodemirrorModule
  ],
  providers: [
    {
      provide: MAT_FORM_FIELD_DEFAULT_OPTIONS,
      useValue: { subscriptSizing: 'dynamic' },
    },
  ],
})
export class SharedModule {}
