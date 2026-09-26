import fs from 'node:fs';
import vm from 'node:vm';

const ROOT = new URL('../', import.meta.url);
const index = fs.readFileSync(new URL('index.html', ROOT), 'utf8');
const raw = index.match(/var RAW\s*=\s*\[\n([\s\S]*?)\n\];\/\* ===== 初始化题库 ===== \*\//);
if (!raw) throw new Error('RAW 题库不存在');
const questions = raw[1].split('\n').filter(x => x.trim().startsWith('{')).map(x => JSON.parse(x.trim().replace(/,$/, '')));
const byId = Object.fromEntries(questions.map(q => [q.id, q]));

const linksMatch = index.match(/var NOTE_LINKS = (\{[^;]+\});/);
if (!linksMatch) throw new Error('NOTE_LINKS 不存在');
const links = JSON.parse(linksMatch[1]);

const context = { window: {} };
vm.createContext(context);
vm.runInContext(fs.readFileSync(new URL('notes_content.js', ROOT), 'utf8'), context);
const notesHtml = context.window.NOTES_DATA.html;
const noteBlocks = [...notesHtml.matchAll(/<div class="ptitle"><span class="pch">([^<]*)<\/span><span class="ppg">教材 ([^<]*)<\/span><\/div>/g)]
  .map(m => ({ chapter: m[1], page: m[2] }));

function pageNumbers(text) {
  const nums = String(text || '').match(/\d+/g);
  if (!nums || !nums.length) return [];
  const a = Number(nums[0]), b = Number(nums[1] || nums[0]), out = [];
  for (let n = Math.min(a, b); n <= Math.max(a, b); n++) out.push(n);
  return out;
}

function pagesOverlap(a, b) {
  const aa = new Set(pageNumbers(a));
  return pageNumbers(b).some(n => aa.has(n));
}

function answerValid(q) {
  if (q.t === 'single') return Number.isInteger(q.a) && Array.isArray(q.o) && q.a >= 0 && q.a < q.o.length;
  if (q.t === 'multi') return Array.isArray(q.a) && Array.isArray(q.o) && q.a.length > 0 && q.a.every(n => Number.isInteger(n) && n >= 0 && n < q.o.length);
  if (q.t === 'judge') return typeof q.a === 'boolean';
  if (q.t === 'case') return Array.isArray(q.sub) && q.sub.length > 0 && q.sub.every(s => s.q && s.a);
  return typeof q.a === 'string' && q.a.trim().length > 0;
}

const required = ['chapter', 'section', 'page', 'knowledge_point', 'verify_status', 'confidence'];
const validStatuses = new Set(['教材已验证', '待人工校验', '拓展内容']);
const validConfidence = new Set(['高', '中', '低']);
const errors = [];
for (const q of questions) {
  const bs = q.book_source;
  if (!bs) { errors.push(`${q.id}: 缺少 book_source`); continue; }
  for (const key of required) if (!(key in bs)) errors.push(`${q.id}: book_source 缺少 ${key}`);
  if (!validStatuses.has(bs.verify_status)) errors.push(`${q.id}: verify_status 非法`);
  if (!validConfidence.has(bs.confidence)) errors.push(`${q.id}: confidence 非法`);
  if (!answerValid(q)) errors.push(`${q.id}: 答案结构非法`);
  if (bs.verify_status === '教材已验证') {
    if (bs.page === '教材页码待人工校验') errors.push(`${q.id}: 已验证题却没有页码`);
    const link = links[q.id];
    if (!link || !Number.isInteger(link.np) || !noteBlocks[link.np]) errors.push(`${q.id}: 已验证题缺少有效笔记锚点`);
    else if (!pagesOverlap(bs.page, noteBlocks[link.np].page)) errors.push(`${q.id}: 题目页码 ${bs.page} 与笔记锚点页码 ${noteBlocks[link.np].page} 不相交`);
  }
}

const ids = questions.map(q => q.id);
if (new Set(ids).size !== ids.length) errors.push('存在重复题号');
if (!index.includes("sourceMeta = [bs.chapter, bs.section, bs.page, bs.knowledge_point")) errors.push('搜索索引未纳入教材定位字段');
if (!index.includes("body.push('案例小问：'")) errors.push('搜索索引未纳入案例小问');
if (!index.includes("App.restoreFromNote()")) errors.push('笔记返回入口不存在');
if (/history\.back\s*\(/.test(index)) errors.push('发现禁止使用的 history.back()');

const statusCounts = questions.reduce((m, q) => (m[q.book_source.verify_status] = (m[q.book_source.verify_status] || 0) + 1, m), {});
const pendingPages = questions.filter(q => q.book_source.page === '教材页码待人工校验');

// 固定种子的确定性随机抽查，确保每次回归选择相同的 50 题。
let seed = 20260926;
function rand() { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; }
const samplePool = questions.slice();
for (let i = samplePool.length - 1; i > 0; i--) {
  const j = Math.floor(rand() * (i + 1));
  [samplePool[i], samplePool[j]] = [samplePool[j], samplePool[i]];
}
const sample = samplePool.slice(0, 50);
const sampleRows = sample.map(q => {
  const bs = q.book_source;
  const link = links[q.id];
  const anchor = link && noteBlocks[link.np];
  const pageOk = bs.verify_status !== '教材已验证' || !!(anchor && pagesOverlap(bs.page, anchor.page));
  const ok = answerValid(q) && !!q.e && pageOk;
  return `| ${q.id} | ${bs.chapter || '—'} | ${bs.page} | ${bs.verify_status} | ${ok ? '通过' : '需复核'} |`;
});

const issues = [
  ['mgmt-0007', '绪论 p2', '多选题边界含混，“包括”使企业员工行为选项也可能成立。', '重写为教材支持表述，答案改为“广义范围＋主要对象＋企业研究抽象一般规律”。'],
  ['mgmt-0027', '第一章 p30—31', '卡茨三技能未在逐段笔记找到，原页码证据不足。', '保留题目，标记拓展内容，页码改为待人工校验。'],
  ['mgmt-0028', '第一章 p32—33', '明茨伯格经理角色理论章节错配且术语不完全符合第二版。', '改为第九章第三节 p220—222，并使用“挂名首脑、监听者、故障排除者”等第二版术语。'],
  ['mgmt-0029', '第一章 p38', '卡茨三技能与“全球化”来源明显错配。', '保留题目，标记拓展内容，页码改为待人工校验。'],
  ['mgmt-0030', '第一章 p32—33', '经理角色理论定位仍在第一章。', '改为第九章第三节 p220—222并校准第二版术语。'],
  ['mgmt-0031', '第一章 p24', '卡茨技能体系证据不足，系统原置信度为低。', '标记拓展内容，页码改为待人工校验。'],
  ['mgmt-0116', '第四章【待校验】', '笔记只列举盈亏平衡分析，未给出该公式例题。', '保留为拓展题，不补造教材页码。'],
  ['mgmt-0119', '第四章 p97', '多元化战略分类未在对应第二版段落找到。', '保留为拓展题，页码改为待人工校验。'],
  ['mgmt-0159', '第五章【待校验】', '计划层次体系未在逐段笔记找到。', '保留为拓展题，不补造教材页码。'],
  ['mgmt-0228', '第七章【待校验】', '原答案漏选“首因效应”，且第二版正文证据不足。', '答案补入首因效应，同时标记拓展内容。'],
  ['mgmt-0229', '第七章 p170', '组织社会化未在逐段笔记找到。', '标记拓展内容，页码改为待人工校验。'],
  ['mgmt-0230', '第七章 p175', '组织社会化三阶段未在逐段笔记找到。', '标记拓展内容，页码改为待人工校验。'],
  ['mgmt-0334', '第十章 p238', '需要层次递进表述过于绝对，遗漏教材的机械论批评。', '改为“基本满足后显现并占优势”，补充机械论局限。'],
  ['mgmt-0446', '第十六章 p373', '原术语转述偏教辅化，仍需纸书逐字复核。', '按单循环/双循环学习重新表述，状态保留待人工校验。'],
  ['mgmt-0474', '结语 p377', '数字孪生来源错配；第二版明确内容实际在第十三章 p312。', '定位改为第十三章第三节 p312；按产品要求仍放入拓展题专区。'],
  ['mgmt-0497', '第十一章 p259', '题目页码与对应逐段笔记锚点 p258 不一致。', '页码改为 p258，并补齐中国式沟通原文段落锚点。'],
  ['mgmt-0512', '第十一章 p259', '题目页码与对应逐段笔记锚点 p258 不一致。', '页码改为 p258，并与名词解释题共用同一原文段落锚点。']
];

let report = '# 教材校验报告\n\n';
report += `校验题量：${questions.length} 题。教材已验证：${statusCounts['教材已验证'] || 0}；待人工校验：${statusCounts['待人工校验'] || 0}；拓展内容：${statusCounts['拓展内容'] || 0}。\n\n`;
report += `未确定页码：${pendingPages.length} 题（${pendingPages.map(q => q.id).join('、')}）。\n\n`;
report += '说明：本次“教材已验证”表示题目页码与项目内第二版逐段笔记的原文页码及段落锚点一致；出版社纸质书仍是最终复核依据。证据不足处均未补造页码。\n\n';
for (const [id, original, problem, suggestion] of issues) {
  report += `题号：${id}\n\n原定位：${original}\n\n问题：${problem}\n\n建议修改：${suggestion}\n\n---\n\n`;
}
fs.writeFileSync(new URL('教材校验报告.md', import.meta.url), report, 'utf8');

let sampleReport = '# 随机抽查 50 题\n\n';
sampleReport += '抽查口径：固定种子随机抽取；检查题号唯一、答案结构、解析非空、`book_source` 六字段、验证状态，以及“教材已验证”题的页码与笔记段落锚点是否相交。\n\n';
sampleReport += '| 题号 | 章节 | 页码 | 状态 | 结果 |\n|---|---|---|---|---|\n';
sampleReport += sampleRows.join('\n') + '\n';
fs.writeFileSync(new URL('随机抽查50题.md', import.meta.url), sampleReport, 'utf8');

console.log(JSON.stringify({
  questions: questions.length,
  statuses: statusCounts,
  pendingPages: pendingPages.length,
  noteBlocks: noteBlocks.length,
  noteLinks: Object.keys(links).length,
  samplePassed: sampleRows.filter(x => x.endsWith('| 通过 |')).length,
  errors
}, null, 2));
if (errors.length) process.exitCode = 1;
