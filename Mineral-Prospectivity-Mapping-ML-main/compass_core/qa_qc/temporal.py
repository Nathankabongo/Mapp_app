"""Contrôles QA/QC temporels."""

from __future__ import annotations

from datetime import datetime, timezone

from compass_core.qa_qc.scores import QCIssue


def parse_date(value) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    s = str(value).strip()
    if not s or s.upper() in {"N/E", "NA", "NAN", "NONE", "NULL", ""}:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y"):
        try:
            dt = datetime.strptime(s[: len(fmt) + 8], fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def check_dates(values: list, *, field: str = "date", max_age_years: float | None = 50) -> tuple[list[QCIssue], dict]:
    issues: list[QCIssue] = []
    now = datetime.now(timezone.utc)
    n_invalid = 0
    n_future = 0
    n_stale = 0
    n_ok = 0
    for i, v in enumerate(values):
        dt = parse_date(v)
        if dt is None and v not in (None, "", "N/E"):
            n_invalid += 1
            issues.append(
                QCIssue(
                    "DATE_INVALID",
                    "warning",
                    f"Date invalide: {v!r}",
                    field,
                    record_index=i,
                )
            )
            continue
        if dt is None:
            continue
        n_ok += 1
        if dt > now:
            n_future += 1
            issues.append(
                QCIssue(
                    "DATE_FUTURE",
                    "warning",
                    f"Date future: {dt.isoformat()}",
                    field,
                    record_index=i,
                )
            )
        if max_age_years is not None:
            age = (now - dt).days / 365.25
            if age > max_age_years:
                n_stale += 1
                issues.append(
                    QCIssue(
                        "DATE_STALE",
                        "info",
                        f"Donnée ancienne ({age:.0f} ans): {dt.date().isoformat()}",
                        field,
                        record_index=i,
                    )
                )
    stats = {
        "n_values": len(values),
        "n_parsed_ok": n_ok,
        "n_invalid": n_invalid,
        "n_future": n_future,
        "n_stale": n_stale,
    }
    return issues, stats
