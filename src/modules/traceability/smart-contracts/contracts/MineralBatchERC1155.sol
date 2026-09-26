// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC1155/ERC1155.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "./interfaces/IMineralTraceability.sol";

/**
 * @title MineralBatchERC1155
 * @notice Contrat multi-token pour la traçabilité fractionnée de sacs de minerai (Cobalt, Cuivre, etc.)
 * Extrait et enrichit les briques de sécurité d'OpenZeppelin (AccessControl, Pausable, ERC1155).
 */
contract MineralBatchERC1155 is ERC1155, AccessControl, Pausable, IMineralTraceability {
    bytes32 public constant MINER_ROLE = keccak256("MINER_ROLE");
    bytes32 public constant INSPECTOR_ROLE = keccak256("INSPECTOR_ROLE");
    bytes32 public constant TRANSPORTER_ROLE = keccak256("TRANSPORTER_ROLE");
    bytes32 public constant PAUSER_ROLE = keccak256("PAUSER_ROLE");

    uint256 private _nextTokenId = 1;

    // Mapping: Token ID => Métadonnées du lot
    mapping(uint256 => MineralMetadata) private _lots;

    // Mapping: Token ID => URI du rapport de conformité
    mapping(uint256 => string) private _inspectionReports;

    constructor(string memory uri_, address defaultAdmin) ERC1155(uri_) {
        _grantRole(DEFAULT_ADMIN_ROLE, defaultAdmin);
        _grantRole(PAUSER_ROLE, defaultAdmin);
    }

    /**
     * @notice Enregistre et émet des tokens représentant des sacs de minerais certifiés au carreau du puits
     */
    function mintBatchLot(
        address to,
        uint256 bagCount,
        string memory mineralSymbol,
        uint256 grossWeightGrams,
        uint256 netWeightGrams,
        string memory pitId,
        string memory cooperativeId,
        string memory tenementId,
        bytes memory data
    ) external onlyRole(MINER_ROLE) whenNotPaused returns (uint256) {
        require(netWeightGrams > 0, "Poids net invalide");
        require(bytes(pitId).length > 0, "ID Puits obligatoire");

        uint256 tokenId = _nextTokenId++;

        _lots[tokenId] = MineralMetadata({
            mineralSymbol: mineralSymbol,
            grossWeightGrams: grossWeightGrams,
            netWeightGrams: netWeightGrams,
            pitId: pitId,
            cooperativeId: cooperativeId,
            tenementId: tenementId,
            waybillHash: bytes32(0),
            status: ComplianceStatus.PENDING,
            extractedAt: block.timestamp
        });

        _mint(to, tokenId, bagCount, data);

        emit LotMinted(tokenId, pitId, mineralSymbol, netWeightGrams, msg.sender);
        return tokenId;
    }

    /**
     * @notice Consigne le statut d'inspection officiel (SGN-C / SAEMAPE / SENTECH)
     */
    function certifyInspection(
        uint256 tokenId,
        ComplianceStatus status,
        string memory reportUri
    ) external onlyRole(INSPECTOR_ROLE) whenNotPaused {
        require(_lots[tokenId].extractedAt > 0, "Lot introuvable");

        _lots[tokenId].status = status;
        _inspectionReports[tokenId] = reportUri;

        emit InspectionCertified(tokenId, msg.sender, status, reportUri);
    }

    /**
     * @notice Met à jour le bordereau de transport lors d'un transit logistique
     */
    function updateWaybill(
        uint256 tokenId,
        address from,
        address to,
        bytes32 waybillHash
    ) external onlyRole(TRANSPORTER_ROLE) whenNotPaused {
        require(_lots[tokenId].extractedAt > 0, "Lot introuvable");
        _lots[tokenId].waybillHash = waybillHash;

        emit CustodyTransferred(tokenId, from, to, waybillHash);
    }

    /**
     * @notice Récupère les métadonnées d'un lot minier
     */
    function getLotMetadata(uint256 tokenId) external view returns (MineralMetadata memory) {
        require(_lots[tokenId].extractedAt > 0, "Lot inexistant");
        return _lots[tokenId];
    }

    /**
     * @notice Contrôle de pause de sécurité
     */
    function pause() external onlyRole(PAUSER_ROLE) {
        _pause();
    }

    function unpause() external onlyRole(PAUSER_ROLE) {
        _unpause();
    }

    function supportsInterface(bytes4 interfaceId)
        public
        view
        virtual
        override(ERC1155, AccessControl)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }
}
