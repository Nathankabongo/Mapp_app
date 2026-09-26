"""Historique des campagnes d'exploration — persistance locale JSON."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_HISTORY_DIR = Path("outputs/campaigns")


@dataclass
class CampaignHistoryEntry:
    campaign_id: str
    zone: str
    mineral: str
    province: str
    created_at: str
    n_targets: int
    top_target_id: str | None
    top_score: float | None
    n_gaps: int
    status: str  # ouverte | en_cours | cloturee
    outcomes: dict[str, str] = field(default_factory=dict)  # target_id → confirmé|abandonné|approfondir
    path: str = ""
    note: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def _ensure_dir(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    return root


def save_campaign(
    campaign: dict[str, Any],
    *,
    history_dir: Path | str = DEFAULT_HISTORY_DIR,
    status: str = "ouverte",
    note: str = "",
) -> CampaignHistoryEntry:
    """Persiste une campagne complète + entrée d'index."""
    root = _ensure_dir(Path(history_dir))
    cid = str(campaign.get("campaign_id") or f"EXP-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}")
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in cid)
    path = root / f"{safe}.json"
    payload = dict(campaign)
    payload["_history"] = {
        "status": status,
        "note": note,
        "saved_at": datetime.now(timezone.utc).isoformat(),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    targets = list(campaign.get("targets") or [])
    top = targets[0] if targets else None
    gaps = (campaign.get("diagnostic") or {}).get("gaps") or []
    entry = CampaignHistoryEntry(
        campaign_id=cid,
        zone=str(campaign.get("zone", "")),
        mineral=str(campaign.get("mineral", "")),
        province=str(campaign.get("province", "")),
        created_at=str(campaign.get("created_at") or ""),
        n_targets=len(targets),
        top_target_id=top.get("target_id") if top else None,
        top_score=float(top["exploration_priority_score"]) if top and top.get("exploration_priority_score") is not None else None,
        n_gaps=len(gaps),
        status=status,
        outcomes=dict((payload.get("_history") or {}).get("outcomes") or {}),
        path=str(path),
        note=note,
    )
    _upsert_index(entry, root)
    return entry


def _index_path(root: Path) -> Path:
    return root / "index.json"


def _upsert_index(entry: CampaignHistoryEntry, root: Path) -> None:
    idx_path = _index_path(root)
    items: list[dict] = []
    if idx_path.exists():
        try:
            items = list(json.loads(idx_path.read_text(encoding="utf-8")).get("campaigns") or [])
        except Exception:
            items = []
    items = [i for i in items if i.get("campaign_id") != entry.campaign_id]
    items.insert(0, entry.to_dict())
    idx_path.write_text(
        json.dumps({"campaigns": items[:100], "updated_at": datetime.now(timezone.utc).isoformat()}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def list_campaigns(*, history_dir: Path | str = DEFAULT_HISTORY_DIR) -> list[dict]:
    root = Path(history_dir)
    idx = _index_path(root)
    if idx.exists():
        try:
            return list(json.loads(idx.read_text(encoding="utf-8")).get("campaigns") or [])
        except Exception:
            pass
    # fallback : scanner les JSON
    if not root.exists():
        return []
    out = []
    for path in sorted(root.glob("EXP-*.json"), reverse=True):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            out.append(
                CampaignHistoryEntry(
                    campaign_id=raw.get("campaign_id", path.stem),
                    zone=raw.get("zone", ""),
                    mineral=raw.get("mineral", ""),
                    province=raw.get("province", ""),
                    created_at=raw.get("created_at", ""),
                    n_targets=len(raw.get("targets") or []),
                    top_target_id=(raw.get("targets") or [{}])[0].get("target_id"),
                    top_score=(raw.get("targets") or [{}])[0].get("exploration_priority_score"),
                    n_gaps=len((raw.get("diagnostic") or {}).get("gaps") or []),
                    status=(raw.get("_history") or {}).get("status", "ouverte"),
                    outcomes=dict((raw.get("_history") or {}).get("outcomes") or {}),
                    path=str(path),
                ).to_dict()
            )
        except Exception:
            continue
    return out


def load_campaign(campaign_id: str, *, history_dir: Path | str = DEFAULT_HISTORY_DIR) -> dict | None:
    root = Path(history_dir)
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in campaign_id)
    path = root / f"{safe}.json"
    if not path.exists():
        # recherche souple
        for p in root.glob("*.json"):
            if p.name == "index.json":
                continue
            try:
                raw = json.loads(p.read_text(encoding="utf-8"))
                if raw.get("campaign_id") == campaign_id:
                    return raw
            except Exception:
                continue
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def update_target_outcome(
    campaign_id: str,
    target_id: str,
    outcome: str,
    *,
    history_dir: Path | str = DEFAULT_HISTORY_DIR,
) -> dict | None:
    """
    Enregistre le sort d'une cible : confirmé | abandonné | approfondir.
    Évite de recommencer des travaux déjà tranchés.
    """
    allowed = {"confirmé", "confirme", "abandonné", "abandonne", "approfondir", "en_cours"}
    key = outcome.strip().lower()
    if key not in allowed:
        raise ValueError(f"Outcome invalide : {outcome}. Attendu : confirmé|abandonné|approfondir")
    normalize = {
        "confirme": "confirmé",
        "confirmé": "confirmé",
        "abandonne": "abandonné",
        "abandonné": "abandonné",
        "approfondir": "approfondir",
        "en_cours": "en_cours",
    }[key]
    camp = load_campaign(campaign_id, history_dir=history_dir)
    if camp is None:
        return None
    hist = dict(camp.get("_history") or {})
    outcomes = dict(hist.get("outcomes") or {})
    outcomes[target_id] = normalize
    hist["outcomes"] = outcomes
    hist["updated_at"] = datetime.now(timezone.utc).isoformat()
    camp["_history"] = hist
    entry = save_campaign(camp, history_dir=history_dir, status=hist.get("status", "en_cours"), note=hist.get("note", ""))
    return {"campaign": entry.to_dict(), "outcomes": outcomes}


def campaign_summary(campaign_id: str, *, history_dir: Path | str = DEFAULT_HISTORY_DIR) -> dict:
    camp = load_campaign(campaign_id, history_dir=history_dir)
    if camp is None:
        return {"status": "NON DISPONIBLE", "message": "Campagne introuvable"}
    targets = camp.get("targets") or []
    outcomes = (camp.get("_history") or {}).get("outcomes") or {}
    return {
        "campaign_id": campaign_id,
        "zone": camp.get("zone"),
        "mineral": camp.get("mineral"),
        "n_targets": len(targets),
        "n_gaps": len((camp.get("diagnostic") or {}).get("gaps") or []),
        "outcomes": outcomes,
        "confirmed": [k for k, v in outcomes.items() if v == "confirmé"],
        "abandoned": [k for k, v in outcomes.items() if v == "abandonné"],
        "needs_followup": [k for k, v in outcomes.items() if v == "approfondir"],
        "disclaimer": "Historique local fichier — pas une base CAMI / corporate.",
    }
