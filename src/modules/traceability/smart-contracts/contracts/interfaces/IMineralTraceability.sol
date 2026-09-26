// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title IMineralTraceability
 * @notice Interface commune pour la traçabilité des minerais de transition en RDC
 */
interface IMineralTraceability {
    enum ComplianceStatus {
        PENDING,
        CERTIFIED_RESPONSIBLE,
        FLAGGED_RISK,
        REJECTED
    }

    struct MineralMetadata {
        string mineralSymbol;     // Cu, Co, Li, Ta, Sn, W
        uint256 grossWeightGrams; // Poids brut en grammes pour précision
        uint256 netWeightGrams;   // Poids net après tare
        string pitId;             // Identifiant unique du puits
        string cooperativeId;     // Coopérative artisanale
        string tenementId;        // Permis CAMI (ZEA / PR)
        bytes32 waybillHash;      // Hash du bordereau de transport
        ComplianceStatus status;  // Statut CIRGL / OCDE
        uint256 extractedAt;      // Horodatage d'extraction
    }

    event LotMinted(
        uint256 indexed tokenId,
        string indexed pitId,
        string mineralSymbol,
        uint256 netWeightGrams,
        address indexed minter
    );

    event InspectionCertified(
        uint256 indexed tokenId,
        address indexed inspector,
        ComplianceStatus status,
        string reportUri
    );

    event CustodyTransferred(
        uint256 indexed tokenId,
        address indexed from,
        address indexed to,
        bytes32 waybillHash
    );
}
