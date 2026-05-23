from flask import Flask, request, jsonify
from flask_cors import CORS
import os

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI

app = Flask(__name__)
CORS(app)

if "OPENAI_API_KEY" not in os.environ or os.environ["OPENAI_API_KEY"] == "TU_API_KEY":
    os.environ["OPENAI_API_KEY"] = "TU_API_KEY"

def load_documents():
    docs = []
    if not os.path.exists("data"):
        print("Error: La carpeta 'data' no existe.")
        return docs
        
    for file in os.listdir("data"):
        if file.endswith(".pdf"):
            ruta_completa = os.path.join("data", file)
            print(f"Cargando documento: {ruta_completa}")
            loader = PyPDFLoader(ruta_completa)
            docs.extend(loader.load())
    return docs

def get_vectorstore():
    embeddings = OpenAIEmbeddings()
    if os.path.exists("vectorstore"):
        print("Cargando vectorstore existente...")
        return FAISS.load_local("vectorstore", embeddings, allow_dangerous_deserialization=True)
    else:
        print("Creando nuevo vectorstore a partir de los PDFs...")
        docs = load_documents()
        if not docs:
            raise ValueError("No se encontraron documentos PDF en la carpeta 'data' para procesar.")
        db = FAISS.from_documents(docs, embeddings)
        db.save_local("vectorstore")
        return db

db = get_vectorstore()

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message")
    if not user_message:
        return jsonify({"reply": "Por favor, escribe un mensaje válido."}), 400

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

    response = llm.invoke(prompt)
    return jsonify({"reply": response.content})

@app.route("/")
def home():
    return "Chatbot Erasmus funcionando perfectamente"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

    app.run(host='0.0.0.0', port=port)
