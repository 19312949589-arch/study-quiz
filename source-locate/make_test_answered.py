# -*- coding: utf-8 -*-
"""创建更稳健的测试页：直接设置已答题状态。"""
import shutil

SRC = r'D:\study-quiz\index.html'
DST = r'D:\study-quiz\source-locate\test_answered.html'

shutil.copy2(SRC, DST)

with open(DST, encoding='utf-8') as f:
    html = f.read()

auto_script = """<script>
window.addEventListener('load', function() {
  function go() {
    try {
      // 直接构造一个已答题的练习状态
      state.mode = 'practice';
      state.view = 'question';
      state.title = '顺序练习';
      state.queue = [];
      for (var i = 0; i < BANK.length; i++) state.queue.push(BANK[i].id);
      state.idx = 1; // mgmt-0002 单选题
      var q = curQ();
      state.answers[q.id] = q.a;
      state.answered[q.id] = true;
      render();
    } catch(e) { console.error('go error:', e); }
  }
  setTimeout(go, 1000);
  setTimeout(go, 2000);
});
</script>
</body>"""

html = html.replace('</body>', auto_script, 1)

with open(DST, 'w', encoding='utf-8', newline='\n') as f:
    f.write(html)
print('Test page created:', DST)
