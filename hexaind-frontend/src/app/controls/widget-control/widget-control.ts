import { ConnectorPoint, ConnectorPointType } from './connector-point';
import { Widget } from '../../models/workflow-models';

export class WidgetControl {
  public Widget: Widget;
  public ConnectorPoints: ConnectorPoint[];
  public ZIndex = 0.0;
  public isSelected: boolean = false;
  public backgroundColor: string | null = null;

  GetPositionX(): number {
    return Widget.GetPositionX(this.Widget);
  }

  GetPositionY(): number {
    return Widget.GetPositionY(this.Widget);
  }

  GetWidth(): number {
    return Widget.GetWidth(this.Widget);
  }

  GetHeight(): number {
    return Widget.GetHeight(this.Widget);
  }

  GetColor(): string {
    return this.Widget.client_tags['Color'];
  }

  constructor(widget: Widget) {
    this.Widget = widget;

    this.ConnectorPoints = [];
    this.ConnectorPoints.push(new ConnectorPoint(this, ConnectorPointType.top));
    this.ConnectorPoints.push(
      new ConnectorPoint(this, ConnectorPointType.bottom),
    );
    this.ConnectorPoints.push(
      new ConnectorPoint(this, ConnectorPointType.left),
    );
    this.ConnectorPoints.push(
      new ConnectorPoint(this, ConnectorPointType.right),
    );
  }
}
