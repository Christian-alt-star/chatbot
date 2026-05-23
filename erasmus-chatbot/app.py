from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from google import genai

app = Flask(__name__)

CORS(app)

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_KEY:
    print("⚠️ CRÍTICO: GEMINI_API_KEY no encontrada.")

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

@app.route("/chat", methods=["POST", "OPTIONS"], strict_slashes=False)
@app.route("/chat/", methods=["POST", "OPTIONS"], strict_slashes=False)
def chat():
    if request.method == "OPTIONS":
        response = jsonify({"status": "ok"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        return response, 200

    if not request.is_json:
        return jsonify({"reply": "Error: Se esperaba formato JSON."}), 400

    user_message = request.json.get("message")
    if not user_message:
        return jsonify({"reply": "Mensaje vacío."}), 400

    try:
        prompt_completo = f"""
Eres el asistente oficial Erasmus de una universidad.
Reglas:\n- Responde en español.\n- Usa SOLO el contexto.\n- Si no está, di que no lo sabes.

CONTEXTO:
{CONTEXTO_BOT}

PREGUNTA:
{user_message}
"""

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt_completo,
            config={
                "temperature": 0.1,
                "max_output_tokens": 800
            }
        )
        
        respuesta_final = jsonify({"reply": response.text.strip() if response.text else "No hay respuesta."})
        respuesta_final.headers.add("Access-Control-Allow-Origin", "*")
        return respuesta_final

    except Exception as e:
        print(f"❌ ERROR CRÍTICO EN /CHAT: {str(e)}")
        error_resp = jsonify({"reply": f"Fallo interno del servidor: {str(e)}"})
        error_resp.headers.add("Access-Control-Allow-Origin", "*")
        return error_resp, 500

@app.route("/")
def home():
    return "Chatbot Erasmus funcionando con Gemini"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
