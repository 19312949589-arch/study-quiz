# -*- coding: utf-8 -*-
import re, json
raw = open(r'D:\study-quiz\index.html', encoding='utf-8').read()
m = re.search(r'var RAW\s*=\s*\[(.*?)\n\];', raw, re.DOTALL)
qs = {}
for ln in m.group(1).split('\n'):
    s = ln.strip().rstrip(',')
    if s.startswith('{'):
        try:
            q = json.loads(s)
            qs[q['id']] = q
        except: pass
# 验证答案
print('mgmt-0002 a:', qs['mgmt-0002']['a'], '(expected 0)')
print('mgmt-0005 a:', qs['mgmt-0005']['a'], '(expected 1)')
print('mgmt-0100 a:', qs['mgmt-0100']['a'])
print('mgmt-0566 a:', str(qs['mgmt-0566']['a'])[:40])
print()
# 置信度分布
from collections import Counter
conf = Counter(q['source']['confidence'] for q in qs.values())
pending = sum(1 for q in qs.values() if '待校验' in q['source']['page'])
print('置信度分布:', dict(conf))
print('待校验(无页码):', pending)
print('已匹配(高+中):', conf['高'] + conf['中'])
print()
# 质量报告前30行
report = open(r'D:\study-quiz\source-locate\quality_report.md', encoding='utf-8').read()
lines = report.split('\n')
print('\n'.join(lines[:25]))
