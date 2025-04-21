import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SearchComponentDlgWrapperComponent } from './search-component-dlg-wrapper.component';

describe('SearchComponentDlgWrapperComponent', () => {
  let component: SearchComponentDlgWrapperComponent;
  let fixture: ComponentFixture<SearchComponentDlgWrapperComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [SearchComponentDlgWrapperComponent]
    });
    fixture = TestBed.createComponent(SearchComponentDlgWrapperComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
