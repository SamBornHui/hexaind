import { Component, Inject } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { NgForm } from '@angular/forms';
import { DataCatalogService } from '../tools/data-catalog/data-catalog.service';
import { ConfigService } from 'src/app/services/config.service';
import { ToastrService } from 'ngx-toastr';


export interface DataElement {
  name: string;
  desc: string;
}

const ELEMENT_DATA: DataElement[] = [
  { name: 'Hydrogen', desc: 'Element 1' },
  { name: 'Helium', desc: 'Element 2' },
  { name: 'Lithium', desc: 'Element 3' },
  { name: 'Beryllium', desc: 'Element 4' },
  { name: 'Boron', desc: 'Element 5' },
  { name: 'Helium', desc: 'Element 2' },
  { name: 'Lithium', desc: 'Element 3' },
  { name: 'Beryllium', desc: 'Element 4' },
  { name: 'Boron', desc: 'Element 5' },
  { name: 'Helium', desc: 'Element 2' },
  { name: 'Lithium', desc: 'Element 3' },
  { name: 'Beryllium', desc: 'Element 4' },
  { name: 'Boron', desc: 'Element 5' },
  { name: 'Helium', desc: 'Element 2' },
  { name: 'Lithium', desc: 'Element 3' },
  { name: 'Beryllium', desc: 'Element 4' },
  { name: 'Boron', desc: 'Element 5' },
];

@Component({
  selector: 'app-create-session',
  templateUrl: './create-session.component.html',
  styleUrls: ['./create-session.component.less'],
})
export class CreateSessionComponent {
  constructor(
    public dialogRef: MatDialogRef<CreateSessionComponent>,
    private dataCatService: DataCatalogService,
    private configService: ConfigService,
    public toaster: ToastrService,
    @Inject(MAT_DIALOG_DATA) public data: any,
  ) {}

  displayedColumns: string[] = ['select', 'name', 'desc'];
  dataSource = ELEMENT_DATA;
  selectedRow: DataElement | null = null;
  newName: string = '';
  newDesc: string = '';

  submit() {
    if (this.newName && this.newDesc) {
      let payload = {
        project_id: this.configService.SelectedProjectId,
        name: this.newName,
        description: this.newDesc,
        data_source_type: 'FD_TRACE',
      };
      this.dataCatService.createSession(payload).subscribe((id: any) => {
        try{
          if(id)
            this.toaster.success('Session created successfully');
            this.onClose();
        }
        catch (error) {
          this.toaster.error('Error creating session');
        }
      });       
    } 
    else {
      this.toaster.error("Please enter Name and Description");
      return;
    }
  }

  onClose() {
    this.dialogRef.close();
  }

  saveNewEntry(form: NgForm) {
    if (form.valid) {
      if (this.newName && this.newDesc) {
        console.log(
          `New Entry - Name: ${this.newName}, Description: ${this.newDesc}`,
        );
        // Logic to save the new entry
        this.clearNewEntry(form); // Optionally clear fields after saving
      }
    } else {
      form.control.markAllAsTouched(); // Mark all controls as touched to show validation errors
    }
  }

  clearNewEntry(form: NgForm) {
    this.newName = '';
    this.newDesc = '';
    form.resetForm(); // Reset the form state
  }
}
