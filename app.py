from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from google import genai
from google.genai import types

app = Flask(__name__)
CORS(app)

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_KEY)

def obtener_contexto_estatico():
    texto_contexto = ""
    ruta_base = os.path.dirname(os.path.abspath(__file__))
    ruta_data = os.path.join(ruta_base, "data")
    
    if not os.path.exists(ruta_data):
        os.makedirs(ruta_data, exist_ok=True)
        return "No hay documentos disponibles en el servidor."
        
    for file in os.listdir(ruta_data):
        if file.lower().endswith(".pdf"):
            try:
                from pypdf import PdfReader
                reader = PdfReader(os.path.join(ruta_data, file))
                for page in reader.pages:
                    txt = page.extract_text()
                    if txt:
                        texto_contexto += txt + "\n"
                print(f"✅ Documento cargado: {file}")
            except Exception as e:
                print(f"❌ Error al leer {file}: {e}")
                
    return texto_contexto.strip()[:30000]

CONTEXTO_BOT = obtener_contexto_estatico()

@app.route("/chat", methods=["POST", "OPTIONS"])
def chat():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    if not request.is_json:
        return jsonify({"reply": "Error: Se esperaba formato JSON."}), 400

    user_message = request.json.get("message")
    if not user_message or not str(user_message).strip():
        return jsonify({"reply": "Por favor, escribe un mensaje válido."}), 400

    try:
        prompt_completo = f"""
Eres el asistente oficial Erasmus de una universidad.

Reglas estrictas:
1. Responde siempre en español.
2. Usa ÚNICAMENTE la información proporcionada en el contexto oficial inferior.
3. Si la respuesta no se encuentra en el contexto, di exactamente: 'Lo siento, no dispongo de esa información en los documentos oficiales.'
4. Sé claro, directo y estructurado.

CONTEXTO OFICIAL EXTRAÍDO DE LOS PDF:
{CONTEXTO_BOT}

PREGUNTA DEL USUARIO:
{user_message}
"""

        response = client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=prompt_completo,
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=800
            )
        )
        
        if response and response.text:
            return jsonify({"reply": response.text.strip()})
        else:
            return jsonify({"reply": "Lo siento, el asistente de Google no generó texto válido."}), 500
        
    except Exception as e:
        print(f"❌ ERROR CRÍTICO EN /CHAT: {str(e)}")
        return jsonify({"reply": f"Fallo interno en el asistente de Google: {str(e)}"}), 500

@app.route("/")
def home():
    return "Chatbot Erasmus funcionando con Gemini en modo gratuito"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)