import { ComponentFixture, TestBed } from '@angular/core/testing';

import { RenameColumnsConfigComponent } from './rename-columns-config.component';

describe('RenameColumnsConfigComponent', () => {
  let component: RenameColumnsConfigComponent;
  let fixture: ComponentFixture<RenameColumnsConfigComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [RenameColumnsConfigComponent]
    });
    fixture = TestBed.createComponent(RenameColumnsConfigComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
