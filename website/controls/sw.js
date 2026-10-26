'use strict';
// Only public static application assets are cached. No robot commands, API calls,
// authentication responses, conversations, audio, or telemetry are cached.
const CACHE='rover-shell-v1';
const ASSETS=['./','./index.html','./style.css','./app.js','./manifest.webmanifest','./icon.svg','./icon-192.png','./icon-512.png'];
self.addEventListener('install',event=>{event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(ASSETS)));});
self.addEventListener('activate',event=>{event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith('rover-shell-')&&k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));});
self.addEventListener('fetch',event=>{const url=new URL(event.request.url);if(event.request.method!=='GET'||url.origin!==self.location.origin)return;const allowed=ASSETS.map(p=>new URL(p,self.registration.scope).pathname);if(!allowed.includes(url.pathname))return;event.respondWith(fetch(event.request).then(response=>{if(response.ok&&!response.redirected&&new URL(response.url).pathname===url.pathname){const copy=response.clone();caches.open(CACHE).then(cache=>cache.put(event.request,copy));}return response;}).catch(()=>caches.match(event.request).then(response=>response||Response.error())));});
