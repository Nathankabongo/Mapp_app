// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "./interfaces/IMineralTraceability.sol";

/**
 * @title MineralLotNFT
 * @notice Token ERC-721 unitaire représentant le Passeport Numérique de Batterie / Certificat d'Origine
 * Conforme aux exigences du passeport européen des batteries et du Dodd-Frank Act.
 */
contract MineralLotNFT is ERC721URIStorage, AccessControl, IMineralTraceability {
    bytes32 public constant ISSUER_ROLE = keccak256("ISSUER_ROLE");
    bytes32 public constant AUDITOR_ROLE = keccak256("AUDITOR_ROLE");

    uint256 private _tokenIds;
    mapping(uint256 => MineralMetadata) private _passports;

    constructor(address defaultAdmin) ERC721("Critical Minerals Battery Passport", "CMPASS") {
        _grantRole(DEFAULT_ADMIN_ROLE, defaultAdmin);
        _grantRole(ISSUER_ROLE, defaultAdmin);
        _grantRole(AUDITOR_ROLE, defaultAdmin);
    }

    /**
     * @notice Émet un passeport numérique unique pour un lot de minerai raffiné / concentré
     */
    function issuePassport(
        address to,
        string memory tokenURI,
        string memory mineralSymbol,
        uint256 grossWeightGrams,
        uint256 netWeightGrams,
        string memory pitId,
        string memory cooperativeId,
        string memory tenementId
    ) external onlyRole(ISSUER_ROLE) returns (uint256) {
        _tokenIds++;
        uint256 newItemId = _tokenIds;

        _mint(to, newItemId);
        _setTokenURI(newItemId, tokenURI);

        _passports[newItemId] = MineralMetadata({
            mineralSymbol: mineralSymbol,
            grossWeightGrams: grossWeightGrams,
            netWeightGrams: netWeightGrams,
            pitId: pitId,
            cooperativeId: cooperativeId,
            tenementId: tenementId,
            waybillHash: bytes32(0),
            status: ComplianceStatus.CERTIFIED_RESPONSIBLE,
            extractedAt: block.timestamp
        });

        emit LotMinted(newItemId, pitId, mineralSymbol, netWeightGrams, to);
        return newItemId;
    }

    /**
     * @notice Consultation des métadonnées du passeport
     */
    function getPassportData(uint256 tokenId) external view returns (MineralMetadata memory) {
        _requireOwned(tokenId);
        return _passports[tokenId];
    }

    function supportsInterface(bytes4 interfaceId)
        public
        view
        virtual
        override(ERC721URIStorage, AccessControl)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }
}
