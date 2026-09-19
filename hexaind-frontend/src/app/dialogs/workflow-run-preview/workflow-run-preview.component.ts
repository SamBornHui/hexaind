import { Component, ElementRef, EventEmitter, Inject, Input, Output, ViewChild } from '@angular/core';
import { Workflow } from 'src/app/models/workflow-models';
import { WorkflowCanvasService } from 'src/app/pages/workflow-designer/workflow-canvas.service';
import { ApiService } from 'src/app/services/api.service';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
@Component({
  selector: 'app-workflow-run-preview',
  templateUrl: './workflow-run-preview.component.html',
  styleUrls: ['./workflow-run-preview.component.less'],
})
export class WorkflowRunPreviewComponent {
  @Input() workflowId!: string;
  @Output() closeDialogClicked = new EventEmitter<any>();
  @ViewChild('myCanvas', { static: true })
  canvas: ElementRef<HTMLCanvasElement> | null = null;

  private editingWorkflow: Workflow | undefined;
  private animationFrameId: number | null = null;
  constructor(
    private dialogRef: MatDialogRef<WorkflowRunPreviewComponent>,
    private apiService: ApiService,
    private workflowCanvasService: WorkflowCanvasService,
    @Inject(MAT_DIALOG_DATA) public dialogData: any
  ) {
    console.log(this.dialogData,"get data from mongo");
  }

  ngAfterViewInit() {
    this.loadWorkflow();
  }

  async loadWorkflow() {
    this.editingWorkflow = await this.apiService.GetWorkflowById(
      '1',
      '2',
      this.workflowId,
    );
  }

  startCanvasDrawing() {
    this.animationFrameId = window.requestAnimationFrame(() => this.draw());
  }

  stopCanvasDrawing() {
    if (this.animationFrameId !== null) {
      window.cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }
  }

  draw() {}

  onClosePanel() {
    this.dialogRef.close();
  }
}
