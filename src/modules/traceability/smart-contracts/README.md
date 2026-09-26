# Module Traceability — Smart Contracts OpenZeppelin

Ce module fournit les contrats intelligents basés sur les standards **OpenZeppelin Contracts v5** pour la tokenisation et la gestion des permissions des minerais stratégiques en RDC.

---

## 📦 Contrats Inclus

1. **`contracts/MineralBatchERC1155.sol` :**
   - **Type :** Semi-fongible (ERC-1155) avec contrôle d'accès granulaire (`AccessControl`) et mécanisme de sécurité d'urgence (`Pausable`).
   - **Usage :** Représentation par sacs ou conteneurs de concentré minéral (Cobalt hydroxyde, concentré de Cuivre, Spodumène).
   - **Rôles gérés :**
     - `MINER_ROLE` : Autorisé à minter les lots au carreau de la mine / ZEA.
     - `INSPECTOR_ROLE` : Autorisé à certifier la conformité (SGN-C / SAEMAPE / SENTECH).
     - `TRANSPORTER_ROLE` : Autorisé à enregistrer les bordereaux de transit logistique.
     - `PAUSER_ROLE` : Verrouillage d'urgence en cas de risque avéré de fraude.

2. **`contracts/MineralLotNFT.sol` :**
   - **Type :** Jeton non-fongible unitaire (ERC-721 URI Storage) avec `AccessControl`.
   - **Usage :** Émission du **Passeport Numérique de Batterie (EU Battery Passport)** et du Certificat d'Origine Responsable.

3. **`contracts/interfaces/IMineralTraceability.sol` :**
   - Interface normalisée regroupant les structures de métadonnées minières, les statuts de conformité (`PENDING`, `CERTIFIED_RESPONSIBLE`, `FLAGGED_RISK`, `REJECTED`) et les événements de traçabilité.

---

## 🛠️ Installation & Compilation

```bash
cd src/modules/traceability/smart-contracts
npm install
```

Pour compiler avec Hardhat :
```bash
npx hardhat compile
```

Pour compiler avec Foundry :
```bash
forge build
```

---

## 🔌 Intégration Python (Web3.py)

Les contrats peuvent être pilotés directement depuis le backend Python de CriticalMineralsCompass :
```python
from web3 import Web3

w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
contract = w3.eth.contract(address="0xContractAddress...", abi=[...])

# Minter un lot de minerai certifié
tx = contract.functions.mintBatchLot(
    "0xBeneficiary...",
    50,              # 50 sacs
    "Co",            # Cobalt
    1250000,         # 1 250 000 g brut
    1200000,         # 1 200 000 g net
    "PIT-KWZ-04",
    "COOP-COMICOC",
    "ZEA-4210",
    b""
).transact({"from": "0xMinerAddress..."})
```
