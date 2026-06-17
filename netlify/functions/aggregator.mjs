// Netlify Scheduled + On-Demand Function to aggregate news
// Runs hourly via export const config.schedule

import cheerio from 'cheerio';

const USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36';
const DEFAULT_HEADERS = { 'User-Agent': USER_AGENT, 'Accept-Language': 'zh-CN,zh;q=0.9' };

export const config = {
  schedule: '0 * * * *', // hourly
};

let cache = { lastUpdatedIso: '', data: {} };

function sourceFromUrl(url) {
  if (url.includes('ithome.com')) return 'IT之家';
  if (url.includes('sina.com.cn') || url.includes('smartcn.cn')) return '新浪科技';
  if (url.includes('36kr.com')) return '36氪';
  if (url.includes('news.cn')) return '新华网';
  return '来源网站';
}

async function fetchWithTimeout(url, options = {}, timeoutMs = 20000) {
  const controller = new AbortController();
  const t = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(url, { ...options, headers: { ...DEFAULT_HEADERS, ...(options.headers || {}) }, signal: controller.signal });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.text();
  } finally {
    clearTimeout(t);
  }
}

function absolutize(href, baseUrl) {
  if (!href) return '';
  if (href.startsWith('//')) return 'https:' + href;
  if (href.startsWith('http://') || href.startsWith('https://')) return href;
  try {
    const u = new URL(href, baseUrl);
    return u.toString();
  } catch {
    return href;
  }
}

function firstParagraphOrVideoHtml($) {
  const ps = $('p').toArray();
  for (const p of ps) {
    const text = $(p).text().trim();
    if (text && text.length >= 20) return `<p>${escapeHtml(text)}</p>`;
  }
  const iframe = $('iframe').first();
  if (iframe && iframe.attr('src')) {
    const src = iframe.attr('src');
    return `<iframe src="${src}" allow="autoplay; encrypted-media" allowfullscreen loading="lazy"></iframe>`;
  }
  const video = $('video').first();
  if (video && video.attr('src')) {
    const src = video.attr('src');
    return `<video src="${src}" controls></video>`;
  }
  return '';
}

function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

async function scrapeList(url, selectors) {
  try {
    const html = await fetchWithTimeout(url);
    const $ = cheerio.load(html);
    const items = new Map();
    for (const sel of selectors) {
      $(sel).each((_, el) => {
        const el$ = $(el);
        const href = absolutize(el$.attr('href'), url);
        const title = (el$.attr('title') || el$.text() || '').trim();
        if (!href || !title) return;
        items.set(href, { title, url: href });
      });
    }
    return Array.from(items.values()).slice(0, 20);
  } catch (e) {
    return [];
  }
}

async function enrichItem(item) {
  try {
    const html = await fetchWithTimeout(item.url);
    const $ = cheerio.load(html);
    const summaryHtml = firstParagraphOrVideoHtml($);
    return { title: item.title, url: item.url, summary_html: summaryHtml, source: sourceFromUrl(item.url) };
  } catch {
    return { title: item.title, url: item.url, summary_html: '', source: sourceFromUrl(item.url) };
  }
}

async function scrapeCategory(category) {
  const tasks = [];
  function add(url, selectors) { tasks.push(scrapeList(url, selectors)); }

  if (category === '手机') {
    add('https://mobile.ithome.com/', ['a[title]', 'h2 a', 'h3 a']);
    add('https://mobile.sina.com.cn/', ['h2 a', 'h3 a', 'a[title]']);
    add('https://www.36kr.com/search/articles/%E6%89%8B%E6%9C%BA', ['a.article-item-title', "a[href*='/p/']"]);
  } else if (category === '智能家电') {
    add('https://www.smartcn.cn/news', ['.news_list a', 'h2 a', 'h3 a']);
    add('https://www.36kr.com/search/articles/%E6%99%BA%E8%83%BD%E5%AE%B6%E7%94%B5', ['a.article-item-title', "a[href*='/p/']"]);
  } else if (category === '汽车') {
    add('https://www.news.cn/auto/index.html', ['h2 a', 'h3 a', 'a[title]']);
    add('https://www.36kr.com/information/travel/', ['a.article-item-title', "a[href*='/p/']"]);
  } else if (category === '芯片') {
    add('https://so.news.cn/#search/0/%E8%8A%AF%E7%89%87/1/0', ['h2 a', 'h3 a', 'a[title]']);
    add('https://www.ithome.com/search/%E8%8A%AF%E7%89%87.html', ['h2 a', 'h3 a', 'a[title]']);
    add('https://www.36kr.com/search/articles/%E8%8A%AF%E7%89%87', ['a.article-item-title', "a[href*='/p/']"]);
  } else if (category === '操作系统') {
    add('https://search.sina.com.cn/?ac=product&from=tech_index&source=tech&range=title&f_name=&col=&c=news&ie=utf-8&c=news&q=%E6%93%8D%E4%BD%9C%E7%B3%BB%E7%BB%9F', ['h2 a', 'h3 a', 'a[title]']);
    add('https://www.36kr.com/search/articles/%E6%93%8D%E4%BD%9C%E7%B3%BB%E7%BB%9F', ['a.article-item-title', "a[href*='/p/']"]);
  }

  const lists = await Promise.allSettled(tasks);
  const flattened = lists.flatMap(r => (r.status === 'fulfilled' ? r.value : []));
  const unique = new Map();
  for (const it of flattened) unique.set(it.url, it);
  const selected = Array.from(unique.values()).slice(0, 12);
  const enriched = await Promise.all(selected.map(enrichItem));
  return enriched;
}

async function refreshAll() {
  const categories = ['手机', '智能家电', '汽车', '操作系统', '芯片'];
  const results = await Promise.all(categories.map(scrapeCategory));
  const nowIso = new Date().toISOString();
  cache = {
    lastUpdatedIso: nowIso,
    data: Object.fromEntries(categories.map((c, i) => [c, results[i]])),
  };
  return cache;
}

export default async (request, context) => {
  try {
    await refreshAll();
  } catch {}
  const body = JSON.stringify(cache);
  return new Response(body, { headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'max-age=0, no-store' } });
};

