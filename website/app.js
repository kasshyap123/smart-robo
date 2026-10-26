import * as THREE from './vendor/three.module.js';
import {OrbitControls} from './vendor/OrbitControls.js';
const $=s=>document.querySelector(s);
const reduced=matchMedia('(prefers-reduced-motion: reduce)');
let paused=reduced.matches, renderer, scene, camera, robot, orbit, geometryData, meshes=[], activePart=null, lastFocus=null, savedScroll=0, detailAge=0, lastTime=0, introStart=0, ready=false, deferredInstall=null;
const clamp=(n,a=0,b=1)=>Math.min(b,Math.max(a,n));
const smooth=n=>{n=clamp(n);return n*n*(3-2*n)};
const details=[
{id:'B01',title:'The front shell',category:'BODY',summary:'The foundation of a familiar face.',description:'The front half of Rover’s body gives the companion its rounded, continuous silhouette.',function:'This integrated enclosure forms the front body volume and carries the surrounding mechanical interfaces. It is an enclosure, not the complete wheeled chassis.',fit:'It meets the rear shell and sits below the front deck. Its original STEP position is preserved in the assembled view.'},
{id:'B02',title:'The rear shell',category:'BODY',summary:'A home for everything within.',description:'The rear body half completes the enclosure and creates a serviceable space for the electronics.',function:'It encloses the rear equipment area and supports the relationship between the service lid and internal tray. The split body lets those areas be accessed independently.',fit:'It joins B01 along the middle of the body. The removable B04 lid sits above it, with the B05 electronics tray inside.'},
{id:'B03',title:'The deck & neck',category:'STRUCTURE',summary:'The connection that holds it together.',description:'A sculpted deck flows into a fixed neck, connecting Rover’s body to its head.',function:'The neck is structural and includes a retained cable passage. This supplied part is fixed: the animated website does not imply that the physical head can turn.',fit:'The front deck sits above B01, with the head shell positioned on the neck. Cable routing and tool access still need physical verification.'},
{id:'B04',title:'The service lid',category:'ACCESS',summary:'Open up. Make things better.',description:'A slim rear panel provides access to the equipment beneath it.',function:'The part combines a 3 mm panel with 3 mm locating lips. Its removal path was checked in the supplied CAD package; printed fit must still be tested.',fit:'It closes the rear shell above the electronics area. Removing it is part of the intended servicing sequence.'},
{id:'B05',title:'The electronics tray',category:'ELECTRONICS',summary:'An organised little nervous system.',description:'One tray brings the board platforms into a single removable structure.',function:'Integrated platforms organise the electronics layout. The design reserves board and service spaces, but these are mechanical provisions rather than proof that every purchased board fits.',fit:'It lives inside B02 and supports the ESP32 carrier. Driver variants, terminal positions, clamps and board undersides remain fit checks.'},
{id:'B06',title:'The ESP32 carrier',category:'ELECTRONICS',summary:'A place for Rover’s reflexes.',description:'An adjustable carrier with integral feet holds the controller that will handle Rover’s local inputs and outputs.',function:'It supports the ESP32 board and provides the intended USB access corridor. The plastic carrier itself contains no electronics or live connection.',fit:'It mounts on the electronics tray. Final retention must leave the USB plug, EN/BOOT buttons and GPIO connections accessible.'},
{id:'B07',title:'The battery cradle',category:'POWER',summary:'A steady home for its energy.',description:'A one-piece cradle locates the battery holder low in the assembly.',function:'It supports the holder and keeps its placement defined relative to the enclosure. The bare-holder service path is documented, while loaded cells and leads still require testing.',fit:'It sits near the base of the rear equipment volume. Attachment holes, insulation and the full installed holder height must be checked against the actual hardware.'},
{id:'B08',title:'The head shell',category:'EXPRESSION',summary:'The shape of a companion.',description:'The rounded head forms the outer volume around Rover’s display and front-facing components.',function:'Integrated mounting rails organise the front assembly. This is the actual supplied shell, with its openings and internal features preserved.',fit:'It sits on the fixed neck, between the front visor assembly and rear cover. Physical harness routing and print tolerance remain to be verified.'},
{id:'B09',title:'The head cover',category:'ACCESS',summary:'Behind every little expression.',description:'The rear head cover closes the enclosure while keeping an access route for assembly and maintenance.',function:'It includes the documented buzzer support and forms the removable rear boundary of the head.',fit:'It mates to B08 behind the visor and display carrier. The actual buzzer flange and lead clearance need a physical check.'},
{id:'B10',title:'The face assembly',category:'EXPRESSION',summary:'Where personality takes shape.',description:'The unified visor brings together the display, microphone and LED mounting regions. Its removable B10R OLED carrier is included here.',function:'The corrected microphone region has a 15.2 mm seat, 7 mm shoulder opening and 21.2 mm outer cup. B10R supports the OLED from behind, so the screen can be serviced separately.',fit:'B10 meets the head shell; B10R sits behind the display opening. This card shows both original solids. The real PCB, microphone pads, spacers and small fasteners still need fit and acoustic checks.'},
{id:'B11',title:'The speaker frames',category:'SOUND',summary:'A little room for a big voice.',description:'Two retaining frames locate the speakers in the lower body.',function:'Each frame is 90 × 60 × 2.5 mm. The assembly contains a left and right copy; the close-up shows one representative frame.',fit:'The supplied exports already place both frames on opposite sides of the lower enclosure. They are not head-mounted speakers. Flanges, terminals and gaskets need verification.'},
{id:'B12',title:'The rear panel',category:'POWER',summary:'Simple access. Clean connections.',description:'A rear panel groups the physical switch openings at the back of the enclosure.',function:'The current geometry contains two 19 × 12 mm switch openings. Despite the source name mentioning charging, this revision has no charging cutout.',fit:'It closes the rear switch area. Rocker latches, panel engagement and insulated terminals need testing with the actual switches.'},
{id:'B13',title:'The chassis feet',category:'STRUCTURE',summary:'Four small points of connection.',description:'Four adjustable feet form the intended interface to the underlying chassis.',function:'Slots provide adjustment for attachment. The close-up shows one foot; all four placed copies are included in the full robot.',fit:'Two feet sit toward the front and two toward the rear. Their alignment remains conditional on measuring the real acrylic chassis holes.'}
];
const grid=$('#parts-grid');
for(const [i,p] of details.entries()){
 const b=document.createElement('button');b.className='part-card';b.dataset.part=p.id;b.setAttribute('aria-label',`Explore ${p.id}: ${p.title}`);b.innerHTML=`<span class="timeline-node" aria-hidden="true">${String(i+1).padStart(2,'0')}</span><span class="card-top"><span>${p.id}${p.id==='B10'?' + B10R':''}</span><span class="card-category">${p.category}</span></span><span class="card-placeholder">Loading original geometry</span><h3>${p.title}</h3><p>${p.summary}</p><span class="card-arrow" aria-hidden="true">↗</span>`;b.onclick=()=>openPart(i);grid.append(b);
}
for(let i=0;i<26;i++){const p=document.createElement('i');p.className='bubble';p.style.setProperty('--x',((i*37.7)%100)+'%');p.style.setProperty('--size',(10+(i*13)%46)+'px');p.style.setProperty('--drift',((i%2?1:-1)*(25+i*3))+'px');p.style.setProperty('--bubble-color',['#b1ffd2','#b291ff','#ffd58a','#7798ff'][i%4]);p.style.animationDuration=(14+(i%7)*2)+'s';p.style.animationDelay=(-i*1.9)+'s';$('#bubble-field').append(p)}
for(const line of document.querySelectorAll('[data-letters]')){const text=line.textContent;line.textContent='';[...text].forEach((letter,i)=>{const span=document.createElement('span');span.className='animated-letter';span.textContent=letter===' '?'\u00a0':letter;span.style.setProperty('--letter-x',((i%2?1:-1)*(50+i*19))+'px');span.style.setProperty('--letter-y',((i%3-1)*100)+'px');span.style.setProperty('--letter-r',((i%2?1:-1)*25)+'deg');span.style.animationDelay=(i*.065+.12)+'s';line.append(span)})}
function updatePause(){document.body.classList.toggle('paused',paused);document.querySelectorAll('.animated-letter').forEach(el=>el.style.animationPlayState=paused?'paused':'running');$('#motion-toggle').textContent=paused?'▷':'Ⅱ';$('#motion-toggle').setAttribute('aria-pressed',String(paused));$('#motion-toggle').setAttribute('aria-label',paused?'Resume ambient motion':'Pause ambient motion')}
$('#motion-toggle').onclick=()=>{paused=!paused;updatePause()};reduced.addEventListener('change',e=>{paused=e.matches;updatePause()});updatePause();
function scrollToPhase(f){const s=$('#story');window.scrollTo({top:s.offsetTop+(s.offsetHeight-innerHeight)*f,behavior:reduced.matches?'instant':'smooth'})}
$('#assemble').onclick=()=>scrollToPhase(.28);$('#explode').onclick=()=>scrollToPhase(.93);
const storyState={progress:0,explosion:0};
function updateStory(){const section=$('#story'),progress=clamp(-section.getBoundingClientRect().top/(section.offsetHeight-innerHeight));storyState.progress=progress;storyState.explosion=smooth((progress-.27)/.63);const hero=1-smooth((progress-.02)/.2),chapter=smooth((progress-.14)/.13);$('#story-copy').style.opacity=hero;$('#story-copy').style.transform=`translateY(${-progress*70}px)`;$('#story-copy').style.visibility=hero<.01?'hidden':'visible';$('#chapter-copy').style.opacity=chapter;$('#model-mount').style.top=((innerWidth<700?24:20)+chapter*12)+'%';$('#chapter-copy').setAttribute('aria-hidden',chapter<.5?'true':'false');const exploded=progress>.5;$('#chapter-label').textContent=exploded?'EVERY PIECE HAS A PURPOSE':'01 / THE ASSEMBLY';$('#chapter-title').textContent=exploded?'Let it all come apart.':"Together, it’s Smart Robo.";$('#chapter-description').textContent=exploded?'Keep scrolling. The parts become a timeline.':'Your original design. A whole new energy.';$('#phase-label').textContent=exploded?'Follow the sparks':'Scroll to take it apart';$('#chapter-number').innerHTML=(exploded?'02':'01')+' <span>/ 03</span>';$('#journey-progress').style.width=progress*100+'%';$('#assemble').setAttribute('aria-pressed',String(!exploded));$('#explode').setAttribute('aria-pressed',String(exploded));}
window.addEventListener('scroll',updateStory,{passive:true});window.addEventListener('resize',()=>{updateStory();resize()});updateStory();
const colors=Object.fromEntries(['B01','B02','B03','B04','B05','B06','B07','B08','B09','B10','B10R','B11','B12','B13'].map(id=>[id,0xcbd0d7]));
function explosionFor(r){let v={B01:[0,-.05,.78],B02:[0,0,-.8],B03:[0,.5,.3],B04:[0,1.2,-1],B05:[0,.7,-.6],B06:[0,1.3,-.4],B07:[0,-.7,-.35],B08:[0,1.2,.45],B09:[0,1.15,-.7],B10:[0,1.05,1.5],B10R:[0,1.75,1.05],B12:[0,.1,-1.65]}[r.master];if(r.master==='B11')v=[r.bounds_mm[1]>0?1:-1,.2,.3];if(r.master==='B13')v=[r.bounds_mm[1]>0?.45:-.45,-.6,r.bounds_mm[0]>0?.55:-.6];return new THREE.Vector3(...v)}
function resize(){if(!renderer)return;const mount=activePart===null?$('#model-mount'):$('#detail-mount');const {width,height}=mount.getBoundingClientRect();if(!width||!height)return;renderer.setSize(width,height,false);camera.aspect=width/height;camera.updateProjectionMatrix()}
function partMeshes(id){return meshes.filter(m=>m.userData.group===id&&(id!=='B11'&&id!=='B13'||m.name===id))}
function setMaterials(){if(conceptHardware)conceptHardware.visible=false;if(robot)robot.scale.setScalar(1);for(const m of meshes){const mat=m.material;mat.opacity=1;mat.transparent=false;mat.depthWrite=true;m.visible=true;m.position.set(0,0,0)}}
function partBounds(id){const b=new THREE.Box3();for(const m of partMeshes(id)){m.geometry.computeBoundingBox();b.union(m.geometry.boundingBox)}return b}
function cameraForBox(b,aspect=1){const size=b.getSize(new THREE.Vector3()),radius=Math.max(size.length()/2,.1);return Math.max(radius/Math.sin(THREE.MathUtils.degToRad(35/2)),radius/(Math.sin(THREE.MathUtils.degToRad(35/2))*aspect))*1.08}
function resetDetailCamera(){if(activePart===null||!ready)return;const id=details[activePart].id,b=partBounds(id),center=b.getCenter(new THREE.Vector3());robot.position.copy(center).multiplyScalar(-1);robot.rotation.set(0,0,0);robot.userData.detailCenter=center.clone();const distance=cameraForBox(b,camera.aspect)*1.12;camera.position.set(.8,.48,1).normalize().multiplyScalar(distance);camera.lookAt(0,0,0);orbit.target.set(0,0,0);orbit.minDistance=distance*.35;orbit.maxDistance=distance*2.5;orbit.update()}
function showDetailGeometry(){if(!ready)return;setMaterials();const selected=partMeshes(details[activePart].id);for(const m of meshes)m.visible=selected.includes(m);resize();resetDetailCamera();detailAge=0}
function openPart(index){if(!$('#part-dialog').open)lastFocus=document.activeElement;activePart=(index+details.length)%details.length;const p=details[activePart],m=geometryData?.masters.find(x=>x.id===p.id);$('#part-id').textContent=p.id==='B10'?'B10 + B10R / FACE ASSEMBLY':p.id+' / '+p.category;$('#part-title').textContent=p.title;$('#part-description').textContent=p.description;$('#part-function').textContent=p.function;$('#part-fit').textContent=p.fit;$('#part-check').textContent=m?.remaining_uncertainty||'Geometry is still loading. See the supplied CAD audit for physical fit checks.';$('#part-specs').innerHTML=`<div><span>PART SIZE / MM</span><strong>${m?m.size_mm.map(n=>Number(n.toFixed(1))).join(' × '):'Loading…'}</strong></div><div><span>ASSEMBLY QUANTITY</span><strong>${p.id==='B10'?'1 visor + 1 carrier':m?m.quantity+' '+(m.quantity===1?'piece':'copies'):'—'}</strong></div>`;$('#part-pagination').textContent=String(activePart+1).padStart(2,'0')+' / 13';if(!$('#part-dialog').open){savedScroll=scrollY;$('#part-dialog').showModal();document.body.style.overflow='hidden';}if(renderer){$('#detail-mount').append(renderer.domElement);orbit.enabled=true;showDetailGeometry()}$('#detail-mount').setAttribute('aria-label',p.title+' CAD model');$('.detail-copy').scrollTop=0;$('.detail-layout').scrollTop=0;$('#announcement').textContent='Showing '+p.title;}
function closeDetail(){if(!$('#part-dialog').open)return;$('#part-dialog').close();}
$('#part-dialog').addEventListener('close',()=>{activePart=null;document.body.style.overflow='';if(renderer){$('#model-mount').append(renderer.domElement);orbit.enabled=false;setMaterials();robot.position.set(0,0,0);resize()}window.scrollTo({top:savedScroll,behavior:'instant'});lastFocus?.focus({preventScroll:true})});
$('#close-detail').onclick=closeDetail;$('#previous-part').onclick=()=>openPart(activePart-1);$('#next-part').onclick=()=>openPart(activePart+1);$('#reset-view').onclick=resetDetailCamera;
$('#part-dialog').addEventListener('keydown',e=>{if(e.target.matches('button,a,input'))return;if(e.key==='ArrowRight'){e.preventDefault();openPart(activePart+1)}if(e.key==='ArrowLeft'){e.preventDefault();openPart(activePart-1)}});
async function thumbnails(){const originalSize=renderer.getSize(new THREE.Vector2()),oldAspect=camera.aspect;renderer.setSize(480,320,false);camera.aspect=1.5;camera.updateProjectionMatrix();setMaterials();for(const p of details){const selected=partMeshes(p.id);for(const m of meshes)m.visible=selected.includes(m);const b=partBounds(p.id);robot.position.copy(b.getCenter(new THREE.Vector3())).multiplyScalar(-1);robot.rotation.set(0,0,0);const distance=cameraForBox(b,1.5);camera.position.set(.9,.55,1.2).normalize().multiplyScalar(distance);camera.lookAt(0,0,0);renderer.render(scene,camera);const image=new Image();image.className='part-thumb';image.alt='CAD geometry of '+p.title;image.width=480;image.height=320;image.src=renderer.domElement.toDataURL('image/png');$(`[data-part="${p.id}"] .card-placeholder`).replaceWith(image);await new Promise(resolve=>setTimeout(resolve,0));}setMaterials();robot.position.set(0,0,0);renderer.setSize(originalSize.x,originalSize.y,false);camera.aspect=oldAspect;camera.updateProjectionMatrix();}
let animationClock=0;
function introTravel(t){if(reduced.matches||storyState.progress>.03)return 0;return t<5?-.7*(1-smooth(t/5)):Math.sin((t-5)*.48)*.065}
function frame(time){
 if(document.hidden)return;const dt=Math.min((time-lastTime)/1000,.05)||.016;lastTime=time;if(!paused)animationClock+=dt;if(!ready)return;
 if(activePart!==null){detailAge+=dt;if(!reduced.matches&&detailAge<1.35){const scale=1+.12*(1-smooth(detailAge/1.35));robot.scale.setScalar(scale);robot.position.copy(robot.userData.detailCenter).multiplyScalar(-scale)}else{robot.scale.setScalar(1);robot.position.copy(robot.userData.detailCenter).multiplyScalar(-1)}orbit.update();renderer.render(scene,camera);return;}
 if($('#story').getBoundingClientRect().bottom<0)return;
 const e=storyState.explosion,t=animationClock;robot.scale.setScalar(1);
 // Fixed orientation: scrolling separates the parts but never turns the robot.
 robot.rotation.set(0,0,0);robot.position.set(0,0,introTravel(t));
 for(const m of meshes){m.visible=true;const target=m.userData.explode.clone().multiplyScalar(e);if(reduced.matches)m.position.copy(target);else m.position.lerp(target,1-Math.exp(-dt*4));m.material.opacity=1;m.material.transparent=false;m.material.depthWrite=true;}
 const distance=(innerWidth<700?7.2:6.2)+e*3.5;camera.position.set(.82,.37,1.25).normalize().multiplyScalar(distance);camera.position.y+=.67;camera.lookAt(0,.67,0);
 animateConcept(t,e,dt);renderer.render(scene,camera);
}
function silverStudio(){
 const studio=new THREE.Scene();studio.background=new THREE.Color('#444a54');
 const panel=(w,h,color,x,y,z)=>{const g=new THREE.PlaneGeometry(w,h),m=new THREE.MeshBasicMaterial({color,side:THREE.DoubleSide}),light=new THREE.Mesh(g,m);light.position.set(x,y,z);light.lookAt(0,0,0);studio.add(light)};
 panel(4,7,new THREE.Color('#ffffff').multiplyScalar(5),-4,3,3);panel(2,6,new THREE.Color('#e5edff').multiplyScalar(3),4,2,1);panel(6,3,new THREE.Color('#ffffff').multiplyScalar(4),0,5,-1);panel(3,6,'#06080b',1,0,-4);
 const pmrem=new THREE.PMREMGenerator(renderer),target=pmrem.fromScene(studio,.02);scene.environment=target.texture;scene.environmentIntensity=1.0;pmrem.dispose();for(const obj of studio.children){obj.geometry.dispose();obj.material.dispose()}
}
async function init(){try{const [metaResponse,binResponse]=await Promise.all([fetch('./assets/geometry.json'),fetch('./assets/robot.bin')]);if(!metaResponse.ok||!binResponse.ok)throw new Error('CAD asset request failed');geometryData=await metaResponse.json();const data=await binResponse.arrayBuffer();renderer=new THREE.WebGLRenderer({alpha:true,antialias:true,preserveDrawingBuffer:true,powerPreference:'high-performance'});renderer.setPixelRatio(Math.min(devicePixelRatio,1.75));renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.08;renderer.domElement.setAttribute('role','img');renderer.domElement.setAttribute('aria-label','Your Rover CAD assembly');scene=new THREE.Scene();silverStudio();camera=new THREE.PerspectiveCamera(35,1,.01,100);robot=new THREE.Group();scene.add(robot);scene.add(new THREE.HemisphereLight(0xf2f5ff,0x353b46,1.4));const key=new THREE.DirectionalLight(0xffffff,2.4);key.position.set(2,4,6);scene.add(key);const rim=new THREE.DirectionalLight(0xffffff,3.0);rim.position.set(-5,2,-3);scene.add(rim);const side=new THREE.DirectionalLight(0xdde8ff,1.6);side.position.set(4,1,-3);scene.add(side);for(const r of geometryData.instances){const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.BufferAttribute(new Float32Array(data,r.offset,r.vertices*3),3));g.computeVertexNormals();g.computeBoundingBox();const material=new THREE.MeshStandardMaterial({color:colors[r.master],metalness:.94,roughness:.20,side:THREE.DoubleSide});const m=new THREE.Mesh(g,material);m.name=r.id;m.userData={...r,explode:explosionFor(r)};robot.add(m);meshes.push(m)}$('#model-mount').append(renderer.domElement);resize();orbit=new OrbitControls(camera,renderer.domElement);orbit.enableDamping=true;orbit.enablePan=false;orbit.enabled=false;orbit.dampingFactor=.09;await thumbnails();createConceptHardware();resize();ready=true;animationClock=0;introStart=performance.now();$('#model-status').classList.add('hidden');if(activePart!==null)openPart(activePart);renderer.setAnimationLoop(frame);window.roverExperience={get state(){return {ready,instances:meshes.length,groups:details.length,activePart:activePart===null?null:details[activePart].id,explosion:storyState.explosion,paused,renderedTriangles:renderer.info.render.triangles}},render:()=>renderer.render(scene,camera)};}catch(error){console.error('Rover model loading failed:',error);$('#model-status').classList.add('error');$('#model-status').textContent='The 3D view could not load on this device. You can still explore every part below or open the control room.';for(const p of document.querySelectorAll('.card-placeholder'))p.textContent='Read part details';}}
window.addEventListener('beforeinstallprompt',e=>{e.preventDefault();deferredInstall=e});$('#install').onclick=async()=>{if(deferredInstall){await deferredInstall.prompt();await deferredInstall.userChoice;deferredInstall=null}else $('#install-dialog').showModal()};$('#close-install').onclick=$('#install-done').onclick=()=>$('#install-dialog').close();window.addEventListener('appinstalled',()=>{deferredInstall=null});
if('serviceWorker' in navigator&&window.isSecureContext)window.addEventListener('load',()=>navigator.serviceWorker.register('./sw.js').catch(()=>{}));


