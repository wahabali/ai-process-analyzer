"""
parser.py — Event log parsing and process statistics extraction.
Handles CSV event logs with columns: case_id, timestamp, activity, resource
"""

import pandas as pd
from datetime import timedelta
from typing import Optional


REQUIRED_COLUMNS = {"case_id", "timestamp", "activity"}


def parse_event_log(file_path: Optional[str] = None, df: Optional[pd.DataFrame] = None) -> dict:
    """
    Parse a CSV event log and return structured process statistics.

    Args:
        file_path: Path to CSV file (optional if df provided)
        df: Pre-loaded DataFrame (optional if file_path provided)

    Returns:
        dict with process stats ready for LLM analysis
    """
    if df is None and file_path is None:
        raise ValueError("Provide either file_path or df")

    if df is None:
        df = pd.read_csv(file_path)

    df.columns = df.columns.str.strip().str.lower()
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values(["case_id", "timestamp"])

    has_resource = "resource" in df.columns

    # --- Case-level stats ---
    case_stats = []
    for case_id, group in df.groupby("case_id"):
        start = group["timestamp"].min()
        end = group["timestamp"].max()
        duration_hours = (end - start).total_seconds() / 3600
        activities = group["activity"].tolist()
        case_stats.append({
            "case_id": case_id,
            "start": start,
            "end": end,
            "duration_hours": round(duration_hours, 2),
            "num_activities": len(activities),
            "activities": activities,
        })

    case_df = pd.DataFrame(case_stats)

    # --- Activity-level stats ---
    activity_durations = []
    for case_id, group in df.groupby("case_id"):
        group = group.reset_index(drop=True)
        for i in range(len(group) - 1):
            duration = (group.loc[i + 1, "timestamp"] - group.loc[i, "timestamp"]).total_seconds() / 3600
            activity_durations.append({
                "activity": group.loc[i, "activity"],
                "duration_to_next_hours": round(duration, 2),
                "resource": group.loc[i, "resource"] if has_resource else "N/A",
            })

    activity_df = pd.DataFrame(activity_durations)
    activity_stats = (
        activity_df.groupby("activity")["duration_to_next_hours"]
        .agg(["mean", "max", "min", "count"])
        .round(2)
        .rename(columns={"mean": "avg_hours", "max": "max_hours", "min": "min_hours", "count": "occurrences"})
        .sort_values("avg_hours", ascending=False)
    )

    # --- Activity frequency ---
    activity_freq = df["activity"].value_counts().to_dict()

    # --- Resource workload ---
    resource_workload = {}
    if has_resource:
        resource_workload = df.groupby("resource")["activity"].count().sort_values(ascending=False).to_dict()

    # --- Rework / loops detection ---
    rework_cases = []
    for case_id, group in df.groupby("case_id"):
        activities = group["activity"].tolist()
        if len(activities) != len(set(activities)):
            duplicates = [a for a in set(activities) if activities.count(a) > 1]
            rework_cases.append({"case_id": case_id, "repeated_activities": duplicates})

    # --- Summary ---
    return {
        "summary": {
            "total_cases": len(case_df),
            "total_events": len(df),
            "unique_activities": df["activity"].nunique(),
            "avg_case_duration_hours": round(case_df["duration_hours"].mean(), 2),
            "median_case_duration_hours": round(case_df["duration_hours"].median(), 2),
            "min_case_duration_hours": round(case_df["duration_hours"].min(), 2),
            "max_case_duration_hours": round(case_df["duration_hours"].max(), 2),
            "rework_case_count": len(rework_cases),
            "rework_rate_pct": round(len(rework_cases) / len(case_df) * 100, 1),
        },
        "activity_stats": activity_stats.reset_index().to_dict(orient="records"),
        "activity_frequency": activity_freq,
        "resource_workload": resource_workload,
        "rework_cases": rework_cases,
        "case_durations": case_df[["case_id", "duration_hours", "num_activities"]].to_dict(orient="records"),
        "process_flow": _extract_process_flow(df),
    }


def _extract_process_flow(df: pd.DataFrame) -> list[dict]:
    """Extract activity transitions and their frequencies."""
    transitions = []
    for _, group in df.groupby("case_id"):
        group = group.reset_index(drop=True)
        for i in range(len(group) - 1):
            transitions.append({
                "from": group.loc[i, "activity"],
                "to": group.loc[i + 1, "activity"],
            })

    if not transitions:
        return []

    flow_df = pd.DataFrame(transitions)
    flow_counts = flow_df.groupby(["from", "to"]).size().reset_index(name="count")
    return flow_counts.sort_values("count", ascending=False).to_dict(orient="records")


def format_stats_for_llm(stats: dict) -> str:
    """Format parsed stats into a readable text block for LLM prompting."""
    s = stats["summary"]
    lines = [
        "## Process Statistics",
        f"- Total cases: {s['total_cases']}",
        f"- Total events: {s['total_events']}",
        f"- Unique activities: {s['unique_activities']}",
        f"- Average case duration: {s['avg_case_duration_hours']} hours",
        f"- Median case duration: {s['median_case_duration_hours']} hours",
        f"- Fastest case: {s['min_case_duration_hours']} hours",
        f"- Slowest case: {s['max_case_duration_hours']} hours",
        f"- Rework/loop cases: {s['rework_case_count']} ({s['rework_rate_pct']}%)",
        "",
        "## Activity Waiting Times (avg hours to next step)",
    ]

    for a in stats["activity_stats"][:10]:
        lines.append(
            f"- {a['activity']}: avg {a['avg_hours']}h, max {a['max_hours']}h ({a['occurrences']} occurrences)"
        )

    if stats["resource_workload"]:
        lines.append("")
        lines.append("## Resource Workload (event count)")
        for resource, count in list(stats["resource_workload"].items())[:8]:
            lines.append(f"- {resource}: {count} events")

    if stats["rework_cases"]:
        lines.append("")
        lines.append("## Rework / Repeated Steps")
        for r in stats["rework_cases"]:
            lines.append(f"- Case {r['case_id']}: repeated {', '.join(r['repeated_activities'])}")

    lines.append("")
    lines.append("## Top Process Transitions")
    for t in stats["process_flow"][:10]:
        lines.append(f"- {t['from']} → {t['to']}: {t['count']} times")

    return "\n".join(lines)
