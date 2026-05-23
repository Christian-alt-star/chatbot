from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from google import genai
from google.genai import types

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}) 

# 🔐 API KEY de Google (Configúrala en las variables de entorno de Render)
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")

if not GEMINI_KEY:
    print("⚠️ CRÍTICO: La variable de entorno GEMINI_API_KEY no está configurada.")

# Inicializamos el nuevo cliente oficial de Google GenAI
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

@app.route("/chat", methods=["POST"])
def chat():
    if not request.is_json:
        return jsonify({"reply": "Error: La petición debe ser JSON."}), 400

    user_message = request.json.get("message")
    if not user_message or not str(user_message).strip():
        return jsonify({"reply": "Por favor, escribe un mensaje válido."}), 400

    try:
        # Instrucciones del sistema para Gemini
        system_instruction = (
            "Eres el asistente oficial Erasmus de una universidad.\n"
            "Reglas estrictas:\n"
            "- Responde siempre en español.\n"
            "- Usa ÚNICAMENTE la información proporcionada en el contexto inferior.\n"
            "- Si la respuesta no se encuentra en el contexto, di exactamente: 'Lo siento, no dispongo de esa información en los documentos oficiales.'\n"
            "- Sé claro, directo y estructurado.\n\n"
            f"CONTEXTO OFICIAL EXTRAÍDO DE LOS PDF:\n{CONTEXTO_BOT}"
        )

        # Llamada oficial a Gemini 1.5 Flash
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=str(user_message),
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.1
            )
        )
        
        return jsonify({"reply": response.text})
        
    except Exception as e:
        print(f"❌ ERROR EN GEMINI API: {str(e)}")
        return jsonify({"reply": f"Fallo interno en el asistente: {str(e)}"}), 500

@app.route("/")
def home():
    return "Chatbot Erasmus funcionando con Gemini en modo gratuito"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
