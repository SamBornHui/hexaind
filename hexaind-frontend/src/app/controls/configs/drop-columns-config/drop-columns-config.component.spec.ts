import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DropColumnsConfigComponent } from './drop-columns-config.component';

describe('DropColumnsConfigComponent', () => {
  let component: DropColumnsConfigComponent;
  let fixture: ComponentFixture<DropColumnsConfigComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [DropColumnsConfigComponent]
    });
    fixture = TestBed.createComponent(DropColumnsConfigComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
