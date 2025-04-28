# import asyncio
import json
import os
from langchain.schema import Document
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from flask import Flask, jsonify

app = Flask(__name__)


def load_documents():
    documents = []
    json_files = ["C:/Users/hp/Desktop/coding/truth-telll/nikita/scraped_data.json"]
    for json_file in json_files:
        if os.path.exists(json_file):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    json_data = json.load(f)
                if isinstance(json_data, list):
                    for item in json_data:
                        documents.append(Document(page_content=json.dumps(item), metadata={"source": json_file}))
                elif isinstance(json_data, dict):
                    documents.append(Document(page_content=json.dumps(json_data), metadata={"source": json_file}))
                print(f"Loaded {len(json_data) if isinstance(json_data, list) else 1} items from {json_file}")
            except Exception as e:
                print(f"Error loading JSON {json_file}: {e}")
    return documents


def get_next_chroma_directory():
    base_dir = "db"
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)

    existing_dirs = [d for d in os.listdir(base_dir) if d.startswith("chroma_db_")]
    if not existing_dirs:
        return os.path.join(base_dir, "chroma_db_1")

    existing_numbers = [int(d.split("_")[-1]) for d in existing_dirs]
    next_number = max(existing_numbers) + 1
    return os.path.join(base_dir, f"chroma_db_{next_number}")


persist_directory = get_next_chroma_directory()
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

def create_or_load_db(persist_directory):
    try:
        documents = load_documents()
        print("loaded doc")
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        texts = text_splitter.split_documents(documents)
        print("directory before passing", persist_directory)
        db = Chroma.from_documents(texts, embeddings, persist_directory=persist_directory)
        print("New vector database created successfully")
        print(f"Vector database loaded successfully with {db._collection.count()} documents")
        return db
    except Exception as e:
        print(f"Error creating Chroma database: {e}")
        return None

@app.route("/create-db", methods=["POST"])
def create_db():
    persist_directory = get_next_chroma_directory()  # ✅ Now calculated on every request
    db = create_or_load_db(persist_directory)
    if db is None:
        return jsonify({"error": "Failed to create or load database"}), 500

    print(f"chromadb created at {persist_directory}")
    return persist_directory

if __name__ == "__main__":
    app.run(debug=True,port=5500)
