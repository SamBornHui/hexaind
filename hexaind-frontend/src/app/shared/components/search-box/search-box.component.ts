import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import {
  debounceTime,
  distinctUntilChanged,
  Subject,
  Subscription,
} from 'rxjs';
import { InputComponent } from '../input/input.component';

@Component({
  selector: 'mst-search-box',
  templateUrl: './search-box.component.html',
  styleUrls: ['./search-box.component.scss'],
  standalone: true,
  imports: [InputComponent],
})
export class SearchBoxComponent implements OnInit {
  private searchSubject = new Subject<string>();
  private searchSubscription!: Subscription;
  @Input() timeout = 300;
  @Input() placeholder = 'Search...';
  @Input() label = 'Search';
  @Input() value = '';
  @Output() search = new EventEmitter<string>();
  ngOnInit() {
    this.searchSubscription = this.searchSubject
      .pipe(
        debounceTime(300), // Debounce for 300ms
        distinctUntilChanged(), // Only emit if value is different
      )
      .subscribe((searchTerm) => {
        this.search.emit(searchTerm);
      });
  }

  ngOnDestroy() {
    this.searchSubscription.unsubscribe(); // Prevent memory leaks
  }

  onSearchInput(searchTerm: string) {
    this.searchSubject.next(searchTerm);
  }
}
