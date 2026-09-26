import fs from 'node:fs';
import vm from 'node:vm';

const INDEX = new URL('../index.html', import.meta.url);
const NOTES = new URL('../notes_content.js', import.meta.url);

const EXTENSION_IDS = new Set([
  'mgmt-0027', 'mgmt-0029', 'mgmt-0031', // 卡茨三技能
  'mgmt-0116', 'mgmt-0119', 'mgmt-0159', // 笔记/正文证据不足的通用教辅内容
  'mgmt-0228', 'mgmt-0229', 'mgmt-0230', // 绩效偏差、组织社会化
  'mgmt-0474' // 按产品要求作为拓展题隔离，但出处纠正为第二版 p312
]);

const OVERRIDES = {
  'mgmt-0027': { source: { page: '【待校验】', confidence: '低' }, knowledge_point: '卡茨管理者三技能（拓展）' },
  'mgmt-0028': {
    source: { chapter: '第九章 领导的一般理论', section: '三、经理角色理论', page: 'p220-222', confidence: '高' },
    knowledge_point: '明茨伯格经理角色理论：三类十种角色'
  },
  'mgmt-0029': { source: { page: '【待校验】', confidence: '低' }, knowledge_point: '卡茨管理者三技能（拓展）' },
  'mgmt-0030': {
    source: { chapter: '第九章 领导的一般理论', section: '三、经理角色理论', page: 'p220-222', confidence: '高' },
    knowledge_point: '明茨伯格经理角色理论：决策制定角色'
  },
  'mgmt-0031': { source: { page: '【待校验】', confidence: '低' }, knowledge_point: '卡茨管理者三技能（拓展）' },
  'mgmt-0116': { source: { page: '【待校验】', confidence: '低' }, knowledge_point: '盈亏平衡分析计算（拓展）' },
  'mgmt-0119': { source: { page: '【待校验】', confidence: '低' }, knowledge_point: '多元化战略类型（拓展）' },
  'mgmt-0159': { source: { page: '【待校验】', confidence: '低' }, knowledge_point: '计划层次体系（拓展）' },
  'mgmt-0228': { source: { page: '【待校验】', confidence: '低' }, knowledge_point: '绩效考评主观误差（拓展）' },
  'mgmt-0229': { source: { page: '【待校验】', confidence: '低' }, knowledge_point: '组织社会化概念（拓展）' },
  'mgmt-0230': { source: { page: '【待校验】', confidence: '低' }, knowledge_point: '组织社会化三阶段（拓展）' },
  'mgmt-0334': { knowledge_point: '马斯洛需要层次理论及其局限' },
  'mgmt-0446': { knowledge_point: '单循环学习与双循环学习' },
  'mgmt-0474': {
    source: { chapter: '第十三章 控制的方法与技术', section: '第三节 控制技术的发展趋势', page: 'p312', confidence: '高' },
    knowledge_point: '数字孪生在业务数字化中的应用（拓展）'
  },
  'mgmt-0497': { source: { page: 'p258', confidence: '高' }, knowledge_point: '中国式沟通的核心特征' },
  'mgmt-0512': { source: { page: 'p258', confidence: '高' }, knowledge_point: '中国式沟通的核心特征' }
};

const REMOVE_NOTE_LINKS = new Set([
  'mgmt-0027', 'mgmt-0029', 'mgmt-0031', 'mgmt-0116', 'mgmt-0119',
  'mgmt-0159', 'mgmt-0228', 'mgmt-0229', 'mgmt-0230'
]);

function cleanPoint(value) {
  return String(value || '')
    .replace(/^(简答|论述|名词解释)\s*[：:]\s*/, '')
    .replace(/[（(][^）)]*[）)]/g, '')
    .replace(/[？?。；;]\s*$/, '')
    .trim();
}

