"""
Top 10 players by position, ranked by average points per start.

Ranks players within each FPL position (Goalkeeper, Defender, Midfielder,
Forward) by total_points / starts ("points per start"), subject to a minimum
minutes floor so bit-part players with a single big haul don't dominate the
table. Produces three views for a season:

  * Full season   - cumulative stats through the season's final gameweek.
  * Start window   - cumulative stats through an early gameweek (default GW10),
                      using a lower, proportional minutes floor.
  * End window     - stats summed over a late-season gameweek range (default
                      the last 10 gameweeks), using the same proportional
                      minutes floor as the start window, so the two are
                      directly comparable "form" snapshots.

Data source: data/{season}/By Gameweek/GW{n}/{players,playerstats,
player_gameweek_stats}.csv, as produced by scripts/export_data.py /
scripts/split_by_gameweek.py. `minutes`, `starts` and `total_points` are
FPL-authoritative fields (see DATA_INTEGRATION_REVIEW.md), so they can be
summed across single-gameweek files or read directly from a cumulative
snapshot without reconciliation.

Usage:
    python3 scripts/top10_by_position.py
    python3 scripts/top10_by_position.py --season 2025-2026 --top-n 10
    python3 scripts/top10_by_position.py --start-gw 10 --end-window 29 38
"""

import argparse
from pathlib import Path

import pandas as pd

POSITION_ORDER = ["Goalkeeper", "Defender", "Midfielder", "Forward"]


def season_dir(season: str) -> Path:
    return Path("data") / season / "By Gameweek"


def load_gw_snapshot(season: str, gw: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Players + cumulative playerstats as of a single gameweek folder."""
    base = season_dir(season) / f"GW{gw}"
    players = pd.read_csv(base / "players.csv")
    # teams.csv has two id-like columns: "code" (the stable FPL team code, what
    # players.team_code references) and "id" (a season-local sequential id).
    # Joining against "id" silently mismatches teams (e.g. Arsenal's code 3
    # would resolve to whichever team happens to hold season-local id 3).
    teams = pd.read_csv(base / "teams.csv")[["code", "short_name"]].rename(
        columns={"code": "team_code", "short_name": "team"}
    )
    players = players.merge(teams, on="team_code", how="left")
    stats = pd.read_csv(base / "playerstats.csv")
    return players, stats


def sum_gw_window(season: str, gw_start: int, gw_end: int) -> pd.DataFrame:
    """Sum discrete per-gameweek stats over [gw_start, gw_end] inclusive."""
    frames = []
    for gw in range(gw_start, gw_end + 1):
        path = season_dir(season) / f"GW{gw}" / "player_gameweek_stats.csv"
        df = pd.read_csv(path, usecols=["id", "total_points", "starts", "minutes"])
        frames.append(df)
    combined = pd.concat(frames, ignore_index=True)
    return combined.groupby("id", as_index=False)[["total_points", "starts", "minutes"]].sum()


def rank_top_n(players: pd.DataFrame, stats: pd.DataFrame, min_minutes: int, top_n: int) -> pd.DataFrame:
    """Join players+stats, compute points/start, filter, and rank within position."""
    merged = players.merge(stats, left_on="player_id", right_on="id", how="inner", suffixes=("", "_stat"))
    merged = merged[merged["minutes"] >= min_minutes].copy()
    merged = merged[merged["starts"] > 0].copy()
    merged["points_per_start"] = (merged["total_points"] / merged["starts"]).round(2)

    merged = merged.sort_values(
        ["position", "points_per_start", "total_points", "minutes"],
        ascending=[True, False, False, False],
    )
    merged["rank"] = merged.groupby("position").cumcount() + 1
    top = merged[merged["rank"] <= top_n]

    cols = ["position", "rank", "web_name", "team", "points_per_start", "total_points", "starts", "minutes"]
    return top[cols].reset_index(drop=True)


def print_tables(title: str, ranked: pd.DataFrame, min_minutes: int) -> None:
    print(f"\n{'=' * 70}\n{title}  (min {min_minutes} minutes)\n{'=' * 70}")
    for pos in POSITION_ORDER:
        sub = ranked[ranked["position"] == pos]
        if sub.empty:
            continue
        print(f"\n-- {pos} --")
        print(f"{'#':<3}{'Player':<20}{'Team':<6}{'Pts/Start':>10}{'Pts':>6}{'Starts':>8}{'Mins':>7}")
        for _, r in sub.iterrows():
            print(
                f"{int(r['rank']):<3}{r['web_name']:<20}{str(r['team']):<6}"
                f"{r['points_per_start']:>10.2f}{int(r['total_points']):>6}"
                f"{int(r['starts']):>8}{int(r['minutes']):>7}"
            )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--season", default="2025-2026", help="Season folder name, e.g. 2025-2026")
    parser.add_argument("--final-gw", type=int, default=38, help="Last gameweek of the season")
    parser.add_argument("--full-min-minutes", type=int, default=1500, help="Minutes floor for the full-season table")
    parser.add_argument("--start-gw", type=int, default=10, help="End of the 'start of season' cumulative window (GW1..N)")
    parser.add_argument("--end-window", type=int, nargs=2, default=[29, 38], metavar=("FROM", "TO"),
                         help="Gameweek range for the 'end of season' form window")
    parser.add_argument("--window-min-minutes", type=int, default=450,
                         help="Minutes floor for the start/end partial-season windows")
    parser.add_argument("--top-n", type=int, default=10)
    args = parser.parse_args()

    # Full season - cumulative through the final gameweek.
    players_final, stats_final = load_gw_snapshot(args.season, args.final_gw)
    full = rank_top_n(players_final, stats_final, args.full_min_minutes, args.top_n)
    print_tables(f"{args.season} FULL SEASON (through GW{args.final_gw})", full, args.full_min_minutes)

    # Start of season - cumulative through an early gameweek.
    players_start, stats_start = load_gw_snapshot(args.season, args.start_gw)
    start = rank_top_n(players_start, stats_start, args.window_min_minutes, args.top_n)
    print_tables(f"{args.season} START OF SEASON (GW1-{args.start_gw})", start, args.window_min_minutes)

    # End of season - summed over the closing gameweeks (run-in form).
    gw_from, gw_to = args.end_window
    stats_end = sum_gw_window(args.season, gw_from, gw_to)
    end = rank_top_n(players_final, stats_end, args.window_min_minutes, args.top_n)
    print_tables(f"{args.season} END OF SEASON (GW{gw_from}-{gw_to})", end, args.window_min_minutes)


if __name__ == "__main__":
    main()
