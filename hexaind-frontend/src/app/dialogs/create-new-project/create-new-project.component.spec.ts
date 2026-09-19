import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CreateNewProjectComponent } from './create-new-project.component';

describe('CreateNewProjectComponent', () => {
  let component: CreateNewProjectComponent;
  let fixture: ComponentFixture<CreateNewProjectComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [CreateNewProjectComponent]
    });
    fixture = TestBed.createComponent(CreateNewProjectComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
