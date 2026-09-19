import { Component, EventEmitter, Inject, OnInit, Output, ViewChild } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { Router, NavigationEnd, NavigationExtras } from '@angular/router';
// import { Role } from 'src/app/pages/dashboards/users/users.component';
import { FormBuilder, FormGroup, FormArray, Validators } from '@angular/forms';
import { MatTabChangeEvent } from '@angular/material/tabs';
import{UsersService} from '../../pages/users/users.service'
import { SnackBarNotificationService } from 'src/app/services/snack-bar-notification.service';
import { ToastrService } from 'ngx-toastr';

interface Role {
  id: number;
  name: string;
  role_type: string;
}
@Component({
  selector: 'app-grant-server-access',
  templateUrl: './grant-server-access.component.html',
  styleUrls: ['./grant-server-access.component.css'],
})
export class grantServerAccessComponent implements OnInit  {
  @Output() addEvent: EventEmitter<any> = new EventEmitter<any>();
  @Output() updateSuccess: EventEmitter<void> = new EventEmitter<void>();
  _serveRoles: Role[] = [];
  private selectedRoleIndex!: string;
  emails: string[] = [];
  emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
  form!: FormGroup;
  inviteType:string='';
  is_sso_user:boolean=false;
  loginMethod:any

  rows: {
    role_id: any;
    added: boolean;
    name: any; 
    user: string,
    role: string 
  }[] = [];
  users: string[] = ['User 1', 'User 2']; // Sample users

  lastAddedUser: string = ''; // Track last added user
  lastAddedRole: string = ''; // Track last added role
  
  getUsers: any;
  selectedUsers: any[] = [];

  getRoles: Role[] = [
    { id: 1, name: 'Server',role_type: '' }
  ];

  @ViewChild('emailInput') emailInput: any;
  constructor(
    public dialogRef: MatDialogRef<grantServerAccessComponent>,
    @Inject(MAT_DIALOG_DATA) public data: any,
    private fb: FormBuilder,
    private usersService:UsersService,
    private snackBarNotification: SnackBarNotificationService,
    public toaster: ToastrService,
    private router: Router) 
    {
      //this.addRow();
    }

  close(): void {
    this.dialogRef.close();
  }

  ngOnInit() {
    const jsonData = {      
      "server_role_values": [ 2, 4 ],
      "skip_own": true
    };
    console.log(jsonData,"get jsonData server");
    this.usersService.getUserListByServer(jsonData).subscribe({
      next: (response) => { 
        this.getUsers = response.results;
            this.rows.push({
              user: '',
              role: '', 
              role_id: '',
              added: false,
              name: undefined
            });
      },
      error: (error) => {
        console.error('Error', error);
      },
      complete: () => {
      }
    });
  }

  getAvailableUsers(rowIndex: number): any[] {
    let availableUsers = this.getUsers.slice();
    this.rows.forEach((row, index) => {
      if (index !== rowIndex && row.user) {
        const selectedIndex = availableUsers.findIndex((user: { id: string; }) => user.id === row.user);
        if (selectedIndex !== -1) {
          availableUsers.splice(selectedIndex, 1);
        }
      }
    });
    this.selectedUsers.forEach(selectedUser => {
      if (!availableUsers.find((user: { id: any; }) => user.id === selectedUser.id)) {
        availableUsers.push(selectedUser);
      }
    });
    console.log(availableUsers,"avaoal users");
    return availableUsers;
  }
  
  

  addRow() {
    
      this.rows.push({
        user: '', role: '',
        added: false,
        name: undefined,
        role_id: undefined
      });    
  }

  removeRow(row: any) {
    if (this.rows.length > 1) { 
      const index = this.rows.indexOf(row);
      if (index !== -1) {
        this.rows.splice(index, 1);
      }
    }
  }

  // trackLastAdded(user: string, role: string, index: number) { 
  //   const selectedUser = this.getUsers(index).find((u: { id: string; }) => u.id === user);
  //   if (selectedUser) {
  //     this.rows[index].name = selectedUser.name;
  //   }
  //   this.rows[index].added = true;
  // }

  trackLastAdded(user: string, role: string, index: number) { 
    const selectedUser = this.getAvailableUsers(index).find(u => u.id === user);
    if (selectedUser) {
      this.rows[index].name = selectedUser.name;
    }
    this.rows[index].added = true;
  }

  saveData() {
    const jsonData = {
      changes: this.rows.map((row, index) => ({
        user_id: row.user,
        server_role_value: row.role,
        server_role: ''
      }))
    };
   
    this.usersService.createUserAccess(jsonData).subscribe({
      next: (response) => {
        if(response.succeeded == true){
          this.toaster.success('successfully Updated Access!');
          this.dialogRef.close();
          window.location.reload();
        }
      },
      error: (error) => {
        console.error('Error', error);
      },
      complete: () => {
      }
    });
  }
  
}
