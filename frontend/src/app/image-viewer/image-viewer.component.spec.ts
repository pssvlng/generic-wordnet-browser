import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MatIconModule } from '@angular/material/icon';
import { ActivatedRoute } from '@angular/router';
import { of, Subject } from 'rxjs';
import { LoadingSpinnerComponent } from '../loading-spinner/loading-spinner.component';
import { WordnetService } from '../services/wordnet.service';

import { ImageViewerComponent } from './image-viewer.component';

describe('ImageViewerComponent', () => {
  let component: ImageViewerComponent;
  let fixture: ComponentFixture<ImageViewerComponent>;
  let images: Subject<string>;
  let wordnet: jasmine.SpyObj<WordnetService>;

  beforeEach(() => {
    images = new Subject<string>();
    wordnet = jasmine.createSpyObj<WordnetService>('WordnetService', ['getImage']);
    wordnet.getImage.and.returnValue(images.asObservable());
    TestBed.configureTestingModule({
      imports: [MatIconModule],
      declarations: [ImageViewerComponent, LoadingSpinnerComponent],
      providers: [
        { provide: WordnetService, useValue: wordnet },
        { provide: ActivatedRoute, useValue: { queryParams: of({
          synsetId: 'ewn-02086723-n', filterLangs: ['en'], level: '3',
        }) } },
      ],
    });
    fixture = TestBed.createComponent(ImageViewerComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('loads an image from the route parameters and renders it when ready', () => {
    expect(wordnet.getImage).toHaveBeenCalledOnceWith(jasmine.objectContaining({
      synsetId: 'ewn-02086723-n', filterLangs: ['en'], level: 3,
    }));
    expect(fixture.nativeElement.querySelector('app-loading-spinner')).not.toBeNull();
    const image = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a6XcAAAAASUVORK5CYII=';
    images.next(image);
    images.complete();
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('img').getAttribute('src')).toBe(image);
    expect(fixture.nativeElement.querySelector('app-loading-spinner')).toBeNull();
  });
});
