# -*- coding: utf-8 -*-
"""将 source_map.json 注入 index.html 的 RAW 数组。"""
import re, json, os

INDEX = r'D:\study-quiz\index.html'
MAP = r'D:\study-quiz\source-locate\source_map.json'

source_map = json.load(open(MAP, encoding='utf-8'))

raw = open(INDEX, encoding='utf-8').read()
# 确认无 BOM
assert not raw.startswith('\ufeff'), 'File has BOM!'

lines = raw.split('\n')
out_lines = []
modified = 0
errors = []

in_raw = False
for i, ln in enumerate(lines):
    if 'var RAW = [' in ln:
        in_raw = True
        out_lines.append(ln)
        continue
    if in_raw and ln.strip() == '];':
        in_raw = False
        out_lines.append(ln)
        continue
    if in_raw and ln.strip().startswith('{'):
        # 解析题目行
        line_stripped = ln.strip()
        trailing_comma = line_stripped.endswith(',')
        if trailing_comma:
            json_str = line_stripped[:-1]
        else:
            json_str = line_stripped
        try:
            q = json.loads(json_str)
            qid = q.get('id', '')
            if qid in source_map:
                s = source_map[qid]
                src = {
                    'chapter': s['chapter'],
                    'section': s['section'],
                    'page': s['page'],
                    'confidence': s['confidence'],
                }
                q['source'] = src
                # 重新序列化，保持紧凑格式
                new_json = json.dumps(q, ensure_ascii=False, separators=(',', ':'))
                # 保持原行的缩进
                indent = ln[:len(ln) - len(ln.lstrip())]
                new_line = indent + new_json + (',' if trailing_comma else '')
                out_lines.append(new_line)
                modified += 1
            else:
                errors.append('Line %d: id %s not in source_map' % (i+1, qid))
                out_lines.append(ln)
        except json.JSONDecodeError as e:
            errors.append('Line %d: JSON parse error: %s' % (i+1, e))
            out_lines.append(ln)
    else:
        out_lines.append(ln)

result = '\n'.join(out_lines)

# 写入：UTF-8 无 BOM，LF 行尾
with open(INDEX, 'w', encoding='utf-8', newline='\n') as f:
    f.write(result)

print('修改题目数:', modified)
print('错误数:', len(errors))
for e in errors[:10]:
    print(' ', e)
print('文件大小:', len(result.encode('utf-8')), 'bytes')

# 验证：重新读取并检查
verify = open(INDEX, encoding='utf-8').read()
assert not verify.startswith('\ufeff'), 'Output has BOM!'
assert '\r' not in verify, 'Output has CRLF!'
print('验证通过: UTF-8 无 BOM, LF 行尾')

# 统计 source 字段
src_count = verify.count('"source":')
print('source 字段出现次数:', src_count)
