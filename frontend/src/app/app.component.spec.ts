import { TestBed } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatIconModule } from '@angular/material/icon';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { RouterTestingModule } from '@angular/router/testing';
import { AppComponent } from './app.component';
import { AppConfig } from './config/app-config';
import { SharedService } from './services/shared.service';

describe('AppComponent', () => {
  beforeEach(() => TestBed.configureTestingModule({
    imports: [RouterTestingModule, FormsModule, MatButtonModule, MatCheckboxModule,
      MatIconModule, NoopAnimationsModule],
    declarations: [AppComponent]
  }));

  it('should create the app', () => {
    const fixture = TestBed.createComponent(AppComponent);
    const app = fixture.componentInstance;
    expect(app).toBeTruthy();
  });

  it('uses the configured application title', () => {
    const fixture = TestBed.createComponent(AppComponent);
    const app = fixture.componentInstance;
    expect(app.title).toEqual(AppConfig.title);
  });

  it('renders the configured title in the page heading', () => {
    const fixture = TestBed.createComponent(AppComponent);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('h1')?.textContent).toBe(AppConfig.title);
  });

  it('opens the language menu with the current selection', async () => {
    const fixture = TestBed.createComponent(AppComponent);
    const selected = [AppConfig.availableLangs[0]];
    TestBed.inject(SharedService).changeAvailableLangs(selected);
    fixture.detectChanges();
    fixture.nativeElement.querySelector('.menu-button').click();
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
    const checkboxes: NodeListOf<HTMLInputElement> = fixture.nativeElement.querySelectorAll('input[type="checkbox"]');
    expect(checkboxes.length).toBe(AppConfig.availableLangs.length + 1);
    expect(checkboxes[0].checked).toBe(AppConfig.availableLangs.length === 1);
    expect(Array.from(checkboxes).slice(1).map(checkbox => checkbox.checked))
      .toEqual(AppConfig.availableLangs.map(lang => selected.includes(lang)));
  });
});
