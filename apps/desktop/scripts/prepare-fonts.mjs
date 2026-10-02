import {mkdir,copyFile} from 'node:fs/promises';
const dest=new URL('../src/fonts/',import.meta.url);
await mkdir(dest,{recursive:true});
for(const name of ['Carlito-Regular.ttf','Carlito-Bold.ttf','OFL.txt'])await copyFile(new URL(`../../../assets/fonts/${name}`,import.meta.url),new URL(name,dest));
