# - Pre-season friendlies export under 'By Tournament/Friendlies/GW0' only;
#   'By Gameweek' folders remain league gameweeks 1-38.
# - Matches with missing gameweeks are inferred from kickoff_time vs GW deadlines.

import os
import sys
import pandas as pd
from supabase import create_client, Client
import logging
from datetime import date, datetime, timezone

from clean_playermatchstats import sanitize as sanitize_playermatchstats

# --- Configuration ---


def derive_season(today: date | None = None) -> str:
    """
    Current season folder name, e.g. "2026-2027". The season flips on
    1 July, matching the scraper repo's season derivation. Override with
    the SEASON env var (e.g. SEASON=2025-2026) to backfill an old season.
    """
    override = os.environ.get("SEASON")
    if override:
        return override
    if today is None:
        today = date.today()
    start = today.year if today.month >= 7 else today.year - 1
    return f"{start}-{start + 1}"


SEASON = derive_season()
BASE_DATA_PATH = os.path.join('data', SEASON)
TOURNAMENT_NAME_MAP = {
    'friendly': 'Friendlies',
    'premier-league': 'Premier League',
    'champions-league': 'Champions League',
    '25-26-cl': 'Champions League',
    'prem': 'Premier League',
    'community-shield': 'Community Shield',
    'uefa-super-cup': 'Uefa Super Cup',
    'efl-cup' : 'EFL Cup',
    'europa-league': 'Europa League',
    'conference-league' : 'Conference League',
    'fa-cup': 'FA Cup'
}

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# --- Column Definitions for Stat Calculation ---
CUMULATIVE_COLS = [
    'total_points', 'minutes', 'goals_scored', 'assists', 'clean_sheets',
    'goals_conceded', 'own_goals', 'penalties_saved', 'penalties_missed',
    'yellow_cards', 'red_cards', 'saves', 'starts', 'bonus', 'bps',
    'transfers_in', 'transfers_out', 'dreamteam_count', 'expected_goals',
    'expected_assists', 'expected_goal_involvements', 'expected_goals_conceded',
    'influence', 'creativity', 'threat', 'ict_index', 'tackles',
    'clearances_blocks_interceptions', 'recoveries', 'defensive_contribution'
]
# Negative gameweek diffs at or above this floor are genuine FPL stat
# corrections (rescinded bonus, post-match reviews, etc. — worst observed in
# 2025-26 is bps -23) and are kept as-is. Anything below it is an upstream
# counter reset (e.g. the GW2 transfers_in reset of ~-6.4M), not a real
# per-GW change, and is treated as no change for that gameweek.
CORRECTION_FLOOR = -50

ID_COLS = ['id', 'first_name', 'second_name', 'web_name']
SNAPSHOT_COLS = [
    'status', 'news', 'news_added', 'now_cost', 'now_cost_rank', 'now_cost_rank_type',
    'selected_by_percent', 'selected_rank', 'selected_rank_type', 'form', 'form_rank',
    'form_rank_type', 'event_points', 'cost_change_event', 'cost_change_event_fall',
    'cost_change_start', 'cost_change_start_fall', 'transfers_in_event', 'transfers_out_event',
    'value_form', 'value_season', 'ep_next', 'ep_this', 'points_per_game',
    'points_per_game_rank', 'points_per_game_rank_type', 'chance_of_playing_next_round',
    'chance_of_playing_this_round', 'influence_rank', 'influence_rank_type',
    'creativity_rank', 'creativity_rank_type', 'threat_rank', 'threat_rank_type',
    'ict_index_rank', 'ict_index_rank_type', 'corners_and_indirect_freekicks_order',
    'direct_freekicks_order', 'penalties_order', 'set_piece_threat',
    'corners_and_indirect_freekicks_text', 'direct_freekicks_text', 'penalties_text',
    'expected_goals_per_90', 'expected_assists_per_90', 'expected_goal_involvements_per_90',
    'expected_goals_conceded_per_90', 'saves_per_90', 'clean_sheets_per_90',
    'goals_conceded_per_90', 'starts_per_90', 'defensive_contribution_per_90', 'gw'
]

