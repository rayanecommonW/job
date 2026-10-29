#!/usr/bin/env python3
"""Read complete public startup/scaleup ATS feeds, retaining coverage evidence."""
import concurrent.futures
import html
import json
import re
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[1]
ASHBY = '''abatable ably acmetric adaptive adaptive-ml aera aindo airbyte aistetic
algolia allica amboss amply amplication andercore andrew ankar anrok apiday
apify appwrite aqemia arbolus arcads arch archipels arcium auctane audiencerate
aurale aurasell autone axiom backmarket beamy betterstack beyondpresence blinq
bolna borne bound brevo briefcase bubble budbee bunch buysight cable cakes
causaly celonis chainguard checkfirst chronicle clarifai climatiq cohere-health
comand coperniq coralogix corbado credal crosby cryptio crystallize cycloid
dash0 datacamp dataiku datawrapper decisio deepgram deepjudge deepki deepopinion
deepset delight dendra desana dexa diagrid digitail doctolib doinstruct dub
duna duo eduki elicita embat emergent emnify emost enter eppo eqtventures
evroc exa exein fathom fiber-ai fin finary finbourne finch firecrawl flexcompute
flink flowla fluency fonoster forma franklin freepik fullenrich gable gendo
genesis getaccept getaleph getbeam getclerk getcontrast getcredo getdash0
getincident getomni getonboard getrex gettandem ghost glasnostic gliff glintsolar
gocardless gotphoto gravitee griptape harmonic-ai heartflow heidi heidihealth
helsing hero herohealth heyflow hibob holidu hopin humanloop hyperexponential
hyperline hyperplane imandra impala incident incident-io inkeep insify intech
intuition ipilot iris itera iteratively james jigsaw juni justito kaiko kameleoon
kandji katch kbit keepit keplr-ai kevin kibo klaara kleene klu koala kokoro
kraken-technologies kustomer lambdaworks lantern lark leaping legalscape lemlist
leonardo-ai levenue levity liberis lightdash lightyear lisa lizzy lottie lumalabs
lumiform lumos lune lyzr magnolia maia makerplane metabase metaview mindee
mindgard mindsdb modernloop mogul monda monite monzo moonpay moshi moveworks
mwm nango nelson neople nextbillion nexthink numeric octolane octomind odyce
okay omnea omnimodular onfido opal openbb opengov orbital orbitmi origami
osapiens overtone panda panda-doc pandadoc parallel perplexity phantombuster
photoroom pimento plane plasmo plauti pluto pocketlaw podero polarsh
polarsynth polyai pomp position-green prewave prime-intellect probook
prolific pronto proxima pulumi puzzle qatalog qovery quantco raycast
recraft recruitmentroom regie-ai remotion remote reown replicache retraced
revenuecat revyze rillet rippling robolytix roger ronde round runware
safebase safetyculture salus sana-labs sarvam scaleway secoda semgrep sequence
sequoia shiftmove shippypro signal-ai silverfin simondata singular singularity
skello slite smartcat smith-ai snyk socket solace solacehealth sonarsource
sorare sourcegraph speckle splice sprocket sprinto squint stanhope-ai
stonly strapi stripe-ae superlinear supernormal surfly swap taktile talentful
talon talentium tanium tecton tenex termgrid tessl textcortex theodo think-cell
thousandeyes tilores tint toast topi traba transact treecard trestle tribble
triplewhale truelayer truv twentynine twitch unified unipile upflow uselotus
vapi veles verisoul vertice vidext voize volumetric voxpopme wamo weavely
weglot wekan wheely whop windfall wisely wondercraft workforcehero xentral
y42 yassir yoti yoummday zappi zenchef zenjob zep zevero ziffi zinc zoe zowie
'''.split()
GREENHOUSE = '''adyen adverity aiven algolia aircall backmarket bexio bloomreach
bolt businessinsider codat comtravo contentsquare couchbase crossbeam currencycloud
dataiku datadog dataminr deliverect deliveroo dixa doctolib duedil elastic emburse
eni financiac fivetran flagstone forterro freshbooks gocardless grafanalabs
guidewire gympass hotjar hypersonix impactcom intercom iovox jasper jobandtalent
klarna leantime lexisnexisrisk letgo lightdash marshmallow medallia mention
miro mollie monzo multiverse n26 natterbox nimbla notion onfido optimizely
pleo posthog preply primer progyny qonto quoins ravelin remofirst remotecom
revenuecat ro rossum sanity sentry silverfin smartlyio snyk soprabanking
soundcloud spotify sumup taxfix teamviewer thoughtmachine thoughtspot
truelayer trustpilot typeform usertesting veeam vestiairecollective vinted
weavegrid wefox wolt workato worldremit yelp zendesk zopa zego
'''.split()
LEVER = '''aircall airalo alicemr amply analyticsengineers babylonhealth balderton
bitpanda bla blablacar boulangerie brevo bumble causa causaly chalk
circula clarityai cloudwalk cohere convey coralogix covariant craft cro
deepl demodesk doordash dott echobox enpal exponentialfi factorial feast
finmid finom flanks fleek float fullcast giskard gojob goma healthforce
heetch holafly hopin impri intergiro inworld jow kittl ledger leeway
lemonway lewagon lightspeed lilt localyze luko lucca malt manta
multiplier mutable-ai nansen nesto nosto numberly numan ogury olx on
ovoko payfit payhawk pennylane personio piggy pilot prometheus qred
quantexa raisin rapyd reonic revolut riotgames roompricegenie sana scoro
sess silvr skale skello slickshift smartcat smartrecruiters solace
sonarsource spendesk squaredance strapi submer swile synthesia taptap
techwolf ten10 thesandbox tilia tinder tines traderepublic travelperk
trengo unic unicorn unobravo upvest velo veriff virtuagym wallapop
wefox weward wisepops workwise xentral yassir zenjob zepz
'''.split()
GEO = re.compile(r'\b(?:Europe|EMEA|EU|France|Paris|Lyon|Germany|Berlin|Munich|Hamburg|Netherlands|Amsterdam|Rotterdam|Spain|Madrid|Barcelona|Portugal|Lisbon|Porto|Italy|Milan|Rome|Sweden|Stockholm|Finland|Helsinki|Denmark|Copenhagen|Poland|Warsaw|Krakow|Austria|Vienna|Belgium|Brussels|Romania|Bucharest|Czech|Prague|Worldwide|Switzerland|Zurich|Lausanne|London|United Kingdom|UK|Ireland|Dublin|Cork|Estonia|Tallinn|Lithuania|Vilnius|Latvia|Riga|Norway|Oslo|Greece|Athens|Hungary|Budapest|Croatia|Zagreb|Remote - Global)\b', re.I)
ROLE = re.compile(r'engineer|developer|technical writer|developer relations', re.I)
EXCLUDE = re.compile(r'\bback[ -]?end\b|\bQA\b|\btest(?:ing)?\b|support|reliability|sales engineer|solutions engineer|engineering manager|director|head of|principal|chief|hardware|mechanical|electrical', re.I)

