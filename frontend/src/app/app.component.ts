import { Component, HostListener } from '@angular/core';
import { AppConfig } from './config/app-config';
import { LANG_ICON_CLASS_LOOKUP, LANGUAGEMAPDESCRIPTIONS } from './constants/lang-icon-lookup';
import { SharedService } from './services/shared.service';

interface CheckboxItem {
  id: string;
  label: string;
}

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {
  title = AppConfig.title;
  flagList = AppConfig.flagList;
  availableLangs = AppConfig.availableLangs;
  langIconClassLookup = LANG_ICON_CLASS_LOOKUP;
  
  items: CheckboxItem[] = AppConfig.availableLangs.map((lang) => {
    return {
      id: lang,
      label: LANGUAGEMAPDESCRIPTIONS[lang]
    }
  });
  
  menuOpen = false;
  allSelected: boolean = true;

  constructor(
    private sharedService: SharedService
  ) {}

  toggleMenu(): void {
    this.menuOpen = !this.menuOpen;
  }

  @HostListener('document:click', ['$event'])
  onOutsideClick(event: Event): void {
    const target = event.target as HTMLElement;
    if (!target.closest('.hamburger-menu')) {
      this.menuOpen = false;
    }
  }

  trackById(index: number, item: CheckboxItem): string {
    return item.id;
  }

  toggleSelectAll(event: any): void {
    this.allSelected = event.checked;
    this.availableLangs = this.allSelected
      ? this.items.map(item => item.id)
      : ['en'];
    this.sharedService.changeAvailableLangs(this.availableLangs);
  }

  toggleSelection(itemId: string, event: any): void {
    if (event.checked) {
      this.availableLangs.push(itemId);
    } else {
      if (this.availableLangs.length === 1) {
        event.source.checked = true;
        return;
      }
      this.availableLangs = this.availableLangs.filter(id => id !== itemId);
    }
    this.allSelected = this.availableLangs.length === this.items.length;
    this.sharedService.changeAvailableLangs(this.availableLangs);
  }

}
