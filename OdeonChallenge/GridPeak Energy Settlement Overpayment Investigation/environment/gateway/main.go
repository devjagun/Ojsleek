package main

import (
	"bytes"
	"database/sql"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"strconv"
	"time"

	"github.com/gorilla/mux"
	_ "github.com/lib/pq"
)

var db *sql.DB
var settlementURL string
var lossCalcURL string

type Generator struct {
	ID            int       `json:"id"`
	Name          string    `json:"name"`
	GeneratorType string    `json:"generator_type"`
	CapacityMW    float64   `json:"capacity_mw"`
	LocationID    int       `json:"location_id"`
	Commissioned  time.Time `json:"commissioned_date"`
	IsActive      bool      `json:"is_active"`
}

type Node struct {
	ID               int     `json:"id"`
	Name             string  `json:"name"`
	Zone             string  `json:"zone"`
	LocationType     string  `json:"location_type"`
	CongestionFactor float64 `json:"congestion_factor"`
}

type Settlement struct {
	SettlementID     int     `json:"settlement_id"`
	GeneratorID      int     `json:"generator_id"`
	GeneratorName    string  `json:"generator_name"`
	PeriodStart      string  `json:"period_start"`
	PeriodEnd        string  `json:"period_end"`
	EnergyMWH        float64 `json:"energy_mwh"`
	GrossPayment     float64 `json:"gross_payment"`
	LossDeduction    float64 `json:"loss_deduction"`
	CongestionCredit float64 `json:"congestion_credit"`
	NetPayment       float64 `json:"net_payment"`
	RateApplied      float64 `json:"rate_applied"`
	LossFactorApplied float64 `json:"loss_factor_applied"`
	CapacityFactor   float64 `json:"capacity_factor"`
}

type MeterReading struct {
	ID              int       `json:"id"`
	GeneratorID     int       `json:"generator_id"`
	Timestamp       time.Time `json:"timestamp"`
	EnergyMW        float64   `json:"energy_mw"`
	IntervalMinutes int       `json:"interval_minutes"`
}

func initDB() {
	host := os.Getenv("DB_HOST")
	port := os.Getenv("DB_PORT")
	user := os.Getenv("DB_USER")
	password := os.Getenv("DB_PASSWORD")
	dbname := os.Getenv("DB_NAME")

	connStr := fmt.Sprintf("host=%s port=%s user=%s password=%s dbname=%s sslmode=disable",
		host, port, user, password, dbname)

	var err error
	db, err = sql.Open("postgres", connStr)
	if err != nil {
		log.Fatal(err)
	}

	for i := 0; i < 30; i++ {
		err = db.Ping()
		if err == nil {
			break
		}
		log.Printf("Waiting for database... attempt %d", i+1)
		time.Sleep(time.Second)
	}

	if err != nil {
		log.Fatal("Could not connect to database:", err)
	}

	settlementURL = os.Getenv("SETTLEMENT_URL")
	lossCalcURL = os.Getenv("LOSS_CALC_URL")
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	json.NewEncoder(w).Encode(map[string]string{"status": "healthy", "service": "gateway"})
}

func getGeneratorsHandler(w http.ResponseWriter, r *http.Request) {
	rows, err := db.Query(`
		SELECT g.id, g.name, g.generator_type, g.capacity_mw, g.location_id, 
		       g.commissioned_date, g.is_active, n.zone, n.location_type
		FROM generators g
		JOIN nodes n ON g.location_id = n.id
		ORDER BY g.id
	`)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	type GeneratorWithNode struct {
		Generator
		Zone         string `json:"zone"`
		LocationType string `json:"location_type"`
	}

	var generators []GeneratorWithNode
	for rows.Next() {
		var g GeneratorWithNode
		err := rows.Scan(&g.ID, &g.Name, &g.GeneratorType, &g.CapacityMW,
			&g.LocationID, &g.Commissioned, &g.IsActive, &g.Zone, &g.LocationType)
		if err != nil {
			continue
		}
		generators = append(generators, g)
	}

	json.NewEncoder(w).Encode(generators)
}

