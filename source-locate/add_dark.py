# -*- coding: utf-8 -*-
INDEX = r'D:\study-quiz\index.html'
with open(INDEX, encoding='utf-8') as f:
    html = f.read()

dark_explain = 'html[data-theme="dark"] .explain.bad{background:#2b171a;border-left-color:#f87171}'
dark_source = dark_explain + '\nhtml[data-theme="dark"] .source-box{background:#1a1f3a;border-left-color:#818cf8}\nhtml[data-theme="dark"] .source-box .src-title{color:#a5b4fc}\nhtml[data-theme="dark"] .source-box .src-book{color:#8b95a7}\nhtml[data-theme="dark"] .source-box .src-ch{color:#e6e9ef}\nhtml[data-theme="dark"] .source-box .src-sec{color:#b8c0cc}\nhtml[data-theme="dark"] .source-box .src-pg{color:#a5b4fc}\nhtml[data-theme="dark"] .src-btn{background:#1e2540;color:#a5b4fc}'

assert dark_explain in html, 'dark explain not found'
html = html.replace(dark_explain, dark_source, 1)

with open(INDEX, 'w', encoding='utf-8', newline='\n') as f:
    f.write(html)
print('Dark mode CSS added')
print('source-box dark:', 'html[data-theme="dark"] .source-box' in html)
