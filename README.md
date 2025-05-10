# LiveTruth

**LiveTruth** is a real-time AI-powered misinformation detection system that verifies news across various formats — text, images, headlines, live broadcasts, and geo-based news. Built with a Go backend, LiveTruth is engineered for speed, security, and adaptability in the fast-paced world of information.

## 🚀 Features

- **Multi-format Verification**: Analyzes text, images (via EasyOCR), URLs, headlines, and live broadcasts.
- **Real-time Fact-Checking**: Verifies claims instantly using dynamic search and intelligent agents.
- **Live Broadcast Analysis**: Checks information claim-by-claim during live video streams.
- **Trending News Detection**: Monitors viral content and stops misinformation at the source.
- **Local News Validation**: Verifies region-specific news with help from local volunteers.
- **Secure Go Backend**: High-performance and scalable architecture built with Golang.


## 🌟 Key Innovations

- **Agentic AI Pipeline**: Uses specialized agents with structured handoffs for accurate, low-hallucination outputs.
- **Dynamic Knowledge Base**: Updates in real time for up-to-date, live fact-checking unlike static RAG systems.
- **Scalable Go Backend**: High concurrency, cross-platform support, and smooth integration with cloud tools.
- **Credibility Scoring**: Confidence scores backed by source reliability analysis to enhance trust and transparency.


## Screenshots
![image](https://github.com/user-attachments/assets/0204cd4b-caf5-4c28-ae2f-883c7f0e8848)
![image](https://github.com/user-attachments/assets/30f8b20b-2783-4413-abd2-81e9d14b88ea)
![image](https://github.com/user-attachments/assets/f457a77f-9620-4038-98ac-4fb4ab62eb7f)
![image](https://github.com/user-attachments/assets/16f4cdb1-5fc4-45bc-8249-1f1219bc5d3c)
![image](https://github.com/user-attachments/assets/06016f0f-2bfc-46f7-96dc-ac47bc50952c)
![image](https://github.com/user-attachments/assets/16995cde-92a6-4085-893a-552905ef5e33)
![image](https://github.com/user-attachments/assets/537d7010-f755-4421-bb6d-e7300c07574f)


## 🛠️ Tech Stack

- **Backend**: Go (Golang), Flask
- **AI/ML**: pydantic, langchain
- **Web scrapping**: Firecrawl API


## 📁 Project Structure

```text

├── agent/                     # Python scripts for core functionalities
│   ├── db-create.py           # Script to create chromadb
│   ├── fakenews.py            # Fake news detection logic
│   ├── final copy.py          
│   ├── final.py               # Main execution script
│   ├── livenews-flask.py      # Flask app for live news processing
│   ├── whatsapp-rag.py        # RAG-based WhatsApp processing script
│
├── resources/js/              # JavaScript resources (frontend logic, if any)
│
├── scraper/                   # Web scraping 
│
├── static/                    # Static files (CSS, images, etc.)
│
├── main.go                    # Main Go application entry point
├── scraped_data.json          # Sample or processed scraped data
```


## Whatsapp Bot
![image](https://github.com/user-attachments/assets/f5bc8a31-de93-4251-a971-3593c52cd8de)



