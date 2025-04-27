from flask import Flask, request, jsonify
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

# NLTK setup
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
load_dotenv()
app = Flask(__name__)

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

def extract_text_from_image(image):
    reader = easyocr.Reader(['en'])
    image_np = np.array(image)
    results = reader.readtext(image_np)
    return "\n".join([result[1] for result in results])

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
        response = requests.get(url, timeout=5, headers=headers)
        if response.status_code != 200:
            return None
        soup = BeautifulSoup(response.content, "html.parser")
        headings = soup.find_all(['h1', 'h2', 'h3'])
        paragraphs = soup.find_all('p')
        content = " | ".join([h.get_text(strip=True) for h in headings])
        content += " " + " ".join([p.get_text(strip=True) for p in paragraphs[:5]])
        return content.strip()
    except Exception as e:
        print(f"Scraping error for {url}: {e}")
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

@app.route("/extract-text", methods=["POST"])
def process_image():
    try:
        if 'image' in request.files:
            image_file = request.files['image']
            image = Image.open(io.BytesIO(image_file.read()))
        elif 'image_url' in request.form:
            image_url = request.form['image_url']
            response = requests.get(image_url)
            response.raise_for_status()  # Raise an exception for bad status codes
            image = Image.open(io.BytesIO(response.content))
        else:
            return jsonify({"error": "No image or image URL provided"}), 400

        # Step 1: OCR
        extracted_text = extract_text_from_image(image)
        if not extracted_text:
            return jsonify({"error": "No text could be extracted from the image"}), 400

        # Step 2: Keywords
        keywords = extract_keywords(extracted_text)

        # Step 3: Google Search
        urls = perform_search(keywords)

        # Step 4: Scraping
        contents = []
        sources = []
        for url in urls:
            content = scrape_important_content(url)
            if content:
                contents.append(content)
                sources.append(url)

        # Step 5: Combine and Summarize
        combined_text = "\n".join(contents)
        print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
        print(combined_text)
        summary = summarize_content(combined_text)
        analysis = analyze_content(combined_text)

        # Determine credibility
        lower_analysis = analysis.lower()
        credibility = "High" if "credible" in lower_analysis or "reliable" in lower_analysis else "Low"

        # Generate scores for visualization
        source_names = [re.sub(r'https?://(www\.)?', '', url).split('/')[0] for url in sources[:3]]
        credibility_scores = [75, 65, 45] if credibility == "High" else [45, 35, 25]

        return jsonify({
            "text": extracted_text,
            "summary": summary,
            "urls": sources,
            "analysis": analysis,
            "credibility": credibility,
            "sources": source_names[:3],  # Top 3 sources for chart
            "scores": credibility_scores[:len(source_names)]  # Matching scores for the sources
        })

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Error fetching image from URL: {str(e)}"}), 500
    except Exception as e:
        print(f"Processing error: {str(e)}")
        return jsonify({"error": f"Error processing image: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)