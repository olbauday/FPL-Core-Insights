# FPL Core Insights: A Comprehensive FPL Dataset

Welcome to **FPL Core Insights**, the data engine powering [fplcore.com](https://fplcore.com).

This project uniquely links official FPL player data with detailed match statistics and historical team Elo ratings, allowing for **unparalleled insights into player and team performance.**

It combines three powerful data sources:
1.  **Official FPL API Data** – Player points, costs, form, ownership, xG/xA, and more.
2.  **Manually Curated Match Stats (Opta-like)** – Deep-dive performance metrics for every player and match.
3.  **ClubElo.com Elo Ratings** – Historical and current team strength ratings for robust fixture analysis.

---

## 💬 Join the Community

Join the official **[FPL Core Discord](https://discord.gg/QXrzKvgGZm)** — where data enthusiasts and football fans collide.

Whether you're using the [FPL Core platform](https://fplcore.com), building your own tools, or just talking football, you'll find a home here.

## 💬 Join the League

We’ve created an official **FPL Core** league for anyone using this data.

It’s a simple way to:
- Compare performance
- See who’s actually extracting value from the insights
- Have a bit of competitive fun along the way

👉 **[Join the FPL Core League](https://fantasy.premierleague.com/leagues/auto-join/2gtyce)**

## Data Updates

The dataset is automatically refreshed twice daily at:
- **7:30 AM UTC**
- **5:30 PM UTC**

All data is provided in **CSV format** for easy import into any data analysis tool.

## Using The Data
Feel free to use the data from this repository in whatever way works best for you—whether for your website, blog posts, or other projects. If possible, I’d greatly appreciate it if you could include a link back to this repository as the data source.

Inspired by the amazing work of [vaastav/Fantasy-Premier-League](https://github.com/vaastav/Fantasy-Premier-League), this project aims to continue the spirit of open data in the FPL community. If you build something cool, let me know – I'd be happy to feature a link to your project!

## What's New for the 2026/27 Season?

<details>
<summary>Click Here to Expand</summary>

### 📅 New Season, Same Structure
The 2026/27 dataset lives in `data/2026-2027/` and follows the same layout as previous seasons, so tools built on last season's files should only need a path change. The promoted clubs — Coventry City, Hull City and Ipswich Town — are included from day one.

### 🏃 Pre-Season Friendlies Under Gameweek 0
Pre-season friendlies are collected under **Gameweek 0**, keeping them cleanly separated from the league campaign. That means you can analyse pre-season minutes and form for FPL-listed players before your first GW1 decisions. (Friendly coverage depends on what gets published for each fixture — smaller venues sometimes only have team-level data.)

Use `minutes_played` as the source of truth for minutes. A player who was named but never came on is recorded as **0 minutes**, not a blank — deriving minutes from `finish_min - start_min` instead will credit those players with a full match. `start_min` / `finish_min` are best-effort: some fixtures arrive with no substitution timeline at all, and every player then shows a start of 0. Both columns are corrected on export where they contradict `minutes_played`; see `scripts/clean_playermatchstats.py` for exactly what is fixed and what is deliberately left alone.

### 🔁 A More Reliable Pipeline
The pipeline behind this repository was overhauled over the summer: cup and European fixtures are picked up automatically as soon as draws are made (no more manually tracked competitions), and daily health checks catch missing or stale data before it reaches the CSVs.

</details>

## What's New for the 2025/26 Season?

<details>
<summary>Click Here to Expand</summary>

## player_gameweek_stats 
This table is auto-generated to provide discrete, analysis-ready stats for a single gameweek. It solves the problem of cumulative data in the playerstats table.
For example, the goals_scored column in this file shows the goals a player scored only in that gameweek, not their season total. It is the recommended source for analyzing week-by-week player performance.
It contains three types of data:
Calculated Performance Stats: Columns like goals_scored, assists, bonus, bps, minutes, etc., are calculated by subtracting the previous gameweek's total from the current one.
Gameweek-Specific Stats: Columns like event_points are taken directly as they already represent the single gameweek.
Snapshot Stats: Columns like now_cost, selected_by_percent, and form represent the player's status at the deadline of that gameweek.
This file uses the same column structure as playerstats for consistency.
Links:
id links to the player_id in the players table.

This season, FPL-Elo-Insights is taking a massive leap forward, pushing beyond what inspired this project to deliver an even richer analytical experience.

### 🏆 Expanded Tournament Coverage Synced to FPL Players
This is the big one! The dataset now includes data from all major competitions, including **pre-season friendlies (which are spotty at best), domestic cups (FA Cup, League Cup), and all European competitions (Champions League, Europa League, Conference League).**

Crucially, this vast new data is directly linked to your FPL player IDs, allowing you to seamlessly track how players perform across all competitions and see how it might impact their FPL potential. No more guessing how pre-season form or European fatigue could influence your picks!

### 🛡️ Enhanced Defensive & Midfield Metrics (CBIT)
Following the new FPL rules that reward defensive contributions, I've integrated **Clearances, Blocks, Interceptions, and Tackles (CBIT)** for every player in every match. This means you can now:
*   Identify defensive gems who might rack up points under the new FPL rules.
*   Analyze how effectively players contribute defensively beyond just clean sheets.
*   Spot differentials in midfield and defense who excel in these often-overlooked areas.

### 📂 New & Improved Data Structure
The data is now organized into a more intuitive structure to make analysis easier than ever. You can access data sliced in different ways depending on your needs.

</details>

## Data Structure Overview
<details>
<summary>Click here to expand</summary>

The data for each season is organized within a dedicated directory, such as `data/2026-2027/`. The structure is designed to provide both high-level summaries and granular, point-in-time snapshots.

### 1. Master Files (Season-Level Data)

These files are located at the root of the season's directory (e.g., `data/2026-2027/`) and contain the most current, aggregated data for the entire season.

*   **Location**: `/data/{season}/`
*   **Description**: The primary, always-up-to-date data files.
*   **Files**:
    *   `players.csv`: A comprehensive list of all players for the season.
    *   `teams.csv`: Details for all teams participating in the season.
    *   `playerstats.csv`: Aggregated season-total statistics for every player.
    *   `gameweek_summaries.csv`: A summary of key events and data for each gameweek.

### 2. By Gameweek (Gameweek-Specific Snapshots)

This directory contains snapshots of the data as it appeared at the end of each specific gameweek. This is useful for historical analysis or replaying a specific point in the season.

*   **Location**: `/data/{season}/By Gameweek/GW{x}/`
*   **Description**: A complete data snapshot for a given gameweek (`GW`).
*   **Files**:
    *   `fixtures.csv`: All scheduled fixtures relevant to that gameweek.
    *   `matches.csv`: Detailed results and data for all matches played up to that gameweek.
    *   `players.csv`: The state of the players list at the end of the gameweek.
    *   `teams.csv`: The state of the teams list at the end of the gameweek.
    *   `playerstats.csv`: Cumulative player statistics up to that gameweek.
    *   `playermatchstats.csv`: Individual player performance for each match within that gameweek.
    *   `player_gameweek_stats.csv`: A summary of each player's performance specifically for that gameweek.

### 3. By Tournament (Tournament-Specific Data)

This section isolates the data for each individual tournament, providing a self-contained view of all relevant matches, players, and stats for that competition.

*   **Location**: `/data/{season}/By Tournament/{tournament_name}/GW{x}/`
*   **Description**: Data filtered to include only information relevant to a specific tournament (e.g., `Premier League`, `EFL Cup`). The data is further organized by the gameweek in which the tournament's matches occurred.
*   **Files**: The file structure within each tournament's gameweek folder is identical to the main "By Gameweek" snapshots, but it only contains data related to that specific tournament.

## Data Tables Explained

<details>
<summary>Click Here to Expand</summary>

### `matches`

This table contains comprehensive match-level data for all **finished** games.

*   `gameweek`: The gameweek of the match.
*   `kickoff_time`: The date and time of the match kickoff.
*   `home_team`, `away_team`: IDs of the home and away teams (referencing the `teams` table).
*   `home_team_elo`, `away_team_elo`: Elo ratings of the home and away teams at the time of the match.
*   `home_score`, `away_score`: The final score of the match.
*   `finished`: Boolean indicating whether the match has finished.
*   `match_id`: A unique identifier for each match.
*   `home_possession`, `away_possession`: Percentage of possession for each team.
*   `home_expected_goals_xg`, `away_expected_goals_xg`: Expected goals for each team.
*   `home_total_shots`, `away_total_shots`: Total shots taken by each team.
*   `home_shots_on_target`, `away_shots_on_target`: Shots on target for each team.
*   `home_big_chances`, `away_big_chances`: Big chances created by each team.
*   `home_big_chances_missed`, `away_big_chances_missed`: Big chances missed by each team.
*   `home_accurate_passes`, `away_accurate_passes`: Number of accurate passes for each team.
*   `home_accurate_passes_pct`, `away_accurate_passes_pct`: Percentage of accurate passes for each team.
*   `home_fouls_committed`, `away_fouls_committed`: Fouls committed by each team.
*   `home_corners`, `away_corners`: Corners won by each team.
*   `home_xg_open_play`, `away_xg_open_play`: Expected goals from open play for each team.
*   `home_xg_set_play`, `away_xg_set_play`: Expected goals from set plays for each team.
*   `home_non_penalty_xg`, `away_non_penalty_xg`: Non-penalty expected goals for each team.
*   `home_xg_on_target_xgot`, `away_xg_on_target_xgot`: Expected goals on target for each team.
*   `home_shots_off_target`, `away_shots_off_target`: Shots off target for each team.
*   `home_blocked_shots`, `away_blocked_shots`: Blocked shots for each team.
*   `home_hit_woodwork`, `away_hit_woodwork`: Times each team hit the woodwork.
*   `home_shots_inside_box`, `away_shots_inside_box`: Shots taken inside the box by each team.
*   `home_shots_outside_box`, `away_shots_outside_box`: Shots taken outside the box by each team.
*   `home_passes`, `away_passes`: Total passes made by each team.
*   `home_own_half`, `away_own_half`: Passes made in each team's own half.
*   `home_opposition_half`, `away_opposition_half`: Passes made in the opposition's half for each team.
*   `home_accurate_long_balls`, `away_accurate_long_balls`: Accurate long balls made by each team.
*   `home_accurate_long_balls_pct`, `away_accurate_long_balls_pct`: Percentage of accurate long balls for each team.
*   `home_accurate_crosses`, `away_accurate_crosses`: Accurate crosses made by each team.
*   `home_accurate_crosses_pct`, `away_accurate_crosses_pct`: Percentage of accurate crosses for each team.
*   `home_throws`, `away_throws`: Throw-ins taken by each team.
*   `home_touches_in_opposition_box`, `away_touches_in_opposition_box`: Touches in the opposition box for each team.
*   `home_offsides`, `away_offsides`: Offsides for each team.
*   `home_yellow_cards`, `away_yellow_cards`: Yellow cards for each team.
*   `home_red_cards`, `away_red_cards`: Red cards for each team.
*   `home_tackles_won`, `away_tackles_won`: Tackles won by each team.
*   `home_tackles_won_pct`, `away_tackles_won_pct`: Percentage of tackles won by each team.
*   `home_interceptions`, `away_interceptions`: Interceptions made by each team.
*   `home_blocks`, `away_blocks`: Blocks made by each team.
*   `home_clearances`, `away_clearances`: Clearances made by each team.
*   `home_keeper_saves`, `away_keeper_saves`: Saves made by each team's goalkeeper.
*   `home_duels_won`, `away_duels_won`: Duels won by each team.
*   `home_ground_duels_won`, `away_ground_duels_won`: Ground duels won by each team.
*   `home_ground_duels_won_pct`, `away_ground_duels_won_pct`: Percentage of ground duels won by each team.
*   `home_aerial_duels_won`, `away_aerial_duels_won`: Aerial duels won by each team.
*   `home_aerial_duels_won_pct`, `away_aerial_duels_won_pct`: Percentage of aerial duels won by each team.
*   `home_successful_dribbles`, `away_successful_dribbles`: Successful dribbles made by each team.
*   `home_successful_dribbles_pct`, `away_successful_dribbles_pct`: Percentage of successful dribbles for each team.
*   `stats_processed`: Boolean indicating whether the match statistics have been processed.
*   `player_stats_processed`: Boolean indicating whether the player statistics for the match have been processed.

**Links:**
*   `home_team` and `away_team` link to the `id` column in the `teams` table.
*   `match_id` links to the `match_id` column in the `playermatchstats` table.

---

### `fixtures`

This table contains data for **upcoming** games. It follows the exact same structure as the `matches` table, but the statistical columns (like scores, possession, xG, etc.) will be empty until the match is played and the data is processed.

---

### `playermatchstats` 

This table provides detailed player-level statistics for each match, now including enhanced defensive and contextual metrics.

*   `player_id`: The ID of the player (referencing the `players` table).
*   `match_id`: The ID of the match (referencing the `matches` table).
*   `start_min`: The minute the player entered the pitch (0 for starters).
*   `finish_min`: The minute the player left the pitch (or the final minute of the match if they played the full game).
*   `minutes_played`: Minutes played by the player in the match.
*   `goals`: Goals scored by the player.
*   `assists`: Assists by the player.
*   `penalties_scored`: Number of penalties scored by the player.
*   `penalties_missed`: Number of penalties missed by the player.
*   `total_shots`: Total shots taken by the player.
*   `xg`: Expected goals for the player.
*   `xa`: Expected assists for the player.
*   `xgot`: Expected goals on target for the player.
*   `shots_on_target`: Shots on target by the player.
*   `successful_dribbles`: Successful dribbles by the player.
*   `successful_dribbles_percent`: Percentage of successful dribbles by the player.
*   `big_chances_missed`: Big chances missed by the player.
*   `touches`: Total touches by the player.
*   `touches_opposition_box`: Touches in the opposition box by the player.
*   `accurate_passes`: Accurate passes made by the player.
*   `accurate_passes_percent`: Percentage of accurate passes by the player.
*   `chances_created`: Chances created by the player.
*   `final_third_passes`: Passes into the final third by the player.
*   `accurate_crosses`: Accurate crosses by the player.
*   `accurate_crosses_percent`: Percentage of accurate crosses by the player.
*   `accurate_long_balls`: Accurate long balls by the player.
*   `accurate_long_balls_percent`: Percentage of accurate long balls by the player.
*   `tackles`: Total number of tackles attempted by the player.
*   `tackles_won`: Tackles won by the player.
*   `tackles_won_percent`: Percentage of tackles won by the player.
*   `interceptions`: Interceptions by the player.
*   `recoveries`: Ball recoveries by the player.
*   `blocks`: Blocks by the player.
*   `clearances`: Clearances by the player.
*   `headed_clearances`: Headed clearances by the player.
*   `dribbled_past`: Times the player was dribbled past.
*   `duels_won`: Duels won by the player.
*   `duels_lost`: Duels lost by the player.
*   `ground_duels_won`: Ground duels won by the player.
*   `ground_duels_won_percent`: Percentage of ground duels won by the player.
*   `aerial_duels_won`: Aerial duels won by the player.
*   `aerial_duels_won_percent`: Percentage of aerial duels won by the player.
*   `was_fouled`: Times the player was fouled.
*   `fouls_committed`: Fouls committed by the player.
*   `offsides`: Number of times the player was caught offside.
*   `saves`: Saves made by the player (typically for goalkeepers).
*   `goals_conceded`: Goals conceded by the player's team (for all positions).
*   `team_goals_conceded`: Total goals conceded by the player's team only while the player was on the pitch.
*   `xgot_faced`: Expected goals on target faced by the player (typically for goalkeepers).
*   `goals_prevented`: Goals prevented by the player (typically for goalkeepers).
*   `sweeper_actions`: Sweeper actions performed by the player (typically for goalkeepers).
*   `high_claim`: Number of high claims by a goalkeeper.
*   `gk_accurate_passes`: Accurate passes made by the goalkeeper.
*   `gk_accurate_long_balls`: Accurate long balls made by the goalkeeper.

**Links:**
*   `player_id` links to the `player_id` column in the `players` table.
*   `match_id` links to the `match_id` column in the `matches` table.

---

### `players`

This table contains basic information about each player from the FPL API.

*   `player_code`: The unique code for the player in the FPL API.
*   `player_id`: A unique identifier for each player within this dataset.
*   `first_name`: The player's first name.
*   `second_name`: The player's second name.
*   `web_name`: The player's name as it appears on the FPL website.
*   `team_code`: The FPL code for the player's team.
*   `position`: The player's position (GKP, DEF, MID, FWD).

**Links:**
*   `player_id` links to the `player_id` column in the `playermatchstats` and `playerstats` tables.

---

### `playerstats` This is the equivalent of FPL API Data

This table stores a wide range of FPL player statistics, updated per gameweek.

*   `id`: The ID of the player (referencing `player_id` in the `players` table).
*   `first_name`, `second_name`, `web_name`: The player's names.
*   `status`: The player's availability status (e.g., 'a' for available, 'i' for injured).
*   `news`: Injury or suspension information.
*   `news_added`: Timestamp for when the news was added.
*   `chance_of_playing_next_round`: The player's chance of playing in the next round (%).
*   `chance_of_playing_this_round`: The player's chance of playing in the current round (%).
*   `now_cost`: The player's current cost in the FPL game.
*   `now_cost_rank`, `now_cost_rank_type`: The player's cost rank overall and by position.
*   `cost_change_event`, `cost_change_event_fall`: Price change in the current gameweek.
*   `cost_change_start`, `cost_change_start_fall`: Price change since the start of the season.
*   `selected_by_percent`: The percentage of FPL managers who have selected the player.
*   `selected_rank`, `selected_rank_type`: The player's rank based on selection percentage overall and by position.
*   `total_points`: The player's total FPL points for the season.
*   `event_points`: The player's FPL points for the current gameweek.
*   `points_per_game`: The player's average FPL points per game.
*   `points_per_game_rank`, `points_per_game_rank_type`: The player's rank based on average points per game overall and by position.
*   `minutes`: Total minutes played in the season.
*   `goals_scored`: Total goals scored.
*   `assists`: Total assists.
*   `clean_sheets`: Total clean sheets.
*   `goals_conceded`: Total goals conceded.
*   `own_goals`: Total own goals.
*   `penalties_saved`: Total penalties saved.
*   `penalties_missed`: Total penalties missed.
*   `yellow_cards`: Total yellow cards.
*   `red_cards`: Total red cards.
*   `saves`: Total saves.
*   `starts`: Total matches started.
*   `bonus`: Total bonus points.
*   `bps`: Total Bonus Points System score.
*   `form`: The player's recent form score.
*   `form_rank`, `form_rank_type`: The player's form rank overall and by position.
*   `value_form`: A measure of the player's value based on recent form and cost.
*   `value_season`: A measure of the player's value based on season performance and cost.
*   `dreamteam_count`: The number of times the player has been in the FPL Dream Team.
*   `transfers_in`, `transfers_in_event`: Total and gameweek transfers in.
*   `transfers_out`, `transfers_out_event`: Total and gameweek transfers out.
*   `ep_next`, `ep_this`: Expected points for the next and current gameweek.
*   `expected_goals`, `expected_assists`, `expected_goal_involvements`, `expected_goals_conceded`: Expected performance metrics for the season.
*   `expected_goals_per_90`, `expected_assists_per_90`, `expected_goal_involvements_per_90`, `expected_goals_conceded_per_90`: The same metrics, but normalized per 90 minutes.
*   `influence`, `creativity`, `threat`, `ict_index`: FPL's proprietary metrics for player performance.
*   `influence_rank`, `influence_rank_type`, `creativity_rank`, `creativity_rank_type`, `threat_rank`, `threat_rank_type`, `ict_index_rank`, `ict_index_rank_type`: Ranks for the ICT metrics.
*   `corners_and_indirect_freekicks_order`, `direct_freekicks_order`, `penalties_order`: Player's rank for taking set pieces.
*   `corners_and_indirect_freekicks_text`, `direct_freekicks_text`, `penalties_text`: Descriptive text about set-piece duties.
*   `defensive_contribution`, `defensive_contribution_per_90`: Defensive action metrics.
*   `saves_per_90`, `clean_sheets_per_90`, `goals_conceded_per_90`, `starts_per_90`: Performance metrics normalized per 90 minutes.
*   `gw`: The gameweek these stats apply to.

**Links:**
*   `id` links to the `player_id` in the `players` table.

---

### `gameweeks` (This won't show up until GW2)

This table stores a snapshot of data for every gameweek in the season, sourced from the FPL API.

*   `id`: The gameweek number (1-38).
*   `name`: The name of the gameweek (e.g., "Gameweek 1").
*   `deadline_time`: The official FPL deadline for the gameweek.
*   `deadline_time_epoch`: The deadline time in Unix epoch format.
*   `deadline_time_game_offset`: Game deadline time offset in hours.
*   `average_entry_score`: The average FPL score for all managers in that gameweek.
*   `highest_score`: The highest score achieved by any manager in that gameweek.
*   `finished`: Boolean indicating if the gameweek has finished.
*   `is_previous`, `is_current`, `is_next`: Booleans indicating the status of the gameweek relative to the current time.
*   `chip_plays`: A JSON object detailing the number of times each chip (e.g., wildcard, freehit) was played.
*   `most_selected`: The player ID of the most selected player for that gameweek.
*   `most_transferred_in`: The player ID of the most transferred-in player.
*   `most_captained`: The player ID of the most captained player.
*   `most_vice_captained`: The player ID of the most vice-captained player.
*   `top_element`: The player ID of the top-scoring player of the gameweek.
*   `top_element_info`: A JSON object with the points and ID of the top player.
*   `transfers_made`: The total number of transfers made in that gameweek.
*   `cup_leagues_created`: Boolean indicating if cup leagues were created.
*   `h2h_ko_matches_created`: Boolean indicating if head-to-head knockout matches were created.

**Links:**
*   Player-related columns like `most_selected` link to the `id` in the `playerstats` table.

---

### `teams`

This table contains information about each team from the FPL API.

*   `code`: The team's unique code in the FPL API.
*   `id`: A unique identifier for each team within this dataset.
*   `name`: The full name of the team.
*   `short_name`: The short name (abbreviation) of the team.
*   `strength`: Overall team strength (FPL rating).
*   `strength_overall_home`, `strength_overall_away`: Overall team strength at home vs. away.
*   `strength_attack_home`, `strength_attack_away`: Attacking strength at home vs. away.
*   `strength_defence_home`, `strength_defence_away`: Defensive strength at home vs. away.
*   `pulse_id`: The team's ID on Pulse Live (a sports data provider).
*   `elo`: The team's Elo rating from ClubElo.com.

**Links:**
*   `id` links to `home_team` and `away_team` in the `matches` and `fixtures` tables.

---

### `calculated_features`

This is a **derived, analysis-ready** sheet (not raw FPL/Opta data). It provides one row per player per gameweek with 22 engineered, model-friendly features — rolling form, team/opponent strength and position-specific rollups — computed entirely from the Premier League tables in this repository.

*   **Location**: `data/{season}/By Tournament/Premier League/GW{x}/calculated_features.csv`
*   **Scope**: **Premier League only.** Every feature is derived from Premier League `player_gameweek_stats`, `players`, `playermatchstats`, `matches` and `fixtures`, so the sheet is written only under the Premier League tournament folder and is not produced for the cup / European folders.
*   **Location note**: the sheet lives **only** under `By Tournament/Premier League` — it is intentionally *not* copied into the `By Gameweek` mirror. That mirror also contains other competitions (cups / Europe), and a copy there would wrongly imply cup fixtures are incorporated into the strength/form features, which they are not.
*   **Leakage-safe**: rolling values are `shift(1)`-lagged, so a GW `N` row uses only gameweeks 1..N-1 and can be joined onto GW `N` to *predict* it without leaking the target. GW1 rolling features are therefore NaN. `team_elo`/`opp_elo` are the **pre-match** rating entering GW `N` (already a function of GW 1..N-1 only), so they carry the same no-leakage contract while being populated from GW1.
*   **Per-fixture scale**: the raw `player_gameweek_stats` table sums a player's matches into one row per gameweek, so a double gameweek arrives at ~2× single-fixture scale. Before any rolling feature is computed, GW-summed player stats (points, minutes, xG, xA, defensive contribution, saves, clean sheets, goals, assists, shots on target, box touches, goals prevented) are divided by that team's number of fixtures in the GW, so every rolling feature is a **per-match rate** and double gameweeks don't double it. The divisor is exported as `n_fixtures`. `creativity`/`threat` come from FPL's GW-level table and are not rescaled.
*   **Double / blank gameweeks**: opponent stats are averaged across both opponents (`has_double_gw = true`); a blank gameweek (no fixture that GW) leaves the team/opponent features NaN and `n_fixtures = 1`.
*   **Position-specific columns** (the `gkp_`, `def_`, `mid_`, `fwd_` prefixes) are populated only for the relevant position and NaN otherwise.

**Column data dictionary:**

| Column | Type | Description | Window |
| --- | --- | --- | --- |
| `player_id` | int | Player id (links to `player_id` in `players`, `id` in `playerstats`). | — |
| `gameweek` | int | Gameweek (1–38) the features are attached to. | — |
| `position` | string | Player position (`GKP`/`DEF`/`MID`/`FWD`). | — |
| `team_code` | int | FPL team code of the player's club. | — |
| `n_fixtures` | int | Number of fixtures the player's club has in this gameweek (1 for a blank/normal GW, 2+ for a double GW). The per-fixture divisor for GW-summed stats. | this GW |
| `points_roll3` | float | Mean FPL points (`event_points`), per fixture. | prior 3 GW |
| `minutes_roll3` | float | Mean minutes played, per fixture. | prior 3 GW |
| `xg_roll3` | float | Mean match expected goals (xG), per fixture. | prior 3 GW |
| `xa_roll3` | float | Mean match expected assists (xA), per fixture. | prior 3 GW |
| `defcon_roll3` | float | Mean defensive contribution (CBIT), per fixture. | prior 3 GW |
| `team_elo` | float | Player's club Elo entering this gameweek's fixture(s) — the pre-match rating (mean across a double GW's fixtures), used unshifted. | this GW (pre-match) |
| `opp_elo` | float | Opponent's Elo entering this gameweek's fixture(s) — pre-match rating (averaged over a double GW's opponents), used unshifted. | this GW (pre-match) |
| `team_xg_for_roll5` | float | Player's club rolling mean xG for. | prior 5 GW |
| `team_xg_against_roll5` | float | Player's club rolling mean xG conceded. | prior 5 GW |
| `opp_xg_against_roll5` | float | Opponent's rolling mean xG conceded (averaged over a double GW's opponents). | prior 5 GW |
| `has_double_gw` | bool | `True`/`False`; `True` if the club has 2+ fixtures in this gameweek. Serialized as `True`/`False` (matching repo convention, e.g. `finished` in `matches`). | this GW |
| `gkp_saves_roll3` | float | GKP only: mean saves, per fixture. | prior 3 GW |
| `gkp_goals_prevented_roll3` | float | GKP only: mean goals prevented (xGOT faced minus goals conceded), per fixture. | prior 3 GW |
| `def_clean_sheet_roll5` | float | DEF only: mean clean sheets, per fixture. | prior 5 GW |
| `def_attacking_return_rate` | float | DEF only: mean attacking returns (goals + assists), per fixture. | prior 5 GW |
| `mid_creativity_roll3` | float | MID only: mean creativity (GW-level, not per-fixture rescaled). | prior 3 GW |
| `mid_threat_roll3` | float | MID only: mean threat (GW-level, not per-fixture rescaled). | prior 3 GW |
| `mid_shots_on_target_roll3` | float | MID only: mean shots on target, per fixture. | prior 3 GW |
| `mid_touches_box_roll3` | float | MID only: mean touches in the opposition box, per fixture. | prior 3 GW |
| `fwd_xg_roll3` | float | FWD only: mean match xG, per fixture. | prior 3 GW |
| `fwd_shots_on_target_roll3` | float | FWD only: mean shots on target, per fixture. | prior 3 GW |
| `fwd_touches_box_roll3` | float | FWD only: mean touches in the opposition box, per fixture. | prior 3 GW |

**Links:**
*   `player_id` links to `player_id` in the `players` table and `id` in the `playerstats` / `player_gameweek_stats` tables.


</details>
