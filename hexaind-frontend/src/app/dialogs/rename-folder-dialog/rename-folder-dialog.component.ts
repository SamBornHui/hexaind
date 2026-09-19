import { Component, Inject } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { ToastrService } from 'ngx-toastr';

@Component({
  selector: 'app-rename-folder-dialog',
  templateUrl: './rename-folder-dialog.component.html',
  styleUrls: ['./rename-folder-dialog.component.less'],
})
export class RenameFolderDialogComponent {
  folder_name:string="";
  folderService:any;
  constructor(
    @Inject(MAT_DIALOG_DATA) public data: any,
    public dialogRef: MatDialogRef<RenameFolderDialogComponent>,
    private toaster:ToastrService
  ) {
    this.folderService = this.data.dataService;
  }

  ngOnInit() {
    this.folder_name = this.data.element.name;
  }



  async renameFolderData() {
    if(this.data.element.name != this.folder_name){
      let dataInfo = {
        "new_name":this.folder_name,
        "source":this.data.element.full_path,
        "dataset_type": this.data.element.dataset_type
      }
      this.folderService
      .renameFolderData(dataInfo)
      .then((response:any) => {
        if (response) {
          this.toaster.success('Folder name updated successfully', '',{
            positionClass: 'custom-toast-position'
          });
          this.dialogRef.close({success:true});
        }
      })
      .catch((error:any) => {
        console.error('Error fetching mounted drive data:', error);
      });
    }
  }
  close(){
    this.dialogRef.close({success:false});
  }
  
}