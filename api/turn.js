// v4.5 TURN 帳密發放（Vercel Serverless Function，網址：/api/turn）
// 為什麼需要：手機網路、學校／公司網路常是「對稱型 NAT」，兩台裝置無法直接連線（WebRTC 打洞失敗），
//   必須透過 TURN 轉傳伺服器。TURN 要帳密，而帳密要用「密鑰」去換；密鑰絕對不能放進網頁（任何人都看得到），
//   所以由這支函式在伺服器端讀環境變數、向 TURN 服務換一組幾小時就過期的帳密，再回給遊戲。
//
// 要在 Vercel 專案 → Settings → Environment Variables 設定（至少一組；設了好幾組 → 全部一起回傳，瀏覽器自己挑能通的）：
//   1. Metered Open Relay（主要，不用信用卡，每月 20 GB 免費）；兩種設定方式擇一（兩種都設 → 用 API Key 那種）：
//      a) API Key（伺服器去換帳密，密鑰不會外流）：
//        METERED_DOMAIN   ＝ 你的 Metered 網域，例如 wireframech.metered.live
//        METERED_API_KEY  ＝ Metered 的 TURN API Key
//      b) 固定帳密（免費方案後台直接給的 username／password）：
//        METERED_USERNAME ＝ 後台的 username
//        METERED_PASSWORD ＝ 後台的 password（credential）
//        METERED_URLS     ＝（選填，逗號分隔）預設 turn:global.relay.metered.ca:80（udp／tcp）、:443，以及 turns:global.relay.metered.ca:443?transport=tcp
//   2. ExpressTURN（加碼，免費方案每月 1000 GB，帳密是固定的長期帳密）：
//        EXPRESSTURN_USERNAME ＝ 後台的 turn_username
//        EXPRESSTURN_PASSWORD ＝ 後台的 turn_password
//        EXPRESSTURN_URLS     ＝（選填，逗號分隔）預設 turn:relay1.expressturn.com:3478 的 udp／tcp ＋ turns:relay1.expressturn.com:443
//   3. Cloudflare Realtime TURN（選用，要綁信用卡，每月 1000 GB 免費）：
//        CF_TURN_KEY_ID     ＝ TURN 金鑰的 Turn Token ID
//        CF_TURN_API_TOKEN  ＝ 同一把金鑰的 API Token
//   選填：TURN_ALLOWED_ORIGINS ＝ 允許呼叫的網站（逗號分隔，可用 * 萬用字元），預設見下方 DEFAULT_ORIGINS
//   注意：TURN 帳密本來就會交給瀏覽器（不然連不上），Metered 固定帳密與 ExpressTURN 的固定帳密因此玩家用開發者工具看得到
//         （被濫用時到各家後台重新產生帳密、更新環境變數即可）；真正藏起來的是 Metered API Key／Cloudflare 的 API 金鑰
//
// 回傳：{ iceServers: [...], ttl: 秒, provider: 'metered+expressturn' 之類 }；一組都沒設 → 503 { error: 'not-configured' }（遊戲會自動改回只用 STUN）
//   某一家失敗、其他家成功 → 照樣回成功的那幾家；全部失敗 → 502

const TTL = 4 * 3600;   // 帳密有效 4 小時（一場 5 分鐘，夠用；網頁會在快過期時重拿）
const DEFAULT_ORIGINS = [
  'https://wireframech.vercel.app',
  'https://*.vercel.app',          // 預覽部署
  'https://*.itch.io',             // itch.io 頁面
  'https://*.itch.zone',           // itch.io 的 HTML5 遊戲實際跑在這個網域的 iframe
  'https://*.hwcdn.net',           // itch.io 舊的遊戲 CDN
  'http://localhost:*', 'http://127.0.0.1:*',
];

function originAllowed(origin) {
  if (!origin) return true;   // 同網域的 GET 不會帶 Origin
  const list = (process.env.TURN_ALLOWED_ORIGINS || '').split(',').map(s => s.trim()).filter(Boolean);
  const pats = list.length ? list : DEFAULT_ORIGINS;
  return pats.some(p => {
    if (p === '*') return true;
    const re = new RegExp('^' + p.replace(/[.+?^${}()|[\]\\]/g, '\\$&').replace(/\*/g, '[^/]*') + '$', 'i');
    return re.test(origin);
  });
}

// 去掉 53 埠（瀏覽器會擋，只會拖慢連線）
function clean(list) {
  return (Array.isArray(list) ? list : []).map(s => {
    const urls = (Array.isArray(s.urls) ? s.urls : [s.urls || s.url]).filter(u => typeof u === 'string' && !/:53(\?|$)/.test(u));
    return { ...s, urls };
  }).filter(s => s.urls.length);
}

async function fetchJson(url, opt) {
  const ac = new AbortController(), t = setTimeout(() => ac.abort(), 4000);
  try {
    const r = await fetch(url, { ...opt, signal: ac.signal });
    if (!r.ok) throw new Error(`${new URL(url).host} 回應 ${r.status}`);
    return await r.json();
  } finally { clearTimeout(t); }
}

