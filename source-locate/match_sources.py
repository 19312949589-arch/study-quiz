# -*- coding: utf-8 -*-
"""
为《管理学》刷题系统题库的每道题匹配教材出处（v2）。
修复：区分真实教材节与笔记内部标签，惩罚导语/概要段，清理节名。
"""
import re, json, os
from collections import defaultdict

BASE = r'D:\study-quiz'
NOTES = r'D:\马克思主义工程管理学第二版\坚持蛊.md'
TEXTBOOK = r'D:\马克思主义工程管理学第二版\原书纯文字版.md'
INDEX = os.path.join(BASE, 'index.html')
OUT_DIR = os.path.join(BASE, 'source-locate')

CHAPTER_NAMES = [
    '绪论', '第一章 管理与管理活动', '第二章 管理理论的历史演变',
    '第三章 决策与决策过程', '第四章 环境分析与决策', '第五章 决策的实施与调整',
    '第六章 组织设计', '第七章 人员配备', '第八章 组织文化',
    '第九章 领导的一般理论', '第十章 激励', '第十一章 沟通',
    '第十二章 控制的类型与过程', '第十三章 控制的方法与技术',
    '第十四章 风险控制与危机管理', '第十五章 创新原理',
    '第十六章 组织变革与创新', '结语 互联网时代的管理变革',
]

STOPWORDS = set('的了是在和与或及等也都就而但并又对于通过进行可以需要一种一些这个那个这些那些以及其之有所不没有被将把让向从到由为对因所以如果虽然但是然而因此于是则即也还又再更最很太已曾正刚才只仅均皆俱各每某另其余其他如此这样那样怎么什么哪里为何是否能否的话来说而言来看以上以下之内之外之中之间')

def extract_bigrams(text):
    text = re.sub(r'[^\u4e00-\u9fff]', ' ', text)
    grams = set()
    for word in text.split():
        for i in range(len(word) - 1):
            bg = word[i:i+2]
            if bg[0] not in STOPWORDS or bg[1] not in STOPWORDS:
                grams.add(bg)
    return grams

def extract_trigrams(text):
    text = re.sub(r'[^\u4e00-\u9fff]', ' ', text)
    grams = set()
    for word in text.split():
        for i in range(len(word) - 2):
            tg = word[i:i+3]
            if tg[0] not in STOPWORDS and tg[2] not in STOPWORDS:
                grams.add(tg)
    return grams

def extract_key_terms(text):
    text = re.sub(r'[^\u4e00-\u9fff]', ' ', text)
    terms = set()
    for word in text.split():
        if len(word) >= 4:
            terms.add(word)
        for i in range(len(word) - 3):
            terms.add(word[i:i+4])
    return terms

def is_real_section(title):
    t = title.strip()
    if re.match(r'^第[一二三四五六七八九十]+节', t):
        return True
    if re.match(r'^[一二三四五六七八九十]+、', t):
        return True
    return False

def clean_section_name(title):
    t = title.strip()
    t = re.sub(r'（教材[^）]*）', '', t)
    t = re.sub(r'\(教材[^)]*\)', '', t)
    t = re.sub(r'（p\d+[^）]*）', '', t)
    return t.strip()

def is_intro_label(title):
    return any(k in title for k in ['导语', '概要', '章首', '本章内容', '绪论内容', '结语内容'])

