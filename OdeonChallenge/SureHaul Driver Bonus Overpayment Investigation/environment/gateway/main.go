package main

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"log/slog"
	"net/http"
	"os"
	"time"

	_ "github.com/lib/pq"
)

var db *sql.DB
var logger *slog.Logger

type Driver struct {
	DriverID int       `json:"driver_id"`
	Name     string    `json:"name"`
	HireDate time.Time `json:"hire_date"`
	Tier     string    `json:"tier"`
	Status   string    `json:"status"`
	Region   string    `json:"region"`
}

type Zone struct {
	ZoneID         int     `json:"zone_id"`
	ZoneName       string  `json:"zone_name"`
	BaseDifficulty float64 `json:"base_difficulty"`
	Region         string  `json:"region"`
}

type Shift struct {
	ShiftID            int       `json:"shift_id"`
	DriverID           int       `json:"driver_id"`
	ShiftDate          time.Time `json:"shift_date"`
	ZoneID             int       `json:"zone_id"`
	DeliveriesComplete int       `json:"deliveries_completed"`
	RouteTarget        int       `json:"route_target"`
}

func main() {
	logger = slog.New(slog.NewJSONHandler(os.Stdout, nil))

	dbURL := os.Getenv("DATABASE_URL")
	if dbURL == "" {
		dbURL = "postgres://surehaul:surehaul123@postgres:5432/surehaul?sslmode=disable"
	}

	var err error
	for i := 0; i < 30; i++ {
		db, err = sql.Open("postgres", dbURL)
		if err == nil {
			err = db.Ping()
			if err == nil {
				break
			}
		}
		logger.Info("waiting for database", "attempt", i+1)
		time.Sleep(2 * time.Second)
	}
	if err != nil {
		logger.Error("failed to connect to database", "error", err)
		os.Exit(1)
	}
	defer db.Close()

	http.HandleFunc("/health", healthHandler)
	http.HandleFunc("/api/drivers", driversHandler)
	http.HandleFunc("/api/drivers/", driverHandler)
	http.HandleFunc("/api/zones", zonesHandler)
	http.HandleFunc("/api/routes/summary", routeSummaryHandler)

	logger.Info("gateway starting", "port", 8080)
	if err := http.ListenAndServe(":8080", nil); err != nil {
		logger.Error("server failed", "error", err)
		os.Exit(1)
	}
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "healthy"})
}

func driversHandler(w http.ResponseWriter, r *http.Request) {
	rows, err := db.Query(`
		SELECT driver_id, name, hire_date, tier, status, region 
		FROM drivers ORDER BY driver_id
	`)
	if err != nil {
		logger.Error("query failed", "error", err)
		http.Error(w, "Internal error", 500)
		return
	}
	defer rows.Close()

	var drivers []Driver
	for rows.Next() {
		var d Driver
		if err := rows.Scan(&d.DriverID, &d.Name, &d.HireDate, &d.Tier, &d.Status, &d.Region); err != nil {
			logger.Error("scan failed", "error", err)
			continue
		}
		drivers = append(drivers, d)
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(drivers)
}

func driverHandler(w http.ResponseWriter, r *http.Request) {
	path := r.URL.Path
	var driverID int
	
	if _, err := fmt.Sscanf(path, "/api/drivers/%d/shifts", &driverID); err == nil {
		driverShiftsHandler(w, r, driverID)
		return
	}
	
	if _, err := fmt.Sscanf(path, "/api/drivers/%d", &driverID); err == nil {
		singleDriverHandler(w, r, driverID)
		return
	}
	
	http.NotFound(w, r)
}

func singleDriverHandler(w http.ResponseWriter, r *http.Request, driverID int) {
	var d Driver
	err := db.QueryRow(`
		SELECT driver_id, name, hire_date, tier, status, region 
		FROM drivers WHERE driver_id = $1
	`, driverID).Scan(&d.DriverID, &d.Name, &d.HireDate, &d.Tier, &d.Status, &d.Region)
	
	if err == sql.ErrNoRows {
		http.Error(w, "Driver not found", 404)
		return
	}
	if err != nil {
		logger.Error("query failed", "error", err)
		http.Error(w, "Internal error", 500)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(d)
}

func driverShiftsHandler(w http.ResponseWriter, r *http.Request, driverID int) {
	startDate := r.URL.Query().Get("start_date")
	endDate := r.URL.Query().Get("end_date")
	
	if startDate == "" || endDate == "" {
		http.Error(w, "start_date and end_date required", 400)
		return
	}

	rows, err := db.Query(`
		SELECT shift_id, driver_id, shift_date, zone_id, deliveries_completed, route_target
		FROM shifts 
		WHERE driver_id = $1 AND shift_date BETWEEN $2 AND $3
		ORDER BY shift_date
	`, driverID, startDate, endDate)
	if err != nil {
		logger.Error("query failed", "error", err)
		http.Error(w, "Internal error", 500)
		return
	}
	defer rows.Close()

	var shifts []Shift
	for rows.Next() {
		var s Shift
		if err := rows.Scan(&s.ShiftID, &s.DriverID, &s.ShiftDate, &s.ZoneID, &s.DeliveriesComplete, &s.RouteTarget); err != nil {
			logger.Error("scan failed", "error", err)
			continue
		}
		shifts = append(shifts, s)
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(shifts)
}

func zonesHandler(w http.ResponseWriter, r *http.Request) {
	rows, err := db.Query(`
		SELECT zone_id, zone_name, base_difficulty, region 
		FROM zones WHERE active = true ORDER BY zone_id
	`)
	if err != nil {
		logger.Error("query failed", "error", err)
		http.Error(w, "Internal error", 500)
		return
	}
	defer rows.Close()

	var zones []Zone
	for rows.Next() {
		var z Zone
		if err := rows.Scan(&z.ZoneID, &z.ZoneName, &z.BaseDifficulty, &z.Region); err != nil {
			logger.Error("scan failed", "error", err)
			continue
		}
		zones = append(zones, z)
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(zones)
}

func routeSummaryHandler(w http.ResponseWriter, r *http.Request) {
	startDate := r.URL.Query().Get("start_date")
	endDate := r.URL.Query().Get("end_date")
	
	if startDate == "" || endDate == "" {
		http.Error(w, "start_date and end_date required", 400)
		return
	}

	var result struct {
		TotalShifts        int     `json:"total_shifts"`
		TotalDeliveries    int     `json:"total_deliveries"`
		TotalTargets       int     `json:"total_targets"`
		AvgDeliveriesShift float64 `json:"avg_deliveries_per_shift"`
		EfficiencyRatio    float64 `json:"efficiency_ratio"`
	}

	err := db.QueryRow(`
		SELECT 
			COUNT(*) as total_shifts,
			SUM(deliveries_completed) as total_deliveries,
			SUM(route_target) as total_targets,
			AVG(deliveries_completed) as avg_deliveries,
			CASE WHEN SUM(route_target) > 0 
				THEN SUM(deliveries_completed)::float / SUM(route_target) 
				ELSE 0 END as efficiency
		FROM shifts 
		WHERE shift_date BETWEEN $1 AND $2
	`, startDate, endDate).Scan(
		&result.TotalShifts, &result.TotalDeliveries, &result.TotalTargets,
		&result.AvgDeliveriesShift, &result.EfficiencyRatio,
	)
	if err != nil {
		logger.Error("query failed", "error", err)
		http.Error(w, "Internal error", 500)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(result)
}
