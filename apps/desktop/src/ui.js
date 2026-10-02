export const escapeHtml = value => String(value).replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
export function moveSlide(story,index,direction){const target=index+direction;if(target<0||target>=story.presentation.slides.length)return false;[story.presentation.slides[index],story.presentation.slides[target]]=[story.presentation.slides[target],story.presentation.slides[index]];return true;}
export function duplicateSlide(story,index,id){const slide=structuredClone(story.presentation.slides[index]);slide.id=id;story.presentation.slides.splice(index+1,0,slide);}
export function isEditor(element){return element?.matches('input,textarea,select,[contenteditable="true"]')??false;}
