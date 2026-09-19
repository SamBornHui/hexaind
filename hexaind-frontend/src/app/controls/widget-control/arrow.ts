import { ConnectorPoint } from './connector-point';

export enum ArrowType {
  OnCompleted,
  OnFailed,
  OnSucceeded,
  OnLoop,
  OnTermianteLoop,
}

export class Arrow {
  startPoint: ConnectorPoint;
  endPoint: ConnectorPoint;
  selected: boolean;
  hovered: boolean;
  arrowType: ArrowType;
  uniqueId: string;

  constructor(
    startPoint: ConnectorPoint,
    endPoint: ConnectorPoint,
    connectorType: ArrowType,
    uniqueId: string,
  ) {
    this.startPoint = startPoint;
    this.endPoint = endPoint;
    this.selected = false;
    this.hovered = false;
    this.arrowType = connectorType;
    this.uniqueId = uniqueId;
  }
}
