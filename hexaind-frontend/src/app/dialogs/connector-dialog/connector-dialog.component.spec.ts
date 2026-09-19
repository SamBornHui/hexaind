import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ConnectorDialogComponent } from './connector-dialog.component';

describe('ConnectorDialogComponent', () => {
  let component: ConnectorDialogComponent;
  let fixture: ComponentFixture<ConnectorDialogComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [ConnectorDialogComponent]
    });
    fixture = TestBed.createComponent(ConnectorDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