// Scroll through a floating three-dimensional stack, using the same thirteen CAD cards.
let timelineIndex=0,orbitProgress=0,orbitVisible=false,orbitTime=0,orbitLast=0;
const timelineCards=[...grid.children],partsSection=$('#parts');
const cardTints=['#ffc28d','#b6a1fc','#74cbbf','#c4dbe2','#8dcde3','#e7ae7e','#a1b5d0','#dfb7e6','#b4e3d3','#93caca','#d6b4ff','#9faedd','#b1d6df'];
timelineCards.forEach((card,i)=>card.style.setProperty('--card-tint',cardTints[i]));
function updateTimeline(){
 const bounds=partsSection.getBoundingClientRect();orbitVisible=bounds.top<innerHeight&&bounds.bottom>0;
 if(reduced.matches){
  let distance=Infinity;timelineCards.forEach((card,i)=>{card.style.transform='none';card.style.opacity='1';card.style.visibility='visible';card.style.pointerEvents='auto';card.tabIndex=0;card.removeAttribute('aria-hidden');const d=Math.abs(card.getBoundingClientRect().top+card.offsetHeight/2-innerHeight*.5);if(d<distance){distance=d;timelineIndex=i}});
 }else{
  const length=partsSection.offsetHeight-innerHeight;orbitProgress=clamp(-bounds.top/length)*12;timelineIndex=Math.round(orbitProgress);renderOrbitCards();
 }
 timelineCards.forEach((card,i)=>{card.classList.toggle('active',i===timelineIndex);card.setAttribute('aria-current',i===timelineIndex?'step':'false')});
 $('#timeline-count').textContent=String(timelineIndex+1).padStart(2,'0')+' / 13';$('#timeline-current').textContent=details[timelineIndex].title;$('#timeline-range').value=timelineIndex;$('#rail-progress').style.width=(timelineIndex/12*100)+'%';
 $('#timeline-prev').disabled=timelineIndex===0;$('#timeline-next').disabled=timelineIndex===12;
 $('#orbit-motion').textContent=paused?'Resume motion ▷':'Pause motion Ⅱ';$('#orbit-motion').setAttribute('aria-label',paused?'Resume ambient motion':'Pause ambient motion');
 document.body.classList.toggle('in-timeline',bounds.top<innerHeight*.25&&bounds.bottom>innerHeight*.6);
}
function renderOrbitCards(){
 const mobile=innerWidth<700,orbitWidth=mobile?innerWidth*.56:Math.min(innerWidth*.36,470);
 timelineCards.forEach((card,i)=>{
  const d=i-orbitProgress,abs=Math.abs(d),visible=abs<2.7;
  card.style.visibility=visible?'visible':'hidden';card.setAttribute('aria-hidden',visible?'false':'true');card.tabIndex=i===timelineIndex?0:-1;card.style.pointerEvents=abs<1.35?'auto':'none';
  if(!visible)return;
  const angle=d*1.22+.16,x=(Math.sin(angle)-(mobile?Math.sin(.16):0))*orbitWidth,y=d*(mobile?210:245)+Math.sin(orbitTime*.5+i)*5,z=(mobile?0:65)-abs*(mobile?380:345);
  card.style.transform=`translate(-50%,-50%) translate3d(${x}px,${y}px,${z}px) rotateY(${-Math.sin(angle)*22}deg) rotateX(${clamp(d,-2,2)*-4}deg) rotateZ(${Math.sin(d)*-4}deg)`;
  card.style.opacity=String(clamp(1-abs*.29,.12,1));card.style.zIndex=String(100-Math.round(abs*20));
 });
}
function goTimeline(index,instant=false){
 index=clamp(index,0,12);const bounds=partsSection.getBoundingClientRect();
 const top=reduced.matches?scrollY+timelineCards[index].getBoundingClientRect().top-90:scrollY+bounds.top+(partsSection.offsetHeight-innerHeight)*index/12;
 window.scrollTo({top,behavior:instant||reduced.matches?'instant':'smooth'});
}
$('#timeline-prev').onclick=()=>goTimeline(timelineIndex-1);$('#timeline-next').onclick=()=>goTimeline(timelineIndex+1);$('#timeline-range').oninput=e=>goTimeline(Number(e.target.value),true);
$('#orbit-motion').onclick=()=>{paused=!paused;updatePause();updateTimeline()};
for(const [i,card] of timelineCards.entries())card.addEventListener('focus',()=>{if(!$('#part-dialog').open&&i!==timelineIndex)goTimeline(i,true)});
partsSection.addEventListener('keydown',e=>{if(e.target.matches('input')||$('#part-dialog').open)return;if(['ArrowDown','ArrowRight','ArrowUp','ArrowLeft'].includes(e.key)){e.preventDefault();goTimeline(timelineIndex+(['ArrowDown','ArrowRight'].includes(e.key)?1:-1))}});
let orbitQueued=false;addEventListener('scroll',()=>{if(!orbitQueued){orbitQueued=true;requestAnimationFrame(()=>{updateTimeline();orbitQueued=false})}},{passive:true});addEventListener('resize',updateTimeline);reduced.addEventListener('change',updateTimeline);updateTimeline();

