import { APP_INITIALIZER, NgModule, importProvidersFrom } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';

import { HttpClient, HttpClientModule } from '@angular/common/http';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';

import { MatCardModule } from '@angular/material/card';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatDialogModule } from '@angular/material/dialog';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatIconModule } from '@angular/material/icon';
import { SearchComponentDlgWrapperComponent } from './search-component-dlg-wrapper/search-component-dlg-wrapper.component';
import { SearchComponent } from './search/search.component';

import { HashLocationStrategy, LocationStrategy } from '@angular/common';
import { ImagePopupComponent } from './image-popup/image-popup.component';
import { ImageViewerComponent } from './image-viewer/image-viewer.component';
import { LoadingSpinnerComponent } from './loading-spinner/loading-spinner.component';
import { SearchWrapperComponent } from './search-wrapper/search-wrapper.component';

import { TranslateLoader, TranslateModule } from '@ngx-translate/core';
import { TranslateHttpLoader } from '@ngx-translate/http-loader';
import { ToastrModule } from 'ngx-toastr';
import { firstValueFrom } from 'rxjs';
import { TranslationService } from './services/translation.service';

import { APP_BASE_HREF, DOCUMENT } from '@angular/common';


export function HttpLoaderFactory(http: HttpClient) {
  return new TranslateHttpLoader(http, './assets/i18n/', '.json');
}

export function preloadTranslationsFactory(translationService: TranslationService) {
  return () => firstValueFrom(translationService.preloadTranslations());
}

@NgModule({
  declarations: [
    AppComponent,    
    SearchComponent,
    SearchComponentDlgWrapperComponent,
    ImageViewerComponent,    
    SearchWrapperComponent,    
    LoadingSpinnerComponent, ImagePopupComponent,        
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    FormsModule,
    ReactiveFormsModule,
    MatFormFieldModule,
    MatInputModule,
    HttpClientModule,
    MatExpansionModule,
    MatCardModule,
    MatDialogModule,
    MatIconModule,  
    MatCheckboxModule,
    BrowserAnimationsModule, // Required for ToastrModule
    ToastrModule.forRoot({
      timeOut: 3000,
      positionClass: 'toast-top-right',
      preventDuplicates: true,
    }),
    TranslateModule.forRoot({
      loader: {
        provide: TranslateLoader,
        useFactory: HttpLoaderFactory,
        deps: [HttpClient]
      }
    })
  ],
  
  bootstrap: [AppComponent],
  providers: [
    { 
      provide: LocationStrategy, useClass: HashLocationStrategy,
    },
    {
      provide: APP_BASE_HREF,
      useFactory: (document: Document) => {     
        const baseHref = document.location.pathname; 
        return baseHref.endsWith('/') ? baseHref : `${baseHref}/`;
      },
      deps: [DOCUMENT]
    },
    {
      provide: APP_INITIALIZER,
      useFactory: preloadTranslationsFactory,
      deps: [TranslationService],
      multi: true
    },
    importProvidersFrom([BrowserAnimationsModule])]
})
export class AppModule { }
