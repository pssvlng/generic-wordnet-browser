import { ChangeDetectorRef, Component, OnDestroy, OnInit } from '@angular/core';
import { MatCheckboxChange } from '@angular/material/checkbox';
import { Subject, takeUntil } from 'rxjs';
import { LANG_ICON_CLASS_LOOKUP, LANGUAGEMAPDESCRIPTIONS } from '../constants/lang-icon-lookup';
import { ImageInputParams } from '../models/image-input-params';
import { WordnetService } from '../services/wordnet.service';

interface StringDictionary {
  [key: string]: string;
}

interface CheckboxItem {
  id: string;
  label: string;
}

@Component({
  selector: 'app-image-popup',
  templateUrl: './image-popup.component.html',
  styleUrls: ['./image-popup.component.css']
})
export class ImagePopupComponent implements OnDestroy, OnInit {
  imageUrl: string = '';
  isVisible: boolean = false;
  imageParams!: ImageInputParams;
  loading: boolean = false;

  langIconClassLookup = LANG_ICON_CLASS_LOOKUP;
  langMapDescriptions: StringDictionary = LANGUAGEMAPDESCRIPTIONS;
  private onDestroy$: Subject<void> = new Subject<void>();

  items: CheckboxItem[] = [];

  constructor(
    private wordnetService: WordnetService,
    private cd: ChangeDetectorRef
  ) {

  }

  ngOnInit(): void {

  }

  ngOnDestroy(): void {
    this.onDestroy$.next();
    this.onDestroy$.complete();
  }

  addSynonyms(count: number): void {
    const result = { ...this.imageParams };
    if (result?.synonymCount) {
      result.synonymCount += count;
      if (result.synonymCount < 1) {
        result.synonymCount = 1
      }

      result.fileName = `hierarchy_partwhole${Date.now()}${result.filterLangs.join('_')}_${result.level}_${result.maxLeafNodes}${result.synonymCount}`;
    }
    this.open(result)
  }

  addMaxLeafNodes(count: number): void {
    const result = { ...this.imageParams };
    if (result?.maxLeafNodes) {
      result.maxLeafNodes += count;
      if (result.maxLeafNodes < 1) {
        result.maxLeafNodes = 1
      }
      result.fileName = `hierarchy_partwhole${Date.now()}${result.filterLangs.join('_')}_${result.level}_${result.maxLeafNodes}${result.synonymCount}`;
    }
    this.open(result)
  }

  addLevel(count: number): void {
    const result = { ...this.imageParams };
    if (result?.level) {
      result.level += count;
      if (result.level < 1) {
        result.level = 1
      }
      result.fileName = `hierarchy_partwhole${Date.now()}${result.filterLangs.join('_')}_${result.level}_${result.maxLeafNodes}${result.synonymCount}`;
    }
    this.open(result)
  }

  open(imageParams: ImageInputParams): void {
    this.items = [];
    this.imageParams = imageParams;
    this.loading = true;
    this.wordnetService.getImage(this.imageParams)
      .pipe(takeUntil(this.onDestroy$))
      .subscribe({
        next: (imageStr: string) => {
          this.imageUrl = imageStr;
          this.cd.detectChanges();
        },
        complete: () => {
          this.loading = false
          for (const lang of this.imageParams.availableLangs) {
            const langDesc = this.langMapDescriptions[lang];
            if (langDesc) {
              this.items.push({ id: lang, label: langDesc });
            }
          }          
        }
      });
    this.isVisible = true;
  }

  toggleSelection(itemId: string, change: MatCheckboxChange): void {
    const isChecked = change.checked;
    if (isChecked) {
        this.imageParams.filterLangs.push(itemId);
    } else {        
        if (this.imageParams.filterLangs.length === 1) {
            change.source.checked = true; 
        } else {
            this.imageParams.filterLangs = this.imageParams.filterLangs.filter(id => id !== itemId);
        }
    }
    this.open(this.imageParams)
  }

  trackById(index: number, item: CheckboxItem): string {
    return item.id;
  }

  close() {
    this.isVisible = false;
  }

}
