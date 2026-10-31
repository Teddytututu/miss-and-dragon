const {test}=require('node:test');
const assert=require('node:assert/strict');
const {translate}=require('../board/i18n.js');
test('English labels and dynamic member counts',()=>{
  assert.equal(translate('需要你做的','en'),'Your actions');
  assert.equal(translate('3 位成员','en'),'3 members');
  assert.equal(translate('今天 · 10-31','en'),'Today · 10-31');
  assert.equal(translate('研究，下午好呀','en'),'研究, Good afternoon');
});
test('Chinese and unknown project content retain their text',()=>{
  assert.equal(translate('需要你做的','zh-CN'),'需要你做的');
  assert.equal(translate('Example study 42','en'),'Example study 42');
  assert.equal(translate('我的研究笔记','en'),'我的研究笔记');
});