# --- Master playerstats schema - all 87 columns in proper order ---
PLAYERSTATS_COLUMNS = [
    'id', 'status', 'chance_of_playing_next_round', 'chance_of_playing_this_round',
    'now_cost', 'now_cost_rank', 'now_cost_rank_type', 'cost_change_event',
    'cost_change_event_fall', 'cost_change_start', 'cost_change_start_fall',
    'selected_by_percent', 'selected_rank', 'selected_rank_type', 'total_points',
    'event_points', 'points_per_game', 'points_per_game_rank', 'points_per_game_rank_type',
    'bonus', 'bps', 'form', 'form_rank', 'form_rank_type', 'value_form', 'value_season',
    'dreamteam_count', 'transfers_in', 'transfers_in_event', 'transfers_out',
    'transfers_out_event', 'ep_next', 'ep_this', 'expected_goals', 'expected_assists',
    'expected_goal_involvements', 'expected_goals_conceded', 'expected_goals_per_90',
    'expected_assists_per_90', 'expected_goal_involvements_per_90',
    'expected_goals_conceded_per_90', 'influence', 'influence_rank', 'influence_rank_type',
    'creativity', 'creativity_rank', 'creativity_rank_type', 'threat', 'threat_rank',
    'threat_rank_type', 'ict_index', 'ict_index_rank', 'ict_index_rank_type',
    'corners_and_indirect_freekicks_order', 'direct_freekicks_order', 'penalties_order',
    'gw', 'set_piece_threat', 'first_name', 'second_name', 'web_name', 'news',
    'news_added', 'minutes', 'goals_scored', 'assists', 'clean_sheets', 'goals_conceded',
    'own_goals', 'penalties_saved', 'penalties_missed', 'yellow_cards', 'red_cards',
    'saves', 'starts', 'defensive_contribution', 'corners_and_indirect_freekicks_text',
    'direct_freekicks_text', 'penalties_text', 'saves_per_90', 'clean_sheets_per_90',
    'goals_conceded_per_90', 'starts_per_90', 'defensive_contribution_per_90', 'tackles',
    'clearances_blocks_interceptions', 'recoveries'
]

# --- Master playermatchstats schema - all 64 columns in proper order ---
PLAYERMATCHSTATS_COLUMNS = [
    'player_id', 'match_id', 'minutes_played', 'goals', 'assists', 'total_shots', 'xg', 'xa',
    'shots_on_target', 'successful_dribbles', 'big_chances_missed', 'touches_opposition_box',
    'touches', 'accurate_passes', 'accurate_passes_percent', 'chances_created',
    'final_third_passes', 'accurate_crosses', 'accurate_crosses_percent', 'accurate_long_balls',
    'accurate_long_balls_percent', 'tackles_won', 'interceptions', 'recoveries', 'blocks',
    'clearances', 'headed_clearances', 'dribbled_past', 'duels_won', 'duels_lost',
    'ground_duels_won', 'ground_duels_won_percent', 'aerial_duels_won', 'aerial_duels_won_percent',
    'was_fouled', 'fouls_committed', 'saves', 'goals_conceded', 'xgot_faced', 'goals_prevented',
    'sweeper_actions', 'gk_accurate_passes', 'gk_accurate_long_balls', 'dispossessed',
    'high_claim', 'corners', 'saves_inside_box', 'offsides', 'successful_dribbles_percent',
    'tackles_won_percent', 'xgot', 'tackles', 'start_min', 'finish_min', 'team_goals_conceded',
    'penalties_scored', 'penalties_missed', 'top_speed', 'distance_covered', 'walking_distance',
    'running_distance', 'sprinting_distance', 'number_of_sprints', 'defensive_contributions'
]


def initialize_supabase_client() -> Client:
    """Initializes and returns a Supabase client."""
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    if not supabase_url or not supabase_key:
        logger.error("❌ Error: SUPABASE_URL and SUPABASE_KEY must be set.")
        sys.exit(1)
    return create_client(supabase_url, supabase_key)

def ensure_playerstats_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Ensures dataframe has all playerstats columns in correct order, adding missing ones as NaN."""
    for col in PLAYERSTATS_COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA
    return df[PLAYERSTATS_COLUMNS]

def ensure_playermatchstats_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Ensures dataframe has all playermatchstats columns in correct order, adding missing ones as NaN."""
    for col in PLAYERMATCHSTATS_COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA
    return df[PLAYERMATCHSTATS_COLUMNS]

