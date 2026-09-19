import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SaveConfigComponent } from './save-config.component';

describe('SaveConfigComponent', () => {
  let component: SaveConfigComponent;
  let fixture: ComponentFixture<SaveConfigComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [SaveConfigComponent]
    });
    fixture = TestBed.createComponent(SaveConfigComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
