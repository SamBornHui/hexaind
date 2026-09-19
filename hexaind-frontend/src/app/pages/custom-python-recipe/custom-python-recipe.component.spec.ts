import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CustomPythonRecipeComponent } from './custom-python-recipe.component';

describe('CustomCodeWidgetBuilderComponent', () => {
  let component: CustomPythonRecipeComponent;
  let fixture: ComponentFixture<CustomPythonRecipeComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [CustomPythonRecipeComponent]
    });
    fixture = TestBed.createComponent(CustomPythonRecipeComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
