// Check authored visible tokens per slide after a real office renderer imported the deck.
import {readFileSync} from 'node:fs';
import {execFileSync} from 'node:child_process';
const [storyPath,pdfPath]=process.argv.slice(2);
if(!storyPath||!pdfPath)throw new Error('Usage: node scripts/native/validate-pdf.mjs story.json rendered.pdf');
const story=JSON.parse(readFileSync(storyPath,'utf8'));
const pages=execFileSync('pdftotext',['-layout',pdfPath,'-'],{encoding:'utf8'}).split('\f').filter(s=>s.trim());
const tokens=s=>String(s).toLowerCase().match(/[\p{L}\p{N}]+/gu)??[];
const text=b=>b.type==='text'?b.text.paragraphs.map(p=>p.runs.map(r=>r.text).join('')).join('\n'):b.type==='card'||b.type==='callout'?`${b.title} ${b.body}`:b.type==='heading'?b.text:b.type==='quote'?`${b.text} ${b.attribution}`:b.type==='metric'?`${b.value} ${b.label} ${b.context}`:b.type==='table'?[...b.table.columns,...b.table.rows.flat()].join(' '):b.type==='group'?b.children.map(text).join(' '):b.type==='positioned'?text(b.block):'';
if(pages.length!==story.presentation.slides.length)throw new Error(`Page count mismatch: ${pages.length}`);
const results=story.presentation.slides.map((slide,i)=>{const available=new Map();for(const token of tokens(pages[i]))available.set(token,(available.get(token)??0)+1);const expected=tokens([slide.title,...slide.blocks.map(text)].join(' '));const missing=[];for(const token of expected){const count=available.get(token)??0;if(!count)missing.push(token);else available.set(token,count-1);}return{slide:i+1,expected_tokens:expected.length,missing_tokens:missing,passed:missing.length===0};});
console.log(JSON.stringify({scope:'Per-slide visible authored token preservation after office PDF import. Does not prove editability or exact geometric parity.',slides:results},null,2));
if(results.some(r=>!r.passed))process.exitCode=1;
