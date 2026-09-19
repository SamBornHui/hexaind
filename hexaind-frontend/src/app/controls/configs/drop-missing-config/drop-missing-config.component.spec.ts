import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DropMissingConfigComponent } from './drop-missing-config.component';

describe('DropMissingConfigComponent', () => {
  let component: DropMissingConfigComponent;
  let fixture: ComponentFixture<DropMissingConfigComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [DropMissingConfigComponent]
    });
    fixture = TestBed.createComponent(DropMissingConfigComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
