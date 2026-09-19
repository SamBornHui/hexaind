import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ConfigsInformationComponent } from './configs-information.component';

describe('ConfigsInformationComponent', () => {
  let component: ConfigsInformationComponent;
  let fixture: ComponentFixture<ConfigsInformationComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [ConfigsInformationComponent]
    });
    fixture = TestBed.createComponent(ConfigsInformationComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
