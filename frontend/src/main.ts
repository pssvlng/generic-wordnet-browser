import { platformBrowserDynamic } from '@angular/platform-browser-dynamic';

import { AppModule } from './app/app.module';


// Keep bookmarks from the former hash router usable after adopting path URLs.
if (window.location.hash.startsWith('#/')) {
  const base = document.querySelector('base')?.getAttribute('href') || '/';
  window.history.replaceState(null, '', base + window.location.hash.slice(2));
}

platformBrowserDynamic().bootstrapModule(AppModule)
  .catch(err => console.error(err));
