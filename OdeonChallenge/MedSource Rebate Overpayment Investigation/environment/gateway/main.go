package main

import (
	"encoding/json"
	"io"
	"log"
	"net/http"
	"os"
	"time"
)

var (
	rebateEngineURL = getEnv("REBATE_ENGINE_URL", "http://rebate-engine:5001")
	analyticsURL    = getEnv("ANALYTICS_URL", "http://analytics:5002")
)

func getEnv(key, fallback string) string {
	if value, ok := os.LookupEnv(key); ok {
		return value
	}
	return fallback
}

type HealthResponse struct {
	Status   string            `json:"status"`
	Service  string            `json:"service"`
	Upstream map[string]string `json:"upstream"`
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	upstream := make(map[string]string)

	client := &http.Client{Timeout: 2 * time.Second}

	resp, err := client.Get(rebateEngineURL + "/health")
	if err != nil {
		upstream["rebate-engine"] = "unhealthy"
	} else {
		resp.Body.Close()
		upstream["rebate-engine"] = "healthy"
	}

	resp, err = client.Get(analyticsURL + "/health")
	if err != nil {
		upstream["analytics"] = "unhealthy"
	} else {
		resp.Body.Close()
		upstream["analytics"] = "healthy"
	}

	response := HealthResponse{
		Status:   "healthy",
		Service:  "gateway",
		Upstream: upstream,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func proxyHandler(targetBase string) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		targetURL := targetBase + r.URL.Path
		if r.URL.RawQuery != "" {
			targetURL += "?" + r.URL.RawQuery
		}

		client := &http.Client{Timeout: 30 * time.Second}

		var req *http.Request
		var err error

		if r.Method == "POST" || r.Method == "PUT" {
			body, _ := io.ReadAll(r.Body)
			req, err = http.NewRequest(r.Method, targetURL, io.NopCloser(
				&readCloser{data: body},
			))
			req.Header.Set("Content-Type", "application/json")
		} else {
			req, err = http.NewRequest(r.Method, targetURL, nil)
		}

		if err != nil {
			http.Error(w, "Failed to create request", http.StatusInternalServerError)
			return
		}

		resp, err := client.Do(req)
		if err != nil {
			log.Printf("Upstream error: %v", err)
			http.Error(w, "Upstream service unavailable", http.StatusBadGateway)
			return
		}
		defer resp.Body.Close()

		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(resp.StatusCode)
		io.Copy(w, resp.Body)
	}
}

type readCloser struct {
	data []byte
	pos  int
}

func (rc *readCloser) Read(p []byte) (n int, err error) {
	if rc.pos >= len(rc.data) {
		return 0, io.EOF
	}
	n = copy(p, rc.data[rc.pos:])
	rc.pos += n
	return n, nil
}

func (rc *readCloser) Close() error {
	return nil
}

func main() {
	mux := http.NewServeMux()

	mux.HandleFunc("/health", healthHandler)
	mux.HandleFunc("/api/rebate/", proxyHandler(rebateEngineURL))
	mux.HandleFunc("/api/analytics/", proxyHandler(analyticsURL))

	log.Println("Gateway starting on :9000")
	log.Fatal(http.ListenAndServe(":9000", mux))
}