# Bzzoiro match enrichment. Column order is taken from the 2025-2026
# files already in the repo so both seasons read identically - those were
# loaded once by hand and never wired into this script, which is why
# 2026-2027 had none of it.
#
# Not essential data: a season that has not been ingested simply has no
# rows, and fetch_all_rows already returns an empty frame on error, so a
# missing table degrades to empty files rather than failing the export.
#
# Two places the column list deliberately departs from the table:
#   - the surrogate `id` on bzzoiro_lineups and bzzoiro_average_positions
#     is a storage detail with no meaning to a reader, so it is dropped;
#   - bzzoiro_lineups.confidence has no 2025-2026 counterpart. It is left
#     out to keep the header identical across seasons; add it to both if
#     it is ever wanted.
# match_enrichment goes the other way: 2025-2026 carries five columns
# (home/away_shot_model_xg, incident_timing_coverage, unlocated_card_count,
# quarantined_incident_count) that this schema has no home for, and two
# it lacks (attendance, lineup_confidence). Exporting what the table
# actually holds beats reindexing five columns of guaranteed blanks.
BZZOIRO_EXPORTS = {
    'shots.csv': ('bzzoiro_shots', [
        'match_id', 'shot_index', 'minute', 'added_time', 'is_home',
        'player_id', 'player_name', 'outcome', 'situation', 'body_part',
        'xg', 'xgot', 'start_x', 'start_y',
        'goal_mouth_y', 'goal_mouth_z', 'goal_mouth_location',
    ]),
    'momentum.csv': ('bzzoiro_momentum', ['match_id', 'minute', 'value']),
    'xg_by_minute.csv': ('bzzoiro_xg_by_minute', [
        'match_id', 'minute', 'home_xg', 'away_xg',
        'home_cumulative_xg', 'away_cumulative_xg',
    ]),
    'lineups.csv': ('bzzoiro_lineups', [
        'match_id', 'team_side', 'team_code', 'player_id', 'player_name',
        'position', 'jersey_number', 'is_starting', 'formation',
        'lineup_status',
    ]),
    'incidents.csv': ('bzzoiro_incidents', [
        'match_id', 'incident_index', 'incident_type', 'minute', 'added_time',
        'team_side', 'player_id', 'player_name',
        'secondary_player_id', 'secondary_player_name',
        'assist_player_id', 'assist_player_name',
        'card_type', 'goal_type', 'home_score', 'away_score', 'text',
    ]),
    'average_positions.csv': ('bzzoiro_average_positions', [
        'match_id', 'team_side', 'player_id', 'player_name',
        'jersey_number', 'position', 'x', 'y',
    ]),
    'match_enrichment.csv': ('bzzoiro_match_enrichment', [
        'match_id', 'travel_distance_km', 'weather_description',
        'temperature_c', 'wind_speed', 'pitch_condition', 'is_local_derby',
        'is_neutral_ground', 'attendance', 'lineup_status',
        'lineup_confidence',
    ]),
    'player_match_enrichment.csv': ('bzzoiro_player_match_enrichment', [
        'player_id', 'match_id', 'player_name', 'rating', 'possession_lost',
        'attacking_shots_blocked', 'total_passes', 'total_long_balls',
        'total_crosses', 'total_dribbles', 'ground_duels_lost',
        'aerial_duels_lost', 'yellow_cards', 'red_cards',
        'goalkeeper_punches',
    ]),
}


def fetch_bzzoiro_exports(supabase: Client) -> dict:
    """{filename: DataFrame} for the enrichment tables, columns normalised."""
    frames = {}
    for filename, (table, columns) in BZZOIRO_EXPORTS.items():
        df = fetch_all_rows(supabase, table)
        # reindex rather than select: it fixes the column order AND
        # supplies any column the table is missing, so the header is the
        # same whether the fetch returned rows, nothing, or an error.
        frames[filename] = df.reindex(columns=columns)
    return frames


def fetch_all_rows(supabase: Client, table_name: str) -> pd.DataFrame:
    """Fetches all rows from a Supabase table, handling pagination."""
    logger.info(f"Fetching latest data for '{table_name}'...")
    all_data = []
    offset = 0
    try:
        while True:
            response = supabase.table(table_name).select("*").range(offset, offset + 1000 - 1).execute()
            batch_data = response.data
            all_data.extend(batch_data)
            if len(batch_data) < 1000:
                break
            offset += 1000
        df = pd.DataFrame(all_data)
        logger.info(f"  > Fetched a total of {len(df)} rows.")
        return df
    except Exception as e:
        logger.error(f"An error occurred while fetching from {table_name}: {e}")
        return pd.DataFrame()

