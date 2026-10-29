# Initialize

Agent: you're here because `AGENTS.local.md` or `profile.yaml` is missing.
This is a fresh clone. Your job is to interview the user, then create their
private files. Don't search for jobs or open application forms until every
step below is done and the user has said go.

Everything you create here is gitignored. Check with `git status` at the end.
None of it should show up.

## 1. Ask about the person

Ask a few questions at a time, not all thirty at once. Write down answers as
you go. If the user doesn't know or won't say, record it as unknown. Never
fill a gap with a guess.

Start by asking for an existing CV or LinkedIn export. Pull what you can from
it, then ask only about what's missing or unclear.

Identity and contact:
- Full name, preferred name, email, phone.
- City and country of residence. Skip the full address unless they want it
  used.
- Links: LinkedIn, GitHub, portfolio.

Work rights:
- Citizenship, and where they can legally work today.
- Where they'd relocate. Keep this separate from where they can work.
- Do they need visa sponsorship, and for which countries?

Background:
- Each job: title, employer, location, real start and end dates, what they
  built, and results they can back up.
- Projects worth citing. For each one, ask what is shipped, what is a
  prototype, and what is only planned.
- Education. Ask whether they want dates shown.
- Languages and honest levels.
- Anything on the CV they don't want repeated in applications.

## 2. Ask about the search

- Which roles? Titles, seniority, role families to exclude.
- Which countries and cities? Is remote OK, and remote from where?
- Hard bans: countries, employers, tech stacks.
- Salary floor and target, with currency. Gross or net.
- Company size and stage they prefer.
- How many applications, and is there a deadline?
- Which job boards they already have accounts on.
- Can the agent sign in with Google or LinkedIn? Can it accept cookie
  prompts? Can it read email, and only for verification codes?
- Which browser profile should the agent drive?
- Should the agent ever message recruiters? The default is no.
- Are any parallel agents planned? If so, how should countries be split
  between them?

## 3. Create the files

Write these from the answers. Show the user each one and ask them to correct
it before moving on.

`profile.yaml` holds facts only. Suggested top-level keys:

```yaml
identity:          # name, email, phone, city, country, links
availability:      # start date, notice period, if known
work_rights:       # citizenship, permits, sponsorship needs
relocation:        # willing destinations, kept apart from work_rights
background_summary: >-
experience:        # list of jobs, each with title, employer, dates, location, bullets
projects:          # each with status: shipped | prototype | planned
education:
languages:
skills:
source_notes:      # where each claim came from, and any caveats
```

`AGENTS.local.md` holds the user's own rules: target locations, banned
employers and countries, salary band, role filters, browser profile, and
anything else personal. It overrides `AGENTS.md`.

`job-search/preferences.md` holds search preferences and stock answers to
common screening questions, as long as the profile supports them.

`START-HERE.md` is a short status line: paused or active, counts, what's next.

Campaign state goes in `job-search/`:

- `jobboards-state.json`: start with
  `{"status": "paused", "confirmed_applications_cumulative": 0, "pending_applications": []}`.
- `session-handoff.md`: notes for the next session. It can start empty.
- `applications.md`: the tracker, with this header:

  ```
  | ID | Company | Role | Job URL or posting ID | Status | Submitted on | CV file | Next follow-up | Notes or confirmation |
  | --- | --- | --- | --- | --- | --- | --- | --- | --- |
  ```

- `applications.json`: `[]`. Same columns as the tracker, as `id`,
  `company`, `role`, `url`, `status`, `submitted_on`, `cv`, `follow_up`,
  `notes`.
- `browser-url-registry.json`: `{}`.
- `applications/` and `history/`: empty folders.

If they want parallel agents, write `parralel-agents.md` with one row per
agent and its scope.

## 4. Set up CV generation

```sh
python3 -m venv .venv
.venv/bin/pip install -r scripts/requirements-cv.txt
```

VITA needs a LaTeX install. Either have one on `PATH`, or install TinyTeX
under `.toolchains/TinyTeX`. Then create `cv-workspace/` with a `main.tex`
template and run `scripts/vita init`, or follow VITA's README. Build one CV,
open the PDF, and go through it with the user line by line.

## 5. Check and hand over

- Run `git status`. No personal file should be listed. If one is, add it to
  `.gitignore` before anything else.
- Sum up what you set up and anything still unknown.
- Ask whether to start searching, or leave the campaign paused.

## Scripts that aren't in the repo

Some of the original helper scripts hardcoded one person's details, so they
were left out. They covered form filling for Greenhouse, Ashby, SmartRecruiters,
Teamtailor and Welcome to the Jungle, plus note and cover letter export. When
you need one, write it fresh and read identity fields from `profile.yaml`.
That way it can be committed.
