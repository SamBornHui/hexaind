import { Component } from '@angular/core';
import { FlexLayoutModule } from '@angular/flex-layout';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { MatButtonToggleModule } from '@angular/material/button-toggle';
import { MatIconModule } from '@angular/material/icon';
import { MatTableModule } from '@angular/material/table';
import { MatChipsModule } from '@angular/material/chips';
import { MatMenuModule } from '@angular/material/menu';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatRadioModule } from '@angular/material/radio';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatNativeDateModule } from '@angular/material/core';
import { MatDividerModule } from '@angular/material/divider';
import {MatBadgeModule} from '@angular/material/badge';
import {MatProgressSpinnerModule} from '@angular/material/progress-spinner';
import {MatSlideToggleModule} from '@angular/material/slide-toggle';
import {MatSliderModule} from '@angular/material/slider';
import {MatTabsModule} from '@angular/material/tabs';

@Component({
  selector: 'app-components',
  templateUrl: './components.component.html',
  styleUrls: ['./components.component.less'],
  standalone: true,
  imports: [
    FlexLayoutModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatButtonModule,
    MatButtonToggleModule,
    MatIconModule,
    MatTableModule,
    MatChipsModule,
    MatMenuModule,
    MatCheckboxModule,
    MatRadioModule,
    MatDatepickerModule,
    MatNativeDateModule,
    MatDividerModule,
    MatBadgeModule,
    MatProgressSpinnerModule,
    MatSlideToggleModule,
    MatSliderModule,
    MatTabsModule,
  ],
})
export class ComponentsComponent {
  displayedColumns: string[] = [
    'name',
    'type',
    'size',
    'uploader',
    'last_modified',
    'actions',
  ];
  dataSource = DATA_LIST;
}

export interface dataTable {
  name: string;
  type: string;
  size: string;
  uploader: string;
  last_modified: string;
}

const DATA_LIST: dataTable[] = [
  {
    name: 'image.png',
    type: 'png',
    size: '22 KB',
    uploader: 'Mike Snow',
    last_modified: '11/27/23 11:00 AM',
  },
  {
    name: 'this-is-a-file.py',
    type: 'py',
    size: '245 MB',
    uploader: 'Srihari Puppala',
    last_modified: '11/27/23 11:00 AM',
  },
  {
    name: 'this-is-a-file.py',
    type: 'py',
    size: '245 MB',
    uploader: 'Rohan Lam',
    last_modified: '11/27/23 11:00 AM',
  },
  {
    name: 'this-is-a-file-2.cfg',
    type: 'cfg',
    size: '224 KB',
    uploader: 'Taimoor Hassan',
    last_modified: '11/27/23 11:00 AM',
  },
];