def parse_notes(path):
    raw = open(path, encoding='utf-8-sig').read()
    raw = raw.replace('\r\n', '\n').replace('\r', '\n')
    lines = raw.split('\n')
    entries = []
    cur_chapter_idx = -1
    cur_chapter_name = ''
    cur_section = ''
    cur_subsection = ''
    cur_page = ''
    in_intro_context = True
    buf = {'orig': '', 'draw': '', 'star': '', 'anno': ''}
    in_block = False
    re_unit = re.compile(r'^##\s+(.+?)\s*·\s*逐段勾画笔记')
    re_heading = re.compile(r'^(#{2,4})\s+(.+)$')
    re_ptitle = re.compile(r'^【(.+?)】（教材\s*(.+?)）')
    re_orig = re.compile(r'^原文：\s*(.*)$')
    re_draw = re.compile(r'^勾画：\s*(.*)$')
    re_star = re.compile(r'^星级：\s*(★+)\s*$')
    re_anno = re.compile(r'^批注：\s*(.*)$')
    re_hr = re.compile(r'^-{3,}\s*$')
    re_sec_in_bracket = re.compile(r'第[一二三四五六七八九十]+节[^】]*')

    def flush():
        nonlocal buf, in_block
        if in_block and (buf['orig'] or buf['draw'] or buf['anno']):
            text_blob = buf['orig'] + ' ' + buf['draw'] + ' ' + buf['anno']
            entries.append({
                'chapter_idx': cur_chapter_idx,
                'chapter_name': cur_chapter_name,
                'section': cur_section,
                'subsection': cur_subsection,
                'page': cur_page,
                'orig': buf['orig'], 'draw': buf['draw'],
                'star': buf['star'], 'anno': buf['anno'],
                'text': text_blob,
                'is_intro': in_intro_context and not cur_section,
                'bigrams': extract_bigrams(text_blob),
                'trigrams': extract_trigrams(text_blob),
                'terms': extract_key_terms(text_blob),
            })
        buf = {'orig': '', 'draw': '', 'star': '', 'anno': ''}
        in_block = False

    for ln in lines:
        ln = ln.rstrip()
        if not ln.strip() or ln.startswith('<!--'):
            continue
        m_unit = re_unit.match(ln)
        if m_unit:
            flush()
            cur_chapter_idx += 1
            cur_chapter_name = m_unit.group(1).strip()
            cur_section = ''
            cur_subsection = ''
            in_intro_context = True
            continue
        m_h = re_heading.match(ln)
        if m_h and '逐段勾画笔记' not in ln:
            flush()
            level = len(m_h.group(1))
            title = clean_section_name(m_h.group(2).strip())
            if is_real_section(title):
                cur_section = title
                cur_subsection = ''
                in_intro_context = False
            elif level == 2:
                if is_intro_label(title):
                    in_intro_context = True
                    cur_section = ''
                else:
                    cur_section = title
                    in_intro_context = False
                cur_subsection = ''
            else:
                cur_subsection = title
            continue
        m_pt = re_ptitle.match(ln)
        if m_pt:
            flush()
            in_block = True
            cur_page = m_pt.group(2).strip()
            bracket_text = m_pt.group(1)
            m_sec = re_sec_in_bracket.search(bracket_text)
            if m_sec and not cur_section:
                cur_section = m_sec.group(0)
                in_intro_context = False
            continue
        if re_hr.match(ln):
            flush()
            continue
        if in_block:
            m_o = re_orig.match(ln)
            if m_o:
                buf['orig'] = m_o.group(1).strip()
                continue
            m_d = re_draw.match(ln)
            if m_d:
                buf['draw'] = m_d.group(1).strip()
                continue
            m_s = re_star.match(ln)
            if m_s:
                buf['star'] = m_s.group(1)
                continue
            m_a = re_anno.match(ln)
            if m_a:
                buf['anno'] = m_a.group(1).strip()
                continue
    flush()
    return entries

def parse_textbook_toc(path):
    raw = open(path, encoding='utf-8-sig').read()
    raw = raw.replace('\r\n', '\n').replace('\r', '\n')
    lines = raw.split('\n')
    toc_start = -1
    toc_end = -1
    for i, ln in enumerate(lines):
        if ln.strip() == '## 目录':
            toc_start = i + 1
        elif toc_start > 0 and ln.strip().startswith('## ') and i > toc_start + 5:
            toc_end = i
            break
    if toc_end < 0:
        toc_end = min(toc_start + 300, len(lines))
    toc_lines = lines[toc_start:toc_end]
    section_pages = {}
    i = 0
    while i < len(toc_lines):
        ln = toc_lines[i].strip()
        if not ln:
            i += 1
            continue
        if re.match(r'^\d+$', ln):
            page = int(ln)
            j = i - 1
            while j >= 0 and not toc_lines[j].strip():
                j -= 1
            if j >= 0:
                section_pages[toc_lines[j].strip()] = page
        i += 1
    return section_pages

def parse_bank(path):
    raw = open(path, encoding='utf-8').read()
    m = re.search(r'var RAW\s*=\s*\[(.*?)\n\];', raw, re.DOTALL)
    if not m:
        raise RuntimeError('Cannot find RAW array')
    body = m.group(1)
    questions = []
    for ln in body.split('\n'):
        ln = ln.strip().rstrip(',')
        if ln.startswith('{'):
            try:
                questions.append(json.loads(ln))
            except json.JSONDecodeError:
                pass
    return questions

def normalize_page(page):
    if not page:
        return ''
    p = page.strip().replace(' ', '')
    if not p.startswith('p') and re.match(r'^\d', p):
        p = 'p' + p
    p = p.replace('—', '-').replace('–', '-')
    return p

