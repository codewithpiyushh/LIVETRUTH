document.addEventListener("DOMContentLoaded", function () {
    alert("connected")
    const apiKey = "AIzaSyARyJIZgSMzvh4xtaveoop8YrBp50SjdQA"; // Replace with your YouTube API key
    const searchQuery = "live news india";
    const apiUrl = `https://www.googleapis.com/youtube/v3/search?part=snippet&eventType=live&type=video&q=${encodeURIComponent(searchQuery)}&key=${apiKey}&maxResults=5&relevanceLanguage=en`;


    fetch(apiUrl)
        .then(response => response.json())
        .then(data => {
            if (data.items && data.items.length > 0) {
                const carousel = document.getElementById("livenews-carousel");
                const liveNewsIframe = document.getElementById("live-news-iframe");

                // Set first video in the iframe
                const firstVideoId = data.items[0].id.videoId;
                if (liveNewsIframe) {
                    liveNewsIframe.src = `https://www.youtube.com/embed/${firstVideoId}?autoplay=1&mute=1`;
                }
                
                // firstVideoId = 'gadjsB5BkK4'
                const videoURL = `https://www.youtube.com/watch?v=${firstVideoId}`;
                // const videoURL = `https://www.youtube.com/watch?v=gadjsB5BkK4`;

                // Polling function
                function pollLiveNews() {
                    fetch("http://localhost:8080/livenews", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({ url: videoURL })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.error) {
                            console.error("Error:", data.error);
                        } else {
                            console.log("Summary:", data.summary);
                            console.log("Fact Check:", data.fact_check);
                            console.log("Timestamp:", data.timestamp);
                
                            // Inject into the HTML
                            const resultContainer = document.getElementById("news-result-container");

                            const newEntry = document.createElement("div");
                            newEntry.classList.add("news-result");
                            newEntry.innerHTML = `
                                <div class="card mb-3">
                                    <div class="card-body">
                                        <h5 class="card-title">📰 Summary:</h5>
                                        <p>${data.summary}</p>
                                        <h6 class="card-subtitle mb-2 text-muted">✅ Fact Check:</h6>
                                        <p>${data.fact_check}</p>
                                        <p class="text-end"><small>🕒 ${data.timestamp}</small></p>
                                    </div>
                                </div>
                            `;
                            resultContainer.prepend(newEntry); // Add new result on top

                        }
                
                        // Call again after delay (e.g., every 30 seconds)
                        setTimeout(pollLiveNews, 1); // 30 sec delay
                    })
                    .catch(error => {
                        console.error("Fetch error:", error);
                
                        // Optional: Show error message on page
                        document.getElementById("news-summary").textContent = "Error fetching summary.";
                        document.getElementById("news-fact-check").textContent = "Error fetching fact check.";
                        document.getElementById("news-timestamp").textContent = "N/A";
                
                        // Retry after delay
                        setTimeout(pollLiveNews, 30);
                    });
                }
                

                // Start polling
                pollLiveNews();

                // Populate the carousel with remaining videos
                data.items.forEach((video, index) => {
                    if (index === 0) return; // Skip the first video, as it's already set in the iframe
                    const videoId = video.id.videoId;
                    const videoTitle = video.snippet.title;
                    const thumbnailUrl = video.snippet.thumbnails.high.url;

                    const videoItem = document.createElement("div");
                    videoItem.classList.add("news-item");
                    videoItem.innerHTML = `
                        <div class="card">
                            <a href="https://www.youtube.com/watch?v=${videoId}" target="_blank">
                                <img src="${thumbnailUrl}" class="card-img-top" alt="Live News">
                            </a>
                            <div class="card-body">
                                <h5 class="card-title">${videoTitle}</h5>
                                <a href="https://www.youtube.com/watch?v=${videoId}" target="_blank" class="btn btn-danger">Watch Live</a>
                            </div>
                        </div>
                    `;
                    carousel.appendChild(videoItem);
                });

                // Initialize Owl Carousel
                $(".owl-carousel").owlCarousel({
                    loop: true,
                    margin: 10,
                    nav: true,
                    autoplay: true,
                    autoplayTimeout: 5000,
                    responsive: {
                        0: { items: 1 },
                        600: { items: 2 },
                        1000: { items: 3 }
                    }
                });
            } else {
                console.warn("No live news videos found.");
            }
        })
        .catch(error => console.error("Error fetching YouTube videos:", error));
});
