import { ScientificNumberPipe } from './scientific-number.pipe';

describe('ScientificNumberPipe', () => {
  it('create an instance', () => {
    const pipe = new ScientificNumberPipe();
    expect(pipe).toBeTruthy();
  });
});
