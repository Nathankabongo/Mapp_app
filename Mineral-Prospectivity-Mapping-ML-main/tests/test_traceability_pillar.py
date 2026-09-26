import sys
import unittest
from pathlib import Path

# Ajouter d:\Mapping au sys.path pour importer src.modules
workspace_root = Path("d:/Mapping")
if str(workspace_root) not in sys.path:
    sys.path.insert(0, str(workspace_root))

from src.modules.traceability.ledger.client import FabricLedgerClient


class TestTraceabilityPillar(unittest.TestCase):
    def setUp(self):
        self.client = FabricLedgerClient(channel_name="test-channel", offline_mode=True)

    def test_create_mineral_lot(self):
        lot = self.client.create_lot(
            lot_id="LOT-KWZ-2026-001",
            mineral_type="Co",
            gross_weight_kg=1250.0,
            net_weight_kg=1220.0,
            pit_id="PIT-KWZ-ZEA04-012",
            cooperative_id="COOP-COMICOC",
            tenement_id="ZEA-4210",
        )
        self.assertEqual(lot.id, "LOT-KWZ-2026-001")
        self.assertEqual(lot.mineral_type, "Co")
        self.assertEqual(lot.net_weight_kg, 1220.0)
        self.assertEqual(lot.current_custodian, "COOP-COMICOC")

    def test_duplicate_lot_rejected(self):
        self.client.create_lot(
            lot_id="LOT-DUP-01",
            mineral_type="Cu",
            gross_weight_kg=500.0,
            net_weight_kg=490.0,
            pit_id="PIT-01",
            cooperative_id="COOP-01",
            tenement_id="ZEA-01",
        )
        with self.assertRaises(ValueError):
            self.client.create_lot(
                lot_id="LOT-DUP-01",
                mineral_type="Cu",
                gross_weight_kg=500.0,
                net_weight_kg=490.0,
                pit_id="PIT-01",
                cooperative_id="COOP-01",
                tenement_id="ZEA-01",
            )

    def test_inspection_and_audit_trail(self):
        self.client.create_lot(
            lot_id="LOT-INSP-01",
            mineral_type="Cu-Co",
            gross_weight_kg=800.0,
            net_weight_kg=780.0,
            pit_id="PIT-02",
            cooperative_id="COOP-02",
            tenement_id="PR-102",
        )

        updated_lot = self.client.record_inspection(
            lot_id="LOT-INSP-01",
            inspector_id="INSP-SENTECH-01",
            agency="SENTECH",
            status="CERTIFIE_CONFORME",
            assay_ppm={"Cu": 22000.0, "Co": 1200.0},
            notes="Standards CRM validés",
            signature="SIG_VALID",
        )

        self.assertEqual(len(updated_lot.inspection_history), 1)
        self.assertEqual(updated_lot.inspection_history[0].status, "CERTIFIE_CONFORME")

        # Transport & transfert de garde
        transported_lot = self.client.record_transport(
            lot_id="LOT-INSP-01",
            carrier_id="LOGEMA-TRUCK-05",
            vehicle_reg="C-492-KAT",
            origin="Puits 02",
            destination="Entrepôt Négociant",
            waybill_hash="hash_waybill_12345",
            gps_lat=-10.7123,
            gps_lon=25.4891,
            new_custodian="NEGOCIANT_AGREE",
        )

        self.assertEqual(transported_lot.current_custodian, "NEGOCIANT_AGREE")
        self.assertEqual(len(transported_lot.transport_history), 1)

        # Audit trail
        audit = self.client.get_audit_trail("LOT-INSP-01")
        self.assertEqual(len(audit), 3)  # CREATE_LOT, RECORD_INSPECTION, RECORD_TRANSPORT


if __name__ == "__main__":
    unittest.main()
