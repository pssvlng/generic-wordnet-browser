import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { ImageViewerComponent } from './image-viewer/image-viewer.component';
import { SearchWrapperComponent } from './search-wrapper/search-wrapper.component';

const routes: Routes = [
  { path: '', redirectTo: '/search-wrapper', pathMatch: 'full' },
  { path: 'image', component: ImageViewerComponent },
  { path: 'search-wrapper', component: SearchWrapperComponent },
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
