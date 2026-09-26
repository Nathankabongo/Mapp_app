# Module Traceability — Hyperledger Fabric Ledger

Ce module extrait et adapte les capacités d'enregistrement immuable d'**Hyperledger Fabric** pour la traçabilité des minerais stratégiques en RDC (Cobalt, Cuivre, Lithium, Coltan).

---

## 🏗️ Architecture des Composants

1. **`chaincode/mineral_lot_contract.go` :**
   - Smart contract écrit en Go avec le SDK `fabric-contract-api-go`.
   - Méthodes exposées :
     - `CreateLot(id, mineralType, grossWeight, netWeight, pitId, coopId, tenementId)` : Enregistrement inviolable au puits.
     - `RecordInspection(lotId, inspectorId, agency, status, assayJson, notes, signature)` : Ingestion des audits SGN-C / SENTECH / SAEMAPE.
     - `RecordTransport(lotId, carrierId, vehicleReg, origin, dest, waybillHash, gpsLat, gpsLon, newCustodian)` : Journal de transport & transfert de garde.
     - `GetLotHistory(lotId)` : Extraction temporelle de l'arbre de transactions (Audit Trail).

2. **`client/fabric_client.py` :**
   - Wrapper Python orienté métier pour interagir avec le réseau Fabric.
   - Fournit un mode **Offline-First / In-Memory** pour exécuter tests et pipelines locaux sans nécessiter de cluster Docker/Kubernetes Fabric complet en développement.

---

## 🚀 Utilisation Rapide (Python Client)

```python
from src.modules.traceability.ledger.client import FabricLedgerClient

# 1. Initialiser le client (mode offline local ou connecté à une Gateway)
client = FabricLedgerClient(channel_name="minerals-channel", offline_mode=True)

# 2. Créer un lot extrait à Kolwezi
lot = client.create_lot(
    lot_id="LOT-KWZ-2026-001",
    mineral_type="Cu-Co",
    gross_weight_kg=1250.0,
    net_weight_kg=1220.0,
    pit_id="PIT-KWZ-ZEA04-012",
    cooperative_id="COOP-COMICOC",
    tenement_id="ZEA-4210"
)

# 3. Consigner l'inspection et les analyses de laboratoire SENTECH
client.record_inspection(
    lot_id="LOT-KWZ-2026-001",
    inspector_id="INSP-SENTECH-08",
    agency="SENTECH",
    status="CERTIFIE_CONFORME",
    assay_ppm={"Cu": 18200.0, "Co": 950.0},
    notes="Conforme standards CIRGL / QA-QC validé",
    signature="SIG_HMAC_SHA256_CERT"
)

# 4. Enregistrer une étape de transport vers l'entrepôt négociant
client.record_transport(
    lot_id="LOT-KWZ-2026-001",
    carrier_id="TRANS-LOGEMA-RDC",
    vehicle_reg="1024-AB-05",
    origin="Puits ZEA-4210",
    destination="Entrepôt Négociant Lubumbashi",
    waybill_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    gps_lat=-10.6541,
    gps_lon=25.5612,
    new_custodian="NEGOCE-KATANGA-EXPORT"
)

# 5. Obtenir l'historique complet pour audit
history = client.get_audit_trail("LOT-KWZ-2026-001")
print(f"Événements enregistrés : {len(history)}")
```

---

## 🧪 Tests du Module
Pour tester le client Python :
```bash
python -m unittest discover -s tests -p "test_traceability*.py"
```
Pour compiler le chaincode Go :
```bash
cd src/modules/traceability/ledger/chaincode
go mod tidy
go build
```
