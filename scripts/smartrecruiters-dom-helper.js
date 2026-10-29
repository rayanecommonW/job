/* Evaluate in an inspected SmartRecruiters form. Uses visible form DOM only. */
({
  inspect() {
    const controls=[];
    function walk(root) { for(const el of root.querySelectorAll('*')) {
      if(el.matches('spl-input,spl-textarea,spl-checkbox')) controls.push({tag:el.tagName,id:el.id,label:el.getAttribute('label'),required:el.hasAttribute('required'),value:el.value});
      if(el.shadowRoot) walk(el.shadowRoot);
    }}
    walk(document);
    return {url:location.href,text:document.body.innerText,controls};
  },
  fill(values) {
    return Object.entries(values).map(([id,value])=>{
      const host=document.querySelector('[id="'+id+'"]');
      const el=host?.shadowRoot?.querySelector('input,textarea');
      if(!el) throw Error('Missing inspected control '+id);
      el.focus();
      Object.getOwnPropertyDescriptor(el.tagName==='TEXTAREA'?HTMLTextAreaElement.prototype:HTMLInputElement.prototype,'value').set.call(el,value);
      el.dispatchEvent(new Event('input',{bubbles:true,composed:true}));
      el.dispatchEvent(new Event('change',{bubbles:true,composed:true}));
      el.blur();
      return {id,value:el.value};
    });
  },
  searchParis() {
    const host=document.querySelector('spl-autocomplete[data-test="location-autocomplete"]');
    const el=host.shadowRoot.querySelector('spl-input').shadowRoot.querySelector('input');
    el.focus();Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(el,'Paris');
    el.dispatchEvent(new Event('input',{bubbles:true,composed:true}));
  },
  parisOptions() {
    return [...document.querySelector('spl-autocomplete[data-test="location-autocomplete"]').shadowRoot.querySelectorAll('spl-select-option')].map(el=>({value:el.getAttribute('value'),text:el.textContent.trim()}));
  },
  selectInspectedParis(value) {
    const el=[...document.querySelector('spl-autocomplete[data-test="location-autocomplete"]').shadowRoot.querySelectorAll('spl-select-option')].find(el=>el.getAttribute('value')===value);
    if(!el||!el.textContent.includes('France')) throw Error('Unverified Paris option');
    el.click();
  }
})
