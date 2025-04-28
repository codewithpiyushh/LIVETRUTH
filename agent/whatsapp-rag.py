from flask import Flask, request, jsonify, session
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import asyncio
import json
import os
import httpx
from dataclasses import dataclass
from pydantic import BaseModel
from langchain.schema import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain.chains import RetrievalQA
from langchain_groq import ChatGroq
from pydantic_ai import Agent
from PIL import Image
import easyocr
import numpy as np
import requests
from bs4 import BeautifulSoup
import io
import re
from googlesearch import search
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import google.generativeai as genai
from dotenv import load_dotenv
import os

# Initialize Flask app
app = Flask(__name__)
app.secret_key ="secret_key"  #

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Twilio credentials
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
client = Client(account_sid, auth_token)

# Nest asyncio for interactive environments
import nest_asyncio
nest_asyncio.apply()

nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)

# Enable CORS to allow requests from your frontend
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST')
    return response

# Gemini setup
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")

def extract_text_from_image(image_url):
    try:
        response = requests.get(image_url, stream=True)
        response.raise_for_status()
        image = Image.open(response.raw).convert('RGB')
        reader = easyocr.Reader(['en'])
        image_np = np.array(image)
        results = reader.readtext(image_np)
        return "\n".join([result[1] for result in results])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching image from {image_url}: {e}")
        return None
    except Exception as e:
        print(f"Error processing image: {e}")
        return None

def extract_keywords(text):
    words = word_tokenize(text)
    stop_words = set(stopwords.words('english'))
    return [word for word in words if word.isalpha() and word.lower() not in stop_words]

def perform_search(keywords):
    query = " ".join(keywords[:5])  # Limit to 5 keywords for better results
    try:
        return list(search(query, num_results=5))
    except Exception as e:
        print(f"Search error: {e}")
        return []

def scrape_important_content(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, timeout=10, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        headings = soup.find_all(['h1', 'h2', 'h3'])
        paragraphs = soup.find_all('p')
        content = " | ".join([h.get_text(strip=True) for h in headings])
        content += " " + " ".join([p.get_text(strip=True) for p in paragraphs[:5]])
        return content.strip()
    except requests.exceptions.RequestException as e:
        print(f"Scraping error for {url}: {e}")
        return None
    except Exception as e:
        print(f"General scraping error for {url}: {e}")
        return None

def analyze_content(corpus):
    try:
        prompt = f"Analyze the following news content and tell whether it's fake or credible. Explain your reasoning in 2-3 sentences: {corpus}"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Analysis error: {e}")
        return "Unable to perform analysis."

def summarize_content(corpus):
    try:
        prompt = f"Summarize the following content into one paragraph of 2-3 sentences: {corpus}"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Summary error: {e}")
        return "Unable to generate summary."


def append_interaction_to_chat_log(question, answer, chat_log=None):
    if chat_log is None:
        chat_log = ""
    return f"{chat_log}\nUser: {question}\nBot: {answer}"



@app.route('/bot', methods=['POST'])
def bot():
    incoming_msg = request.values.get('Body', '').strip()
    print("Incoming Message:", incoming_msg)

    r = MessagingResponse()

    if not incoming_msg:
        r.message("Message cannot be empty!")
        return str(r)
    
    extracted_text = None
    if incoming_msg.startswith("http"):
        try:
            extracted_text = extract_text_from_image(incoming_msg)
            if extracted_text:
                print("Extracted Text from Image:", extracted_text)
                incoming_msg = extracted_text # Use extracted text for analysis
            else:
                r.message("Could not extract text from the provided image URL.")
                return str(r)
        except Exception as e:
            print(f"Error processing URL as image: {e}")
            r.message("Error processing the provided URL.")
            return str(r)

    keywords = extract_keywords(incoming_msg)
    urls = perform_search(keywords)
    contents = []
    sources = []
    for url in urls:
        content = scrape_important_content(url)
        if content:
            contents.append(content)
            sources.append(url)

    # Step 5: Combine and Summarize
    combined_text = "\n".join(contents)
  
    summary = summarize_content(combined_text)
    analysis = analyze_content(combined_text)
    print("##################", analysis)

    lower_analysis = analysis.lower()
    credibility = "High" if "credible" in lower_analysis or "reliable" in lower_analysis else "Low"

    # Generate scores for visualization
    source_names = [re.sub(r'https?://(www\.)?', '', url).split('/')[0] for url in sources[:3]]
    credibility_scores = [75, 65, 45] if credibility == "High" else [45, 35, 25]

    response_text = f"""
    Summary: {summary}

    Analysis: {analysis}

    Credibility: {credibility}

    Sources:
    - {sources[0] if len(sources) > 0 else 'N/A'}
    - {sources[1] if len(sources) > 1 else 'N/A'}
    - {sources[2] if len(sources) > 2 else 'N/A'}
    """
    print("Response Text:", response_text)


    chat_log = session.get('chat_log', '')
    #summary = summarize_result(results)
    session['chat_log'] = append_interaction_to_chat_log(incoming_msg, analysis , chat_log)


    r.message(response_text)
    return str(r)

if __name__ == '__main__':
    app.run(debug=True, port=5000)