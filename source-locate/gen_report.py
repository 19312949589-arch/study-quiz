# -*- coding: utf-8 -*-
"""生成教材出处匹配质量报告，含100题随机抽样。"""
import json, re, random

INDEX = r'D:\study-quiz\index.html'
OUT = r'D:\study-quiz\source-locate\quality_report.md'

# 解析题库
raw = open(INDEX, encoding='utf-8').read()
m = re.search(r'var RAW\s*=\s*\[(.*?)\n\];', raw, re.DOTALL)
body = m.group(1)
questions = []
for ln in body.split('\n'):
    ln = ln.strip().rstrip(',')
    if ln.startswith('{'):
        try:
            questions.append(json.loads(ln))
        except:
            pass

total = len(questions)
high = sum(1 for q in questions if q.get('source', {}).get('confidence') == '高')
mid = sum(1 for q in questions if q.get('source', {}).get('confidence') == '中')
low = sum(1 for q in questions if q.get('source', {}).get('confidence') == '低')
pending = sum(1 for q in questions if '待校验' in q.get('source', {}).get('page', ''))
matched = high + mid  # 有明确页码且置信度中以上
unmatched = pending  # 无明确页码

report = []
report.append('# 教材出处匹配质量报告')
report.append('')
report.append('## 一、总体统计')
report.append('')
report.append('| 指标 | 数量 | 占比 |')
report.append('|------|------|------|')
report.append('| 总题量 | %d | 100%% |' % total)
report.append('| 已匹配（高置信） | %d | %.1f%% |' % (high, high/total*100))
report.append('| 已匹配（中置信） | %d | %.1f%% |' % (mid, mid/total*100))
report.append('| 已匹配（低置信） | %d | %.1f%% |' % (low, low/total*100))
report.append('| 待人工校验（无页码） | %d | %.1f%% |' % (pending, pending/total*100))
report.append('| **已匹配合计（高+中）** | **%d** | **%.1f%%** |' % (matched, matched/total*100))
report.append('')
report.append('## 二、待人工校验题目')
report.append('')
for q in questions:
    s = q.get('source', {})
    if '待校验' in s.get('page', ''):
        report.append('- **%s** (ch=%d, %s)：%s' % (q['id'], q['ch'], q['t'], q['q'][:60].replace('\n', ' ')))
report.append('')
report.append('## 三、各章节匹配分布')
report.append('')
report.append('| 章节 | 题数 | 高 | 中 | 低 | 待校验 |')
report.append('|------|------|----|----|----|--------|')
from collections import defaultdict
by_ch = defaultdict(lambda: {'total':0, 'high':0, 'mid':0, 'low':0, 'pending':0})
for q in questions:
    ch = q['ch']
    s = q.get('source', {})
    by_ch[ch]['total'] += 1
    c = s.get('confidence', '')
    if c == '高': by_ch[ch]['high'] += 1
    elif c == '中': by_ch[ch]['mid'] += 1
    elif c == '低': by_ch[ch]['low'] += 1
    if '待校验' in s.get('page', ''): by_ch[ch]['pending'] += 1

CHAPTER_NAMES = ['绪论','第一章','第二章','第三章','第四章','第五章','第六章','第七章',
                 '第八章','第九章','第十章','第十一章','第十二章','第十三章','第十四章',
                 '第十五章','第十六章','结语']
for ch in sorted(by_ch.keys()):
    d = by_ch[ch]
    name = CHAPTER_NAMES[ch] if 0 <= ch < len(CHAPTER_NAMES) else 'ch%d' % ch
    report.append('| %s | %d | %d | %d | %d | %d |' % (name, d['total'], d['high'], d['mid'], d['low'], d['pending']))
report.append('')

# 随机抽样100题
random.seed(20260925)
sample = random.sample(questions, min(100, total))
sample.sort(key=lambda q: q['id'])

report.append('## 四、随机抽查100题：题目→页码对应')
report.append('')
report.append('| 题号 | 题型 | 题干（节选） | 章节 | 节 | 页码 | 置信度 |')
report.append('|------|------|-------------|------|-----|------|--------|')
type_map = {'single':'单选','multi':'多选','judge':'判断','term':'名词','short':'简答','essay':'论述','case':'案例'}
for q in sample:
    s = q.get('source', {})
    qtext = q['q'][:35].replace('\n', ' ').replace('|', '｜')
    tname = type_map.get(q['t'], q['t'])
    ch_short = s.get('chapter', '')[:12]
    sec_short = s.get('section', '')[:16]
    report.append('| %s | %s | %s | %s | %s | %s | %s |' % (
        q['id'], tname, qtext, ch_short, sec_short, s.get('page',''), s.get('confidence','')))

report.append('')
report.append('## 五、匹配方法说明')
report.append('')
report.append('1. **数据源**：以《坚持蛊.md》逐段勾画笔记为主要匹配源（1893段，每段含教材页码），原书纯文字版目录为兜底。')
report.append('2. **匹配算法**：利用题目已有 ch（章节）字段缩小范围，提取题干+答案+解析+选项的中文二元组/三元组/关键术语，与笔记段落原文+勾画+批注做加权重叠匹配。')
report.append('3. **置信度**：高（术语级匹配+高分）、中（较好匹配）、低（弱匹配）、待校验（无匹配或纯计算题）。')
report.append('4. **禁止猜测**：无法在笔记中定位的题目标记【待校验】，不编造页码。')

with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join(report))

print('报告已生成:', OUT)
print('总题数:', total)
print('高:', high, '中:', mid, '低:', low, '待校验:', pending)
print('已匹配(高+中):', matched, '%.1f%%' % (matched/total*100))
