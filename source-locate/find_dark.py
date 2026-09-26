# -*- coding: utf-8 -*-
raw = open(r'D:\study-quiz\index.html', encoding='utf-8').read()
lines = raw.split('\n')
for i, ln in enumerate(lines):
    if 'data-theme="dark"' in ln and ('explain' in ln or 'source' in ln or 'subj' in ln or 'ansline' in ln):
        print('L%d: %s' % (i+1, ln[:140]))
