# Pilier 1 : Traçabilité (Blockchain & IoT)

Le pilier **Traçabilité** assure l'enregistrement inaltérable, l'auditabilité et la tokenisation des flux de minerais stratégiques en RDC, du front de taille jusqu'aux fonderies et constructeurs industriels.

---

## 🏛️ Sous-modules

| Sous-module | Dépôt Source | Rôle Opérationnel | Technologie |
| :--- | :--- | :--- | :--- |
| [`ledger/`](ledger/) | `hyperledger/fabric` | Registre de consortium d'entreprise pour l'immuabilité des lots, inspections étatiques et journaux de transport. | Go (Chaincode) + Python (Client SDK) |
| [`smart-contracts/`](smart-contracts/) | `OpenZeppelin/openzeppelin-contracts` | Contrats intelligents pour la tokenisation semi-fongible (ERC-1155) et unitaire (ERC-721 Battery Passport) avec contrôle d'accès RBAC. | Solidity ^0.8.20 + OpenZeppelin v5 |

---

## 🔗 Cycle de Traçabilité Intégré

```
[ Puits de Mine (PIT-ID) ]
        |
        v
[ Pesée Numérique sur Site ] -----> Enregistrement Fabric (CreateLot)
        |
        v
[ Inspection QA/QC (SGN-C / SENTECH) ] --> Certification Fabric & OpenZeppelin
        |
        v
[ Transfert de Garde / Transport ] ------> Waybill Hash & Géo-clôture
        |
        v
[ Tokenisation / Export ] ---------------> Émission ERC-721 / ERC-1155 (Passport)
```

---

## 🧪 Tests Rapides

Pour lancer la suite de tests automatisée du pilier Traçabilité :
```bash
python -m unittest tests/test_traceability_pillar.py
```
