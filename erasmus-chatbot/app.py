from flask import Flask, request, jsonify
from flask_cors import CORS
import os

from langchain.document_loaders import PyPDFLoader
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI

app = Flask(__name__)
CORS(app)

# 🔐 API KEY
os.environ["OPENAI_API_KEY"] = "TU_API_KEY"

# 🔹 1. Cargar documentos
def load_documents():
    docs = []
    for file in os.listdir("data"):
        if file.endswith(".pdf"):
            loader = PyPDFLoader(f"data/{file}")
            docs.extend(loader.load())
    return docs

# 🔹 2. Crear o cargar base vectorial
def get_vectorstore():
    if os.path.exists("vectorstore"):
        return FAISS.load_local("vectorstore", OpenAIEmbeddings())
    else:
        docs = load_documents()
        db = FAISS.from_documents(docs, OpenAIEmbeddings())
        db.save_local("vectorstore")
        return db

db = get_vectorstore()

# 🔹 3. Modelo
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message")

    # 🔎 Buscar contexto
    docs = db.similarity_search(user_message, k=3)
    context = "\n\n".join([d.page_content for d in docs])

    prompt = f"""
Eres el asistente oficial Erasmus de una universidad.

Reglas:
- Responde en español
- Usa SOLO la información proporcionada
- Si no está en el contexto, di que no lo sabes
- Sé claro y estructurado

Contexto:
{context}

Pregunta:
{user_message}
"""

    response = llm.predict(prompt)

    return jsonify({"reply": response})

@app.route("/")
def home():
    return "Chatbot Erasmus funcionando"

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)