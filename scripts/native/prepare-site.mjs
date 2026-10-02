// Assemble a portable site from current native artifacts; no build framework.
import {readFile,mkdir,copyFile,cp,rm,writeFile,readdir} from 'node:fs/promises';
import {execFileSync} from 'node:child_process';import {fileURLToPath} from 'node:url';import {join} from 'node:path';
const root=fileURLToPath(new URL('../../',import.meta.url));const binary=join(root,'target/release/storyboard');
const assets=join(root,'site/assets');await mkdir(assets,{recursive:true});
for(const [source,name] of [['assets/logo.svg','logo.svg'],['assets/fonts/Carlito-Regular.ttf','Carlito-Regular.ttf'],['assets/fonts/Carlito-Bold.ttf','Carlito-Bold.ttf'],['assets/fonts/OFL.txt','OFL.txt'],['docs/screenshots/native/doctor.png','doctor.png']])await copyFile(join(root,source),join(assets,name));
for(const name of await readdir(assets))if(!['logo.svg','Carlito-Regular.ttf','Carlito-Bold.ttf','OFL.txt','doctor.png'].includes(name))await rm(join(assets,name));
const catalog=JSON.parse(await readFile(join(root,'gallery/native/catalog.json'),'utf8'));await cp(join(root,'gallery/native'),join(root,'site/gallery'),{recursive:true});
for(const example of catalog.examples){const folder=join(root,'gallery/native',example.id);for(const name of await readdir(folder))if(/^slide-\d+\.svg$/.test(name)){const index=Number(name.match(/\d+/)[0]);execFileSync(binary,['preview',join(folder,'deck.story.json'),'--svg','--slide',String(index),'-o',join(folder,name),'--force'],{stdio:'pipe'});await copyFile(join(folder,name),join(root,'site/gallery',example.id,name));}}
for(let index=1;index<=9;index++)execFileSync(binary,['preview',join(root,'gallery/native/startup-pitch/deck.story.json'),'--svg','--slide',String(index),'-o',join(root,'site/gallery/startup-pitch',`slide-${String(index).padStart(2,'0')}.svg`),'--force'],{stdio:'pipe'});
await writeFile(join(root,'site/themes.json'),execFileSync(binary,['themes','--json']));
console.log(`Prepared ${catalog.examples.length} native examples, current SVG previews, fonts and real desktop evidence.`);
