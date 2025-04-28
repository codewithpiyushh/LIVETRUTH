package scraper

import (
        "context"
        "encoding/json"
        "fmt"
        "io/ioutil"
        "net/http"
        "strings"
        "sync"
        "time"

        "github.com/chromedp/chromedp"
)

const (
        firecrawlAPIKey = ""
        firecrawlAPIURL = "https://api.firecrawl.dev/v1/scrape"
        maxWorkers      = 5 // Adjust based on system capability
)

type ScrapePayload struct {
        Formats             []string          `json:"formats"`
        OnlyMainContent     bool              `json:"onlyMainContent"`
        WaitFor             int               `json:"waitFor"`
        Mobile              bool              `json:"mobile"`
        SkipTLSVerification bool              `json:"skipTlsVerification"`
        Timeout             int               `json:"timeout"`
        Location            map[string]string `json:"location"`
        BlockAds            bool              `json:"blockAds"`
        URL                 string            `json:"url"`
}

type ScrapeResult struct {
        URL   string      `json:"url"`
        Data  interface{} `json:"data"`
        Error string      `json:"error,omitempty"`
}

// ExtractRelevantUrls fetches search results from Bing.
func ExtractRelevantUrls(query string) ([]string, error) {
        ctx, cancel := chromedp.NewContext(context.Background())
        defer cancel()

        var urls []string
        searchURL := "https://www.bing.com/search?q=" + strings.ReplaceAll(query, " ", "+") + "&count=10"

        fmt.Println("🔍 Searching Bing for:", query)

        err := chromedp.Run(ctx,
                chromedp.Navigate(searchURL),
                chromedp.Sleep(5*time.Second),
                chromedp.Evaluate(`Array.from(document.querySelectorAll('li.b_algo h2 a')).map(a => a.href)`, &urls),
        )

        if err != nil {
                return nil, err
        }

        fmt.Println("✅ Found", len(urls), "URLs:")
        for _, url := range urls {
                fmt.Println("  -", url)
        }

        return urls, nil
}

// ScrapeData sends an HTTP request to Firecrawl API to scrape a given URL.
func ScrapeData(url string, wg *sync.WaitGroup, resultsChan chan<- ScrapeResult) {
        defer wg.Done()
        fmt.Println("📄 Scraping data from:", url)

        payload := ScrapePayload{
                Formats:             []string{"markdown"},
                OnlyMainContent:     true,
                WaitFor:             0,
                Mobile:              false,
                SkipTLSVerification: false,
                Timeout:             60000,
                Location:            map[string]string{"country": "US"},
                BlockAds:            true,
                URL:                 url,
        }

        jsonPayload, _ := json.Marshal(payload)
        req, _ := http.NewRequest("POST", firecrawlAPIURL, strings.NewReader(string(jsonPayload)))
        req.Header.Set("Authorization", "Bearer "+firecrawlAPIKey)
        req.Header.Set("Content-Type", "application/json")

        client := &http.Client{Timeout: 60 * time.Second}
        resp, err := client.Do(req)
        if err != nil {
                fmt.Println("❌ Error scraping", url, ":", err)
                resultsChan <- ScrapeResult{URL: url, Error: err.Error()}
                return
        }
        defer resp.Body.Close()

        body, _ := ioutil.ReadAll(resp.Body)
        var data interface{}
        json.Unmarshal(body, &data)

        fmt.Println("✅ Successfully scraped:", url)
        resultsChan <- ScrapeResult{URL: url, Data: data}
}

// Worker starts scraping jobs in parallel using goroutines.
func Worker(urls []string, resultsChan chan<- ScrapeResult) {
        var wg sync.WaitGroup
        sem := make(chan struct{}, maxWorkers) // Semaphore to limit concurrent goroutines

        for _, url := range urls {
                wg.Add(1)
                sem <- struct{}{} // Acquire slot
                go func(url string) {
                        defer func() { <-sem }() // Release slot after completion
                        ScrapeData(url, &wg, resultsChan)
                }(url)
        }

        wg.Wait()
        close(resultsChan)
}