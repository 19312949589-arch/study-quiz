# -*- coding: utf-8 -*-
"""创建自动跳转到单选题并答题的测试版本。"""
import shutil

SRC = r'D:\study-quiz\index.html'
DST = r'D:\study-quiz\source-locate\test_single.html'

shutil.copy2(SRC, DST)

with open(DST, encoding='utf-8') as f:
    html = f.read()

auto_script = """<script>
window.addEventListener('load', function() {
  setTimeout(function() {
    try {
      App.startSeq();
      // 跳到第2题（单选题 mgmt-0002）
      setTimeout(function() {
        try {
          state.idx = 1;
          render();
          // 自动选择正确答案
          setTimeout(function() {
            try {
              var q = curQ();
              if (q && q.t === 'single') {
                App.choose(q.a);
              }
            } catch(e) {}
          }, 400);
        } catch(e) {}
      }, 500);
    } catch(e) { console.error(e); }
  }, 800);
});
</script>
</body>"""

html = html.replace('</body>', auto_script, 1)

with open(DST, 'w', encoding='utf-8', newline='\n') as f:
    f.write(html)
print('Test page created:', DST)