def calculate_discrete_gameweek_stats():
    """
    Calculates discrete gameweek stats for both the main 'By Gameweek'
    folders and all 'By Tournament' sub-folders.
    """
    logger.info("\n--- 4. Calculating and Saving Discrete Gameweek Player Stats ---")
    by_gameweek_path = os.path.join(BASE_DATA_PATH, 'By Gameweek')
    by_tournament_path = os.path.join(BASE_DATA_PATH, 'By Tournament')
    output_filename = 'player_gameweek_stats.csv'

    if not os.path.isdir(by_gameweek_path):
        logger.error(f"  > Main 'By Gameweek' directory not found. Aborting calculation.")
        return

    # --- Part 1: Process 'By Gameweek' folders ---
    logger.info("\nProcessing main 'By Gameweek' directory...")
    try:
        gameweek_dirs = sorted([d for d in os.listdir(by_gameweek_path) if d.startswith('GW')], key=lambda x: int(x[2:]))
    except (ValueError, IndexError):
        logger.error("  > Could not parse gameweek numbers. Skipping 'By Gameweek' processing.")
        gameweek_dirs = []

    for i, gw_dir in enumerate(gameweek_dirs):
        current_stats_path = os.path.join(by_gameweek_path, gw_dir, 'playerstats.csv')
        if not os.path.exists(current_stats_path):
            logger.warning(f"  > {gw_dir}: playerstats.csv not found, skipping.")
            continue
        
        current_df = pd.read_csv(current_stats_path)
        
        if i == 0:
            logger.info(f"Processing baseline: {gw_dir}...")
            final_cols = ID_COLS + SNAPSHOT_COLS + CUMULATIVE_COLS
            existing_cols = [col for col in final_cols if col in current_df.columns]
            output_df = current_df[existing_cols]
        else:
            prev_gw_dir = gameweek_dirs[i-1]
            logger.info(f"Processing {gw_dir} (comparing with {prev_gw_dir})...")
            prev_stats_path = os.path.join(by_gameweek_path, prev_gw_dir, 'playerstats.csv')

            if not os.path.exists(prev_stats_path):
                logger.warning(f"  > Previous gameweek stats not found for {gw_dir}. Skipping.")
                continue

            prev_df = pd.read_csv(prev_stats_path)
            # Only use columns that exist in previous dataframe
            prev_cols_to_merge = [col for col in ID_COLS + CUMULATIVE_COLS if col in prev_df.columns]
            merged_df = pd.merge(current_df, prev_df[prev_cols_to_merge], on='id', how='left', suffixes=('', '_prev'))

            # total_points has an exact per-GW value in event_points already —
            # use it directly instead of diffing the cumulative season total.
            if 'total_points' in merged_df.columns and 'event_points' in merged_df.columns:
                merged_df['total_points'] = merged_df['event_points']

            for col in CUMULATIVE_COLS:
                if col == 'total_points':
                    continue
                if col in merged_df.columns and f"{col}_prev" in merged_df.columns:
                    merged_df[f"{col}_prev"] = merged_df[f"{col}_prev"].fillna(0)
                    # Calculate the difference
                    diff = merged_df[col] - merged_df[f"{col}_prev"]
                    # Keep negative diffs down to CORRECTION_FLOOR — they are
                    # genuine FPL stat corrections. Below the floor is an
                    # upstream counter reset, so treat it as no change (0).
                    merged_df[col] = diff.where(diff >= CORRECTION_FLOOR, 0)

            final_cols = ID_COLS + SNAPSHOT_COLS + CUMULATIVE_COLS
            existing_final_cols = [col for col in final_cols if col in merged_df.columns]
            output_df = merged_df[existing_final_cols]

        output_path = os.path.join(by_gameweek_path, gw_dir, output_filename)
        output_df.to_csv(output_path, index=False)
        logger.info(f"  > Saved calculated stats for {gw_dir}.")

    # --- Part 2: Process 'By Tournament' folders ---
    logger.info("\nProcessing 'By Tournament' sub-directories...")
    if not os.path.isdir(by_tournament_path):
        logger.warning("  > 'By Tournament' directory not found. Skipping.")
        return
        
    for tournament_name in os.listdir(by_tournament_path):
        tournament_dir = os.path.join(by_tournament_path, tournament_name)
        if not os.path.isdir(tournament_dir): continue

        logger.info(f"Scanning Tournament: {tournament_name}...")
        try:
            tournament_gw_dirs = sorted([d for d in os.listdir(tournament_dir) if d.startswith('GW')], key=lambda x: int(x[2:]))
        except (ValueError, IndexError):
            logger.error(f"  > Could not parse gameweek numbers for {tournament_name}. Skipping.")
            continue

        for gw_dir in tournament_gw_dirs:
            gw_num = int(gw_dir[2:])
            if gw_num == 0:
                # Pre-season: no FPL playerstats exist yet, so there is
                # nothing to diff (playermatchstats.csv carries the data).
                continue
            current_stats_path = os.path.join(tournament_dir, gw_dir, 'playerstats.csv')
            if not os.path.exists(current_stats_path):
                logger.warning(f"  > {tournament_name}/{gw_dir}: playerstats.csv not found, skipping.")
                continue

            current_df = pd.read_csv(current_stats_path)

            if gw_num == 1:
                final_cols = ID_COLS + SNAPSHOT_COLS + CUMULATIVE_COLS
                existing_cols = [col for col in final_cols if col in current_df.columns]
                output_df = current_df[existing_cols]
            else:
                prev_stats_path = os.path.join(by_gameweek_path, f'GW{gw_num - 1}', 'playerstats.csv')
                if not os.path.exists(prev_stats_path):
                    logger.warning(f"  > {tournament_name}/{gw_dir}: Baseline stats from GW{gw_num - 1} not found. Skipping.")
                    continue
                
                prev_df = pd.read_csv(prev_stats_path)
                # Only use columns that exist in previous dataframe
                prev_cols_to_merge = [col for col in ID_COLS + CUMULATIVE_COLS if col in prev_df.columns]
                merged_df = pd.merge(current_df, prev_df[prev_cols_to_merge], on='id', how='left', suffixes=('', '_prev'))

                # total_points has an exact per-GW value in event_points already —
                # use it directly instead of diffing the cumulative season total.
                if 'total_points' in merged_df.columns and 'event_points' in merged_df.columns:
                    merged_df['total_points'] = merged_df['event_points']

                for col in CUMULATIVE_COLS:
                    if col == 'total_points':
                        continue
                    if col in merged_df.columns and f"{col}_prev" in merged_df.columns:
                        merged_df[f"{col}_prev"] = merged_df[f"{col}_prev"].fillna(0)
                        # Calculate the difference
                        diff = merged_df[col] - merged_df[f"{col}_prev"]
                        # Keep negative diffs down to CORRECTION_FLOOR — they are
                        # genuine FPL stat corrections. Below the floor is an
                        # upstream counter reset, so treat it as no change (0).
                        merged_df[col] = diff.where(diff >= CORRECTION_FLOOR, 0)

                final_cols = ID_COLS + SNAPSHOT_COLS + CUMULATIVE_COLS
                existing_final_cols = [col for col in final_cols if col in merged_df.columns]
                output_df = merged_df[existing_final_cols]
            
            output_path = os.path.join(tournament_dir, gw_dir, output_filename)
            output_df.to_csv(output_path, index=False)
            logger.info(f"  > Saved calculated stats for {tournament_name}/{gw_dir}.")


