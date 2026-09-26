package main

import (
	"encoding/json"
	"fmt"
	"time"

	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

// MineralLotContract gère le cycle de vie immuable des lots de minerais sur Hyperledger Fabric
type MineralLotContract struct {
	contractapi.Contract
}

// Status de conformité et d'inspection
type InspectionStatus string

const (
	StatusPending   InspectionStatus = "EN_ATTENTE_INSPECTION"
	StatusCertified InspectionStatus = "CERTIFIE_CONFORME"
	StatusRejected  InspectionStatus = "REJETE_NON_CONFORME"
)

// TransportEvent enregistre une étape de déplacement logistique
type TransportEvent struct {
	Timestamp     string  `json:"timestamp"`
	CarrierID     string  `json:"carrier_id"`
	VehicleReg    string  `json:"vehicle_reg"`
	Origin        string  `json:"origin"`
	Destination   string  `json:"destination"`
	WaybillHash   string  `json:"waybill_hash"`
	GPSLat        float64 `json:"gps_lat"`
	GPSLon        float64 `json:"gps_lon"`
}

// InspectionRecord consigne un audit physique/chimique sur site ou laboratoire
type InspectionRecord struct {
	InspectorID string           `json:"inspector_id"`
	Agency      string           `json:"agency"` // SGN-C, SAEMAPE, SENTECH
	Status      InspectionStatus `json:"status"`
	AssayPPM    map[string]float64 `json:"assay_ppm"`
	Notes       string           `json:"notes"`
	Timestamp   string           `json:"timestamp"`
	Signature   string           `json:"signature"`
}

// MineralLot structure centrale d'un lot de minerai extrait
type MineralLot struct {
	ID                string             `json:"id"`                 // Ex: "LOT-KWZ-2026-001"
	MineralType       string             `json:"mineral_type"`       // Cu, Co, Li, 3T
	GrossWeightKg     float64            `json:"gross_weight_kg"`
	NetWeightKg       float64            `json:"net_weight_kg"`
	PitID             string             `json:"pit_id"`             // ID Puits d'origine
	CooperativeID     string             `json:"cooperative_id"`     // Coopérative minière artisanale
	TenementID        string             `json:"tenement_id"`        // Permis CAMI (ZEA / PR / PE)
	CurrentCustodian  string             `json:"current_custodian"`  // Titulaire actuel de la garde physique
	CreatedAt         string             `json:"created_at"`
	InspectionHistory []InspectionRecord `json:"inspection_history"`
	TransportHistory  []TransportEvent   `json:"transport_history"`
}

// HistoryQueryResult structure pour les audits temporels de provenance
type HistoryQueryResult struct {
	TxId      string     `json:"tx_id"`
	Timestamp string     `json:"timestamp"`
	IsDelete  bool       `json:"is_delete"`
	Value     MineralLot `json:"value"`
}

// InitLedger initialise le registre avec un lot pilote
func (c *MineralLotContract) InitLedger(ctx contractapi.TransactionContextInterface) error {
	sampleLot := MineralLot{
		ID:               "LOT-INIT-001",
		MineralType:      "Cu-Co",
		GrossWeightKg:    1000.0,
		NetWeightKg:      980.0,
		PitID:            "PIT-KWZ-ZEA01-001",
		CooperativeID:    "COOP-KOLWEZI-PILOTE",
		TenementID:       "ZEA-4210",
		CurrentCustodian: "COOP-KOLWEZI-PILOTE",
		CreatedAt:        time.Now().UTC().Format(time.RFC3339),
		InspectionHistory: []InspectionRecord{},
		TransportHistory:  []TransportEvent{},
	}

	lotJSON, err := json.Marshal(sampleLot)
	if err != nil {
		return fmt.Errorf("erreur de sérialisation du lot initial: %v", err)
	}

	return ctx.GetStub().PutState(sampleLot.ID, lotJSON)
}

// CreateLot enregistre un nouveau lot scellé au carreau de la mine
func (c *MineralLotContract) CreateLot(
	ctx contractapi.TransactionContextInterface,
	id string,
	mineralType string,
	grossWeightKg float64,
	netWeightKg float64,
	pitID string,
	cooperativeID string,
	tenementID string,
) error {
	exists, err := c.LotExists(ctx, id)
	if err != nil {
		return err
	}
	if exists {
		return fmt.Errorf("le lot %s existe déjà sur le registre", id)
	}

	txTimestamp, err := ctx.GetStub().GetTxTimestamp()
	if err != nil {
		return fmt.Errorf("impossible de récupérer l'horodatage de transaction: %v", err)
	}
	createdAt := time.Unix(txTimestamp.Seconds, int64(txTimestamp.Nanos)).UTC().Format(time.RFC3339)

	lot := MineralLot{
		ID:                id,
		MineralType:       mineralType,
		GrossWeightKg:     grossWeightKg,
		NetWeightKg:       netWeightKg,
		PitID:             pitID,
		CooperativeID:     cooperativeID,
		TenementID:        tenementID,
		CurrentCustodian:  cooperativeID,
		CreatedAt:         createdAt,
		InspectionHistory: []InspectionRecord{},
		TransportHistory:  []TransportEvent{},
	}

	lotJSON, err := json.Marshal(lot)
	if err != nil {
		return err
	}

	return ctx.GetStub().PutState(id, lotJSON)
}

// RecordInspection consigne les conclusions d'inspection et teneurs de laboratoire
func (c *MineralLotContract) RecordInspection(
	ctx contractapi.TransactionContextInterface,
	lotID string,
	inspectorID string,
	agency string,
	status InspectionStatus,
	assayJSON string,
	notes string,
	signature string,
) error {
	lot, err := c.QueryLot(ctx, lotID)
	if err != nil {
		return err
	}

	var assays map[string]float64
	if assayJSON != "" {
		if err := json.Unmarshal([]byte(assayJSON), &assays); err != nil {
			return fmt.Errorf("format JSON des analyses invalide: %v", err)
		}
	}

	txTimestamp, _ := ctx.GetStub().GetTxTimestamp()
	recordTime := time.Unix(txTimestamp.Seconds, int64(txTimestamp.Nanos)).UTC().Format(time.RFC3339)

	inspection := InspectionRecord{
		InspectorID: inspectorID,
		Agency:      agency,
		Status:      status,
		AssayPPM:    assays,
		Notes:       notes,
		Timestamp:   recordTime,
		Signature:   signature,
	}

	lot.InspectionHistory = append(lot.InspectionHistory, inspection)

	updatedJSON, err := json.Marshal(lot)
	if err != nil {
		return err
	}

	return ctx.GetStub().PutState(lotID, updatedJSON)
}

// RecordTransport consigne une étape de transport et transfert de garde
func (c *MineralLotContract) RecordTransport(
	ctx contractapi.TransactionContextInterface,
	lotID string,
	carrierID string,
	vehicleReg string,
	origin string,
	destination string,
	waybillHash string,
	gpsLat float64,
	gpsLon float64,
	newCustodian string,
) error {
	lot, err := c.QueryLot(ctx, lotID)
	if err != nil {
		return err
	}

	txTimestamp, _ := ctx.GetStub().GetTxTimestamp()
	transportTime := time.Unix(txTimestamp.Seconds, int64(txTimestamp.Nanos)).UTC().Format(time.RFC3339)

	transport := TransportEvent{
		Timestamp:   transportTime,
		CarrierID:   carrierID,
		VehicleReg:  vehicleReg,
		Origin:      origin,
		Destination: destination,
		WaybillHash: waybillHash,
		GPSLat:      gpsLat,
		GPSLon:      gpsLon,
	}

	lot.TransportHistory = append(lot.TransportHistory, transport)
	if newCustodian != "" {
		lot.CurrentCustodian = newCustodian
	}

	updatedJSON, err := json.Marshal(lot)
	if err != nil {
		return err
	}

	return ctx.GetStub().PutState(lotID, updatedJSON)
}

// QueryLot lit l'état actuel d'un lot
func (c *MineralLotContract) QueryLot(ctx contractapi.TransactionContextInterface, id string) (*MineralLot, error) {
	lotJSON, err := ctx.GetStub().GetState(id)
	if err != nil {
		return nil, fmt.Errorf("erreur lors de la lecture de l'état: %v", err)
	}
	if lotJSON == nil {
		return nil, fmt.Errorf("le lot %s n'existe pas", id)
	}

	var lot MineralLot
	if err := json.Unmarshal(lotJSON, &lot); err != nil {
		return nil, err
	}

	return &lot, nil
}

// GetLotHistory retourne la totalité de la chaîne de traçabilité immuable
func (c *MineralLotContract) GetLotHistory(ctx contractapi.TransactionContextInterface, id string) ([]HistoryQueryResult, error) {
	iterator, err := ctx.GetStub().GetHistoryForKey(id)
	if err != nil {
		return nil, err
	}
	defer iterator.Close()

	var records []HistoryQueryResult
	for iterator.HasNext() {
		response, err := iterator.Next()
		if err != nil {
			return nil, err
		}

		var lot MineralLot
		if len(response.Value) > 0 {
			if err := json.Unmarshal(response.Value, &lot); err != nil {
				return nil, err
			}
		}

		record := HistoryQueryResult{
			TxId:      response.TxId,
			Timestamp: time.Unix(response.Timestamp.Seconds, int64(response.Timestamp.Nanos)).UTC().Format(time.RFC3339),
			IsDelete:  response.IsDelete,
			Value:     lot,
		}
		records = append(records, record)
	}

	return records, nil
}

// LotExists vérifie l'existence d'une clé dans l'état mondial
func (c *MineralLotContract) LotExists(ctx contractapi.TransactionContextInterface, id string) (bool, error) {
	lotJSON, err := ctx.GetStub().GetState(id)
	if err != nil {
		return false, fmt.Errorf("erreur de lecture: %v", err)
	}
	return lotJSON != nil, nil
}

func main() {
	chaincode, err := contractapi.NewChaincode(&MineralLotContract{})
	if err != nil {
		fmt.Printf("Erreur création chaincode: %s", err.Error())
		return
	}

	if err := chaincode.Start(); err != nil {
		fmt.Printf("Erreur démarrage chaincode: %s", err.Error())
	}
}
