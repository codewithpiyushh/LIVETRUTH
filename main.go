package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"html/template"
	"io"
	"io/ioutil"
	"net/http"
	"project/scraper"
	"time"
	"sync"
)

// Structs

type ClaimResult struct {
	Claim           string `json:"claim"`
	Output          bool   `json:"output"`
	ConfidenceScore int    `json:"confidence_score"`
	Explanation     string `json:"explanation"`
	Date            string `json:"date"`
}

type ContextResult struct {
	URL              string `json:"url"`
	CredibilityScore int    `json:"credibility_score"`
}


type RequestPayload struct {
    URL string `json:"url"`
}

var Urls []string

// Handlers for HTML templates

func homeHandler(w http.ResponseWriter, r *http.Request) {
	tmpl := template.Must(template.ParseFiles("static/index.html"))
	tmpl.Execute(w, nil)
}
func TrendingHandler(w http.ResponseWriter, r *http.Request) {
	tmpl := template.Must(template.ParseFiles("static/trending.html"))
	tmpl.Execute(w, nil)
}
func VolunteerHandler(w http.ResponseWriter, r *http.Request) {
	tmpl := template.Must(template.ParseFiles("static/volunteer.html"))
	tmpl.Execute(w, nil)
}
func LiveHandler(w http.ResponseWriter, r *http.Request) {
	tmpl := template.Must(template.ParseFiles("static/liveanalysis.html"))
	tmpl.Execute(w, nil)
}
func ImageHandler(w http.ResponseWriter, r *http.Request) {
	tmpl := template.Must(template.ParseFiles("static/imagenews.html"))
	tmpl.Execute(w, nil)
}

// ScrapeHandler - triggers scraping based on query
func ScrapeHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Access-Control-Allow-Methods", "POST, OPTIONS")
	w.Header().Set("Access-Control-Allow-Headers", "Content-Type")
	w.Header().Set("Content-Type", "application/json")

	if r.Method == http.MethodOptions {
		w.WriteHeader(http.StatusOK)
		return
	}

	if r.Method != http.MethodPost {
		http.Error(w, "Invalid request method", http.StatusMethodNotAllowed)
		return
	}

	query := r.FormValue("query")
	if query == "" {
		http.Error(w, "Query parameter is required", http.StatusBadRequest)
		return
	}

	fmt.Println("🔍 Received query:", query)
	urls, err := scraper.ExtractRelevantUrls(query)
	if err != nil || len(urls) == 0 {
		http.Error(w, fmt.Sprintf("Failed to get URLs: %v", err), http.StatusInternalServerError)
		return
	}

	Urls = urls


	resultsChan := make(chan scraper.ScrapeResult, len(urls))
	go scraper.Worker(urls, resultsChan)

	var results []scraper.ScrapeResult
	for result := range resultsChan {
		results = append(results, result)
	}

	jsonData, _ := json.MarshalIndent(results, "", "  ")
	ioutil.WriteFile("scraped_data.json", jsonData, 0644)

	// Convert to desired JSON format
	var formatted []map[string]string
	for _, url := range urls {
		formatted = append(formatted, map[string]string{"url": url})
	}

	// fmt.Print(json.Marshal(formatted))
	// Encode the final result
	err = json.NewEncoder(w).Encode(formatted)
	if err != nil {
		http.Error(w, fmt.Sprintf("Error encoding json: %v", err), http.StatusInternalServerError)
		return
	}
}