async function fromCloudflare(id, token) {
  const j = await fetchJson(`https://rtc.live.cloudflare.com/v1/turn/keys/${encodeURIComponent(id)}/credentials/generate-ice-servers`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ ttl: TTL }),
  });
  return { iceServers: clean(j.iceServers), ttl: TTL, provider: 'cloudflare' };
}

async function fromMetered(domain, key) {
  const host = String(domain).replace(/^https?:\/\//, '').replace(/\/.*$/, '');
  const j = await fetchJson(`https://${host}/api/v1/turn/credentials?apiKey=${encodeURIComponent(key)}`);
  return { iceServers: clean(Array.isArray(j) ? j : j.iceServers), ttl: 3600, provider: 'metered' };   // Metered 的帳密預設長效，保守當 1 小時
}

const METERED_STATIC_URLS = [
  'turn:global.relay.metered.ca:80',
  'turn:global.relay.metered.ca:80?transport=tcp',
  'turn:global.relay.metered.ca:443',
  'turns:global.relay.metered.ca:443?transport=tcp',
];
function fromMeteredStatic(user, pass, urlsEnv) {   // 固定帳密：不用打 API
  const urls = urlsEnv ? String(urlsEnv).split(',').map(s => s.trim()).filter(Boolean) : METERED_STATIC_URLS;
  const stun = urls.filter(u => /^stuns?:/i.test(u)), turn = urls.filter(u => !/^stuns?:/i.test(u));
  return { iceServers: clean([{ urls: stun.length ? stun : ['stun:stun.relay.metered.ca:80'] }, { urls: turn, username: user, credential: pass }]), ttl: TTL, provider: 'metered' };
}

const EXPRESSTURN_DEFAULT_URLS = [
  'turn:relay1.expressturn.com:3478?transport=udp',
  'turn:relay1.expressturn.com:3478?transport=tcp',
  'turns:relay1.expressturn.com:443?transport=tcp',
];
function fromExpressTurn(user, pass, urlsEnv) {   // 固定帳密：不用打 API
  const urls = urlsEnv ? String(urlsEnv).split(',').map(s => s.trim()).filter(Boolean) : EXPRESSTURN_DEFAULT_URLS;
  return { iceServers: clean([{ urls, username: user, credential: pass }]), ttl: TTL, provider: 'expressturn' };
}

const hasTurn = out => out.iceServers.some(s => s.urls.some(u => /^turns?:/i.test(u)));

module.exports = async (req, res) => {
  const origin = req.headers.origin || '';
  res.setHeader('Vary', 'Origin');
  res.setHeader('Cache-Control', 'no-store');
  if (origin && originAllowed(origin)) {
    res.setHeader('Access-Control-Allow-Origin', origin);
    res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
    res.setHeader('Access-Control-Max-Age', '86400');
  }
  if (req.method === 'OPTIONS') { res.statusCode = 204; return res.end(); }
  if (!originAllowed(origin)) { res.statusCode = 403; return res.json({ error: 'origin-not-allowed' }); }
  if (req.method !== 'GET') { res.statusCode = 405; return res.json({ error: 'method-not-allowed' }); }

  const env = process.env, jobs = [];   // 順序＝回傳順序：Metered → ExpressTURN → Cloudflare
  if (env.METERED_DOMAIN && env.METERED_API_KEY) jobs.push(fromMetered(env.METERED_DOMAIN, env.METERED_API_KEY));
  else if (env.METERED_USERNAME && env.METERED_PASSWORD) jobs.push(Promise.resolve().then(() => fromMeteredStatic(env.METERED_USERNAME, env.METERED_PASSWORD, env.METERED_URLS)));   // 沒有 API Key 才用固定帳密
  if (env.EXPRESSTURN_USERNAME && env.EXPRESSTURN_PASSWORD) jobs.push(Promise.resolve().then(() => fromExpressTurn(env.EXPRESSTURN_USERNAME, env.EXPRESSTURN_PASSWORD, env.EXPRESSTURN_URLS)));
  if (env.CF_TURN_KEY_ID && env.CF_TURN_API_TOKEN) jobs.push(fromCloudflare(env.CF_TURN_KEY_ID, env.CF_TURN_API_TOKEN));
  if (!jobs.length) { res.statusCode = 503; return res.json({ error: 'not-configured' }); }

  const got = [];
  for (const r of await Promise.allSettled(jobs)) {   // 同時問，一家壞掉不影響其他家
    if (r.status === 'fulfilled' && hasTurn(r.value)) got.push(r.value);
    else console.error('[turn]', r.status === 'rejected' ? (r.reason && r.reason.message) : `${r.value.provider} 回應裡沒有 TURN 伺服器`);   // 只記錯誤訊息，不記密鑰
  }
  if (!got.length) { res.statusCode = 502; return res.json({ error: 'upstream-failed' }); }
  res.statusCode = 200;
  return res.json({
    iceServers: got.flatMap(o => o.iceServers.filter(s => s.urls.some(u => /^turns?:/i.test(u)))),   // 只回 TURN（STUN 遊戲自己有）
    ttl: Math.min(...got.map(o => o.ttl)),
    provider: got.map(o => o.provider).join('+'),
  });
};

module.exports.originAllowed = originAllowed;   // 給自動測試用
module.exports.clean = clean;
