import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatIconModule } from '@angular/material/icon';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { Subject } from 'rxjs';
import { LoadingSpinnerComponent } from '../loading-spinner/loading-spinner.component';
import { WordnetService } from '../services/wordnet.service';

import { ImagePopupComponent } from './image-popup.component';

describe('ImagePopupComponent', () => {
  let component: ImagePopupComponent;
  let fixture: ComponentFixture<ImagePopupComponent>;
  let images: Subject<string>;
  let wordnet: jasmine.SpyObj<WordnetService>;

  beforeEach(() => {
    images = new Subject<string>();
    wordnet = jasmine.createSpyObj<WordnetService>('WordnetService', ['getImage']);
    wordnet.getImage.and.returnValue(images.asObservable());
    TestBed.configureTestingModule({
      imports: [FormsModule, MatCheckboxModule, MatIconModule, NoopAnimationsModule],
      declarations: [ImagePopupComponent, LoadingSpinnerComponent],
      providers: [{ provide: WordnetService, useValue: wordnet }],
    });
    fixture = TestBed.createComponent(ImagePopupComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('shows the requested image and closes from the close button', async () => {
    const params = {
      synsetId: 'ewn-02086723-n', fileName: 'dog', level: 2, maxLeafNodes: 5,
      synonymCount: 1, availableLangs: ['en', 'de'], filterLangs: ['en'],
      hierarchy: 'True', partWhole: 'True', woi: 'dog',
    };
    component.open(params);
    fixture.detectChanges();
    expect(wordnet.getImage).toHaveBeenCalledOnceWith(params);
    expect(fixture.nativeElement.querySelector('app-loading-spinner')).not.toBeNull();
    const image = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a6XcAAAAASUVORK5CYII=';
    images.next(image);
    images.complete();
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('img').getAttribute('src')).toBe(image);
    expect(fixture.nativeElement.querySelector('app-loading-spinner')).toBeNull();
    expect(fixture.nativeElement.querySelectorAll('mat-checkbox').length).toBe(2);
    fixture.nativeElement.querySelector('.close-button').click();
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('.overlay')).toBeNull();
  });
});