func getGeneratorHandler(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	id, _ := strconv.Atoi(vars["id"])

	var g Generator
	var zone, locType string
	err := db.QueryRow(`
		SELECT g.id, g.name, g.generator_type, g.capacity_mw, g.location_id,
		       g.commissioned_date, g.is_active, n.zone, n.location_type
		FROM generators g
		JOIN nodes n ON g.location_id = n.id
		WHERE g.id = $1
	`, id).Scan(&g.ID, &g.Name, &g.GeneratorType, &g.CapacityMW,
		&g.LocationID, &g.Commissioned, &g.IsActive, &zone, &locType)

	if err != nil {
		http.Error(w, "Generator not found", http.StatusNotFound)
		return
	}

	result := map[string]interface{}{
		"id":               g.ID,
		"name":             g.Name,
		"generator_type":   g.GeneratorType,
		"capacity_mw":      g.CapacityMW,
		"location_id":      g.LocationID,
		"commissioned_date": g.Commissioned,
		"is_active":        g.IsActive,
		"zone":             zone,
		"location_type":    locType,
	}

	json.NewEncoder(w).Encode(result)
}

func getNodesHandler(w http.ResponseWriter, r *http.Request) {
	rows, err := db.Query(`SELECT id, name, zone, location_type, congestion_factor FROM nodes ORDER BY id`)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	var nodes []Node
	for rows.Next() {
		var n Node
		rows.Scan(&n.ID, &n.Name, &n.Zone, &n.LocationType, &n.CongestionFactor)
		nodes = append(nodes, n)
	}

	json.NewEncoder(w).Encode(nodes)
}

func getSettlementsHandler(w http.ResponseWriter, r *http.Request) {
	generatorID := r.URL.Query().Get("generator_id")
	periodStart := r.URL.Query().Get("period_start")
	periodEnd := r.URL.Query().Get("period_end")

	query := `
		SELECT s.settlement_id, s.generator_id, g.name, s.period_start, s.period_end,
		       s.energy_mwh, s.gross_payment, s.loss_deduction, s.congestion_credit,
		       s.net_payment, s.rate_applied, s.loss_factor_applied, s.capacity_factor
		FROM settlements s
		JOIN generators g ON s.generator_id = g.id
		WHERE 1=1
	`
	var args []interface{}
	argCount := 0

	if generatorID != "" {
		argCount++
		query += fmt.Sprintf(" AND s.generator_id = $%d", argCount)
		gid, _ := strconv.Atoi(generatorID)
		args = append(args, gid)
	}

	if periodStart != "" {
		argCount++
		query += fmt.Sprintf(" AND s.period_start >= $%d", argCount)
		args = append(args, periodStart)
	}

	if periodEnd != "" {
		argCount++
		query += fmt.Sprintf(" AND s.period_end <= $%d", argCount)
		args = append(args, periodEnd)
	}

	query += " ORDER BY s.settlement_id"

	rows, err := db.Query(query, args...)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	var settlements []Settlement
	for rows.Next() {
		var s Settlement
		rows.Scan(&s.SettlementID, &s.GeneratorID, &s.GeneratorName, &s.PeriodStart,
			&s.PeriodEnd, &s.EnergyMWH, &s.GrossPayment, &s.LossDeduction,
			&s.CongestionCredit, &s.NetPayment, &s.RateApplied, &s.LossFactorApplied,
			&s.CapacityFactor)
		settlements = append(settlements, s)
	}

	json.NewEncoder(w).Encode(settlements)
}

func getMeterReadingsHandler(w http.ResponseWriter, r *http.Request) {
	generatorID := r.URL.Query().Get("generator_id")
	startTime := r.URL.Query().Get("start")
	endTime := r.URL.Query().Get("end")
	limit := r.URL.Query().Get("limit")

	query := `SELECT id, generator_id, timestamp, energy_mw, interval_minutes FROM meter_readings WHERE 1=1`
	var args []interface{}
	argCount := 0

	if generatorID != "" {
		argCount++
		query += fmt.Sprintf(" AND generator_id = $%d", argCount)
		gid, _ := strconv.Atoi(generatorID)
		args = append(args, gid)
	}

	if startTime != "" {
		argCount++
		query += fmt.Sprintf(" AND timestamp >= $%d", argCount)
		args = append(args, startTime)
	}

	if endTime != "" {
		argCount++
		query += fmt.Sprintf(" AND timestamp < $%d", argCount)
		args = append(args, endTime)
	}

	query += " ORDER BY timestamp"

	if limit != "" {
		argCount++
		query += fmt.Sprintf(" LIMIT $%d", argCount)
		l, _ := strconv.Atoi(limit)
		args = append(args, l)
	}

	rows, err := db.Query(query, args...)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	var readings []MeterReading
	for rows.Next() {
		var m MeterReading
		rows.Scan(&m.ID, &m.GeneratorID, &m.Timestamp, &m.EnergyMW, &m.IntervalMinutes)
		readings = append(readings, m)
	}

	json.NewEncoder(w).Encode(readings)
}

