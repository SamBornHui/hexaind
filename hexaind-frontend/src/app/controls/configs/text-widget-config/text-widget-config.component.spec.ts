import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TextWidgetConfigComponent } from './text-widget-config.component';

describe('TextWidgetConfigComponent', () => {
  let component: TextWidgetConfigComponent;
  let fixture: ComponentFixture<TextWidgetConfigComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [TextWidgetConfigComponent]
    });
    fixture = TestBed.createComponent(TextWidgetConfigComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
