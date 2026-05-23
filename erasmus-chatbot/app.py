from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from openai import OpenAI

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# 🔐 API KEY (Se configurará de forma segura en Render)
OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "TU_API_KEY")
client = OpenAI(api_key=OPENAI_KEY)

# 🔹 Cargar texto de los documentos de forma ultraligera
def obtener_contexto_estatico():
    texto_contexto = ""
    ruta_data = "data"
    
    if not os.path.exists(ruta_data):
        return "No hay documentos disponibles."
        
    # En lugar de usar pesadas librerías de vectores, leemos de forma directa
    for file in os.listdir(ruta_data):
        if file.endswith(".pdf"):
            try:
                # Importación local para no saturar la memoria inicial
                from pypdf import PdfReader
                reader = PdfReader(os.path.join(ruta_data, file))
                for page in reader.pages:
                    texto_contexto += page.extract_text() + "\n"
            except Exception as e:
                print(f"Error al leer {file}: {e}")
                
    # Recortamos el contexto para no saturar los tokens de la API
    return texto_contexto[:15000] 

# Cargamos el texto una sola vez al encender el servidor
CONTEXTO_BOT = obtener_contexto_estatico()

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message")
    if not user_message:
        return jsonify({"reply": "Por favor, escribe un mensaje válido."}), 400

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.2,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Eres el asistente oficial Erasmus de una universidad.\n"
                        "Reglas:\n- Responde en español.\n"
                        "- Usa SOLO la información proporcionada en el contexto.\n"
                        "- Si la respuesta no está en el contexto, di textualmente que no lo sabes.\n"
                        "- Sé claro y estructurado.\n\n"
                        f"Contexto disponible:\n{CONTEXTO_BOT}"
                    )
                },
                {"role": "user", "content": user_message}
            ]
        )
        return jsonify({"reply": response.choices[0].message.content})
    except Exception as e:
        return jsonify({"reply": f"Error interno en el asistente: {str(e)}"}), 500

@app.route("/")
def home():
    return "Chatbot Erasmus funcionando perfectamente en modo ligero"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