func getLossFactorsHandler(w http.ResponseWriter, r *http.Request) {
	rows, err := db.Query(`
		SELECT id, zone, energy_threshold, loss_rate, effective_date 
		FROM loss_factors 
		ORDER BY zone, effective_date DESC
	`)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	type LossFactor struct {
		ID              int     `json:"id"`
		Zone            string  `json:"zone"`
		EnergyThreshold float64 `json:"energy_threshold"`
		LossRate        float64 `json:"loss_rate"`
		EffectiveDate   string  `json:"effective_date"`
	}

	var factors []LossFactor
	for rows.Next() {
		var f LossFactor
		rows.Scan(&f.ID, &f.Zone, &f.EnergyThreshold, &f.LossRate, &f.EffectiveDate)
		factors = append(factors, f)
	}

	json.NewEncoder(w).Encode(factors)
}

func getRateTiersHandler(w http.ResponseWriter, r *http.Request) {
	rows, err := db.Query(`
		SELECT tier_id, generator_type, min_capacity_factor, location_type, 
		       rate_per_mwh, priority_order
		FROM rate_tiers
		ORDER BY generator_type, priority_order
	`)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	type RateTier struct {
		TierID           int      `json:"tier_id"`
		GeneratorType    string   `json:"generator_type"`
		MinCapacityFactor *float64 `json:"min_capacity_factor"`
		LocationType     *string  `json:"location_type"`
		RatePerMWH       float64  `json:"rate_per_mwh"`
		PriorityOrder    int      `json:"priority_order"`
	}

	var tiers []RateTier
	for rows.Next() {
		var t RateTier
		rows.Scan(&t.TierID, &t.GeneratorType, &t.MinCapacityFactor, &t.LocationType,
			&t.RatePerMWH, &t.PriorityOrder)
		tiers = append(tiers, t)
	}

	json.NewEncoder(w).Encode(tiers)
}

func getWeatherDataHandler(w http.ResponseWriter, r *http.Request) {
	zone := r.URL.Query().Get("zone")
	startTime := r.URL.Query().Get("start")
	endTime := r.URL.Query().Get("end")

	query := `SELECT id, timestamp, zone, temperature, demand_factor FROM weather_data WHERE 1=1`
	var args []interface{}
	argCount := 0

	if zone != "" {
		argCount++
		query += fmt.Sprintf(" AND zone = $%d", argCount)
		args = append(args, zone)
	}

	if startTime != "" {
		argCount++
		query += fmt.Sprintf(" AND timestamp >= $%d", argCount)
		args = append(args, startTime)
	}

	if endTime != "" {
		argCount++
		query += fmt.Sprintf(" AND timestamp < $%d", argCount)
		args = append(args, endTime)
	}

	query += " ORDER BY timestamp LIMIT 1000"

	rows, err := db.Query(query, args...)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	type WeatherRecord struct {
		ID           int     `json:"id"`
		Timestamp    string  `json:"timestamp"`
		Zone         string  `json:"zone"`
		Temperature  float64 `json:"temperature"`
		DemandFactor float64 `json:"demand_factor"`
	}

	var records []WeatherRecord
	for rows.Next() {
		var r WeatherRecord
		rows.Scan(&r.ID, &r.Timestamp, &r.Zone, &r.Temperature, &r.DemandFactor)
		records = append(records, r)
	}

	json.NewEncoder(w).Encode(records)
}

