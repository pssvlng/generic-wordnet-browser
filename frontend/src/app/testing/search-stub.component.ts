import { Component, forwardRef, Input } from '@angular/core';
import { InputParams } from '../models/input-params';
import { SearchComponent } from '../search/search.component';

// Parent tests exercise their real templates without starting child lookups.
// Preserve the class token used by SearchWrapperComponent's ViewChild query.
@Component({
  selector: 'app-search',
  template: '',
  providers: [{ provide: SearchComponent, useExisting: forwardRef(() => SearchStubComponent) }],
})
export class SearchStubComponent {
  @Input() inputParams!: InputParams;
  @Input() fromText = '';
  setAvailableLangs = jasmine.createSpy('setAvailableLangs');
}
