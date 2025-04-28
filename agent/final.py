import asyncio
import json
import os
import sys
from langchain.schema import Document
from dataclasses import dataclass
from pydantic_ai.models.groq import GroqModel
from pydantic_ai.providers.groq import GroqProvider
from langchain_groq import ChatGroq
import httpx
from httpx import AsyncClient
from langchain_chroma import Chroma
from langchain.chains import RetrievalQA
# from langchain_community.embeddings import HuggingFaceEmbeddings
# from langchain.embeddings import HuggingFaceEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings

from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from langchain_google_genai import ChatGoogleGenerativeAI

# from langchain.text_splitter import RecursiveCharacterTextSplitter
from pydantic_ai import Agent, RunContext
from pydantic import BaseModel
import warnings
from flask import Flask, request, jsonify
# import threading
# from flask import Flask, request, jsonify
# import asyncio
# import json
# import os
import re
# import httpx
import nest_asyncio
# import warnings
# from dataclasses import dataclass
# from typing import List
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
# from pydantic import BaseModel
# from pydantic_ai import Agent
# from pydantic_ai.models.groq import GroqModel
# from pydantic_ai.providers.groq import GroqProvider
# from langchain_chroma import Chroma
# from langchain.schema import Document
# from langchain.chains import RetrievalQA
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain_community.embeddings import HuggingFaceEmbeddings
# from langchain_groq import ChatGroq

# NLTK Setup
import nltk
# nltk.download('punkt')
# nltk.download('stopwords')
stop_words = set(stopwords.words('english'))

# Environment and warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)
nest_asyncio.apply()

app = Flask(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")
setup_done = False

custom_http_client = AsyncClient(timeout=30)
model = GeminiModel(
    'gemini-2.0-flash',
    provider=GoogleGLAProvider(api_key=GOOGLE_API_KEY, http_client=custom_http_client), #replace with your API key
)

@dataclass
class ClientAndKey:
    http_client: httpx.AsyncClient
    api_key: str

class UrlCredibility(BaseModel):
    url: str
    credibility_score: int

class Answer(BaseModel):
    output: bool
    confidence_score: int
    explanation: str

# Load the scraped JSON data
def load_scraped_data():
    path = "C:/Users/hp/Desktop/coding/truth-telll/nikita/scraped_data.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# Get URL-specific data
def getdatabyurl(url_to_find, json_data):
    print("jsonnnnn dataaaaa",json_data)
    print("urll to find",url_to_find)
    for entry in json_data:
        print("entry is ",entry)
        if entry['url'] == url_to_find:
            data = entry.get('data', {})
            error = data.get('error', None)
            print("@@@@@@@@@@@@@@@@@@@@@@")
            print(f"data: {data}, error: {error}")
            print("@@@@@@@@@@@@@@@@@@@@@@")
            return {'data': data, 'error': error}
    return None

# Clean text
def clean_text(text):
    text = re.sub(r'http\S+|www\S+', '', text)
    text = re.sub(r'[\/\\{}|*#`\'’:,@()_]', '', text)
    words = word_tokenize(text)
    cleaned_words = [word for word in words if word.lower() not in stop_words]
    return ' '.join(cleaned_words)

# persist_directory = get_next_chroma_directory()
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

def setup(chroma_db_directory):
    global db, retriever, qa, setup_done
    if setup_done:
        return
    db = Chroma(persist_directory=chroma_db_directory, embedding_function=embeddings)
    print(f"Vector database loaded successfully from {chroma_db_directory} with {db._collection.count()} documents")
    retriever = db.as_retriever()
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=GOOGLE_API_KEY)
    qa = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever, return_source_documents=True)    
    setup_done = True

async def context_rag_run(query: str, url, url_data, qa):
    url_data = url_data[1000:2000]
    result = qa.invoke(query)
    context = "\n".join([doc.page_content for doc in result["source_documents"]])
    final_query = f"""
    Given the claim: "{query}"
    webpage: "{url}"
    Webpage data (partial): "{url_data}"
    Relevant context: "{context}"
    Assess the credibility of the webpage, considering factors like source reputation, factual accuracy, and potential biases.
    """
    async with httpx.AsyncClient(timeout=30) as client:
        model = GroqModel('gemma2-9b-it', provider=GroqProvider(api_key=GROQ_API_KEY, http_client=client))
        agent = Agent(model, system_prompt="You are an analytical expert evaluating website credibility.")
        agent_result = await agent.run(final_query)
        return agent_result.data

async def context_process_claim(query, url, url_data):
    url_data = clean_text(str(url_data))
    rag_result = await context_rag_run(query, url, url_data, qa)
    agent = Agent(model,
        # GroqModel('gemma2-9b-it', provider=GroqProvider(api_key=GROQ_API_KEY)),
        result_type=UrlCredibility,
        system_prompt="""
        From the following text, extract:
        1. A credibility score (0-100)
        Respond only in JSON:
        {
            "credibility_score": <integer>
        }
        """
    )
    final = await agent.run(rag_result)
    return {"url": url, "credibility_score": final.data.credibility_score}