func getTransmissionUpgradesHandler(w http.ResponseWriter, r *http.Request) {
	rows, err := db.Query(`
		SELECT id, line_id, zone, upgrade_date, capacity_increase, description
		FROM transmission_upgrades
		ORDER BY upgrade_date DESC
	`)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	type Upgrade struct {
		ID               int     `json:"id"`
		LineID           string  `json:"line_id"`
		Zone             string  `json:"zone"`
		UpgradeDate      string  `json:"upgrade_date"`
		CapacityIncrease float64 `json:"capacity_increase"`
		Description      string  `json:"description"`
	}

	var upgrades []Upgrade
	for rows.Next() {
		var u Upgrade
		rows.Scan(&u.ID, &u.LineID, &u.Zone, &u.UpgradeDate, &u.CapacityIncrease, &u.Description)
		upgrades = append(upgrades, u)
	}

	json.NewEncoder(w).Encode(upgrades)
}

func getMeterFirmwareHandler(w http.ResponseWriter, r *http.Request) {
	rows, err := db.Query(`
		SELECT id, generator_id, firmware_version, update_date, notes
		FROM meter_firmware_updates
		ORDER BY update_date DESC
	`)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	type FirmwareUpdate struct {
		ID              int    `json:"id"`
		GeneratorID     int    `json:"generator_id"`
		FirmwareVersion string `json:"firmware_version"`
		UpdateDate      string `json:"update_date"`
		Notes           string `json:"notes"`
	}

	var updates []FirmwareUpdate
	for rows.Next() {
		var u FirmwareUpdate
		rows.Scan(&u.ID, &u.GeneratorID, &u.FirmwareVersion, &u.UpdateDate, &u.Notes)
		updates = append(updates, u)
	}

	json.NewEncoder(w).Encode(updates)
}

func calculateSettlementHandler(w http.ResponseWriter, r *http.Request) {
	body, _ := io.ReadAll(r.Body)
	
	resp, err := http.Post(settlementURL+"/calculate", "application/json", bytes.NewBuffer(body))
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	defer resp.Body.Close()

	respBody, _ := io.ReadAll(resp.Body)
	w.Header().Set("Content-Type", "application/json")
	w.Write(respBody)
}

func recalculateAllHandler(w http.ResponseWriter, r *http.Request) {
	body, _ := io.ReadAll(r.Body)

	resp, err := http.Post(settlementURL+"/recalculate_all", "application/json", bytes.NewBuffer(body))
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	defer resp.Body.Close()

	respBody, _ := io.ReadAll(resp.Body)
	w.Header().Set("Content-Type", "application/json")
	w.Write(respBody)
}

func getSettlementSummaryHandler(w http.ResponseWriter, r *http.Request) {
	periodStart := r.URL.Query().Get("period_start")
	periodEnd := r.URL.Query().Get("period_end")

	query := `
		SELECT g.generator_type, n.zone,
		       COUNT(*) as settlement_count,
		       SUM(s.energy_mwh) as total_energy,
		       SUM(s.gross_payment) as total_gross,
		       SUM(s.loss_deduction) as total_loss_deduction,
		       SUM(s.congestion_credit) as total_congestion_credit,
		       SUM(s.net_payment) as total_net,
		       AVG(s.rate_applied) as avg_rate,
		       AVG(s.loss_factor_applied) as avg_loss_factor
		FROM settlements s
		JOIN generators g ON s.generator_id = g.id
		JOIN nodes n ON g.location_id = n.id
		WHERE 1=1
	`
	var args []interface{}
	argCount := 0

	if periodStart != "" {
		argCount++
		query += fmt.Sprintf(" AND s.period_start >= $%d", argCount)
		args = append(args, periodStart)
	}

	if periodEnd != "" {
		argCount++
		query += fmt.Sprintf(" AND s.period_end <= $%d", argCount)
		args = append(args, periodEnd)
	}

	query += " GROUP BY g.generator_type, n.zone ORDER BY g.generator_type, n.zone"

	rows, err := db.Query(query, args...)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	type Summary struct {
		GeneratorType         string  `json:"generator_type"`
		Zone                  string  `json:"zone"`
		SettlementCount       int     `json:"settlement_count"`
		TotalEnergy           float64 `json:"total_energy_mwh"`
		TotalGross            float64 `json:"total_gross_payment"`
		TotalLossDeduction    float64 `json:"total_loss_deduction"`
		TotalCongestionCredit float64 `json:"total_congestion_credit"`
		TotalNet              float64 `json:"total_net_payment"`
		AvgRate               float64 `json:"avg_rate"`
		AvgLossFactor         float64 `json:"avg_loss_factor"`
	}

	var summaries []Summary
	for rows.Next() {
		var s Summary
		rows.Scan(&s.GeneratorType, &s.Zone, &s.SettlementCount, &s.TotalEnergy,
			&s.TotalGross, &s.TotalLossDeduction, &s.TotalCongestionCredit,
			&s.TotalNet, &s.AvgRate, &s.AvgLossFactor)
		summaries = append(summaries, s)
	}

	json.NewEncoder(w).Encode(summaries)
}