def validate_gameweek_stats():
    """
    Independently re-derives every player_gameweek_stats.csv from the
    playerstats.csv snapshots and reports any mismatch. Guards against the
    negative-diff corruption (issues #48/#55) silently returning: the export
    fails loudly instead of committing corrupt per-gameweek data.
    Returns the number of violations found.
    """
    logger.info("\n--- 5. Validating Discrete Gameweek Player Stats ---")
    by_gameweek_path = os.path.join(BASE_DATA_PATH, 'By Gameweek')
    violations = 0
    try:
        gameweek_dirs = sorted([d for d in os.listdir(by_gameweek_path) if d.startswith('GW')], key=lambda x: int(x[2:]))
    except (FileNotFoundError, ValueError, IndexError):
        logger.error("  > Could not scan 'By Gameweek' directory for validation.")
        return 1

    for i, gw_dir in enumerate(gameweek_dirs):
        out_path = os.path.join(by_gameweek_path, gw_dir, 'player_gameweek_stats.csv')
        if not os.path.exists(out_path):
            continue
        out_df = pd.read_csv(out_path)

        # Invariant 1: total_points must be the exact per-GW event_points value.
        if 'total_points' in out_df.columns and 'event_points' in out_df.columns:
            bad = out_df[out_df['total_points'].fillna(0) != out_df['event_points'].fillna(0)]
            if not bad.empty:
                violations += len(bad)
                sample = bad.iloc[0]
                logger.error(f"  > {gw_dir}: {len(bad)} rows where total_points != event_points "
                             f"(e.g. {sample.get('web_name', sample.get('id'))}: "
                             f"{sample['total_points']} vs {sample['event_points']})")

        # Invariant 2: every cumulative column matches an independent
        # recomputation from the raw snapshots (diff, floored at CORRECTION_FLOOR).
        if i == 0:
            continue
        cur_path = os.path.join(by_gameweek_path, gw_dir, 'playerstats.csv')
        prev_path = os.path.join(by_gameweek_path, gameweek_dirs[i - 1], 'playerstats.csv')
        if not (os.path.exists(cur_path) and os.path.exists(prev_path)):
            continue
        cur_df = pd.read_csv(cur_path)
        prev_df = pd.read_csv(prev_path)
        cols = [c for c in CUMULATIVE_COLS if c != 'total_points'
                and c in cur_df.columns and c in prev_df.columns and c in out_df.columns]
        merged = pd.merge(cur_df[['id'] + cols], prev_df[['id'] + cols],
                          on='id', how='left', suffixes=('', '_prev'))
        merged = pd.merge(merged, out_df[['id'] + cols].rename(columns={c: f"{c}_out" for c in cols}),
                          on='id', how='inner')
        for col in cols:
            diff = merged[col] - merged[f"{col}_prev"].fillna(0)
            expected = diff.where(diff >= CORRECTION_FLOOR, 0)
            bad = merged[(expected - merged[f"{col}_out"]).abs() > 1e-6]
            if not bad.empty:
                violations += len(bad)
                logger.error(f"  > {gw_dir}: {len(bad)} rows where '{col}' does not match recomputation "
                             f"(e.g. id={bad.iloc[0]['id']}: file has {bad.iloc[0][f'{col}_out']}, "
                             f"expected {expected.loc[bad.index[0]]})")

    if violations:
        logger.error(f"❌ Validation failed with {violations} violation(s).")
    else:
        logger.info("  > All gameweek stat files passed validation.")
    return violations


