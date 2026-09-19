import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CustomCodeWidgetBuilderComponent } from './custom-code-widget-builder.component';

describe('CustomCodeWidgetBuilderComponent', () => {
  let component: CustomCodeWidgetBuilderComponent;
  let fixture: ComponentFixture<CustomCodeWidgetBuilderComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [CustomCodeWidgetBuilderComponent]
    });
    fixture = TestBed.createComponent(CustomCodeWidgetBuilderComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
