# -*- coding: utf-8 -*-
"""为 index.html 添加教材出处 UI 显示。"""
import re

INDEX = r'D:\study-quiz\index.html'

with open(INDEX, encoding='utf-8') as f:
    html = f.read()

# ── 1. 添加 sourceHTML 和 toggleSrc 辅助函数 ──
esc_func = """function esc(s) {
  if (s === undefined || s === null) return '';
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}"""

src_funcs = """function esc(s) {
  if (s === undefined || s === null) return '';
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
function sourceHTML(q) {
  if (!q || !q.source) return '';
  var s = q.source;
  var pending = s.page && s.page.indexOf('待校验') >= 0;
  var h = '<div class="source-box">';
  h += '<div class="src-title">📖 教材出处</div>';
  h += '<div class="src-book">《管理学》（第二版）</div>';
  if (s.chapter) h += '<div class="src-ch">' + esc(s.chapter) + '</div>';
  if (s.section) h += '<div class="src-sec">' + esc(s.section) + '</div>';
  if (pending) h += '<div class="src-pending">教材 ' + esc(s.page) + '</div>';
  else if (s.page) h += '<div class="src-pg">教材 ' + esc(s.page) + '</div>';
  h += '</div>';
  return h;
}
function toggleSrc() {
  var el = document.getElementById('srcDetail');
  if (el) el.classList.toggle('open');
}"""

assert esc_func in html, 'esc function not found'
html = html.replace(esc_func, src_funcs, 1)
print('1. sourceHTML functions added')

# ── 2. 在题目头部添加"查看教材出处"按钮 ──
# 找到标记按钮那行
mark_btn = """html += '<button class="mark-btn ' + (marked ? 'active' : '') + '" onclick="App.toggleMark()">' + (marked ? '★ 已标记' : '☆ 标记') + '</button>';"""

mark_btn_with_src = """html += '<button class="mark-btn ' + (marked ? 'active' : '') + '" onclick="App.toggleMark()">' + (marked ? '★ 已标记' : '☆ 标记') + '</button>';
  html += '<button class="src-btn" onclick="toggleSrc()">📖 教材出处</button>';"""

assert mark_btn in html, 'mark button not found'
html = html.replace(mark_btn, mark_btn_with_src, 1)
print('2. source button added to header')

# ── 3. 在题目文本后添加可折叠的教材出处详情 ──
qtext_line = """html += '<div class="qtext">' + esc(q.q) + '</div>';"""

qtext_with_src = """html += '<div class="qtext">' + esc(q.q) + '</div>';
  html += '<div class="src-detail" id="srcDetail">' + sourceHTML(q) + '</div>';"""

assert qtext_line in html, 'qtext line not found'
html = html.replace(qtext_line, qtext_with_src, 1)
print('3. collapsible source detail added after question')

# ── 4. 在客观题解析下方添加教材出处（已答题时始终显示） ──
explain_end = """    if (q.e) html += '<div class="body">' + esc(q.e) + '</div>';
    html += '</div>';
  }

  html += '</div></div>';"""

explain_end_with_src = """    if (q.e) html += '<div class="body">' + esc(q.e) + '</div>';
    html += '</div>';
  }

  if (answered && !isExam) html += sourceHTML(q);

  html += '</div></div>';"""

assert explain_end in html, 'explain end not found'
html = html.replace(explain_end, explain_end_with_src, 1)
print('4. source display added after objective explanation')

# ── 5. 在主观题答案后添加教材出处 ──
# 简答题/名词解释答案区域
subj_end = """      if (!answered) {
        html += '<div class="row self-rating" id="selfJudge" style="display:none">';
        html += '<button class="btn btn-g" onclick="App.judgeSelf(2)">✓ 会，采分点完整</button>';
        html += '<button class="btn btn-o" onclick="App.judgeSelf(1)">△ 模糊/漏点</button>';
        html += '<button class="btn btn-r" onclick="App.judgeSelf(0)">✗ 不会</button></div>';
      }
    }
    html += '</div>';
  }

  if (q.t === 'case') {"""

subj_end_with_src = """      if (!answered) {
        html += '<div class="row self-rating" id="selfJudge" style="display:none">';
        html += '<button class="btn btn-g" onclick="App.judgeSelf(2)">✓ 会，采分点完整</button>';
        html += '<button class="btn btn-o" onclick="App.judgeSelf(1)">△ 模糊/漏点</button>';
        html += '<button class="btn btn-r" onclick="App.judgeSelf(0)">✗ 不会</button></div>';
      }
      if (answered) html += sourceHTML(q);
    }
    html += '</div>';
  }

  if (q.t === 'case') {"""

assert subj_end in html, 'subj end not found'
html = html.replace(subj_end, subj_end_with_src, 1)
print('5. source display added after subjective answer')

# ── 6. 案例题答案后添加教材出处 ──
case_end = """      if (!answered) {
        html += '<div class="row self-rating" id="caseJudge" style="display:none">';
        html += '<button class="btn btn-g" onclick="App.judgeCase(2)">✓ 会，采分点完整</button>';
        html += '<button class="btn btn-o" onclick="App.judgeCase(1)">△ 模糊/漏点</button>';
        html += '<button class="btn btn-r" onclick="App.judgeCase(0)">✗ 不会</button></div>';
      }
    }
    html += '</div>';
  }

  if (answered && !isExam && (q.t === 'single'"""

case_end_with_src = """      if (!answered) {
        html += '<div class="row self-rating" id="caseJudge" style="display:none">';
        html += '<button class="btn btn-g" onclick="App.judgeCase(2)">✓ 会，采分点完整</button>';
        html += '<button class="btn btn-o" onclick="App.judgeCase(1)">△ 模糊/漏点</button>';
        html += '<button class="btn btn-r" onclick="App.judgeCase(0)">✗ 不会</button></div>';
      }
      if (answered) html += sourceHTML(q);
    }
    html += '</div>';
  }

  if (answered && !isExam && (q.t === 'single'"""

assert case_end in html, 'case end not found'
html = html.replace(case_end, case_end_with_src, 1)
print('6. source display added after case answer')

# ── 写入文件 ──
with open(INDEX, 'w', encoding='utf-8', newline='\n') as f:
    f.write(html)

print('\nAll UI modifications done. File size:', len(html.encode('utf-8')), 'bytes')

# 验证
assert 'sourceHTML' in html
assert 'toggleSrc' in html
assert 'src-btn' in html
assert 'source-box' in html
assert html.count('sourceHTML(q)') == 3  # 3 places: detail + objective + subjective/case
print('Verification passed.')