def create_or_load_db(chroma_db_directory):
    try:
        if os.path.exists(os.path.join(chroma_db_directory, "chroma.sqlite3")):
            # Database exists, load it
            db = Chroma(persist_directory=chroma_db_directory, embedding_function=embeddings)
            print(f"Vector database loaded successfully from {chroma_db_directory} with {db._collection.count()} documents")
            return db
    except Exception as e:
        print(f"Error creating/loading Chroma database: {e}")
        return None

async def rag_run(query: str, qa):
    result = qa.invoke(query)
    context = "\n".join([doc.page_content for doc in result["source_documents"]])
    final_query = f"""
    Given the claim: "{query}"
    And the following context: "{context}"
    Determine if the claim is true or false based on the provided context.
    Provide a detailed supporting explanation and reasoning.
    """
    # async with httpx.AsyncClient(timeout=30) as client:
    #     model = GroqModel(
    #         'gemma2-9b-it',
    #         provider=GroqProvider(api_key=GROQ_API_KEY, http_client=client),
    #     )
    agent = Agent(model, system_prompt='Be concise, reply within 200 words. Check if the claim is true or false, and give a short explanation.')
    agent_result = await agent.run(final_query)
    return agent_result.data

news_claim_agent = Agent(model,
    # GroqModel('gemma2-9b-it', provider=GroqProvider(api_key=GROQ_API_KEY)),
    result_type=list[str],
    system_prompt="""
    Extract all distinct claims from the given news article.
    Do not modify the claims or add any additional information.
    Return them as a list of strings. Focus on factual statements that can be verified.
    """,
)

async def process_claim(claim, qa, results_final):
    rag_result = await rag_run(claim, qa)

    agent = Agent(model,
        # GroqModel('gemma2-9b-it', provider=GroqProvider(api_key=GROQ_API_KEY)),
        result_type=Answer,
        system_prompt="""
        From the given text, extract the true or false answer and its confidence score and its explanation.
        Return the result as a JSON object with 'output' (boolean), 'confidence_score' (percentage), 'explanation' (string) fields.
        """,
    )
    final = await agent.run(rag_result)

    results_final.append({
        "claim": claim,
        "output": final.data.output,
        "confidence_score": final.data.confidence_score,
        "explanation": final.data.explanation,
    })

@app.route('/analyze', methods=['POST'])
def analyze():
    global setup_done
    data = request.get_json()
    urls = data.get("urls", [])  # expecting a list
    query = data.get("article")
    chroma_db_directory = data.get("chroma-db", "")
    print("urls recieved",urls)
    if not setup_done:
        setup(chroma_db_directory)
        setup_done = True


    if not urls or not query:
        return jsonify({"error": "Missing 'urls' list or 'article'"}), 400

    json_data = load_scraped_data()
    print("@@@@@@@@@@@@@@@@@@@@@@json data after loading: ",json_data)
    async def process_all():
        print("@@@@@@@@@@@@@@@@@@@@@@entered loop")
        tasks = []
        for url in urls:
            url_info = getdatabyurl(url, json_data)
            print("URL info:", url_info)
            # if not url_info or url_info["error"]:
            #     continue  # Skip if data not found or has error
            tasks.append(context_process_claim(query, url, url_info["data"]))
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and map back to urls
        processed = []
        for res in results:
            if isinstance(res, dict) and "url" in res:
                processed.append(res)
        return processed

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    results = loop.run_until_complete(process_all())
    return jsonify(results)

@app.route("/verify-claims", methods=["POST"])
async def verify_claims():
    data = request.get_json()
    chroma_db_directory = data.get("chroma-db", "")
    news_article = data.get("article", "")

    print(f"Received chroma_db_directory: {chroma_db_directory}")
    print(f"Received article: {news_article}")

    if not news_article or not chroma_db_directory:
        return jsonify({"error": "Missing chroma-db or article"}), 400

    db = create_or_load_db(chroma_db_directory)
    if db is None:
        return jsonify({"error": "Failed to create or load database"}), 500

    retriever = db.as_retriever()
    llm = ChatGroq(groq_api_key=GROQ_API_KEY, model_name='gemma2-9b-it')
    qa = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever, return_source_documents=True)

    claims = await news_claim_agent.run(news_article)

    results_final = []
    tasks = [asyncio.create_task(process_claim(claim, qa, results_final)) for claim in claims.data]

    await asyncio.gather(*tasks)

    print(json.dumps(results_final, indent=4))
    return (json.dumps(results_final, indent=4))

if __name__ == "__main__":
    app.run(debug=True,port=5000)