// A luminous particle ribbon behind the cards; no substitute robot geometry.
let particleRenderer,particleScene,particleCamera,particleSculpture,particleDust;
function createOrbitParticles(){
 try{
  particleRenderer=new THREE.WebGLRenderer({canvas:$('#orbit-particles'),alpha:true,antialias:false,powerPreference:'low-power'});particleRenderer.setPixelRatio(Math.min(devicePixelRatio,1.5));
  particleScene=new THREE.Scene();particleCamera=new THREE.PerspectiveCamera(45,1,.1,50);particleCamera.position.set(0,0,10);
  const n=innerWidth<700?3600:6500,positions=new Float32Array(n*3),colors=new Float32Array(n*3);const palette=[new THREE.Color('#9c75ff'),new THREE.Color('#64cfda'),new THREE.Color('#efa77c'),new THREE.Color('#e08edf')];
  const noise=i=>{const v=Math.sin(i*127.1+31.7)*43758.5453;return v-Math.floor(v)};
  for(let i=0;i<n;i++){
   const h=noise(i+9)*11-5.5,angle=h*1.95+(i%2)*Math.PI+noise(i+50)*.5,radius=1.15+Math.sin(h*1.5)*.28+(noise(i+90)-.5)*.86;
   positions[i*3]=Math.cos(angle)*radius+(noise(i+80)-.5)*.23;positions[i*3+1]=h;positions[i*3+2]=Math.sin(angle)*radius;
   const color=palette[Math.floor((h+5.5)/2.75)%4].clone().lerp(new THREE.Color('#ffffff'),noise(i+130)*.18).multiplyScalar(1.65);color.toArray(colors,i*3);
  }
  const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.BufferAttribute(positions,3));g.setAttribute('color',new THREE.BufferAttribute(colors,3));
  const sprite=document.createElement('canvas');sprite.width=sprite.height=32;const c=sprite.getContext('2d'),gradient=c.createRadialGradient(16,16,0,16,16,16);gradient.addColorStop(0,'#fff');gradient.addColorStop(.2,'#ffffffe0');gradient.addColorStop(1,'#ffffff00');c.fillStyle=gradient;c.fillRect(0,0,32,32);
  const texture=new THREE.CanvasTexture(sprite),material=new THREE.PointsMaterial({size:.095,map:texture,vertexColors:true,transparent:true,opacity:.88,depthWrite:false,blending:THREE.AdditiveBlending});
  particleSculpture=new THREE.Points(g,material);particleSculpture.rotation.z=-.12;particleScene.add(particleSculpture);
  const dustPositions=new Float32Array(450*3);for(let i=0;i<450;i++){dustPositions[i*3]=(noise(i+200)-.5)*15;dustPositions[i*3+1]=(noise(i+300)-.5)*12;dustPositions[i*3+2]=-3-noise(i+400)*4}
  const dustG=new THREE.BufferGeometry();dustG.setAttribute('position',new THREE.BufferAttribute(dustPositions,3));particleDust=new THREE.Points(dustG,new THREE.PointsMaterial({map:texture,color:'#9fb3dc',size:.024,transparent:true,opacity:.45,depthWrite:false}));particleScene.add(particleDust);
  const resizeParticles=()=>{const r=$('.timeline-stage').getBoundingClientRect();particleRenderer.setSize(r.width,r.height,false);particleCamera.aspect=r.width/r.height;particleCamera.position.z=innerWidth<700?12:10;particleCamera.updateProjectionMatrix()};addEventListener('resize',resizeParticles);resizeParticles();
 }catch(error){console.warn('Particle background unavailable; CAD cards remain available.');$('#orbit-particles').hidden=true}
}
createOrbitParticles();
function animateOrbit(now){
 requestAnimationFrame(animateOrbit);const dt=Math.min((now-orbitLast)/1000,.05)||.016;orbitLast=now;
 if(!orbitVisible||document.hidden||$('#part-dialog').open)return;
 if(!paused&&!reduced.matches)orbitTime+=dt;
 if(!reduced.matches)renderOrbitCards();
 if(particleRenderer){particleSculpture.rotation.y=orbitTime*.09+orbitProgress*.34;particleSculpture.position.y=Math.sin(orbitTime*.22)*.09;particleDust.rotation.z=orbitTime*.007;particleRenderer.render(particleScene,particleCamera)}
}
requestAnimationFrame(animateOrbit);

