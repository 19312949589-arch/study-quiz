# -*- coding: utf-8 -*-
import re, json
raw = open(r'D:\study-quiz\index.html', encoding='utf-8').read()
m = re.search(r'var RAW\s*=\s*\[(.*?)\n\];', raw, re.DOTALL)
count = 0
has_source = 0
for ln in m.group(1).split('\n'):
    s = ln.strip().rstrip(',')
    if s.startswith('{'):
        try:
            q = json.loads(s)
            count += 1
            if 'source' in q: has_source += 1
        except: pass
print('题库题目数:', count)
print('含source字段:', has_source)
print('sourceHTML函数:', 'function sourceHTML' in raw)
print('toggleSrc函数:', 'function toggleSrc' in raw)
print('教材出处按钮:', '教材出处' in raw)
print('source-box CSS:', '.source-box' in raw)
dark_ok = 'html[data-theme="dark"] .source-box' in raw
print('暗色模式:', dark_ok)
print('文件大小:', len(raw.encode('utf-8')), 'bytes')
print('UTF-8无BOM:', not raw.startswith('\ufeff'))
print('LF行尾:', '\r' not in raw)
# 答案未变
lines = raw.split('\n')
q2 = json.loads(lines[490].strip().rstrip(','))
q5 = json.loads(lines[493].strip().rstrip(','))
print('mgmt-0002 a:', q2['a'], '(expected 0)')
print('mgmt-0005 a:', q5['a'], '(expected 1)')
print('mgmt-0002 source:', json.dumps(q2['source'], ensure_ascii=False))
