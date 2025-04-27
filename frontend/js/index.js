document.addEventListener("DOMContentLoaded", () => {
    const button = document.getElementById("analyzeBtn");
    button.addEventListener("click", analyzeNews);
  });
  
  async function analyzeNews(event) {
    event.preventDefault(); // Prevent form submission or refresh
  
    const inputField = document.getElementById("newsInput");
    const input = inputField.value.trim();
    const resultBox = document.getElementById("analysisResult");
    resultBox.innerHTML = ""; // Clear previous results ONCE at the beginning
    document.getElementById("graphContainer").classList.add("d-none");
    if (!input) {
      resultBox.innerHTML = "<span class='text-danger'>⚠️ Please enter some news text to analyze.</span>";
      return;
    }
  
    // resultBox.innerHTML = "⏳ Scraping related articles, please wait...";
  
    try {
      // 🔹 Step 1: Call /scrape endpoint
      const scrapeResponse = await fetch("http://localhost:8080/scrape", {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: new URLSearchParams({ query: input }),
      });
  
      console.log("Scrape response:", scrapeResponse);
      if (!scrapeResponse.ok) {
        const errorText = await scrapeResponse.text();
        throw new Error("Scrape failed: " + errorText);
      }
  
      const scrapedData = await scrapeResponse.json();
      // resultBox.innerHTML = ""; // REMOVE this line
      if (!Array.isArray(scrapedData) || scrapedData.length === 0) {
        resultBox.innerHTML = "<span class='text-warning'>⚠️ No related articles found.</span>";
        return;
      }
  
      // 🔹 Step 2: Call /process endpoint
      // resultBox.innerHTML = "⏳ Analyzing claims, please wait..."; // Update message for processing
      const processResponse = await fetch("http://localhost:8080/process", {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: new URLSearchParams({ query: input }),
      });
      // resultBox.innerHTML = ""; // REMOVE this line
      const ragResultsDiv = document.createElement("div");
      ragResultsDiv.classList.add("mt-4");
      resultBox.appendChild(ragResultsDiv);
  
      const rawText = await processResponse.text();
      console.log("🪵 Raw response:", rawText);
  
      if (processResponse.ok) {
        try {
          const results = JSON.parse(rawText);
          const claims = results.claims || [];
  
          if (!Array.isArray(claims) || claims.length === 0) {
            ragResultsDiv.innerHTML = "<p class='text-muted'>No analysis results available.</p>";
            return;
          }
  
          claims.forEach((result, index) => {
            const div = document.createElement("div");
            div.className = "border p-3 mb-3 bg-light rounded";
  
            const rawScore = typeof result.confidence_score === "number"
              ? result.confidence_score
              : 0;
            const confidenceScore = rawScore.toFixed(2);
  
            div.innerHTML = `
              <p>🔹 <strong>Claim:</strong> ${result.claim || "N/A"}</p>
              <p><strong>Output:</strong> ${result.output || "N/A"}</p>
              <p>✅ <strong>Truth Score:</strong> ${confidenceScore}</p>
              <div class="truth-bar-container mt-1">
                <canvas id="truthBar-${index}" width="150" height="25"></canvas>
              </div>
              <p>📝 <strong>Explanation:</strong> ${result.explanation || "N/A"}</p>
             
            `;
            ragResultsDiv.appendChild(div);
            console.log(rawScore)
            // renderSmallBarChart(`truthBar-${index}`, rawScore);
          });
  
          const vizButton = document.createElement("button");
          vizButton.textContent = "📊 See Visualizations";
          vizButton.className = "btn btn-outline-primary mt-3 fw-bold rounded-pill";
          vizButton.addEventListener("click", () => {
            showGraph(results.context || []);
          });
  
          ragResultsDiv.appendChild(vizButton);
          document.getElementById("feedbackSection").classList.remove("d-none");
          
          console.log("🔍 Parsed JSON:", results);
          const feedbackSection = document.getElementById("feedbackSection");
          if (claims.length > 0 || contextData.length > 0) {
            document.getElementById("feedbackSection").classList.remove("d-none");
            const feedbackText = document.getElementById("feedback-text");
          }
          else {
            console.warn("⚠️ feedbackSection not found in the DOM.");
          }
        } catch (jsonError) {
          console.error("JSON parsing error:", jsonError);
          ragResultsDiv.innerHTML = `<p class="text-danger">❌ Error parsing JSON response.</p>`;
        }
      } else {
        console.error("RAG processing failed:", processResponse.status, rawText);
        ragResultsDiv.innerHTML = `<p class="text-danger">❌ Failed to process RAG: ${rawText}</p>`;
      }
    } catch (error) {
      console.error("❌ Fetch error:", error);
      resultBox.innerHTML += `<p class="text-danger">❌ Error: ${error.message}</p>`;
    }
    
  }
//   function renderSmallBarChart(canvasId, score) {
//     const ctx = document.getElementById(canvasId).getContext("2d");
//     const normalizedScore = Math.max(0, Math.min(1, score));

//     new Chart(ctx, {
//         type: "bar",
//         data: {
//             labels: ["Truth"],
//             datasets: [{
//                 data: [normalizedScore],
//                 backgroundColor: "rgba(13, 110, 253, 0.7)",
//                 borderColor: "rgba(13, 110, 253, 1)",
//                 borderWidth: 1,
//             }],
//         },
//         options: {
//             indexAxis: 'y',
//             responsive: false,
//             maintainAspectRatio: false,
//             scales: {
//                 x: {
//                     beginAtZero: true,
//                     max: 1,
//                     display: false,
//                 },
//                 y: {
//                     display: false,
//                 },
//             },
//             plugins: {
//                 legend: { display: false },
//                 tooltip: { enabled: true },
//             },
//         },
//     });
// }
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
  

