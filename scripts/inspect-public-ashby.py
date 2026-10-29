#!/usr/bin/env python3
"""Inspect a public form only when the T3 browser reports no connected host."""
import json,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
url=sys.argv[1];dest=Path(sys.argv[2])
with sync_playwright() as p:
 b=p.chromium.launch(headless=True);page=b.new_page();page.goto(url,wait_until='domcontentloaded');page.wait_for_timeout(1400)
 data=page.evaluate('''()=>({url:location.href,text:document.body.innerText,links:[...document.querySelectorAll('a')].map(x=>({text:x.innerText,url:x.href})),inputs:[...document.querySelectorAll('input,textarea,select')].map(x=>({id:x.id,type:x.type,name:x.name,required:x.required,value:x.value,options:x.tagName==='SELECT'?[...x.options].map(o=>({value:o.value,text:o.text})):undefined})),labels:[...document.querySelectorAll('label')].map(x=>({for:x.htmlFor,text:x.innerText})),buttons:[...document.querySelectorAll('button')].map(x=>({text:x.innerText,type:x.type}))})''')
 dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(data,indent=2));print(json.dumps(data,indent=2));b.close()
