<h2 style="display: flex; align-items: center;">
  <img src="https://github.com/user-attachments/assets/c95b3292-bdc5-402e-bcc4-a4b6840e6867" width="200" height="60" style="margin-right: 10px;" />
 &nbsp;&nbsp;&nbsp;
  LiveTruth: AI-powered Misinformation Detection System
</h2>

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


##  Installation

Follow the steps below to set up and run **LiveTruth** locally on your machine:

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/LiveTruth.git
cd LiveTruth
```
### 2. Set Up the Python Environment
Navigate to the agent folder and install the required dependencies:
```bash
cd agent
pip install -r requirements.txt
```
### 3. Initialize Vector Database & Start RAG Pipeline
Run the following scripts to set up ChromaDB, launch the RAG pipeline, and start real-time analysis
```bash
python db-create.py
python final.py
python live-analysis.py
```
### 4.Run the Go Backend
Return to the root directory and start the Go server:
```bash
go run main.go
```
## 🧠 Future Scope

- Integrate multilingual support for regional misinformation detection  
- Deploy as a cloud-native microservice with Docker & Kubernetes  
- Incorporate user feedback to improve model accuracy over time  
- Build a mobile-friendly interface   
- Enhance live broadcast analysis with speaker attribution

## 👥 Team

Meet the amazing minds behind LiveTruth:

- [Piyush Singh](https://www.linkedin.com/in/piyushhh-singhh/) 
- [Nikita Babbar](https://www.linkedin.com/in/nikita-babbar-b0291026a/)   
- [Manya Joshi](https://www.linkedin.com/in/manya-joshi-ai/) 

 
