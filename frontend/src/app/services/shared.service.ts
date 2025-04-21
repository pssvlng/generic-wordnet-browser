import { Injectable, OnDestroy } from '@angular/core';
import { BehaviorSubject } from 'rxjs';
import { AppConfig } from '../config/app-config';

@Injectable({
  providedIn: 'root'
})
export class SharedService implements OnDestroy {

  private messageSource = new BehaviorSubject<string[]>(AppConfig.availableLangs);
  currentMessage = this.messageSource.asObservable();

  changeAvailableLangs(message: string[]) {
    this.messageSource.next(message);
  }

  ngOnDestroy() {
    this.messageSource.complete();
  }

}
