#!/usr/bin/env python3
"""
Seed the running ResShare in-memory store with 2026 sports briefing documents.

The Flask backend must be running. Because ResShare may use STORAGE_TYPE=memory,
rerun this script after restarting the backend.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import requests

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from mcp_server.config import load_mcp_env


SPORTS_BRIEFINGS = {
    "2026_sports_world_cup_brief.txt": """2026 Sports Briefing: FIFA World Cup 2026

Document status: curated local briefing for ResShare memory seeding.
Snapshot date: 2026-06-03.
Primary source: Wikipedia article "2026 FIFA World Cup" and FIFA official materials.

Overview
The 2026 FIFA World Cup will be the 23rd FIFA World Cup. It runs from June 11
through July 19, 2026 across Canada, Mexico, and the United States. This is
the first men's World Cup hosted by three nations, the first with 48 teams
(expanded from 32), and the first North American World Cup since 1994. Argentina
are the defending champions (2022). The United 2026 bid beat Morocco 134-65 at
the 68th FIFA Congress in Moscow on June 13, 2018.

Format and expansion
- 48 teams in 12 groups of four.
- Top two in each group plus the eight best third-placed teams advance to a
  new Round of 32 (104 total matches, up from 64 in 2022).
- Knockout rounds: Round of 32 (June 28-July 3), Round of 16 (July 4-7),
  quarter-finals (July 9-11), semi-finals (July 14-15), third-place match
  (July 18), final (July 19).
- Each team still plays three group matches. Tournament lasts 39 days.
- Final squad deadline: June 2, 2026. Final matchday at club level for named
  players: May 24, 2026.

Host nations and automatic qualification
Canada, Mexico, and the United States automatically qualified as hosts.
Mexico was pre-placed in Group A; Canada in Group B; United States in Group D.

Draw (December 5, 2025, Kennedy Center, Washington, D.C.)
Group A: Mexico (host), South Africa, Korea Republic, Czechia
Group B: Canada (host), Bosnia and Herzegovina, Qatar, Switzerland
Group C: Brazil, Morocco, Haiti, Scotland
Group D: United States (host), Paraguay, Australia, Turkiye
Group E: Germany, Curaçao, Côte d'Ivoire, Ecuador
Group F: Netherlands, Japan, Sweden, Tunisia
Group G: Belgium, Egypt, IR Iran, New Zealand
Group H: Spain, Cape Verde, Saudi Arabia, Uruguay
Group I: France, Senegal, Iraq, Norway
Group J: Argentina, Algeria, Austria, Jordan
Group K: Portugal, DR Congo, Uzbekistan, Colombia
Group L: England, Croatia, Ghana, Panama

Opening matches
- June 11, 2026: Mexico vs South Africa at Estadio Azteca (Mexico City Stadium)
  — tournament opening match.
- June 11, 2026: Korea Republic vs Czechia at Estadio Akron (Guadalajara).
- June 12, 2026: Canada vs Bosnia and Herzegovina at BMO Field (Toronto).
- June 12, 2026: United States vs Paraguay at SoFi Stadium (Los Angeles).

Final
July 19, 2026 at New York New Jersey Stadium (MetLife Stadium, East Rutherford,
New Jersey) at 15:00 local / 19:00 GMT.

