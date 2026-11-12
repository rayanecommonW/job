#!/usr/bin/env python3
"""Agent-tailored CV for one application, without an LLM API.

  tailor-cv.py start <id>   copy the category CV's LaTeX source to <app>/cv.tex
  (edit <app>/cv.tex for the posting, following job-search/cv-tailoring-policy.md)
  tailor-cv.py finish <id>  build, check one page, record provenance

Run after reuse-reviewed-cv.py has scaffolded the application folder.
"""
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

root = Path(__file__).resolve().parents[1]
mode, app_id = sys.argv[1], sys.argv[2]
app = root / 'job-search/applications' / app_id
assert app.parent == root / 'job-search/applications' and app.is_dir(), 'run reuse-reviewed-cv.py first'
provenance_path = app / 'cv-provenance.json'
provenance = json.loads(provenance_path.read_text())

if mode == 'start':
    before_note = app / 'vita-cv-before-note.pdf'
    if before_note.exists():
        # Prepared earlier with a category CV and note: drop the note page, tailor, then re-append the note.
        assert '--redo' in sys.argv, 'note already appended; pass --redo to tailor and re-append it afterwards'
        verification = json.loads((app / 'verification.json').read_text())
        assert not verification.get('submitted')
        import yaml
        name = yaml.safe_load((root / 'profile.yaml').read_text())['identity']['name']
        (app / f"{name.replace(' ', '_')}_CV.pdf").write_bytes(before_note.read_bytes())
        before_note.unlink()
    source = root / 'job-search/applications' / provenance['source_application'] / 'cv.tex'
    if not source.exists():
        source = root / 'cv-workspace/main.tex'
    (app / 'cv.tex').write_text(source.read_text())
    (app / 'cv-base.tex').write_text(source.read_text())
    print(f'{app / "cv.tex"} (base: {source.relative_to(root)})')
elif mode == 'finish':
    tex = (app / 'cv.tex').read_text()
    assert tex != (app / 'cv-base.tex').read_text(), 'cv.tex is unchanged; tailor it to the posting'
    import re
    assert '\\write18' not in tex and not re.search(r'\\(input|include)\{(?!glyphtounicode\})', tex), 'no external inputs'
    subprocess.run([sys.executable, str(root / 'scripts/rebuild-reviewed-cv.py'), app_id], check=True)
    provenance.update(cv_mode='agent-tailored', unchanged_pdf=False, tailored_on=date.today().isoformat(),
                      tailoring='Agent edited the category LaTeX for this posting under job-search/cv-tailoring-policy.md')
    provenance_path.write_text(json.dumps(provenance, indent=2, ensure_ascii=False) + '\n')
    meta_path = app / 'metadata.json'
    meta = json.loads(meta_path.read_text())
    meta['cv_mode'] = 'agent-tailored'
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + '\n')
    (app / 'review.md').write_text('Posting-specific CV: agent-tailored from ' + provenance['source_application'] +
                                   ' (diff: cv-base.tex -> cv.tex). Check cv-text.txt and cv-preview.png for facts and layout.\n')
else:
    raise SystemExit(__doc__)
