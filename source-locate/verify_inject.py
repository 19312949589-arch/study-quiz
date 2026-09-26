# -*- coding: utf-8 -*-
import json
raw = open(r'D:\study-quiz\index.html', encoding='utf-8').read()
lines = raw.split('\n')
print('=== 前3题 source ===')
for i in [490, 491, 492]:
    ln = lines[i].strip().rstrip(',')
    q = json.loads(ln)
    print(q['id'], '->', json.dumps(q.get('source', {}), ensure_ascii=False))
print()
print('=== 最后1题 ===')
for i in range(len(lines)-1, 0, -1):
    s = lines[i].strip()
    if s.startswith('{"ch"'):
        q = json.loads(s.rstrip(','))
        print(q['id'], '->', json.dumps(q.get('source', {}), ensure_ascii=False))
        break
print()
print('=== 答案未变验证 ===')
q2 = json.loads(lines[491].strip().rstrip(','))
q5 = json.loads(lines[494].strip().rstrip(','))
print('mgmt-0002 a:', q2['a'], 'q:', q2['q'][:30])
print('mgmt-0005 a:', q5['a'], 'q:', q5['q'][:30])
print()
print('=== 待校验题 ===')
for i, ln in enumerate(lines):
    s = ln.strip()
    if s.startswith('{"ch"') and '待校验' in s:
        q = json.loads(s.rstrip(','))
        print(q['id'], '->', q['source']['page'], '|', q['q'][:40])