func getSettlementEnergyAnalysisHandler(w http.ResponseWriter, r *http.Request) {
	query := `
		SELECT
			bucket_label,
			bucket_order,
			COUNT(*) as settlement_count,
			ROUND(AVG(s.loss_factor_applied)::numeric, 6) as avg_loss_factor,
			ROUND(MIN(s.loss_factor_applied)::numeric, 6) as min_loss_factor,
			ROUND(AVG(s.loss_deduction)::numeric, 2) as avg_loss_deduction,
			ROUND(SUM(s.loss_deduction)::numeric, 2) as total_loss_deduction,
			SUM(CASE WHEN s.loss_factor_applied = 1.0 THEN 1 ELSE 0 END) as unity_factor_count,
			ROUND(AVG(s.net_payment)::numeric, 2) as avg_net_payment,
			ROUND(SUM(s.net_payment)::numeric, 2) as total_net_payment
		FROM (
			SELECT settlements.*,
				CASE
					WHEN energy_mwh < 50 THEN '0-50'
					WHEN energy_mwh < 100 THEN '50-100'
					WHEN energy_mwh < 125 THEN '100-125'
					WHEN energy_mwh < 150 THEN '125-150'
					WHEN energy_mwh < 200 THEN '150-200'
					WHEN energy_mwh < 300 THEN '200-300'
					WHEN energy_mwh < 500 THEN '300-500'
					WHEN energy_mwh < 1000 THEN '500-1000'
					ELSE '1000+'
				END as bucket_label,
				CASE
					WHEN energy_mwh < 50 THEN 1
					WHEN energy_mwh < 100 THEN 2
					WHEN energy_mwh < 125 THEN 3
					WHEN energy_mwh < 150 THEN 4
					WHEN energy_mwh < 200 THEN 5
					WHEN energy_mwh < 300 THEN 6
					WHEN energy_mwh < 500 THEN 7
					WHEN energy_mwh < 1000 THEN 8
					ELSE 9
				END as bucket_order
			FROM settlements
		) s
		GROUP BY bucket_label, bucket_order
		ORDER BY bucket_order
	`

	rows, err := db.Query(query)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	type BucketAnalysis struct {
		EnergyBucket       string  `json:"energy_bucket"`
		SettlementCount    int     `json:"settlement_count"`
		AvgLossFactor      float64 `json:"avg_loss_factor"`
		MinLossFactor      float64 `json:"min_loss_factor"`
		AvgLossDeduction   float64 `json:"avg_loss_deduction"`
		TotalLossDeduction float64 `json:"total_loss_deduction"`
		UnityFactorCount   int     `json:"unity_factor_count"`
		AvgNetPayment      float64 `json:"avg_net_payment"`
		TotalNetPayment    float64 `json:"total_net_payment"`
	}

	var results []BucketAnalysis
	for rows.Next() {
		var b BucketAnalysis
		var bucketOrder int
		rows.Scan(&b.EnergyBucket, &bucketOrder, &b.SettlementCount, &b.AvgLossFactor,
			&b.MinLossFactor, &b.AvgLossDeduction, &b.TotalLossDeduction,
			&b.UnityFactorCount, &b.AvgNetPayment, &b.TotalNetPayment)
		results = append(results, b)
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(results)
}

func getSettlementDataQualityAnalysisHandler(w http.ResponseWriter, r *http.Request) {
	query := `
		WITH generator_quality AS (
			SELECT
				generator_id,
				COUNT(*) FILTER (WHERE quality_flag IS NOT NULL) as flagged_count,
				COUNT(*) FILTER (WHERE quality_flag = 'DECOMMISSIONED') as decommissioned_count,
				COUNT(*) as total_readings
			FROM meter_readings
			GROUP BY generator_id
		)
		SELECT
			CASE WHEN COALESCE(gq.flagged_count, 0) > 0
				THEN 'has_flagged_readings'
				ELSE 'clean_only'
			END as data_quality_group,
			n.location_type,
			COUNT(*) as settlement_count,
			ROUND(AVG(s.rate_applied)::numeric, 2) as avg_rate_applied,
			ROUND(AVG(s.loss_factor_applied)::numeric, 6) as avg_loss_factor,
			SUM(CASE WHEN s.loss_factor_applied = 1.0 THEN 1 ELSE 0 END) as unity_loss_count,
			ROUND(AVG(s.net_payment)::numeric, 2) as avg_net_payment,
			ROUND(SUM(s.net_payment)::numeric, 2) as total_net_payment,
			ROUND(AVG(s.capacity_factor)::numeric, 4) as avg_capacity_factor
		FROM settlements s
		JOIN generators g ON s.generator_id = g.id
		JOIN nodes n ON g.location_id = n.id
		LEFT JOIN generator_quality gq ON gq.generator_id = s.generator_id
		GROUP BY
			CASE WHEN COALESCE(gq.flagged_count, 0) > 0
				THEN 'has_flagged_readings'
				ELSE 'clean_only'
			END,
			n.location_type
		ORDER BY data_quality_group, n.location_type
	`

	rows, err := db.Query(query)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	type QualityAnalysis struct {
		DataQualityGroup string  `json:"data_quality_group"`
		LocationType     string  `json:"location_type"`
		SettlementCount  int     `json:"settlement_count"`
		AvgRateApplied   float64 `json:"avg_rate_applied"`
		AvgLossFactor    float64 `json:"avg_loss_factor"`
		UnityLossCount   int     `json:"unity_loss_count"`
		AvgNetPayment    float64 `json:"avg_net_payment"`
		TotalNetPayment  float64 `json:"total_net_payment"`
		AvgCapacityFactor float64 `json:"avg_capacity_factor"`
	}

	var results []QualityAnalysis
	for rows.Next() {
		var q QualityAnalysis
		rows.Scan(&q.DataQualityGroup, &q.LocationType, &q.SettlementCount,
			&q.AvgRateApplied, &q.AvgLossFactor, &q.UnityLossCount,
			&q.AvgNetPayment, &q.TotalNetPayment, &q.AvgCapacityFactor)
		results = append(results, q)
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(results)
}

func main() {
	initDB()

	r := mux.NewRouter()

	r.HandleFunc("/health", healthHandler).Methods("GET")
	r.HandleFunc("/api/generators", getGeneratorsHandler).Methods("GET")
	r.HandleFunc("/api/generators/{id}", getGeneratorHandler).Methods("GET")
	r.HandleFunc("/api/nodes", getNodesHandler).Methods("GET")
	r.HandleFunc("/api/settlements", getSettlementsHandler).Methods("GET")
	r.HandleFunc("/api/settlements/summary", getSettlementSummaryHandler).Methods("GET")
	r.HandleFunc("/api/settlements/energy_analysis", getSettlementEnergyAnalysisHandler).Methods("GET")
	r.HandleFunc("/api/settlements/data_quality_analysis", getSettlementDataQualityAnalysisHandler).Methods("GET")
	r.HandleFunc("/api/meter_readings", getMeterReadingsHandler).Methods("GET")
	r.HandleFunc("/api/loss_factors", getLossFactorsHandler).Methods("GET")
	r.HandleFunc("/api/rate_tiers", getRateTiersHandler).Methods("GET")
	r.HandleFunc("/api/weather", getWeatherDataHandler).Methods("GET")
	r.HandleFunc("/api/transmission_upgrades", getTransmissionUpgradesHandler).Methods("GET")
	r.HandleFunc("/api/meter_firmware", getMeterFirmwareHandler).Methods("GET")

	r.HandleFunc("/api/calculate", calculateSettlementHandler).Methods("POST")
	r.HandleFunc("/api/recalculate_all", recalculateAllHandler).Methods("POST")

	log.Println("Gateway starting on :8080")
	log.Fatal(http.ListenAndServe(":8080", r))
}