def plain(text):
    return re.sub('<[^>]+>', ' ', html.unescape(html.unescape(text or '')))

def fetch(item):
    ats, slug = item
    endpoints = {'ashby': f'https://api.ashbyhq.com/posting-api/job-board/{slug}', 'greenhouse': f'https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true', 'lever': f'https://api.lever.co/v0/postings/{slug}?mode=json'}
    audit = {'ats': ats, 'board': slug, 'endpoint': endpoints[ats]}
    try:
        r = requests.get(endpoints[ats], timeout=18)
        audit['status'] = r.status_code
        if r.status_code != 200:
            return audit, []
        data = r.json()
        jobs = data if ats == 'lever' else data.get('jobs', [])
        audit['complete_feed_jobs'] = len(jobs)
        rows = []
        for j in jobs:
            title = j.get('title') or j.get('text', '')
            location = (str(j.get('location', '')) + ' ' + str(j.get('secondaryLocations', []))) if ats == 'ashby' else str(j.get('location', '') if ats == 'greenhouse' else j.get('categories', {}).get('location', ''))
            if re.search(r'\b(?:France|Paris|Lyon)\b', location, re.I):
                continue  # Multi-location postings can be reviewed separately for a non-France destination.
            if not ROLE.search(title) or EXCLUDE.search(title) or ('staff' in title.lower() and not re.search('senior\\s*(/|or|and|&)\\s*staff', title, re.I)) or not GEO.search(location):
                continue
            posting = j.get('descriptionPlain', '') if ats == 'ashby' else plain(j.get('content', '')) if ats == 'greenhouse' else j.get('descriptionPlain', '') + '\n' + '\n'.join(x.get('text', '') + '\n' + plain(x.get('content', '')) for x in j.get('lists', [])) + '\n' + j.get('additionalPlain', '')
            rows.append({'company': slug, 'title': title, 'role': title, 'location': location, 'url': j.get('jobUrl') or j.get('absolute_url') or j.get('hostedUrl'), 'posting': posting, 'published': j.get('publishedAt') or j.get('updated_at'), 'compensation': j.get('compensation') or j.get('salaryRange'), 'ats': ats, 'discovery': 'Complete official public ATS feed; company growth/ranking status requires review'})
        audit['candidate_jobs'] = len(rows)
        return audit, rows
    except Exception as e:
        audit['error'] = str(e)
        return audit, []

def main():
    blacklist = json.loads((ROOT / 'job-search/company-blacklist.json').read_text())
    blocked = {re.sub('[^a-z0-9]', '', v.casefold()) for e in blacklist for v in [e['company'], e.get('slug', ''), *e.get('aliases', [])]}
    boards = [(ats, slug) for ats, slugs in [('ashby', ASHBY), ('greenhouse', GREENHOUSE), ('lever', LEVER)] for slug in dict.fromkeys(slugs) if re.sub('[^a-z0-9]', '', slug.casefold()) not in blocked]
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
        results = list(pool.map(fetch, boards))
    rows = [row for audit, candidates in results for row in candidates]
    out = ROOT / 'job-search/europe-expanded-1514-2026-10-15-queue.json'
    audits = [a for a, _ in results]
    out.write_text(json.dumps({'scope': 'Europe startups and scaleups; preliminary role/location filters only', 'candidates': rows, 'coverage': audits}, indent=2) + '\n')
    print(json.dumps({'path': str(out), 'boards_requested': len(boards), 'successful_complete_feeds': sum(a.get('status') == 200 for a in audits), 'jobs_scanned': sum(a.get('complete_feed_jobs', 0) for a in audits), 'preliminary_candidates': len(rows)}))

if __name__ == '__main__':
    main()
