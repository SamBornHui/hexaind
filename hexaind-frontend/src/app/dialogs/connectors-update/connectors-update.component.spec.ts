import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ConnectorsUpdateComponent } from './connectors-update.component';

describe('ConnectorsUpdateComponent', () => {
  let component: ConnectorsUpdateComponent;
  let fixture: ComponentFixture<ConnectorsUpdateComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [ConnectorsUpdateComponent]
    });
    fixture = TestBed.createComponent(ConnectorsUpdateComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