function defaultKnowledgePoint(q, source) {
  const fromQuestion = cleanPoint(q.q);
  if (/^(简答|论述|名词解释)/.test(String(q.q || '')) && fromQuestion.length <= 42) return fromQuestion;
  const section = String(source.section || '').replace(/^(第?[一二三四五六七八九十百]+节|[一二三四五六七八九十]+)[、.．]\s*/, '').trim();
  if (section) return section;
  return fromQuestion.length <= 42 ? fromQuestion : `${fromQuestion.slice(0, 40)}…`;
}

function normalizedPage(page) {
  const p = String(page || '').trim();
  return !p || p.includes('待校验') ? '教材页码待人工校验' : p;
}

function patchQuestion(q) {
  const override = OVERRIDES[q.id] || {};
  if (override.source) q.source = { ...q.source, ...override.source };

  if (q.id === 'mgmt-0007') {
    q.q = '下列关于管理学研究对象的表述，符合教材的有（　　）';
    q.o = [
      '广义上包括对个体活动和群体活动的管理',
      '现代管理学主要研究人类有组织的群体活动的管理',
      '现代管理学通常通过剖析企业管理活动来抽象一般规律',
      '管理学只研究企业组织，不适用于其他类型组织'
    ];
    q.a = [0, 1, 2];
    q.e = '教材区分广义研究范围与现代管理学的主要研究对象，并指出企业研究中抽象出的一般管理理论对其他类型组织也有普遍指导意义。';
  }
  if (q.id === 'mgmt-0028') {
    q.q = '明茨伯格经理角色理论中，下列不属于人际关系方面角色的是（　　）';
    q.o = ['挂名首脑', '监听者', '联络者', '领导者'];
    q.a = 1;
    q.e = '第二版将经理角色分为三类十种：人际关系方面包括挂名首脑、领导者、联络者；信息传递方面包括监听者、传播者、发言人；决策制定方面包括企业家、故障排除者、资源分配者、谈判者。';
  }
  if (q.id === 'mgmt-0030') {
    q.q = '明茨伯格认为，经理的决策制定角色包括企业家、故障排除者、资源分配者和传播者。';
    q.a = false;
    q.e = '决策制定方面的角色包括企业家、故障排除者、资源分配者和谈判者；传播者属于信息传递方面的角色。';
  }
  if (q.id === 'mgmt-0228') {
    q.a = [0, 1, 2, 3, 4];
    q.e = '按通用绩效管理资料，晕轮效应、近因效应、刻板效应、宽厚误差和首因效应均可能造成主观考评偏差。本题未在第二版逐段笔记中找到明确对应，故保留为拓展题。';
  }
  if (q.id === 'mgmt-0334') {
    q.a = '需要层次理论由美国心理学家亚伯拉罕·马斯洛提出。\n（1）五个层次：生理需要、安全需要、社交需要、尊重需要、自我实现需要。\n（2）五个层次分为高低两级：生理需要、安全需要和社交需要属于较低层次；尊重需要和自我实现需要属于较高层次。\n（3）主要观点：①人是有需要的动物，只有尚未满足的需要能够影响行为；②低层次需要基本满足后，高层次需要才会显现并逐渐占据优势；③未满足的需要才具有激励作用。\n（4）局限：该理论带有机械论色彩，现实中不同层次需要可能同时存在，其先后次序也会因人和情境而异。';
    q.e = '口诀“生安社尊我”。答题避免写成“一个层次完全满足后，另一个层次才出现”的绝对命题，并写出教材对机械论色彩的评价。';
  }
  if (q.id === 'mgmt-0446') {
    q.q = '双循环学习只在现有框架内纠错，不改变组织规范、目标和错误假设。';
    q.a = false;
    q.e = '单循环学习（适应性学习）是在现有框架内纠错；双循环学习会检视并矫正组织规范、目标和错误假设。';
  }

  const source = q.source || {};
  const status = EXTENSION_IDS.has(q.id)
    ? '拓展内容'
    : (normalizedPage(source.page) === '教材页码待人工校验' || source.confidence !== '高')
      ? '待人工校验'
      : '教材已验证';
  q.book_source = {
    chapter: source.chapter || '',
    section: source.section || '',
    page: normalizedPage(source.page),
    knowledge_point: override.knowledge_point || defaultKnowledgePoint(q, source),
    verify_status: status,
    confidence: source.confidence || '低'
  };
  return q;
}

