from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from google import genai
from google.genai import types

app = Flask(__name__)

# CONFIGURACIÓN DE CORS BLINDADA PARA PRODUCCIÓN
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["POST", "GET", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_KEY)

# 🔹 Cargar texto de tus PDFs
def obtener_contexto_estatico():
    texto_contexto = ""
    ruta_base = os.path.dirname(os.path.abspath(__file__))
    ruta_data = os.path.join(ruta_base, "data")
    
    if not os.path.exists(ruta_data):
        os.makedirs(ruta_data, exist_ok=True)
        return "No hay documentos disponibles."
        
    for file in os.listdir(ruta_data):
        if file.lower().endswith(".pdf"):
            try:
                from pypdf import PdfReader
                reader = PdfReader(os.path.join(ruta_data, file))
                for page in reader.pages:
                    if page.extract_text():
                        texto_contexto += page.extract_text() + "\n"
                print(f"✅ Documento cargado: {file}")
            except Exception as e:
                print(f"❌ Error al leer {file}: {e}")
                
    return texto_contexto[:40000] # Gemini aguanta mucho más texto que OpenAI

CONTEXTO_BOT = obtener_contexto_estatico()

@app.route("/chat", methods=["POST", "OPTIONS"])
def chat():
    # Responder de inmediato a las peticiones de control del navegador (Preflight)
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    if not request.is_json:
        return jsonify({"reply": "Error: Formato no válido."}), 400

    user_message = request.json.get("message")
    if not user_message:
        return jsonify({"reply": "Mensaje vacío."}), 400

    try:
        system_instruction = (
            "Eres el asistente oficial Erasmus de una universidad.\n"
            "Reglas:\n- Responde en español.\n- Usa SOLO el contexto proporcionado.\n"
            "- Si no está, di que no dispones de la información.\n\n"
            f"CONTEXTO:\n{CONTEXTO_BOT}"
        )

        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=str(user_message),
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.1
            )
        )
        
        # Extraemos el texto de forma directa y segura
        respuesta_texto = response.text if response.text else "No se generó respuesta."
        return jsonify({"reply": respuesta_texto})
        
    except Exception as e:
        print(f"❌ ERROR EN /CHAT: {str(e)}")
        return jsonify({"reply": f"Error del servidor: {str(e)}"}), 500

@app.route("/")
def home():
    return "Chatbot Erasmus funcionando con Gemini en modo gratuito"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
