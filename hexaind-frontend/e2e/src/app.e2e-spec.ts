// npm install protractor -g
// https://googlechromelabs.github.io/chrome-for-testing/#stable

describe('A suite is just a function', function () {
  var a;
  it('and so is a spec', function () {
    a = true;
    expect(a).toBe(true);
  });
});
