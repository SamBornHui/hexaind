import { ArrowType } from './arrow';
import { ConnectorPointType } from './connector-point';

export interface ArrowObject {
  start_urn: string;
  end_urn: string;
  start_connector_point_type: ConnectorPointType;
  end_connector_point_type: ConnectorPointType;
  arrow_type: ArrowType;
}