function loadNotesHtml() {
  const context = { window: {} };
  vm.createContext(context);
  vm.runInContext(fs.readFileSync(NOTES, 'utf8'), context);
  return context.window.NOTES_DATA.html;
}

function noteIndexFor(html, phrase) {
  const pos = html.indexOf(phrase);
  if (pos < 0) throw new Error(`笔记中未找到锚点短语：${phrase}`);
  return html.slice(0, pos).split('<div class="ptitle">').length - 2;
}

function lastNoteIndexFor(html, phrase) {
  const pos = html.lastIndexOf(phrase);
  if (pos < 0) throw new Error(`笔记中未找到锚点短语：${phrase}`);
  return html.slice(0, pos).split('<div class="ptitle">').length - 2;
}

let html = fs.readFileSync(INDEX, 'utf8');
const rawMatch = html.match(/var RAW\s*=\s*\[\n([\s\S]*?)\n\];\/\* ===== 初始化题库 ===== \*\//);
if (!rawMatch) throw new Error('无法定位 RAW 题库');
const questions = rawMatch[1].split('\n').filter(line => line.trim().startsWith('{')).map(line => JSON.parse(line.trim().replace(/,$/, '')));
const upgraded = questions.map(patchQuestion);
const rawText = upgraded.map((q, i) => `${JSON.stringify(q)}${i === upgraded.length - 1 ? '' : ','}`).join('\n');
html = html.replace(rawMatch[0], `var RAW = [\n${rawText}\n];/* ===== 初始化题库 ===== */`);

const notesHtml = loadNotesHtml();
const managerNp = noteIndexFor(notesHtml, '经理角色理论是加拿大学者明茨伯格提出的');
const twinNp = noteIndexFor(notesHtml, '业务层应用数字孪生和虚拟现实技术');
const chineseCommunicationNp = lastNoteIndexFor(notesHtml, '中国式沟通是在中华文化语境中形成的独特沟通模式');
const linksMatch = html.match(/var NOTE_LINKS = (\{[^;]+\});/);
if (!linksMatch) throw new Error('无法定位 NOTE_LINKS');
const links = JSON.parse(linksMatch[1]);
for (const id of REMOVE_NOTE_LINKS) delete links[id];
links['mgmt-0028'] = { id: `note_ch10_${String(managerNp + 1).padStart(3, '0')}`, anchor: `np-${managerNp}`, np: managerNp };
links['mgmt-0030'] = { id: `note_ch10_${String(managerNp + 1).padStart(3, '0')}`, anchor: `np-${managerNp}`, np: managerNp };
links['mgmt-0474'] = { id: `note_ch14_${String(twinNp + 1).padStart(3, '0')}`, anchor: `np-${twinNp}`, np: twinNp };
links['mgmt-0497'] = { id: `note_ch12_${String(chineseCommunicationNp + 1).padStart(3, '0')}`, anchor: `np-${chineseCommunicationNp}`, np: chineseCommunicationNp };
links['mgmt-0512'] = { id: `note_ch12_${String(chineseCommunicationNp + 1).padStart(3, '0')}`, anchor: `np-${chineseCommunicationNp}`, np: chineseCommunicationNp };
html = html.replace(linksMatch[0], `var NOTE_LINKS = ${JSON.stringify(links)};`);

fs.writeFileSync(INDEX, html, 'utf8');
console.log(JSON.stringify({ questions: upgraded.length, managerNp, twinNp, chineseCommunicationNp, extensions: EXTENSION_IDS.size }, null, 2));