def match_question(q, notes_by_chapter):
    ch = q.get('ch', 0)
    qtext = q.get('q', '')
    etext = q.get('e', '')
    atext = ''
    otext = ''
    if q.get('t') == 'single':
        if isinstance(q.get('a'), int) and q.get('o'):
            atext = q['o'][q['a']] if q['a'] < len(q['o']) else ''
    elif q.get('t') == 'multi':
        if isinstance(q.get('a'), list) and q.get('o'):
            atext = ' '.join(q['o'][i] for i in q['a'] if i < len(q['o']))
    elif q.get('t') == 'judge':
        atext = '正确' if q.get('a') else '错误'
    else:
        atext = str(q.get('a', ''))
    if q.get('o'):
        otext = ' '.join(q['o'])
    search_text = qtext + ' ' + atext + ' ' + etext + ' ' + otext
    q_bigrams = extract_bigrams(search_text)
    q_trigrams = extract_trigrams(search_text)
    q_terms = extract_key_terms(search_text)
    if not q_bigrams:
        return None
    cjk_chars = len(re.findall(r'[\u4e00-\u9fff]', search_text))
    is_quantitative = cjk_chars < 15

    candidates = notes_by_chapter.get(ch, [])
    if not candidates:
        for dc in (-1, 1):
            candidates = notes_by_chapter.get(ch + dc, [])
            if candidates:
                break
    if not candidates:
        return None

    best = None
    best_score = 0
    best_non_intro = None
    best_non_intro_score = 0
    best_detail = {}

    for entry in candidates:
        bg_overlap = len(q_bigrams & entry['bigrams'])
        tg_overlap = len(q_trigrams & entry['trigrams'])
        term_overlap = len(q_terms & entry['terms'])
        phrase_hits = 0
        for phrase in entry['terms']:
            if len(phrase) >= 4 and phrase in search_text:
                phrase_hits += 1
        score = bg_overlap * 1.0 + tg_overlap * 3.0 + term_overlap * 5.0 + phrase_hits * 8.0
        star_len = len(entry['star'])
        score *= (1.0 + star_len * 0.05)
        effective_score = score * 0.25 if entry['is_intro'] else score
        if effective_score > best_score:
            best_score = effective_score
            best = entry
            best_detail = {'bg': bg_overlap, 'tg': tg_overlap, 'term': term_overlap, 'phrase': phrase_hits}
        if not entry['is_intro'] and score > best_non_intro_score:
            best_non_intro_score = score
            best_non_intro = entry

    if best and best['is_intro'] and best_non_intro and best_non_intro_score >= best_score * 0.5:
        best = best_non_intro
        best_score = best_non_intro_score

    min_score = 8.0 if not is_quantitative else 15.0
    if not best or best_score < min_score:
        chapter_name = CHAPTER_NAMES[ch] if 0 <= ch < len(CHAPTER_NAMES) else ''
        return {
            'chapter': chapter_name, 'section': '',
            'page': '【待校验】', 'confidence': '低',
            'score': round(best_score, 1), 'matched': False,
        }

    if best_score >= 20.0 and best_detail['term'] >= 1:
        confidence = '高'
    elif best_score >= 10.0:
        confidence = '中'
    else:
        confidence = '低'

    page = normalize_page(best['page'])
    section = best['section']
    if not section:
        section = best['subsection']
    return {
        'chapter': CHAPTER_NAMES[ch] if 0 <= ch < len(CHAPTER_NAMES) else best['chapter_name'],
        'section': section, 'page': page, 'confidence': confidence,
        'score': round(best_score, 1), 'matched': True,
        'note_preview': best['orig'][:60], 'is_intro': best['is_intro'],
    }

def main():
    print('=== 解析笔记 ===')
    notes = parse_notes(NOTES)
    print('笔记段落数:', len(notes))
    print('导语/概要段:', sum(1 for e in notes if e['is_intro']))
    notes_by_chapter = defaultdict(list)
    for e in notes:
        notes_by_chapter[e['chapter_idx']].append(e)

    print('\n=== 解析题库 ===')
    questions = parse_bank(INDEX)
    print('题目数:', len(questions))

    print('\n=== 开始匹配 ===')
    source_map = {}
    stats = {'matched_high': 0, 'matched_mid': 0, 'matched_low': 0, 'unmatched': 0}
    for q in questions:
        qid = q['id']
        result = match_question(q, notes_by_chapter)
        if result is None:
            result = {
                'chapter': CHAPTER_NAMES[q.get('ch', 0)] if 0 <= q.get('ch', 0) < len(CHAPTER_NAMES) else '',
                'section': '', 'page': '【待校验】', 'confidence': '低',
                'score': 0, 'matched': False,
            }
        source_map[qid] = result
        if result['matched']:
            if result['confidence'] == '高':
                stats['matched_high'] += 1
            elif result['confidence'] == '中':
                stats['matched_mid'] += 1
            else:
                stats['matched_low'] += 1
        else:
            stats['unmatched'] += 1

    out_path = os.path.join(OUT_DIR, 'source_map.json')
    with open(out_path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(source_map, f, ensure_ascii=False, indent=2)
    print('\n结果已写入:', out_path)

    total = len(questions)
    print('\n=== 匹配统计 ===')
    print('总题数:', total)
    print('高置信:', stats['matched_high'])
    print('中置信:', stats['matched_mid'])
    print('低置信:', stats['matched_low'])
    print('待校验:', stats['unmatched'])
    print('有出处率(高+中): %.1f%%' % ((stats['matched_high'] + stats['matched_mid']) / total * 100))
    print('仍匹配导语段:', sum(1 for r in source_map.values() if r.get('is_intro')))
    print('空节名:', sum(1 for r in source_map.values() if not r['section']))

    print('\n=== 待校验题 ===')
    for q in questions:
        r = source_map[q['id']]
        if not r['matched']:
            print('[%s] ch=%s %s Q: %s' % (q['id'], q['ch'], q['t'], q['q'][:70].replace('\n', ' ')))

    print('\n=== 前15题样本 ===')
    for q in questions[:15]:
        r = source_map[q['id']]
        print('[%s] %s -> %s | %s | %s (%.1f)' % (
            q['id'], r['confidence'], r['chapter'][:12], r['section'][:22], r['page'], r['score']))

if __name__ == '__main__':
    main()