// Concept hardware is a removable visual layer, separate from the verified CAD meshes.
let conceptHardware=null, driveWheels=[], faceAssembly=null, oledContext=null, oledTexture=null;
let helloAt=-100,lastOledFrame=-1;
function hardwareMesh(geometry,color,metalness=.25,roughness=.4){return new THREE.Mesh(geometry,new THREE.MeshStandardMaterial({color,metalness,roughness}))}
function createConceptHardware(){
 conceptHardware=new THREE.Group();conceptHardware.name='Illustrative hardware — fit unverified';robot.add(conceptHardware);
 const plate=hardwareMesh(new THREE.BoxGeometry(1.48,.03,2.55),0xaab1bc,.9,.23);plate.position.y=-.015;conceptHardware.add(plate);
 // Four matching wheels on two axles; illustrative dimensions only.
 for(const sign of [-1,1])for(const axle of [-.77,.77]){
  const wheel=new THREE.Group();wheel.name=`${sign<0?"Left":"Right"} ${axle>0?"front":"rear"} wheel`;wheel.userData={side:sign,axle};wheel.position.set(sign*.86,-.09,axle);conceptHardware.add(wheel);driveWheels.push(wheel);
  const tire=hardwareMesh(new THREE.CylinderGeometry(.315,.315,.205,64),0x13191e,.08,.83);tire.rotation.z=Math.PI/2;wheel.add(tire);
  for(let j=0;j<24;j++){const a=j/24*Math.PI*2;const tread=hardwareMesh(new THREE.BoxGeometry(.208,.028,.07),0x212a30,.05,.9);tread.position.set(0,.315*Math.cos(a),.315*Math.sin(a));tread.rotation.x=a;wheel.add(tread)}
  for(const side of [-1,1]){
   const hub=hardwareMesh(new THREE.CylinderGeometry(.21,.21,.015,48),0xdde2e8,.95,.16);hub.rotation.z=Math.PI/2;hub.position.x=side*.109;wheel.add(hub);
   const center=hardwareMesh(new THREE.CylinderGeometry(.095,.095,.026,32),0xbcc3cd,.94,.22);center.rotation.z=Math.PI/2;center.position.x=side*.12;wheel.add(center);
   const trim=hardwareMesh(new THREE.TorusGeometry(.215,.012,8,48),0xe4e9ee,.98,.13);trim.rotation.y=Math.PI/2;trim.position.x=side*.12;wheel.add(trim);
   for(let j=0;j<6;j++){const a=j/6*Math.PI*2;const bolt=hardwareMesh(new THREE.SphereGeometry(.018,8,6),0xaab2bd,.9,.2);bolt.position.set(side*.122,.15*Math.cos(a),.15*Math.sin(a));wheel.add(bolt)}
  }
 }
 faceAssembly=new THREE.Group();conceptHardware.add(faceAssembly);
 // The supplied OLED aperture is 24.7 x 14.2 mm, centred at CAD Y0/Z161.75.
 const glass=hardwareMesh(new THREE.BoxGeometry(.246,.142,.012),0x061318,.2,.17);glass.position.set(0,1.6175,1.01);faceAssembly.add(glass);
 const oled=document.createElement('canvas');oled.width=256;oled.height=144;oledContext=oled.getContext('2d');oledTexture=new THREE.CanvasTexture(oled);oledTexture.colorSpace=THREE.SRGBColorSpace;
 const screen=new THREE.Mesh(new THREE.PlaneGeometry(.235,.130),new THREE.MeshBasicMaterial({map:oledTexture,toneMapped:false}));screen.name='Single OLED display';screen.position.set(0,1.6175,1.017);faceAssembly.add(screen);
 // Nominal ultrasonic modules populate the two front openings.
 for(const middle of [-.27,.27]){
  const board=hardwareMesh(new THREE.BoxGeometry(.445,.196,.02),0xaeb5c0,.85,.24);board.position.set(middle,1.32,1.003);faceAssembly.add(board);
  for(const offset of [-.135,.135]){
   const barrel=hardwareMesh(new THREE.CylinderGeometry(.077,.077,.10,32),0xb8c8cb,.82,.24);barrel.rotation.x=Math.PI/2;barrel.position.set(middle+offset,1.32,1.065);faceAssembly.add(barrel);
   const disk=hardwareMesh(new THREE.CylinderGeometry(.061,.061,.006,32),0x23343c,.4,.6);disk.rotation.x=Math.PI/2;disk.position.set(middle+offset,1.32,1.119);faceAssembly.add(disk);
   for(let n=-2;n<=2;n++){const grille=hardwareMesh(new THREE.BoxGeometry(.099,.003,.003),0xc1c8d0,.9,.22);grille.position.set(middle+offset,1.32+n*.016,1.123);faceAssembly.add(grille)}
  }
 }
 for(const x of [-.445,-.355,.355,.445]){const led=new THREE.Mesh(new THREE.SphereGeometry(.020,12,8),new THREE.MeshStandardMaterial({color:0xd9edff,emissive:0x77bfff,emissiveIntensity:.8,roughness:.25}));led.position.set(x,1.635,1.012);faceAssembly.add(led)}
 drawOled(0);
}
function drawOled(t){
 if(!oledContext)return;const ctx=oledContext;ctx.fillStyle='#030c12';ctx.fillRect(0,0,256,144);
 const names=['Curious','Happy','Surprised','Sleepy'],cycle=(t%20),phase=Math.floor(cycle/5),mood=t-helloAt<5?'Happy':names[reduced.matches?0:phase];
 const blinkAt=(at,width)=>Math.max(0,1-Math.abs(t%13.7-at)/width),blink=Math.max(blinkAt(3.1,.13),blinkAt(8.7,.15),blinkAt(9.05,.1));
 const gaze=mood==='Curious'?Math.sin(t*.8)*9:0;ctx.fillStyle='#b4edff';ctx.strokeStyle='#b4edff';ctx.shadowColor='#51bfff';ctx.shadowBlur=14;
 const transition=1-.65*Math.pow(Math.max(0,1-(cycle%5)/.28),2);
 for(const [i,x] of [77,177].entries()){
  ctx.save();ctx.translate(x+gaze,62);ctx.scale(1,transition*(1-blink*.92));ctx.beginPath();
  if(mood==='Happy'){ctx.lineWidth=10;ctx.lineCap='round';ctx.arc(0,7,18,Math.PI,2*Math.PI);ctx.stroke()}
  else{const height=mood==='Sleepy'?9:mood==='Surprised'?57:i===0?37:48;ctx.roundRect(-18,-height/2,36,height,mood==='Surprised'?18:Math.min(12,height/2));ctx.fill()}
  ctx.restore();
 }
 if(mood==='Happy'){ctx.lineWidth=5;ctx.beginPath();ctx.arc(128,88,16,0,Math.PI);ctx.stroke()}
 if(mood==='Surprised'){ctx.beginPath();ctx.ellipse(128,106,7,9,0,0,Math.PI*2);ctx.fill()}
 ctx.shadowBlur=0;oledTexture.needsUpdate=true;
 const badge=$('#intro-mood');if(badge&&badge.textContent!==mood+' · OLED expression')badge.textContent=mood+' · OLED expression';
}
function animateConcept(t,e,dt){
 if(!conceptHardware)return;conceptHardware.visible=true;
 const b10=meshes.find(m=>m.name==='B10');faceAssembly.position.copy(b10.position);
 for(const wheel of driveWheels){wheel.position.x=wheel.userData.side*(.86+e*.45);wheel.position.y=-.09-e*.25;wheel.position.z=wheel.userData.axle*(1+e*.3);wheel.rotation.x=-introTravel(t)/.315*(1-e)}
 const frame=Math.floor(t*24);if(frame!==lastOledFrame){drawOled(t);lastOledFrame=frame}
}
$('#say-hello').onclick=()=>{helloAt=animationClock;drawOled(animationClock);$('#announcement').textContent='Rover says hello with smiling OLED eyes.'};
init();
