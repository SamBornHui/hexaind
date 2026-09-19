import { Injectable } from '@angular/core';
import { DirectoryItem, Utils } from './../utils';
import { Observable, Subject } from 'rxjs';
import { ConfigService } from './config.service';
import { WebSocketSubject, webSocket } from 'rxjs/webSocket';
import {
  HttpClient,
  HttpErrorResponse,
  HttpHeaders,
  HttpEventType,
} from '@angular/common/http';
import { catchError, map } from 'rxjs/operators';

import { User } from '../models/user-models';

import { SharedDataService } from './shared services/shared-data.service';



@Injectable({
  providedIn: 'root',
})
export class UserService { 
  constructor(
   
  ) {}
  

  
}
