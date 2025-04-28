document.addEventListener("DOMContentLoaded", function () {
  const apiKey = "";
  const trendingNewsList = document.getElementById("trending-headlines-list");
  const newsContainer = document.getElementById("news-container");
  const searchInput = document.getElementById("news-search-input");
  const searchButton = document.getElementById("news-search-button");
  const categoryButtons = document.querySelectorAll(".category-btn");
  const resultsDiv = document.getElementById("results");
  const processBtn = document.getElementById("processBtn");

  let selectedCategory = "general";
  let currentArticleTitle = "";
  let isFetchingNews = false;

  function debounce(func, delay) {
    let timer;
    return function (...args) {
      clearTimeout(timer);
      timer = setTimeout(() => func(...args), delay);
    };
  }

  const fetchNews = debounce(async (query = "") => {
    if (isFetchingNews) return;
    isFetchingNews = true;

    try {
      let url = `https://newsapi.org/v2/top-headlines?category=${selectedCategory}&country=us&apiKey=${apiKey}`;
      if (query) {
        url = `https://newsapi.org/v2/everything?q=${query}&language=en&apiKey=${apiKey}`;
      }

      const response = await fetch(url);
      if (!response.ok)
        throw new Error(`HTTP Error! Status: ${response.status}`);

      const data = await response.json();
      console.log("Fetched articles:", data.articles);

      if (data.articles && data.articles.length > 0) {
        displayNews(data.articles);
      } else {
        newsContainer.innerHTML = "<p>No news available for this category.</p>";
      }
    } catch (error) {
      console.error("Error fetching news:", error);
      newsContainer.innerHTML =
        "<p>Failed to load news. Please try again later.</p>";
    } finally {
      isFetchingNews = false;
    }
  }, 500);

  async function displayNews(articles) {
    console.log("entered displayNews function");
    newsContainer.innerHTML = "";
    resultsDiv.innerHTML = "";
    if (processBtn) processBtn.style.display = "none";

    const topArticle = articles[0];
    if (!topArticle.title || currentArticleTitle === topArticle.title) return;
    currentArticleTitle = topArticle.title;
    console.log("Current Article Title:", currentArticleTitle);

    const newsHeading = document.createElement("h2");
    newsHeading.textContent = topArticle.title;

    const newsDescription = document.createElement("p");
    newsDescription.textContent =
      topArticle.description || "No description available.";

    const newsImage = document.createElement("img");
    newsImage.src = topArticle.urlToImage || "images/default-news.jpg";
    Object.assign(newsImage.style, {
      width: "100%",
      height: "400px",
      objectFit: "cover",
      borderRadius: "10px",
    });

    newsContainer.appendChild(newsHeading);

    newsContainer.appendChild(newsImage);
    newsContainer.appendChild(document.createElement("hr"));
    // newsContainer.appendChild(newsDescription);
    const description = topArticle.description || "";

    if (description.trim()) {
      newsDescription.textContent = " Description: " + description;
    } else {
      newsDescription.textContent = "No description available.";
    }
    // newsContainer.appendChild(newsDescription);

    // Add summary placeholder
    const summaryPara = document.getElementById("trending-content");
    // summaryPara.textContent = "📋 Generating summary...";

    // Call Gemini to get summary
    const summary = await summarizeWithMetaLlama(description);
    summaryPara.textContent =   summary;

    await performScraping(topArticle.title);

    trendingNewsList.innerHTML = "";
    articles.slice(0, 5).forEach((article) => {
      const listItem = document.createElement("li");
      listItem.innerHTML = `<a href="${article.url}" target="_blank">${article.title}</a>`;
      trendingNewsList.appendChild(listItem);
    });
  }

  async function performScraping(articleTitle) {
    resultsDiv.innerHTML = " Scraping data...";
    document.getElementById("graphContainer").classList.add("d-none");

    try {
      const scrapeResponse = await fetch("http://localhost:8080/scrape", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({ query: articleTitle }),
      });

      if (!scrapeResponse.ok) throw new Error("Scraping request failed");
      const scrapedData = await scrapeResponse.json();

      if (scrapedData.length === 0) {
        resultsDiv.innerHTML = "<p>No results found.</p>";
        return;
      }

      resultsDiv.innerHTML = "<p>Scraping completed. Now processing...</p>";

      const processResponse = await fetch("http://localhost:8080/process", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({ query: articleTitle }),
      });

      const ragResultsDiv = document.createElement("div");
      ragResultsDiv.classList.add("mt-4");
      resultsDiv.appendChild(ragResultsDiv);

      const rawText = await processResponse.text();
      if (processResponse.ok) {
        const results = JSON.parse(rawText);
        const claims = results.claims || [];

        if (!Array.isArray(claims) || claims.length === 0) {
          ragResultsDiv.innerHTML =
            "<p class='text-muted'>No analysis results available.</p>";
          return;
        }

        claims.forEach((result, index) => {
          const div = document.createElement("div");
          div.className = "border p-3 mb-3 bg-light rounded";

          const rawScore =
            typeof result.confidence_score === "number"
              ? result.confidence_score
              : 0;
          const confidenceScore = rawScore.toFixed(2);

          div.innerHTML = `
                        <p>🔹 <strong>Claim:</strong> ${
                          result.claim || "N/A"
                        }</p>
                        <p><strong>Output:</strong> ${
                          result.output || "N/A"
                        }</p>
                        <p> <strong>Truth Score:</strong> ${confidenceScore}</p>
                        <div class="truth-bar-container mt-1">
                            <canvas id="truthBar-${index}" width="150" height="25"></canvas>
                        </div>
                        <p> <strong>Explanation:</strong> ${
                          result.explanation || "N/A"
                        }</p>
                        // <p> <strong>Date:</strong> ${result.date || "N/A"}</p>
                    `;

          ragResultsDiv.appendChild(div);
          
        });
        const vizButton = document.createElement("button");
          vizButton.textContent = "📊 See Visualizations";
          vizButton.className = "btn btn-outline-primary mt-3 fw-bold rounded-pill";
          vizButton.addEventListener("click", () => {
            showGraph(results.context || []);
          });
          ragResultsDiv.appendChild(vizButton);
          document.getElementById("feedbackSection").classList.remove("d-none");
          const feedbackSection = document.getElementById("feedbackSection");
          if (claims.length > 0 || contextData.length > 0) {
            document.getElementById("feedbackSection").classList.remove("d-none");
            const feedbackText = document.getElementById("feedback-text");
          }
          else {
            console.warn("⚠️ feedbackSection not found in the DOM.");
          }
      } else {
        throw new Error("RAG processing failed");
      }
    } catch (error) {
      console.error("❌ Error during scraping and processing:", error);
      resultsDiv.innerHTML = `<p class="text-danger">❌ Error: ${error.message}</p>`;
    }
  }

  
  categoryButtons.forEach((button) => {
    button.addEventListener("click", function (event) {
      event.preventDefault();
      categoryButtons.forEach((btn) => btn.classList.remove("active"));
      this.classList.add("active");

      selectedCategory = this.getAttribute("data-category");
      fetchNews();
    });
  });

  searchButton.addEventListener("click", function (event) {
    event.preventDefault();
    const query = searchInput.value.trim();
    if (query !== "") {
      fetchNews(query);
    }
  });

  fetchNews();
});
async function summarizeWithMetaLlama(text) {
  const GROQ_API_KEY =
    ""; // Replace with your Groq API key
  const model = "llama-3.3-70b-versatile"; // Or another suitable Groq model

  try {
    const response = await fetch(
      "https://api.groq.com/openai/v1/chat/completions",
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${GROQ_API_KEY}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          model: model,
          messages: [
            {
              role: "user",
              content: `explain this:\n\n${text} in 300 words`,
            },
          ],
        }),
      }
    );

    if (!response.ok) {
      const errorBody = await response.json();
      console.error("Groq API error:", errorBody);
      throw new Error(`Failed to summarize with Groq: ${response.statusText}`);
    }

    const result = await response.json();

    const summary = result?.choices?.[0]?.message?.content;

    return summary || "No summary available.";
  } catch (err) {
    console.error("Groq API error:", err);
    return "❌ Error while summarizing with Groq.";
  }
}
function showGraph(contextData) {
    const graphContainer = document.getElementById("graphContainer");
    graphContainer.classList.remove("d-none");
  
    if (!Array.isArray(contextData) || contextData.length === 0) {
      graphContainer.innerHTML = `<p class="text-muted">No credibility data found to visualize.</p>`;
      return;
    }
  
    const labels = contextData.map((item) => {
      try {
        const url = new URL(item.url);
        return url.hostname.replace("www.", "");
      } catch (e) {
        return "Unknown Source";
      }
    });
  
    const scores = contextData.map((item) =>
      typeof item.credibility_score === "number" ? item.credibility_score / 100 : 0
    );
  
    graphContainer.innerHTML = `
      <h3 class="text-center fw-bold my-4">📊 Credibility Scores of Sources</h3>
      <canvas id="truthChart" height="100" width="300"></canvas>
    `;
  
    const ctx = document.getElementById("truthChart").getContext("2d");
  
    new Chart(ctx, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Credibility Score",
            data: scores,
            backgroundColor: scores.map(score => getColorForScore(score)),
            borderColor: scores.map(score => getColorForScore(score).replace("0.7", "1")),
            borderWidth: 1,
          },
        ],
      },
      options: {
        responsive: true,
        scales: {
          y: {
            beginAtZero: true,
            max: 1,
            ticks: {
              stepSize: 0.2,
              color: "#333",
              font: {
                size: 14,
                weight: 'bold'
              }
            },
            title: {
              display: true,
              text: "Credibility Score (0 to 1)",
              font: {
                size: 16,
                weight: 'bold'
              },
              color: "#444"
            },
          },
          x: {
            ticks: {
              color: "#333",
              font: {
                size: 12,
                weight: 'bold'
              }
            },
          },
        },
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            callbacks: {
              label: function (context) {
                return `Credibility Score: ${context.parsed.y.toFixed(2)}`;
              }
            }
          }
        }
      },
    });
  }
  
  
  function getColorForScore(score) {
    if (score >= 0.85) {
      return "rgba(0, 128, 255, 0.7)"; // Bright blue (very credible)
    } else if (score >= 0.7) {
      return "rgba(102, 204, 255, 0.7)"; // Light blue
    } else if (score >= 0.5) {
      return "rgba(255, 204, 0, 0.7)"; // Yellow
    } else if (score >= 0.3) {
      return "rgba(255, 102, 102, 0.7)"; // Coral
    } else {
      return "rgba(204, 0, 0, 0.7)"; // Deep red
    }
  }
  


