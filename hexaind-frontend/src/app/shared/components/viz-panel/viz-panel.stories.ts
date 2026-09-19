import type { Meta, StoryObj } from '@storybook/angular';
import { getCitiesByState } from 'src/tests/mocks/cities';
import { getDashboardList } from 'src/tests/mocks/dashboards';
import { convertVizData } from '../charts/chart-utils';
import { DashboardRow, DatasetData } from '../models';
import { VizPanelComponent } from './viz-panel.component';

const rowInfo = getDashboardList()[0].config?.rows[0] as DashboardRow;
const cellInfo = rowInfo.cells[0];

// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
const meta: Meta<VizPanelComponent> = {
  title: 'Components/Visualization',
  component: VizPanelComponent,
  args: {
    config: cellInfo.viz,
    data: convertVizData(getCitiesByState('US', 'Alabama') as DatasetData),
  },
};

export default meta;
type Story = StoryObj<VizPanelComponent>;

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const Primary: Story = {};
