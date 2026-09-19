import { Injectable } from '@angular/core';
import { webSocket, WebSocketSubject } from 'rxjs/webSocket';
import { environment } from 'src/environments/environment';
import { Subscription, EMPTY, Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class WebSocketService {
  private socket$!: WebSocketSubject<any>;
  private imageSocket$!: WebSocketSubject<any>;
  private imageProgressSocket$!: WebSocketSubject<any>;
  private rescaleSocket$: WebSocketSubject<any> | null = null;

  private socketSubscription: Subscription | null = null;
  private socketProgSubscription: Subscription | null = null;
  private rescaleSocketSubscription: Subscription | null = null;

  private imageSocketURL:string='';
  private imageProgressSocketURL:string='';
  private rescaleSocketURL: string = '';


  constructor() { 
    const socketImag = `${environment.apiUrl}/v1/image_analysis/image_batch_processing_socket`
    this.imageSocketURL = socketImag.replace(/^http/, 'ws');

    const socketImagPrg = `${environment.apiUrl}/v1/image_analysis/image_progress_socket`
    this.imageProgressSocketURL = socketImagPrg.replace(/^http/, 'ws');

    const socketRescale = `${environment.apiUrl}/v1/assets/rescale_status`;
    this.rescaleSocketURL = socketRescale.replace(/^http/, 'ws');
  }

  connect(url: string): void {
   console.log("Connecting") 
    this.socket$ = webSocket(url);    
    if (this.socket$) {
      // this.socket$.subscribe(
      //   (msg) => console.log('message received: ' + JSON.stringify(msg)),
      //   (err) => console.error('Error occurred:', err),
      //   () => console.log('Completed!')
      // );
      console.log("WebSocket connection established successfully.");
    } else {
      console.error("WebSocket connection could not be established.");
    }
  }

  connectImageSocket(): void {
    this.imageSocket$ = webSocket(this.imageSocketURL);

    // Ensure socket$ is defined before subscribing
    if (this.imageSocket$) {
      this.imageSocket$.subscribe(
        (msg) => console.log('message received: ' + msg),
        (err) => console.error('Error occurred:', err),
        () => console.log('Completed!')
      );
      console.log("WebSocket connection established successfully.");
    } else {
      console.error("WebSocket connection could not be established.");
    }
  }

  disconnectImageSocket(): void {
    if (this.socketSubscription) {
      this.socketSubscription.unsubscribe();
      console.log("WebSocket connection closed.");
      this.socketSubscription = null; // Clear subscription
    }
  }

  connectImagePrgressSocket(): void {
    this.imageProgressSocket$ = webSocket(this.imageProgressSocketURL);

    // Ensure socket$ is defined before subscribing
    if (this.imageProgressSocket$) {
      this.imageProgressSocket$.subscribe(
        (msg) => console.log('message received: ' + msg),
        (err) => console.error('Error occurred:', err),
        () => console.log('Completed!')
      );
      console.log("WebSocket connection established successfully.");
    } else {
      console.error("WebSocket connection could not be established.");
    }
  }

  disconnectImageProgressSocket(): void {
    if (this.socketProgSubscription) {
      this.socketProgSubscription.unsubscribe();
      console.log("WebSocket connection closed.");
      this.socketProgSubscription = null; // Clear subscription
    }
  }

  connectRescaleSocket(): void {
    if (!this.rescaleSocket$) {
        this.rescaleSocket$ = webSocket(this.rescaleSocketURL);
  
        this.rescaleSocketSubscription = this.rescaleSocket$.subscribe(
          // (msg) => console.log('Rescale message received:', msg),
          // (err) => console.error('Rescale WebSocket error:', err),
          // () => console.log('Rescale WebSocket connection completed!')
        );
         console.log("Rescale WebSocket connection established successfully.");
      } else {
         console.warn("Rescale WebSocket is already connected.");
      }
  }

  disconnectRescaleSocket(): void {
    if (this.rescaleSocket$) {
      this.rescaleSocket$.complete();
      this.rescaleSocket$ = null;
    }
    if (this.rescaleSocketSubscription) {
      this.rescaleSocketSubscription.unsubscribe();
      this.rescaleSocketSubscription = null;
    }
  }

  get messages() {
    return this.socket$.asObservable();
  }

  get imageSocketMessages() {
    return this.imageSocket$.asObservable();
  }

  get imagePogressSocketMessages() {
    return this.imageProgressSocket$.asObservable();
  }

  get rescaleSocketMessages(): Observable<any> {
    return this.rescaleSocket$ ? this.rescaleSocket$.asObservable() : EMPTY;
  }

}
