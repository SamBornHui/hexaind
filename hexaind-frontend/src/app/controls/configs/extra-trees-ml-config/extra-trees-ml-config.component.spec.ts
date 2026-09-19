import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ExtraTreesMlConfigComponent } from './extra-trees-ml-config.component';

describe('ExtraTreesMlConfigComponent', () => {
  let component: ExtraTreesMlConfigComponent;
  let fixture: ComponentFixture<ExtraTreesMlConfigComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [ExtraTreesMlConfigComponent]
    });
    fixture = TestBed.createComponent(ExtraTreesMlConfigComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
