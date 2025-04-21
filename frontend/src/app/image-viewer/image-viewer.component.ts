import { ChangeDetectorRef, Component, OnDestroy, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { Subject, takeUntil } from 'rxjs';
import { ImageInputParams } from '../models/image-input-params';
import { WordnetService } from '../services/wordnet.service';

@Component({
  selector: 'app-image-viewer',
  templateUrl: './image-viewer.component.html',
  styleUrls: ['./image-viewer.component.css']
})
export class ImageViewerComponent implements OnInit, OnDestroy {

  imageParams!: ImageInputParams;
  imageSrc!: string;
  imageMaximized: boolean = false;
  loading: boolean = false;

  private onDestroy$: Subject<void> = new Subject<void>();

  constructor(
    private route: ActivatedRoute,
    private wordnetService: WordnetService,
    private cd: ChangeDetectorRef,
  ) {


  }

  addSynonyms(count: number): void {

    if (this.imageParams?.synonymCount) {
      this.imageParams.synonymCount += count;
      if (this.imageParams.synonymCount < 1) {
        this.imageParams.synonymCount = 1
      }
      this.loadImage();
    }

  }

  addMaxLeafNodes(count: number): void {
    if (this.imageParams?.maxLeafNodes) {
      this.imageParams.maxLeafNodes += count;
      if (this.imageParams.maxLeafNodes < 1) {
        this.imageParams.maxLeafNodes = 1
      }
      this.loadImage();
    }

  }

  addLevel(count: number): void {
    if (this.imageParams?.level) {
      this.imageParams.level += count;
      if (this.imageParams.level < 1) {
        this.imageParams.level = 1
      }
      this.loadImage();
    }

  }

  private loadImage(): void {
    if (this.imageParams && this.imageParams.synsetId) {
      this.imageParams.fileName = `hierarchy_partwhole${Date.now()}${['de'].join('_')}_${this.imageParams.level}_${this.imageParams.maxLeafNodes}${this.imageParams.synonymCount}`;      
      this.loading = true;
      this.wordnetService.getImage(this.imageParams)        
        .pipe(takeUntil(this.onDestroy$))
        .subscribe({
          next: (imageStr: string) => {
            this.imageSrc = imageStr;
            this.cd.detectChanges();
          },          
          complete: () => this.loading = false
        });                
    }

  }

  ngOnInit(): void {

    this.route.queryParams.subscribe(params => {

      this.imageParams = {
        fileName: params["fileName"] as string,
        synsetId: params["synsetId"] as string,
        level: params["level"] ? parseInt(params["level"]) : 2,
        maxLeafNodes: params["maxLeafNodes"] ? parseInt(params["maxLeafNodes"]) : 5,
        synonymCount: params["synonymCount"] ? parseInt(params["synonymCount"]) : 1,
        availableLangs: params["filterLangs"] ? params["filterLangs"] as string []: ['de'],
        filterLangs: params["filterLangs"] ? params["filterLangs"] as string []: ['de'],
        partWhole: params["partWhole"] ? params["partWhole"] as string : "True",
        hierarchy: params["hierarchy"] ? params["hierarchy"] as string : "True",
        woi: params["woi"] ? params["woi"] as string : undefined,
      };
      this.loadImage();

    });

  }

  ngOnDestroy(): void {
    this.onDestroy$.next();
    this.onDestroy$.complete();
  }

}