Sixteen host cities and FIFA tournament stadium names
Atlanta — Atlanta Stadium (Mercedes-Benz Stadium)
Boston — Boston Stadium (Gillette Stadium, Foxborough)
Dallas — Dallas Stadium (AT&T Stadium, Arlington) — hosts most matches (9)
Guadalajara — Guadalajara Stadium (Estadio Akron, Zapopan)
Houston — Houston Stadium (NRG Stadium)
Kansas City — Kansas City Stadium (Arrowhead Stadium)
Los Angeles — Los Angeles Stadium (SoFi Stadium, Inglewood)
Mexico City — Mexico City Stadium (Estadio Azteca)
Miami — Miami Stadium (Hard Rock Stadium, Miami Gardens)
Monterrey — Monterrey Stadium (Estadio BBVA, Guadalupe)
New York/New Jersey — New York New Jersey Stadium (MetLife Stadium)
Philadelphia — Philadelphia Stadium (Lincoln Financial Field)
San Francisco Bay Area — San Francisco Bay Area Stadium (Levi's Stadium, Santa Clara)
Seattle — Seattle Stadium (Lumen Field)
Toronto — Toronto Stadium (BMO Field)
Vancouver — Vancouver Stadium (BC Place)

Match distribution
United States hosts 78 matches including all quarter-finals onward. Canada and
Mexico each host 13 matches. Estadio Akron is the only venue with no knockout
fixture. AT&T Stadium in Arlington hosts the most games (9).

Notable qualifying storylines
World Cup debuts: Cape Verde, Curaçao, Jordan, Uzbekistan.
Italy failed to qualify for a third consecutive World Cup (lost playoff final
to Bosnia and Herzegovina on penalties). Costa Rica, Cameroon, Denmark, Poland,
Serbia, and Wales (all 2022 participants) also missed out.
DR Congo and Haiti return after only previous appearances in 1974. Iraq returns
after 1986. Austria, Norway, and Scotland return after 1998.

Regional groupings for scheduling
Western Region: Vancouver, Seattle, San Francisco, Los Angeles
Central Region: Guadalajara, Mexico City, Monterrey, Houston, Dallas, Kansas City
Eastern Region: Atlanta, Miami, Toronto, Boston, Philadelphia, New York/New Jersey

Sources
- Wikipedia: 2026 FIFA World Cup
- FIFA World Cup 26 match schedule:
  https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/articles/fifa-world-cup-26-match-schedule-revealed
- FIFA knockout stage schedule:
  https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/articles/knockout-stage-match-schedule-bracket
""",
    "2026_sports_winter_olympics_brief.txt": """2026 Sports Briefing: Milano Cortina 2026 Olympic Winter Games

Document status: curated local briefing for ResShare memory seeding.
Snapshot date: 2026-06-03.
Primary source: Wikipedia articles "2026 Winter Olympics" and "2026 Winter Olympics
medal table".

Overview
Milano Cortina 2026 (XXV Olympic Winter Games) were held in Italy from
February 6 through February 22, 2026. The Paralympic Winter Games followed from
March 6 through March 15, 2026. Milan and Cortina d'Ampezzo were selected as
host cities on June 24, 2019. This was the first Olympics officially co-hosted
by two cities and the third Winter Olympics in Italy (after Cortina 1956 and
Torino 2006). Motto: "IT's Your Vibe". Opened by President Sergio Mattarella;
closed by IOC president Kirsty Coventry (first Games under her presidency).

Participation and scale
- 92 National Olympic Committees (including Individual Neutral Athletes).
- 2,884 athletes (1,535 men, 1,349 women) — highest women's participation in
  Winter Olympic history at 47%.
- 116 medal events in 8 sports across 16 disciplines.
- Ski mountaineering debuted (men's sprint, women's sprint, mixed relay).
- Competitions began February 4 (curling mixed doubles) before the opening
  ceremony on February 6.

Distributed venue model
Ice events (except curling) primarily in the Milan cluster. Sliding and snow
events in clusters around Cortina d'Ampezzo, Livigno (Valtellina), and Val di
Fiemme. Opening ceremony: Stadio San Siro, Milan. Closing ceremony: Verona
Arena, Verona. Two Olympic cauldrons were lit — one in Milan and one in Cortina
(a first in Games history).

Key venues
Milan cluster: San Siro (opening), Santa Giulia Ice Hockey Arena (new, 12,000),
Rho Ice Hockey Arena, Milano Speed Skating Stadium, Milano Ice Skating Arena
(figure skating and short track).
Cortina cluster: Tofane (women's alpine), Anterselva (biathlon), Cortina Curling
Olympic Stadium, Cortina Sliding Centre (new — bobsleigh, luge, skeleton).
Valtellina: Stelvio (men's alpine, ski mountaineering), Livigno Snow Park
(snowboard, freestyle).
Val di Fiemme: Predazzo (ski jumping, Nordic combined), Tesero (cross-country,
Nordic combined).

Medal table (final)
Rank  NOC           Gold  Silver  Bronze  Total
  1   Norway          18      12      11     41
  2   United States   12      12       9     33
  3   Netherlands     10       7       3     20
  4   Italy (host)    10       6      14     30
  5   Germany          8      10       8     26
  6   France           8       9       6     23
  7   Sweden           8       6       4     18
  8   Switzerland      6       9       8     23
  9   Austria          5       8       5     18
 10   Japan            5       7      12     24
 11   Canada           5       7       9     21
 12   China            5       4       6     15
 13   South Korea      3       4       3     10
 14   Australia        3       2       1      6
 15   Great Britain    3       1       1      5

Norway set records for most gold (18) and most total medals (41) at a single
Winter Olympics. The United States had their most successful Winter Olympics by
gold count (12). Italy set a national record with 30 total medals. Brazil and
Georgia won their first-ever Winter Olympic medals. Brazil became the first
tropical/Latin American/South American NOC to win Winter Olympic gold.

Notable sport changes
- NHL players returned to men's ice hockey for the first time since 2014.
- New events: ski mountaineering (3), dual moguls (2), luge doubles return (2),
  alpine team combined (2), women's large hill ski jumping, skeleton mixed relay.
- Dropped: alpine mixed team parallel. Alpine combined and Nordic combined
  switched to pairs format.

Russian and Belarusian athletes competed as Individual Neutral Athletes (AIN)
under IOC suspension rules; 20 athletes total (13 Russia, 7 Belarus).

Sources
- Wikipedia: 2026 Winter Olympics, 2026 Winter Olympics medal table
- Olympics.com Milano Cortina 2026:
  https://support.olympics.com/hc/en-gb/articles/43002165477267-Where-and-when-will-the-2026-Olympic-Winter-Games-take-place
""",
    "2026_sports_formula_1_brief.txt": """2026 Sports Briefing: Formula 1 2026 Regulation Change

Document status: curated local briefing for ResShare memory seeding.
Snapshot date: 2026-06-03.
Primary source: Formula 1 official articles, FIA technical regulations, Honda F1
regulations overview.

Overview
Formula 1 introduced its most significant technical regulation change in 2026,
overhauling both power units and chassis rules. Goals: closer racing, lighter and
more agile cars, simpler and more road-relevant hybrid systems, and full
transition to sustainable fuels as part of F1's net-zero 2030 commitment.

Power unit architecture (2026)
- Retains turbocharged 1.6-litre V6 internal combustion engine (ICE).
- MGU-H (Motor Generator Unit – Heat) is REMOVED — no exhaust-gas energy
  recovery. TERS (Thermal Energy Recovery System) is eliminated.
- MGU-K becomes the sole energy recovery system, harvesting kinetic energy
  under braking (as in road-car hybrids).
- MGU-K electrical output increases from ~120 kW to 350 kW (nearly 3×).
- ICE maximum output drops from ~550-560 kW to ~400 kW (~540 PS) due to fuel
  energy flow limits.
- Overall power balance shifts to roughly 50:50 ICE vs electrical.
- Energy recharge cap: 7 MJ per lap (down from 8 MJ with MGU-H present).
- Compression ratio limited to 16:1 (previously 18:1). Variable intake banned.
- Single turbocharger retained; turbo lag mitigation is a key engineering challenge
  without MGU-H.

Sustainable fuel
- From 2026 all cars use 100% Advanced Sustainable Fuel (fully sustainable,
  drop-in compatible with conventional ICE vehicles).
- No new fossil carbon burned. Carbon sourced from non-food biomass, municipal
  waste, or carbon capture.
- Fuel flow regulated by energy content/density rather than mass flow alone.
- FIA mandates pre- and post-event fuel sampling and certification.
- F2 and F3 successfully trialled these fuels in 2025.

Chassis and aerodynamic changes
- Cars designed to be lighter and more agile with active aerodynamic elements.
- "Manual Override Mode" / MGU-K Override: following car can deploy 350 kW up
  to ~337 kph on straights (~0.5 MJ extra energy) to aid overtaking when within
  one second of the car ahead.
- Drag reduction system behaviour adjusted for the new aero package.

Manufacturer landscape
The simplified PU attracted new entrants. Audi joined as a works team (Sauber).
Ford partnered with Red Bull Powertrains. Honda returned as a power unit supplier.
Existing manufacturers: Mercedes, Ferrari, Renault (Alpine), Red Bull Ford.

Why MGU-H was removed
FIA and manufacturers judged MGU-H too complex and expensive for new PU entrants,
with limited road-car adoption over 18 years despite effectiveness in F1. Removing
it concentrates development on MGU-K technology present in road hybrids.

Sources
- Formula 1, 2026 regulations explainer:
  https://www.formula1.com/en/latest/article/2026-regulations-explained-all-you-need-to-know-about-f1s-new-power-units.14jfv7a36905uDJDdNyfQd
- Formula 1, 2026 power unit regulations FIA article:
  https://www.formula1.com/en/latest/article/explained-2026-power-unit-regulations-fia.68izKQ2tn1voQPWvgLVMXN
- FIA 2026 Formula 1 Technical Regulations (Issue 8):
  https://www.fia.com/sites/default/files/fia_2026_formula_1_technical_regulations_issue_8_-_2024-06-24.pdf
- Honda Global, 2026 Formula 1 Regulations Overview:
  https://global.honda/en/F1/features/2026_Commentary/regulations/
""",
    "2026_sports_ufc_recent_events_brief.txt": """2026 Sports Briefing: UFC Recent and Upcoming Events

Document status: curated local briefing for ResShare memory seeding.
Snapshot date: 2026-06-03.
Primary source: Wikipedia, UFC.com — includes post-cutoff 2026 events unlikely in
LLM pretraining data (UFC Freedom 250, UFC 329).

================================================================================
UFC FIGHT NIGHT 278 — Muhammad vs Bonfim (NEXT on calendar)
================================================================================
Event: UFC Fight Night: Muhammad vs. Bonfim (UFC Vegas 118)
Date: Saturday, June 6, 2026
Venue: Meta APEX, Enterprise, Nevada (Las Vegas Valley)
Broadcast: Paramount+ (prelims 5:00 PM EDT; main card 8:00 PM EDT)

Main card (8:00 PM EDT)
  Welterweight: Belal Muhammad (#11) vs Gabriel Bonfim (#10) — headliner
  Middleweight: Brendan Allen vs Edmen Shahbazyan
  Lightweight: Farès Ziam vs Tom Nolan
  Bantamweight: Bryce Mitchell vs Santiago Luna
  Light Heavyweight: Iwo Baraniewski vs Junior Tafa

Prelims (5:00 PM EDT)
  Catchweight (130 lb): Matt Schnell vs Alessandro Costa
  Bantamweight: Marcus McGhee vs John Yannis
  Flyweight: Bruno Gustavo da Silva vs Édgar Chárez
  Women's Bantamweight: Priscila Cachoeira vs Chelsea Chandler
  Featherweight: Jordan Leavitt vs Joanderson Brito
  Women's Flyweight: Jeisla Chaves vs Yuneisy Duben
  Women's Strawweight: Ketlen Souza vs Ariane Carnelossi

Context: Bonfim on 4-fight win streak (19-1 overall). Muhammad seeks to stop a
three-fight slide. No results exist as of June 3 snapshot — event is 3 days away.

================================================================================
UFC FREEDOM 250 — Topuria vs Gaethje (White House card)
================================================================================
Also known as: UFC White House, UFC at the White House
Date: Sunday, June 14, 2026
Venue: South Lawn of the White House, Washington, D.C. (1600 Pennsylvania Avenue)
Broadcast: Paramount+ (main card ~8:00 PM ET); limited prelims on CBS
Presented by: Crypto.com and Ram

Event significance
- First professional sporting event ever staged at the White House / presidential
  residence.
- Named for the 250th anniversary of the United States Declaration of Independence.
- Originally announced by President Donald Trump July 3, 2025; Dana White confirmed
  August 29, 2025 after White House meeting. Formal name revealed at UFC 326
  broadcast March 7, 2026.
- Scheduled June 14 (Flag Day; also Trump's 80th birthday) — moved from initial
  July 4 reports due to logistics.
- Third UFC visit to Washington, D.C.; first since UFC on ESPN: Overeem vs.
  Rozenstruik (December 2019).

Weekend schedule (June 12-14)
  Friday June 12: UFC Freedom 250 Fan Fest Day 1
  Saturday June 13: Fan Fest Day 2 at The Ellipse (3:30 PM–12:00 AM ET) — Zac Brown
    Band concert, ceremonial weigh-ins, meet & greets, watch party build-up
  Sunday June 14: Fight card on South Lawn

Venue and attendance
- South Lawn capacity ~4,300 (invite-only; mostly military personnel).
  Dana White: "most of them will be military." ~1,200 seats to active military;
  Trump allocated ~1,000 tickets; White ~200; TKO CEO Ari Emanuel ~200.
- The Ellipse public viewing: up to 85,000 free tickets (large screens).
- Custom "Freedom 250" title belts revealed May 6 for both title-fight winners.
- Temporary arena includes "the claw" — massive lighting/cover structure built in
  Europe and shipped to the U.S.; White House kept visible as backdrop for fights.
- Ceremonial weigh-ins and press conference at Lincoln Memorial.
- Zac Brown Band performs live U.S. national anthem (first live anthem on UFC
  card since early numbered events).
- Estimated production cost $60M+ (exceeds UFC 306 Sphere show ~$21M). UFC pays
  full cost including ~$700,000 South Lawn restoration; no taxpayer funding sought.
- Crypto.com $1 million cryptocurrency bonus for top performance on the card.

Regulatory note
- Federal property — D.C. Combat Sports Commission not primary regulator; UFC
  self-regulates with Association of Boxing Commissions (ABC) as independent
  third-party oversight. D.C. commission noted outcomes may not count on official
  records without $100 permit (disputed/special circumstances).

Fight card (7 bouts announced at UFC 326, March 7-8, 2026)
Main event — UFC Lightweight Championship (unification)
  Ilia Topuria (c, 17-0, 9-0 UFC) vs Justin Gaethje (interim c, 27-5, 10-5 UFC)
  Topuria: undefeated; former featherweight champ; won lightweight belt with R1 KO
  of Charles Oliveira (June 2025). Gaethje: two-time interim champ; winless in
  undisputed title bouts (lost to Khabib 2020, Oliveira 2022).
  Backup: Arman Tsarukyan (injury replacement if needed).
  Topuria reportedly preferred Islam Makhachev (welterweight) for three-division
  history attempt; Makhachev unavailable due to hand injury → Gaethje booked.

Co-main — Interim UFC Heavyweight Championship
  Alex Pereira (13-3 MMA, 10-2 UFC) vs Ciryl Gane (13-2 MMA, 10-2 UFC)
  Pereira vacated light heavyweight title April 2026 to move up. If he wins, first
  fighter to hold UFC titles in three divisions (middleweight, light heavyweight,
  heavyweight). Tom Aspinall (HW champ) out with eye injury from UFC 321 defense.

Rest of card
  Bantamweight: Sean O'Malley (former champ) vs Aiemann Zahabi (7-fight win streak)
  Lightweight: Maurício Ruffy vs Michael Chandler (3× Bellator LW champ)
  Middleweight: Bo Nickal (3× NCAA wrestling champ) vs Kyle Daukaus
  Featherweight: Diego Lopes vs Steve Garcia (7 straight UFC wins)
  Heavyweight: Derrick Lewis vs Josh Hokit (9-0) — added after Trump requested
    Lewis appear following Hokit's UFC 327 win April 11.

Not on card (planning notes)
  Jon Jones negotiated but did not agree on pay; requested UFC release.
  Conor McGregor not seriously considered — slotted for UFC 329 in July instead.
  Kayla Harrison vs Amanda Nunes discussed but Harrison not ready.

================================================================================
UFC 329 — McGregor vs Holloway 2 (International Fight Week)
================================================================================
Date: Saturday, July 11, 2026
Venue: T-Mobile Arena, Paradise, Nevada (Las Vegas)
Broadcast: Paramount+ only
  Early prelims 5:00 PM EDT / 2:00 PM PT
  Prelims 7:00 PM EDT / 4:00 PM PT
  Main card 9:00 PM EDT / 6:00 PM PT
Tickets: On sale May 29, 2026 (Fight Club presale May 27; newsletter May 28)

Event significance
- Headline event of UFC International Fight Week 2026 (14th annual).
- 2026 UFC Hall of Fame induction ceremony: July 9, 2026.
- Main event announced May 16, 2026 by Dana White.

Main event — Welterweight (170 lb)
  Conor McGregor vs Max Holloway 2
  McGregor: former UFC featherweight and lightweight champion; first fight since
  leg break at UFC 264 (July 2021). Holloway: former featherweight champion;
  welterweight debut. First meeting: UFC Fight Night 26, August 17, 2013 —
  McGregor won unanimous decision (featherweight, early careers). Rematch is
  13 years later at 170 lbs.

Full fight card
Main card (9:00 PM EDT, Paramount+)
  Welterweight: Conor McGregor vs Max Holloway
  Lightweight: Paddy Pimblett (#6) vs Benoît Saint Denis (#5)
  Bantamweight: Cory Sandhagen vs Mario Bautista
  Flyweight: Brandon Royval vs Lone'er Kavanagh
  Heavyweight: Gable Steveson vs Elisha Ellison
  Light Heavyweight: Robert Whittaker vs Nikita Krylov
  Bantamweight: Cody Garbrandt vs Adrian Yañez

Prelims (7:00 PM EDT)
  Featherweight: Luke Riley vs Kai Kamaka III
  Middleweight: Damian Pinas vs César Almeida

Early prelims (5:00 PM EDT)
  Women's Flyweight: Tracy Cortez vs Wang Cong
  Flyweight: Ode' Osbourne vs Cody Durden
  Middleweight: Ryan Gandra vs Zachary Reese

Notes: Leon Edwards vs Daniel Rodriguez welterweight bout was linked but Rodriguez
booked elsewhere (Uroš Medić main event in Oklahoma City instead).

================================================================================
2026 UFC chronology (near-term)
================================================================================
Past (before snapshot): UFC Fight Night: Song vs Figueiredo
June 6:  UFC Fight Night: Muhammad vs Bonfim (Meta APEX, Las Vegas)
June 14: UFC Freedom 250: Topuria vs Gaethje (White House, Washington D.C.)
June 20: UFC Fight Night: Kape vs Horiguchi (approx — per event chronology)
July 11: UFC 329: McGregor vs Holloway 2 (T-Mobile Arena, Las Vegas)

Sources
- Wikipedia: UFC Fight Night: Muhammad vs. Bonfim, UFC Freedom 250, UFC 329
- UFC Freedom 250: https://www.ufc.com/freedom250
- UFC 329: https://www.ufc.com/event/ufc-329
- UFC Muhammad vs Bonfim: https://www.ufc.com/event/ufc-fight-night-june-06-2026
- UFC McGregor-Holloway announcement:
  https://www.ufc.com/news/conor-mcgregor-rematches-max-holloway-welterweight-main-event-ufc-329-live-paramount
""",
    "2026_sports_ipl_playoffs_brief.txt": """2026 Sports Briefing: TATA IPL 2026

Document status: curated local briefing for ResShare memory seeding.
Snapshot date: 2026-06-03.
Primary source: Wikipedia "2026 Indian Premier League", IPLT20.com, ESPNcricinfo.

Overview
The 2026 Indian Premier League (TATA IPL 2026, IPL 19) ran March 28 through
May 31, 2026 across 13 venues. Ten teams played 74 matches. Defending champions
Royal Challengers Bengaluru (RCB) defeated Gujarat Titans by 5 wickets in the
final to win back-to-back titles — only the third franchise after CSK and MI to
retain the IPL crown.

Champions: Royal Challengers Bengaluru (2nd title)
Runners-up: Gujarat Titans
Most runs: Vaibhav Sooryavanshi (Rajasthan Royals) — 776 runs
Most wickets: Kagiso Rabada (Gujarat Titans) — 29 wickets
Most valuable player: Vaibhav Sooryavanshi (Rajasthan Royals)

Opening match (March 28, 2026)
Royal Challengers Bengaluru vs Sunrisers Hyderabad at M. Chinnaswamy Stadium,
Bengaluru. RCB won by 6 wickets chasing 203. Virat Kohli 69*; Jacob Duffy (RCB)
Player of the Match.

League stage final standings
Pos  Team                          Pld  W   L  Pts   NRR
 1   Royal Challengers Bengaluru    14   9   5   18  +0.783  → Qualifier 1
 2   Gujarat Titans                 14   9   5   18  +0.695  → Qualifier 1
 3   Sunrisers Hyderabad            14   9   5   18  +0.524  → Eliminator
 4   Rajasthan Royals               14   8   6   16  +0.189  → Eliminator
 5   Punjab Kings                   14   7   6   15  +0.309  (eliminated)
 6   Delhi Capitals                 14   7   7   14  -0.651
 7   Kolkata Knight Riders          14   6   7   13  -0.147
 8   Chennai Super Kings            14   6   8   12  -0.345
 9   Mumbai Indians                 14   4  10    8  -0.584
10   Lucknow Super Giants           14   4  10    8  -0.740

Playoff bracket and results
Qualifier 1 — May 26, HPCA Cricket Stadium, Dharamshala
  RCB 254/5 (20) beat GT 162 (19.3) by 92 runs.
  Rajat Patidar 93* (33), Player of the Match. Highest IPL playoff score ever.

Eliminator — May 27, Maharaja Yadavindra Singh Stadium, Mullanpur (New Chandigarh)
  RR 243/8 (20) beat SRH 196 (19.2) by 47 runs.
  Vaibhav Sooryavanshi 97 (29), Player of the Match.

Qualifier 2 — May 29, Maharaja Yadavindra Singh Stadium, Mullanpur
  GT 219/3 (18.4) beat RR 214/6 (20) by 7 wickets.
  Shubman Gill 104 (53), Player of the Match.

Final — May 31, Narendra Modi Stadium, Ahmedabad
  GT 155/8 (20) vs RCB 161/5 (18 overs).
  RCB won by 5 wickets with 12 balls remaining.
  Virat Kohli 75* (42, 9 fours, 3 sixes), Player of the Match.
  Washington Sundar 50* (37) top-scored for GT.
  RCB captain Rajat Patidar won the toss and elected to field.
  Rajat Patidar joins MS Dhoni (2010-11) and Rohit Sharma (2019-20) as captains
  to win back-to-back IPL titles.

Schedule notes
First-phase fixtures (20 matches, March 28-April 12) announced March 11 due to
state elections in Assam, Tamil Nadu, and West Bengal. Full league schedule
released March 26. Playoff venues confirmed May 6. Final shifted from Bengaluru
to Ahmedabad (Narendra Modi Stadium's fourth IPL final after 2022, 2023, 2025).

Sources
- Wikipedia: 2026 Indian Premier League
- IPLT20 final match report:
  https://www.iplt20.com/news/4377/tata-ipl-2026-final-rcb-v-gt-match-report
- IPLT20 playoff schedule:
  https://www.iplt20.com/news/4359/tata-ipl-2026-playoffs-tickets-to-go-live-from-may-20
""",
    "2026_sports_premier_league_brief.txt": """2026 Sports Briefing: Premier League 2025/26

Document status: curated local briefing for ResShare memory seeding.
Snapshot date: 2026-06-03.
Primary source: Wikipedia "2025–26 Premier League", PremierLeague.com.

Overview
The 2025-26 Premier League was the 34th season of the competition. Season ran
August 2025 through May 24, 2026 (38 matchdays, 380 matches). Arsenal won their
fourth Premier League title and first in 22 years, clinching with one game to
spare and receiving the trophy after a 2-1 win at Crystal Palace on the final day
(May 24, 2026). Manager Mikel Arteta won Manager of the Season.

Final league table
Pos  Team                    Pld  W   D   L   GF  GA   GD  Pts  Notes
 1   Arsenal (C)              38  26   7   5   71  27  +44   85  Champions League
 2   Manchester City          38  23   9   6   77  35  +42   78  Champions League
 3   Manchester United        38  20  11   7   69  50  +19   71  Champions League
 4   Aston Villa              38  19   8  11   56  49   +7   65  Champions League
 5   Liverpool                38  17   9  12   63  53  +10   60  Champions League
 6   Bournemouth              38  13  18   7   58  54   +4   57  Europa League
 7   Sunderland               38  14  12  12   42  48   -6   54  Europa League
 8   Brighton & Hove Albion   38  14  11  13   52  46   +6   53  Conference League
 9   Brentford                38  14  11  13   55  52   +3   53
10   Chelsea                  38  14  10  14   58  52   +6   52
11   Fulham                   38  15   7  16   47  51   -4   52
12   Newcastle United         38  14   7  17   53  55   -2   49
13   Everton                  38  13  10  15   47  50   -3   49
14   Leeds United             38  11  14  13   49  56   -7   47
15   Crystal Palace           38  11  12  15   41  51  -10   45  Europa League*
16   Nottingham Forest        38  11  11  16   48  51   -3   44
17   Tottenham Hotspur        38  10  11  17   48  57   -9   41
18   West Ham United (R)      38  10   9  19   46  65  -19   39  Relegated
19   Burnley (R)              38   4  10  24   38  75  -37   22  Relegated
20   Wolverhampton Wanderers  38   3  11  24   27  68  -41   20  Relegated

*Crystal Palace also qualified for Europa League via FA Cup win.

Season records and statistics
- Highest scoring match: Fulham 4-5 Brentford
- Longest winning run: 8 matches (Aston Villa)
- Longest unbeaten run: 18 matches (Arsenal)
- Promoted clubs (Sunderland, Leeds, Burnley) all survived or competed — first
  time since 2011-12 all three promoted sides avoided immediate relegation until
  Burnley went down on the final day.

Individual awards
Golden Boot: Erling Haaland (Manchester City) — 27 goals (3rd in 4 seasons)
Golden Glove: David Raya (Arsenal) — 19 clean sheets (3rd consecutive)
Playmaker (most assists): Bruno Fernandes (Manchester United) — 21 assists
Player of the Season: Bruno Fernandes (Manchester United)
Young Player of the Season: Nico O'Reilly (Manchester City)
Manager of the Season: Mikel Arteta (Arsenal)
Goal of the Season: Harrison Reed (Fulham)
Save of the Season: Jordan Pickford (Everton)

Top scorers
 1. Erling Haaland (Man City) — 27
 2. Igor Thiago (Brentford) — 22
 3. Antoine Semenyo (Bournemouth/Man City) — 17
 4. Ollie Watkins (Aston Villa) — 16
 5. Morgan Gibbs-White (Nottm Forest) / João Pedro (Chelsea) — 15

European qualification summary
Champions League (top 5): Arsenal, Man City, Man United, Aston Villa, Liverpool
Europa League: Bournemouth, Sunderland, Crystal Palace (FA Cup)
Conference League: Brighton & Hove Albion

Sources
- Wikipedia: 2025–26 Premier League
- Premier League season summary:
  https://www.premierleague.com/en/news/4668605/everything-thats-been-decided-in-202526-premier-league
""",
    "2026_sports_bundesliga_brief.txt": """2026 Sports Briefing: Bundesliga 2025/26

Document status: curated local briefing for ResShare memory seeding.
Snapshot date: 2026-06-03.
Primary source: Wikipedia "2025–26 Bundesliga", Bundesliga.com.

Overview
The 2025-26 Bundesliga was the 63rd season. Ran August 22, 2025 through May 16,
2026. Bayern Munich won their 34th Bundesliga title (35th German title overall),
clinching with four matches to spare on April 19, 2026 after beating VfB Stuttgart
4-2. Bayern set a new Bundesliga single-season goals record with 122 goals (beating
their own 101 from 1971-72), the second-highest in Europe's top five leagues ever
(behind Torino's 125 in 1947-48).

Final league table
Pos  Team                  Pld  W   D   L   GF   GA   GD  Pts  Notes
 1   Bayern Munich (C)      34  28   5   1  122   36  +86   89  Champions League
 2   Borussia Dortmund      34  22   7   5   70   34  +36   73  Champions League
 3   RB Leipzig             34  20   5   9   66   47  +19   65  Champions League
 4   VfB Stuttgart          34  18   8   8   71   49  +22   62  Champions League
 5   TSG Hoffenheim         34  18   7   9   65   52  +13   61  Europa League
 6   Bayer Leverkusen       34  17   8   9   68   47  +21   59  Europa League*
 7   SC Freiburg            34  13   8  13   51   57   -6   47  Conference League
 8   Eintracht Frankfurt    34  11  11  12   61   65   -4   44
 9   FC Augsburg            34  12   7  15   45   61  -16   43
10   Mainz 05               34  10  10  14   44   53   -9   40
11   Union Berlin           34  10   9  15   44   58  -14   39
12   Borussia M'gladbach    34   9  11  14   42   53  -11   38
13   Hamburger SV           34   9  11  14   40   54  -14   38
14   1. FC Köln             34   7  11  16   49   63  -14   32
15   Werder Bremen          34   8   8  18   37   60  -23   32
16   VfL Wolfsburg (R)      34   7   8  19   45   69  -24   29  Relegation play-off
17   1. FC Heidenheim (R)   34   6   8  20   41   72  -31   26  Relegated
18   FC St. Pauli (R)       34   6   8  20   29   60  -31   26  Relegated

*Bayern won DFB-Pokal so Europa League spot passed to 6th (Leverkusen).

Season statistics
- Total goals: 990 (3.24 per match)
- Top scorer: Harry Kane (Bayern Munich) — 36 goals
- Biggest home win: Bayern Munich 8-1 Wolfsburg
- Biggest away win: Augsburg 0-6 RB Leipzig
- Highest scoring: Mönchengladbach 4-6 Eintracht Frankfurt
- Longest winning run: 9 games (Bayern Munich)
- Longest unbeaten run: 18 games (Bayern Munich)
- Longest winless run: 15 games (Heidenheim)
- Longest losing run: 9 games (St. Pauli)
- Average attendance: 42,311 (12,947,047 total)

Team changes
Promoted: Hamburger SV (7-year absence), 1. FC Köln (1-year absence).
Relegated from 2024-25: Holstein Kiel, VfL Bochum.

Relegation play-off (May 21 and 25, 2026)
VfL Wolfsburg vs 1. FC Nürnberg at Volkswagen Arena — Wolfsburg survived.

Sources
- Wikipedia: 2025–26 Bundesliga
- Bundesliga official table:
  https://www.bundesliga.com/en/bundesliga/table/2025-2026
""",
    "2026_sports_laliga_brief.txt": """2026 Sports Briefing: LALIGA EA SPORTS 2025/26

Document status: curated local briefing for ResShare memory seeding.
Snapshot date: 2026-06-03.
Primary source: Wikipedia "2025–26 La Liga", LaLiga.com.

Overview
The 2025-26 La Liga (La Liga EA Sports) was the 95th season. Ran August 15, 2025
through May 24, 2026 (38 matchdays). Barcelona were defending champions. Barcelona
won their 29th La Liga title and second consecutive crown, clinching with three
matches to spare on May 10, 2026 after a 2-0 El Clásico win over Real Madrid at
home. Hansi Flick managed Barcelona to back-to-back titles.

Final league table
Pos  Team                  Pld  W   D   L   GF  GA   GD  Pts  Notes
 1   Barcelona (C)          38  31   1   6   95  36  +59   94  Champions League
 2   Real Madrid            38  27   5   6   77  35  +42   86  Champions League
 3   Villarreal             38  22   6  10   72  46  +26   72  Champions League
 4   Atlético Madrid        38  21   6  11   62  44  +18   69  Champions League
 5   Real Betis             38  15  15   8   59  48  +11   60  Champions League*
 6   Celta Vigo             38  14  12  12   53  48   +5   54  Europa League
 7   Getafe                 38  15   6  17   32  38   -6   51  Conference League
 8   Rayo Vallecano         38  12  14  12   41  44   -3   50
 9   Valencia               38  13  10  15   46  55   -9   49
10   Real Sociedad          38  11  13  14   59  61   -2   46  Europa League**
11   Espanyol               38  12  10  16   43  55  -12   46
12   Athletic Bilbao        38  13   6  19   43  58  -15   45
13   Sevilla                38  12   7  19   46  60  -14   43
14   Alavés                 38  11  10  17   44  56  -12   43
15   Elche                  38  10  13  15   49  57   -8   43
16   Levante                38  11   9  18   47  61  -14   42
17   Osasuna                38  11   9  18   44  50   -6   42
18   Mallorca (R)           38  11   9  18   47  57  -10   42  Relegated
19   Girona (R)             38   9  14  15   39  55  -16   41  Relegated
20   Real Oviedo (R)        38   6  11  21   26  60  -34   29  Relegated

*La Liga gained an extra Champions League spot via European Performance Spot.
**Real Sociedad qualified for Europa League as 2025-26 Copa del Rey winners.

Season statistics
- Total goals: 1,024 (2.69 per match)
- Top scorer: Kylian Mbappé — 25 goals
- Best goalkeeper: Joan Garcia — 0.70 goals/match
- Biggest home win: Barcelona 6-0 Valencia (September 14, 2025)
- Biggest away win: Girona 0-4 Levante (September 20, 2025)
- Highest scoring: Real Betis 3-5 Barcelona (December 6, 2025)
- Longest winning run: 11 matches (Barcelona)
- Longest unbeaten run: 13 matches (Atlético Madrid)
- Highest attendance: 78,107 (Real Madrid 2-1 Barcelona, October 26, 2025)
- Average attendance: 30,944

El Clásico results 2025-26
- Matchday 10 (October 26, 2025): Real Madrid 2-1 Barcelona at Bernabéu
- Matchday 35 (May 10, 2026): Barcelona 2-0 Real Madrid at Camp Nou — title-clincher

Promotion and relegation
Promoted: Levante (3-year absence), Elche (2-year), Real Oviedo (24-year absence).
Relegated 2024-25: Valladolid, Las Palmas, Leganés.

Sources
- Wikipedia: 2025–26 La Liga
- LaLiga official standings:
  https://www.laliga.com/en-CA/laliga-easports/standing
""",
}


def _post_json(
    session: requests.Session,
    api_base_url: str,
    path: str,
    payload: dict[str, Any],
) -> tuple[int, dict[str, Any]]:
    response = session.post(f"{api_base_url}{path}", json=payload, timeout=30)
    return response.status_code, _response_json(response)


def _response_json(response: requests.Response) -> dict[str, Any]:
    try:
        data = response.json()
    except ValueError:
        return {"message": response.text}
    if isinstance(data, dict):
        return data
    return {"message": data}


def _ensure_account(
    session: requests.Session,
    api_base_url: str,
    username: str,
    password: str,
) -> None:
    credentials = {"username": username, "password": password}
    signup_status, signup_data = _post_json(session, api_base_url, "/signup", credentials)
    signup_result = signup_data.get("result") or signup_data.get("message")

    if signup_status == 200 and signup_result == "SUCCESS":
        print(f"Created ResShare account: {username}")
    elif signup_result == "USER_EXISTS":
        print(f"Using existing ResShare account: {username}")
    else:
        raise RuntimeError(f"Signup failed for {username}: {signup_result}")

    login_status, login_data = _post_json(session, api_base_url, "/login", credentials)
    login_result = login_data.get("result") or login_data.get("message")
    if login_status != 200 or login_result != "SUCCESS":
        raise RuntimeError(f"Login failed for {username}: {login_result}")


def _ensure_folder(
    session: requests.Session,
    api_base_url: str,
    folder_path: str,
) -> None:
    response = session.post(
        f"{api_base_url}/create-folder",
        json={"folder_path": folder_path},
        timeout=30,
    )
    payload = _response_json(response)
    result = payload.get("result") or payload.get("message")
    if response.status_code in {200, 201} and result == "SUCCESS":
        print(f"Created folder: {folder_path}")
        return
    if response.status_code == 409 and result == "DUPLICATE_NAME":
        print(f"Folder already exists: {folder_path}")
        return
    raise RuntimeError(f"Folder creation failed for {folder_path}: {result}")


def _upload_file(
    session: requests.Session,
    api_base_url: str,
    local_path: Path,
    folder_path: str,
) -> dict[str, Any]:
    with local_path.open("rb") as file_handle:
        response = session.post(
            f"{api_base_url}/upload",
            files={"file": (local_path.name, file_handle)},
            data={"path": folder_path, "skip_ai_processing": "false"},
            timeout=120,
        )
    payload = _response_json(response)
    if response.status_code != 200 or payload.get("message") != "SUCCESS":
        raise RuntimeError(f"Upload failed for {local_path.name}: {payload}")
    return payload


def _verify_chat(session: requests.Session, api_base_url: str) -> None:
    query = (
        "Using only my uploaded 2026 sports briefing documents, answer three "
        "things: who won the 2025/26 Premier League, where was the TATA IPL "
        "2026 final scheduled, and what is the next UFC event in the files?"
    )
    response = session.post(f"{api_base_url}/chat", json={"query": query}, timeout=120)
    payload = _response_json(response)
    print("\nVerification query:")
    print(query)
    print("\nVerification answer:")
    print(payload.get("answer") or payload)
    print("\nSources:")
    print(payload.get("sources", []))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Upload curated 2026 sports briefing docs into ResShare memory."
    )
    parser.add_argument(
        "--api-base-url",
        default=os.environ.get("RESSHARE_API_BASE_URL", "http://127.0.0.1:5000"),
        help="ResShare Flask API base URL.",
    )
    parser.add_argument(
        "--username",
        default=os.environ.get("RESSHARE_USERNAME", ""),
        help="ResShare username. Defaults to RESSHARE_USERNAME.",
    )
    parser.add_argument(
        "--password",
        default=os.environ.get("RESSHARE_PASSWORD", ""),
        help="ResShare password. Defaults to RESSHARE_PASSWORD.",
    )
    parser.add_argument(
        "--folder",
        default="root/2026-sports-briefing",
        help="ResShare folder path to create and upload into.",
    )
    parser.add_argument(
        "--label",
        default=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        help="Filename label used to avoid duplicate names on repeated seeding.",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Ask ResShare chat a verification question after upload.",
    )
    return parser.parse_args()


def main() -> int:
    load_mcp_env()
    args = _parse_args()
    api_base_url = args.api_base_url.rstrip("/")
    username = args.username.strip()
    password = args.password.strip()
    if not username or not password:
        print("Set RESSHARE_USERNAME and RESSHARE_PASSWORD or pass --username/--password.", file=sys.stderr)
        return 1

    session = requests.Session()
    _ensure_account(session, api_base_url, username, password)
    _ensure_folder(session, api_base_url, args.folder)

    with TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        for filename, content in SPORTS_BRIEFINGS.items():
            output_path = temp_root / f"{args.label}_{filename}"
            output_path.write_text(content, encoding="utf-8")
            payload = _upload_file(session, api_base_url, output_path, args.folder)
            print(
                f"Uploaded {output_path.name}: "
                f"rag_processed={payload.get('rag_processed')} "
                f"rag_skipped={payload.get('rag_skipped')}"
            )

    stats_response = session.get(f"{api_base_url}/chat/stats", timeout=30)
    print("\nChat stats:")
    print(_response_json(stats_response))

    if args.verify:
        _verify_chat(session, api_base_url)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
