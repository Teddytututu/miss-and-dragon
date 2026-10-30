/* Match note colours to the rendered row and column after every layout change. */
(() => {
 const paper=document.querySelector('#todo .card');if(!paper)return;
 let frame;
 const paint=()=>{
  cancelAnimationFrame(frame);frame=requestAnimationFrame(()=>{
   const columns=getComputedStyle(paper).gridTemplateColumns.split(/\s+/).filter(Boolean).length||1;
   const pink=document.documentElement.classList.contains('theme-pink');
   const colors=pink?['#fff7df','#fff0f5','#eaf3ff']:['#eaf3ff','#fff7df','#eef5ef'];
   [...paper.querySelectorAll('.todo-item')].forEach((note,index)=>note.style.setProperty('--note-paper',colors[(Math.floor(index/columns)+index%columns)%colors.length]));
  });
 };
 new MutationObserver(paint).observe(paper,{childList:true,subtree:true});
 new ResizeObserver(paint).observe(paper);window.addEventListener('themechange',paint);paint();
})();
