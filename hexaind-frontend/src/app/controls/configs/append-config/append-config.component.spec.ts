import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AppendComponent } from './append-config.component';

describe('AppendComponent', () => {
  let component: AppendComponent;
  let fixture: ComponentFixture<AppendComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [AppendComponent],
    });
    fixture = TestBed.createComponent(AppendComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