// runPythonScript - calls Flask services
func runPythonScript(newsArticle string, urls []string) ([]ClaimResult, []ContextResult, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 120*time.Second)
	defer cancel()

	// Step 1: Create vector DB
	createDBReq, err := http.NewRequestWithContext(ctx, "POST", "http://127.0.0.1:5500/create-db", nil)
	if err != nil {
		return nil, nil, fmt.Errorf("failed to create create-db request: %v", err)
	}
	createDBResp, err := http.DefaultClient.Do(createDBReq)
	if err != nil {
		return nil, nil, fmt.Errorf("create-db request failed: %v", err)
	}
	defer createDBResp.Body.Close()

	chromaDirBytes, err := io.ReadAll(createDBResp.Body)
	if err != nil {
		return nil, nil, fmt.Errorf("failed to read create-db response: %v", err)
	}
	chromaDirectory := string(chromaDirBytes)
	fmt.Println("🌐 Chroma Directory:", chromaDirectory)

	var (
		claimResults   []ClaimResult
		contextResults []ContextResult
		claimErr       error
		contextErr     error
		wg             sync.WaitGroup
	)

	wg.Add(2)

	// ➤ Verify-Claims (RAG call)
	go func() {
		defer wg.Done()
		ragPayload := map[string]string{
			"chroma-db": chromaDirectory,
			"article":   newsArticle,
		}
		ragJSON, _ := json.Marshal(ragPayload)

		ragReq, _ := http.NewRequestWithContext(ctx, "POST", "http://127.0.0.1:5000/verify-claims", bytes.NewBuffer(ragJSON))
		ragReq.Header.Set("Content-Type", "application/json")

		ragResp, err := http.DefaultClient.Do(ragReq)
		if err != nil {
			claimErr = fmt.Errorf("verify-claims request failed: %v", err)
			return
		}
		defer ragResp.Body.Close()

		ragRespBody, _ := io.ReadAll(ragResp.Body)
		fmt.Println("🌐 RAG Response:", string(ragRespBody))

		if err := json.Unmarshal(ragRespBody, &claimResults); err != nil {
			claimErr = fmt.Errorf("failed to parse claim results: %v", err)
		}
	}()

	// ➤ Analyze Context Credibility
	go func() {
		defer wg.Done() // Decrement counter when this goroutine completes

		//  Static response for testing
		staticResponse := []ContextResult{
			{URL: "http://pib.gov.in/", CredibilityScore: 94},
			{URL: "https://timesofindia.indiatimes.com/", CredibilityScore: 70},
			{URL: "https://www.hindustantimes.com/", CredibilityScore: 75},
			{URL: "https://en.wikipedia.org/", CredibilityScore: 50},
			
		}

		// Simulate a successful response.
		contextResults = staticResponse
		return

		// Comment out the actual HTTP call
		/*
		contextPayload := map[string]interface{}{
			"chroma-db": chromaDirectory,
			"urls":      urls,
			"article":   newsArticle,
		}
		contextJSON, _ := json.Marshal(contextPayload)

		contextReq, _ := http.NewRequestWithContext(ctx, "POST", "http://127.0.0.1:5000/analyze", bytes.NewBuffer(contextJSON))
		contextReq.Header.Set("Content-Type", "application/json")

		contextResp, err := http.DefaultClient.Do(contextReq)
		if err != nil {
			contextErr = fmt.Errorf("analyze request failed: %v", err)
			return // IMPORTANT: Return on error
		}
		defer func() {
			if contextResp != nil {
				contextResp.Body.Close() // Ensure body is closed.
			}
		}()

		contextRespBody, _ := io.ReadAll(contextResp.Body)
		fmt.Println("🌐 Context Response:", string(contextRespBody))

		if err := json.Unmarshal(contextRespBody, &contextResults); err != nil {
			contextErr = fmt.Errorf("failed to parse context results: %v", err)
		}
		*/
	}()

	wg.Wait() // Wait for both goroutines to finish

	// Check for errors after both goroutines have completed.
	if claimErr != nil {
		return nil, nil, claimErr
	}
	if contextErr != nil {
		return nil, nil, contextErr
	}

	return claimResults, contextResults, nil
}

// ProcessHandler - main RAG endpoint
func ProcessHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Access-Control-Allow-Methods", "POST, OPTIONS")
	w.Header().Set("Access-Control-Allow-Headers", "Content-Type")

	if r.Method != http.MethodPost {
		http.Error(w, "Invalid request method", http.StatusMethodNotAllowed)
		return
	}

	var payload struct {
		Article string   `json:"article"`
		Urls    []string `json:"urls"`
	}

	query := r.FormValue("query")
	if query == "" {
		http.Error(w, "Query parameter is required", http.StatusBadRequest)
		return
	}
	payload.Article = query
	payload.Urls = Urls
	
	fmt.Println(payload.Article)
	fmt.Println(payload.Urls)

	// err := json.NewDecoder(r.Body).Decode(&payload)
	// if err != nil || payload.Article == "" {
	// 	http.Error(w, "Invalid JSON or missing 'article'", http.StatusBadRequest)
	// 	return
	// }

	fmt.Println("📝 Received article for processing")
	claims, contextResults, err := runPythonScript(payload.Article, payload.Urls)
	if err != nil {
		http.Error(w, fmt.Sprintf("Error running Python script: %v", err), http.StatusInternalServerError)
		return
	}

	// Final JSON response
	response := map[string]interface{}{
		"claims":  claims,
		"context": contextResults,
	}
	if err := json.NewEncoder(w).Encode(response); err != nil {
		http.Error(w, fmt.Sprintf("Error encoding response: %v", err), http.StatusInternalServerError)
	}
}

func LiveNewsHandler(w http.ResponseWriter, r *http.Request) {
    if r.Method != http.MethodPost {
        http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
        return
    }

    var payload RequestPayload
    if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
        http.Error(w, "Invalid JSON", http.StatusBadRequest)
        return
    }

    // Forward to Flask
    flaskURL := "http://localhost:5100/liveanalysis"
    reqBody, _ := json.Marshal(payload)

    resp, err := http.Post(flaskURL, "application/json", bytes.NewBuffer(reqBody))
    if err != nil {
        http.Error(w, fmt.Sprintf("Failed to call Flask service: %v", err), http.StatusInternalServerError)
        return
    }
    defer resp.Body.Close()

    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(resp.StatusCode)
    io.Copy(w, resp.Body) // Pass Flask's response back to the client
}

// main - start server
func main() {
	http.HandleFunc("/", homeHandler)
	http.HandleFunc("/scrape", ScrapeHandler)
	http.HandleFunc("/process", ProcessHandler)
	http.HandleFunc("/livenews", LiveNewsHandler)
	http.HandleFunc("/trending.html", TrendingHandler)
	http.HandleFunc("/liveanalysis.html", LiveHandler)
	http.HandleFunc("/imagenews.html", ImageHandler)
	http.HandleFunc("/volunteer.html", VolunteerHandler)
	http.Handle("/static/", http.StripPrefix("/static/", http.FileServer(http.Dir("static"))))
	http.Handle("/resources/", http.StripPrefix("/resources/", http.FileServer(http.Dir("resources"))))

	fmt.Println("🚀 Server started at http://localhost:8080")
	http.ListenAndServe(":8080", nil)
}
