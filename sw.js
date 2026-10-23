/* Service worker de Evaluación Física Voleibol — versión Supabase 2 */
const CACHE='evaluacion-voleibol-supabase-2';
const SUPA='https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.118.0/dist/umd/supabase.js';
const CORE=['./','./index.html','./manifest.webmanifest','./icon.svg'];
// La librería de la CDN se guarda aparte: si no se puede descargar, la app igual queda instalada
self.addEventListener('install',e=>{e.waitUntil(caches.open(CACHE).then(c=>c.addAll(CORE).then(()=>c.add(new Request(SUPA,{mode:'cors'})).catch(()=>{}))).then(()=>self.skipWaiting()))});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()))});
self.addEventListener('fetch',e=>{
 const req=e.request;if(req.method!=='GET')return;const url=new URL(req.url);
 if(req.mode==='navigate'||(url.origin===location.origin&&url.pathname.endsWith('.html'))){
  e.respondWith(fetch(req).then(r=>{if(r.ok){const cp=r.clone();caches.open(CACHE).then(c=>c.put('./index.html',cp))}return r}).catch(()=>caches.match('./index.html')));return;
 }
 e.respondWith(caches.match(req).then(hit=>hit||fetch(req).then(r=>{if(r&&(r.ok||r.type==='opaque')&&(url.origin===location.origin||/fonts\.(googleapis|gstatic)\.com$/.test(url.hostname)||url.href===SUPA)){const cp=r.clone();caches.open(CACHE).then(c=>c.put(req,cp))}return r}).catch(()=>hit)));
});