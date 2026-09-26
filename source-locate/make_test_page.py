# -*- coding: utf-8 -*-
"""创建自动跳转到题目页的测试版本，用于Edge无头验证。"""
import shutil

SRC = r'D:\study-quiz\index.html'
DST = r'D:\study-quiz\source-locate\test_question.html'

shutil.copy2(SRC, DST)

with open(DST, encoding='utf-8') as f:
    html = f.read()

# 在 </body> 前添加自动跳转脚本
auto_script = """<script>
window.addEventListener('load', function() {
  setTimeout(function() {
    try {
      // 进入顺序练习，显示第一题
      if (typeof App !== 'undefined' && App.startSeq) {
        App.startSeq();
      }
    } catch(e) { console.error('auto-nav error:', e); }
  }, 800);
  // 再等一会自动答题以显示解析
  setTimeout(function() {
    try {
      var q = curQ();
      if (q && q.t === 'single' && typeof q.a === 'number') {
        App.choose(q.a);
      }
    } catch(e) {}
  }, 1600);
});
</script>
</body>"""

html = html.replace('</body>', auto_script, 1)

with open(DST, 'w', encoding='utf-8', newline='\n') as f:
    f.write(html)

print('Test page created:', DST)
