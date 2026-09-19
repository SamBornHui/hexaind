import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ConfigActionBarComponent } from './config-action-bar.component';

describe('ConfigActionBarComponent', () => {
  let component: ConfigActionBarComponent;
  let fixture: ComponentFixture<ConfigActionBarComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [ConfigActionBarComponent]
    });
    fixture = TestBed.createComponent(ConfigActionBarComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
