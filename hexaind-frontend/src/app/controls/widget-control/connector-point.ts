import { WidgetControl } from './widget-control';

export enum ConnectorPointType {
  top,
  left,
  right,
  bottom,
}

export class ConnectorPoint {
  widgetControl: WidgetControl;
  connectorPointType: ConnectorPointType;

  constructor(widgetControl: WidgetControl, type: ConnectorPointType) {
    this.widgetControl = widgetControl;
    this.connectorPointType = type;
  }

  get x(): number {
    switch (this.connectorPointType) {
      case ConnectorPointType.top:
      case ConnectorPointType.bottom:
        return (
          this.widgetControl.GetPositionX() + this.widgetControl.GetWidth() / 2
        );
      case ConnectorPointType.left:
        return this.widgetControl.GetPositionX();
      case ConnectorPointType.right:
        return (
          this.widgetControl.GetPositionX() + this.widgetControl.GetWidth()
        );
    }
  }

  get y(): number {
    switch (this.connectorPointType) {
      case ConnectorPointType.top:
        return this.widgetControl.GetPositionY();
      case ConnectorPointType.bottom:
        return (
          this.widgetControl.GetPositionY() + this.widgetControl.GetHeight()
        );
      case ConnectorPointType.left:
      case ConnectorPointType.right:
        return (
          this.widgetControl.GetPositionY() + this.widgetControl.GetHeight() / 2
        );
    }
  }
}
