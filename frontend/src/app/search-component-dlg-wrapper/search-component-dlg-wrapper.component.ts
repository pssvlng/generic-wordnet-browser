import { Component, Input } from '@angular/core';
import { MatDialogRef } from '@angular/material/dialog';
import { InputParams } from '../models/input-params';
import { SearchComponent } from '../search/search.component';

@Component({
  selector: 'app-search-component-dlg-wrapper',
  templateUrl: './search-component-dlg-wrapper.component.html',
  styleUrls: ['./search-component-dlg-wrapper.component.css']
})
export class SearchComponentDlgWrapperComponent {

  @Input() inputParams!: InputParams;
  @Input() fromText!: string;

  constructor(private dialogRef: MatDialogRef<SearchComponent>) {

  }

  onCloseClick(): void {
    this.dialogRef.close();
  }

}