def main():
    """
    Runs the full, corrected data export pipeline with nuanced historical locking
    based on the 'finished' status of a gameweek.
    """
    logger.info(f"--- Starting Comprehensive Data Update for Season {SEASON} ---")
    logger.info(f"Timestamp: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")

    supabase = initialize_supabase_client()

    # --- Fetch ALL data at the beginning ---
    gameweeks_df = fetch_all_rows(supabase, 'gameweeks')
    players_df = fetch_all_rows(supabase, 'players')
    playerstats_df = fetch_all_rows(supabase, 'playerstats')
    teams_df = fetch_all_rows(supabase, 'teams')
    matches_df = fetch_all_rows(supabase, 'matches')
    playermatchstats_df = fetch_all_rows(supabase, 'playermatchstats')
    bzzoiro_dfs = fetch_bzzoiro_exports(supabase)

    essential_dfs = [gameweeks_df, players_df, playerstats_df, teams_df, matches_df]
    if any(df.empty for df in essential_dfs):
        logger.error("❌ Critical: One or more essential tables could not be fetched. Aborting.")
        sys.exit(1)

    # playermatchstats is legitimately empty at the start of a season (no
    # matches played yet). An empty Supabase result has no columns at all,
    # which would crash every ['match_id'] lookup below - normalize it to
    # the canonical column set so filters return empty frames instead.
    if playermatchstats_df.empty:
        logger.info("  > 'playermatchstats' is empty (season not started?) - continuing with empty stats.")
        playermatchstats_df = ensure_playermatchstats_columns(pd.DataFrame())

    # Correct the known upstream defects (phantom appearances, null minutes on
    # non-appearances, timelines that contradict minutes_played) once, here,
    # so every file written below inherits the cleaned rows. See
    # scripts/clean_playermatchstats.py for what is fixed and why.
    logger.info("\n--- Sanitising playermatchstats ---")
    playermatchstats_df = sanitize_playermatchstats(
        playermatchstats_df, players_df, matches_df, logger=logger
    )

    # --- Data Pre-processing ---
    def extract_tournament_slug(match_id):
        if not isinstance(match_id, str): return None
        for slug in TOURNAMENT_NAME_MAP.keys():
            if slug in match_id:
                return slug
        return None
    matches_df['tournament'] = matches_df['match_id'].apply(extract_tournament_slug)

    # --- Infer missing gameweeks from kickoff_time ---
    missing_gw_count = matches_df['gameweek'].isna().sum()
    if missing_gw_count > 0 and 'kickoff_time' in matches_df.columns:
        logger.info(f"\nInferring gameweek for {missing_gw_count} matches with missing gameweek...")
        gw_deadlines = gameweeks_df[['id', 'deadline_time']].copy()
        gw_deadlines['deadline_time'] = pd.to_datetime(gw_deadlines['deadline_time'], utc=True)
        gw_deadlines = gw_deadlines.sort_values('deadline_time')

        def infer_gameweek(kickoff):
            if pd.isna(kickoff) or kickoff is None:
                return None
            try:
                kickoff_dt = pd.to_datetime(kickoff, utc=True)
            except Exception:
                return None
            # Find the latest deadline that is before or equal to the kickoff
            valid = gw_deadlines[gw_deadlines['deadline_time'] <= kickoff_dt]
            if valid.empty:
                return gw_deadlines['id'].iloc[0]  # Before first deadline, assign GW1
            return valid['id'].iloc[-1]

        mask = matches_df['gameweek'].isna()
        matches_df.loc[mask, 'gameweek'] = matches_df.loc[mask, 'kickoff_time'].apply(infer_gameweek)
        inferred = missing_gw_count - matches_df['gameweek'].isna().sum()
        logger.info(f"  > Inferred gameweek for {inferred} matches.")

    logger.info(f"  > Processing {len(matches_df)} matches (incl. pre-season GW0 friendlies).")

    # --- 1. Update Master Data Files (These are always the latest) ---
    logger.info("\n--- 1. Updating Master Data Files ---")
    os.makedirs(BASE_DATA_PATH, exist_ok=True)
    gameweeks_df.to_csv(os.path.join(BASE_DATA_PATH, 'gameweek_summaries.csv'), index=False)
    players_df.to_csv(os.path.join(BASE_DATA_PATH, 'players.csv'), index=False)
    # Ensure playerstats has all columns in consistent order
    playerstats_normalized = ensure_playerstats_columns(playerstats_df)
    playerstats_normalized.to_csv(os.path.join(BASE_DATA_PATH, 'playerstats.csv'), index=False)
    teams_df.to_csv(os.path.join(BASE_DATA_PATH, 'teams.csv'), index=False)
    logger.info("  > Master files updated successfully.")

    # --- Maintain per-gameweek team membership history (issue #54) ---
    # The FPL API only exposes a player's *current* team, so mid-season
    # transfers would otherwise get stamped onto every historical gameweek
    # whenever folders are regenerated. Team membership is recorded per
    # gameweek here instead: finished gameweeks keep their recorded team
    # forever, while open and future gameweeks track the current roster.
    team_history_path = os.path.join(BASE_DATA_PATH, 'team_history.csv')
    if os.path.exists(team_history_path):
        team_history_df = pd.read_csv(team_history_path)
    else:
        team_history_df = pd.DataFrame(columns=['player_id', 'gw', 'team_code'])
    finished_gw_ids = set(gameweeks_df.loc[gameweeks_df['finished'] == True, 'id'].dropna().astype(int))
    current_teams = players_df[['player_id', 'team_code']].dropna().astype(int)
    history_frames = []
    for hist_gw in sorted(gameweeks_df['id'].dropna().astype(int)):
        recorded = team_history_df[team_history_df['gw'] == hist_gw]
        if hist_gw in finished_gw_ids and not recorded.empty:
            history_frames.append(recorded[['player_id', 'gw', 'team_code']])
        else:
            snapshot = current_teams.copy()
            snapshot['gw'] = hist_gw
            history_frames.append(snapshot[['player_id', 'gw', 'team_code']])
    team_history_df = pd.concat(history_frames, ignore_index=True).sort_values(['gw', 'player_id'])
    team_history_df.to_csv(team_history_path, index=False)
    logger.info("  > Per-gameweek team membership history updated.")


    # Helper function to handle the nuanced file writing logic
    def write_gameweek_files(gw_path, gw, is_finished, gw_dfs):
        os.makedirs(gw_path, exist_ok=True)

        gw_matches, gw_playermatchstats, gw_playerstats = gw_dfs

        # Always write the dynamic data files
        gw_matches.to_csv(os.path.join(gw_path, 'matches.csv'), index=False)
        # Ensure playermatchstats has all columns in consistent order
        gw_playermatchstats_normalized = ensure_playermatchstats_columns(gw_playermatchstats)
        gw_playermatchstats_normalized.to_csv(os.path.join(gw_path, 'playermatchstats.csv'), index=False)
        gw_matches.to_csv(os.path.join(gw_path, 'fixtures.csv'), index=False)
        # Ensure playerstats has all columns in consistent order
        gw_playerstats_normalized = ensure_playerstats_columns(gw_playerstats)
        gw_playerstats_normalized.to_csv(os.path.join(gw_path, 'playerstats.csv'), index=False)

        # Enrichment goes with the dynamic files, not the locked snapshot:
        # Bzzoiro can publish a match late, and a finished gameweek must
        # still be able to receive it.
        gw_match_ids = set(gw_matches['match_id'].dropna())
        for filename, (_table, columns) in BZZOIRO_EXPORTS.items():
            frame = bzzoiro_dfs[filename]
            rows = frame[frame['match_id'].isin(gw_match_ids)]
            rows.to_csv(os.path.join(gw_path, filename), index=False)

        players_path = os.path.join(gw_path, 'players.csv')
        teams_path = os.path.join(gw_path, 'teams.csv')

        if is_finished and os.path.exists(players_path) and os.path.exists(teams_path):
            logger.info(f"  > Snapshot for finished GW{gw} is locked. Dynamic data updated.")
        else:
            if not is_finished:
                logger.info(f"  > Updating all files for open GW{gw}...")
            else:
                 logger.info(f"  > Writing final historical snapshot for newly finished GW{gw}...")
            # Write the roster with each player's team as of THIS gameweek,
            # so regenerating a folder never stamps current teams onto
            # historical gameweeks (issue #54).
            gw_players_df = players_df
            overrides = team_history_df.loc[team_history_df['gw'] == gw, ['player_id', 'team_code']]
            if not overrides.empty:
                gw_players_df = players_df.merge(
                    overrides.rename(columns={'team_code': 'gw_team_code'}), on='player_id', how='left')
                gw_players_df['team_code'] = (
                    gw_players_df['gw_team_code'].fillna(gw_players_df['team_code']).astype('Int64'))
                gw_players_df = gw_players_df.drop(columns=['gw_team_code'])
            gw_players_df.to_csv(players_path, index=False)
            teams_df.to_csv(teams_path, index=False)


    # --- 2. Populate 'By Tournament' Folders ---
    logger.info("\n--- 2. Populating 'By Tournament' Folders ---")
    unique_tournaments = matches_df['tournament'].dropna().unique()
    for slug in unique_tournaments:
        folder_name = TOURNAMENT_NAME_MAP.get(slug, slug.replace('-', ' ').title())
        logger.info(f"Processing Tournament: {folder_name}...")
        
        tournament_matches = matches_df[matches_df['tournament'] == slug]
        gws_in_tournament = sorted(tournament_matches['gameweek'].dropna().unique().astype(int))

        for gw in gws_in_tournament:
            if gw == 0:
                # Pre-season (GW0) is not an FPL gameweek: treat it as never
                # finished so friendly data keeps refreshing all summer.
                is_finished = False
            elif gw not in gameweeks_df['id'].values:
                continue
            else:
                is_finished = gameweeks_df.loc[gameweeks_df['id'] == gw, 'finished'].iloc[0]
            tournament_gw_path = os.path.join(BASE_DATA_PATH, 'By Tournament', folder_name, f'GW{gw}')
            
            gw_tournament_matches = tournament_matches[tournament_matches['gameweek'] == gw]
            match_ids = gw_tournament_matches['match_id'].unique().tolist()
            gw_tournament_playerstats = playermatchstats_df[playermatchstats_df['match_id'].isin(match_ids)]
            gw_tournament_playerstats_slice = playerstats_df[playerstats_df['gw'] == gw]
            
            write_gameweek_files(tournament_gw_path, gw, is_finished, (gw_tournament_matches, gw_tournament_playerstats, gw_tournament_playerstats_slice))


    # --- 3. Populate 'By Gameweek' Folders ---
    logger.info("\n--- 3. Populating 'By Gameweek' Folders ---")
    unique_gameweeks = sorted(gameweeks_df['id'].dropna().unique().astype(int))

    for gw in unique_gameweeks:
        if gw not in gameweeks_df['id'].values: continue
        
        is_finished = gameweeks_df.loc[gameweeks_df['id'] == gw, 'finished'].iloc[0]
        gw_path = os.path.join(BASE_DATA_PATH, 'By Gameweek', f'GW{gw}')
        
        gw_matches = matches_df[matches_df['gameweek'] == gw]
        match_ids = gw_matches['match_id'].unique().tolist()
        gw_playermatchstats = playermatchstats_df[playermatchstats_df['match_id'].isin(match_ids)]
        gw_playerstats_slice = playerstats_df[playerstats_df['gw'] == gw]

        write_gameweek_files(gw_path, gw, is_finished, (gw_matches, gw_playermatchstats, gw_playerstats_slice))

    # --- 4. Perform the discrete gameweek calculation ---
    calculate_discrete_gameweek_stats()

    # --- 5. Validate the generated files; fail loudly on corruption ---
    if validate_gameweek_stats():
        logger.error("❌ Aborting: generated gameweek stats failed validation. Not safe to publish.")
        sys.exit(1)

    logger.info("\n--- Comprehensive data update process completed successfully! ---")


if __name__ == "__main__":
    main()
