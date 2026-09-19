import { ComponentFixture, TestBed } from '@angular/core/testing';
import { CustomTooltipComponent } from './custom-tooltip.component'; // Adjust path as necessary

describe('CustomTooltipComponent', () => {
  let component: CustomTooltipComponent;
  let fixture: ComponentFixture<CustomTooltipComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [CustomTooltipComponent],
    });
    fixture = TestBed.createComponent(CustomTooltipComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create the component', () => {
    expect(component).toBeTruthy();
  });

  it('should display "N/A" when tooltipContent is undefined', () => {
    expect(component.purpose).toBe('N/A');
    expect(component.input).toBe('N/A');
    expect(component.output).toBe('N/A');
  });

  it('should display provided tooltip content', () => {
    const tooltipContent = {
      purpose: 'Test Purpose',
      input: 'Test Input',
      output: 'Test Output',
    };
    component.tooltipContent = tooltipContent;
    fixture.detectChanges();

    expect(component.purpose).toBe(tooltipContent.purpose);
    expect(component.input).toBe(tooltipContent.input);
    expect(component.output).toBe(tooltipContent.output);
  });
});
