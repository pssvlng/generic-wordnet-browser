import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { ImageViewerComponent } from './image-viewer/image-viewer.component';
import { SearchWrapperComponent } from './search-wrapper/search-wrapper.component';

const routes: Routes = [
  { path: '', component: SearchWrapperComponent, pathMatch: 'full' },
  { path: 'image', component: ImageViewerComponent },
  { path: 'search-wrapper', redirectTo: '', pathMatch: 'full' },
  ...['lemma', 'synset', 'ili'].flatMap(kind => [
    { path: `view/${kind}/:value`, component: SearchWrapperComponent, data: { kind } },
    { path: `view/:lang/${kind}/:value`, component: SearchWrapperComponent, data: { kind } },
    { path: `${kind}/:value`, redirectTo: `view/${kind}/:value`, pathMatch: 'full' as const },
    { path: `:lang/${kind}/:value`, redirectTo: `view/:lang/${kind}/:value`, pathMatch: 'full' as const },
  ]),
  { path: 'id/:value', redirectTo: 'view/synset/:value', pathMatch: 'full' },
  { path: ':lang/id/:value', redirectTo: 'view/:lang/synset/:value', pathMatch: 'full' },
  { path: 'view/id/:value', redirectTo: 'view/synset/:value', pathMatch: 'full' },
  { path: 'view/:lang/id/:value', redirectTo: 'view/:lang/synset/:value', pathMatch: 'full' },
  { path: '**', component: SearchWrapperComponent, data: { invalid: true } },
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
