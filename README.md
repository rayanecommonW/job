# Career automation

A setup for running a job search with a coding agent such as Claude Code or
Codex. The agent builds a queue of postings, writes a tailored CV for each
one, fills the forms in a real browser, and counts an application only once
the site shows a receipt.

## Getting started

Clone the repo and open it in your agent. It reads `AGENTS.md`, sees that your
profile is missing, and walks you through `INITIALIZE.md`. Expect questions
about your background, where you can work, and what you're looking for.

Your answers land in gitignored files (`profile.yaml`, `AGENTS.local.md`,
`job-search/`), so you can pull updates without mixing your data into the
repo.

## What's here

- `AGENTS.md`: rules every agent follows.
- `INITIALIZE.md`: first-run setup.
- `scripts/`: sourcing from public job feeds (Ashby, Greenhouse, Lever,
  Recruitee, The Hub, YC, Arbeitnow), queue filtering, receipt recording,
  browser helpers, and the `vita` wrapper for CV builds.
- `scripts/requirements-cv.txt`: Python dependencies for CV generation.

Many scripts in `scripts/` were written for one campaign. They have hardcoded
paths, dates or batch numbers. Read a script before you run it.

## Privacy

`.gitignore` blocks every top-level path except the ones listed in it. Scripts
that held personal details are excluded by name. Before you push, grep the
tracked files for your name, email and phone number.
