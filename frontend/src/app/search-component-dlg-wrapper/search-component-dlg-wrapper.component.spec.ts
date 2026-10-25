import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { By } from '@angular/platform-browser';
import { SearchStubComponent } from '../testing/search-stub.component';

import { SearchComponentDlgWrapperComponent } from './search-component-dlg-wrapper.component';

describe('SearchComponentDlgWrapperComponent', () => {
  let component: SearchComponentDlgWrapperComponent;
  let fixture: ComponentFixture<SearchComponentDlgWrapperComponent>;
  let dialog: jasmine.SpyObj<MatDialogRef<SearchComponentDlgWrapperComponent>>;

  beforeEach(() => {
    dialog = jasmine.createSpyObj<MatDialogRef<SearchComponentDlgWrapperComponent>>('MatDialogRef', ['close']);
    TestBed.configureTestingModule({
      imports: [MatDialogModule],
      declarations: [SearchComponentDlgWrapperComponent, SearchStubComponent],
      providers: [{ provide: MatDialogRef, useValue: dialog }],
    });
    fixture = TestBed.createComponent(SearchComponentDlgWrapperComponent);
    component = fixture.componentInstance;
    component.inputParams = {
      lookup: { kind: 'ili', value: 'i46360' }, availableLangs: ['en'],
      woi: undefined, pos: undefined, lemma: undefined, lang: undefined,
      category: undefined, wordkey: undefined, ili: undefined,
    };
    component.fromText = 'dog';
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('passes lookup inputs to the search and closes the dialog from its button', () => {
    const child = fixture.debugElement.query(By.directive(SearchStubComponent)).componentInstance as SearchStubComponent;
    expect(child.inputParams).toBe(component.inputParams);
    expect(child.fromText).toBe('dog');
    fixture.nativeElement.querySelector('button').click();
    expect(dialog.close).toHaveBeenCalledTimes(1);
  });
});
