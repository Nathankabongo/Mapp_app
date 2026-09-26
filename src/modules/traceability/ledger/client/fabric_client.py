"""Client d'interaction avec le registre Hyperledger Fabric pour la traçabilité minière."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class FabricInspectionRecord:
    inspector_id: str
    agency: str  # SGN-C, SAEMAPE, SENTECH
    status: str  # EN_ATTENTE_INSPECTION, CERTIFIE_CONFORME, REJETE_NON_CONFORME
    assay_ppm: Dict[str, float] = field(default_factory=dict)
    notes: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    signature: str = ""


@dataclass
class FabricTransportEvent:
    carrier_id: str
    vehicle_reg: str
    origin: str
    destination: str
    waybill_hash: str
    gps_lat: float
    gps_lon: float
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class FabricMineralLot:
    id: str
    mineral_type: str
    gross_weight_kg: float
    net_weight_kg: float
    pit_id: str
    cooperative_id: str
    tenement_id: str
    current_custodian: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    inspection_history: List[FabricInspectionRecord] = field(default_factory=list)
    transport_history: List[FabricTransportEvent] = field(default_factory=list)


class FabricLedgerClient:
    """
    Client de haut niveau pour l'orchestration des smart contracts Hyperledger Fabric.
    Supporte le mode Gateway gRPC officiel et un mode 'in-memory ledger' pour les tests offline.
    """

    def __init__(
        self,
        channel_name: str = "minerals-channel",
        chaincode_name: str = "mineral_lot_contract",
        gateway_endpoint: Optional[str] = None,
        msp_id: str = "Org1MSP",
        offline_mode: bool = True,
    ):
        self.channel_name = channel_name
        self.chaincode_name = chaincode_name
        self.gateway_endpoint = gateway_endpoint
        self.msp_id = msp_id
        self.offline_mode = offline_mode
        self._local_state: Dict[str, Dict[str, Any]] = {}
        self._history: Dict[str, List[Dict[str, Any]]] = {}

    def create_lot(
        self,
        lot_id: str,
        mineral_type: str,
        gross_weight_kg: float,
        net_weight_kg: float,
        pit_id: str,
        cooperative_id: str,
        tenement_id: str,
    ) -> FabricMineralLot:
        """Enregistre un nouveau lot de minerai sur le registre immuable."""
        if self.offline_mode or not self.gateway_endpoint:
            if lot_id in self._local_state:
                raise ValueError(f"Le lot {lot_id} existe déjà sur le ledger.")

            lot = FabricMineralLot(
                id=lot_id,
                mineral_type=mineral_type,
                gross_weight_kg=gross_weight_kg,
                net_weight_kg=net_weight_kg,
                pit_id=pit_id,
                cooperative_id=cooperative_id,
                tenement_id=tenement_id,
                current_custodian=cooperative_id,
            )
            data = asdict(lot)
            self._local_state[lot_id] = data
            self._record_history(lot_id, data, "CREATE_LOT")
            return lot

        # Mode Gateway réseau réel
        raise NotImplementedError("Gateway gRPC requiert une connexion réseau Fabric active.")

    def record_inspection(
        self,
        lot_id: str,
        inspector_id: str,
        agency: str,
        status: str,
        assay_ppm: Optional[Dict[str, float]] = None,
        notes: str = "",
        signature: str = "",
    ) -> FabricMineralLot:
        """Consigne un rapport d'inspection et teneurs chimiques certifiées."""
        lot_data = self._local_state.get(lot_id)
        if not lot_data:
            raise KeyError(f"Lot introuvable: {lot_id}")

        inspection = FabricInspectionRecord(
            inspector_id=inspector_id,
            agency=agency,
            status=status,
            assay_ppm=assay_ppm or {},
            notes=notes,
            signature=signature,
        )
        lot_data["inspection_history"].append(asdict(inspection))
        self._record_history(lot_id, lot_data, "RECORD_INSPECTION")
        return self._dict_to_lot(lot_data)

    def record_transport(
        self,
        lot_id: str,
        carrier_id: str,
        vehicle_reg: str,
        origin: str,
        destination: str,
        waybill_hash: str,
        gps_lat: float,
        gps_lon: float,
        new_custodian: Optional[str] = None,
    ) -> FabricMineralLot:
        """Enregistre un événement de transport et met à jour le titulaire de garde."""
        lot_data = self._local_state.get(lot_id)
        if not lot_data:
            raise KeyError(f"Lot introuvable: {lot_id}")

        event = FabricTransportEvent(
            carrier_id=carrier_id,
            vehicle_reg=vehicle_reg,
            origin=origin,
            destination=destination,
            waybill_hash=waybill_hash,
            gps_lat=gps_lat,
            gps_lon=gps_lon,
        )
        lot_data["transport_history"].append(asdict(event))
        if new_custodian:
            lot_data["current_custodian"] = new_custodian

        self._record_history(lot_id, lot_data, "RECORD_TRANSPORT")
        return self._dict_to_lot(lot_data)

    def query_lot(self, lot_id: str) -> Optional[FabricMineralLot]:
        """Consulte l'état mondial (World State) pour un lot."""
        data = self._local_state.get(lot_id)
        if not data:
            return None
        return self._dict_to_lot(data)

    def get_audit_trail(self, lot_id: str) -> List[Dict[str, Any]]:
        """Retourne l'historique complet et inaltérable des transactions du lot."""
        return self._history.get(lot_id, [])

    def _record_history(self, lot_id: str, state: Dict[str, Any], action: str):
        if lot_id not in self._history:
            self._history[lot_id] = []
        self._history[lot_id].append({
            "action": action,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "state_snapshot": json.loads(json.dumps(state)),
        })

    def _dict_to_lot(self, data: Dict[str, Any]) -> FabricMineralLot:
        return FabricMineralLot(
            id=data["id"],
            mineral_type=data["mineral_type"],
            gross_weight_kg=data["gross_weight_kg"],
            net_weight_kg=data["net_weight_kg"],
            pit_id=data["pit_id"],
            cooperative_id=data["cooperative_id"],
            tenement_id=data["tenement_id"],
            current_custodian=data["current_custodian"],
            created_at=data["created_at"],
            inspection_history=[FabricInspectionRecord(**i) for i in data.get("inspection_history", [])],
            transport_history=[FabricTransportEvent(**t) for t in data.get("transport_history", [])],
        )
