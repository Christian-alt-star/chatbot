from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from google import genai

app = Flask(__name__)
# Permitir peticiones desde tu localhost sin restricciones
CORS(app)

# 🔐 API KEY de Google 
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_KEY:
    print("⚠️ CRÍTICO: GEMINI_API_KEY no encontrada.")

# Inicialización según la documentación oficial de google-genai
client = genai.Client(api_key=GEMINI_KEY)

# 🔹 Cargar texto de tus PDFs de forma limpia
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
                
    # Nos aseguramos de limpiar espacios innecesarios y limitar de forma segura
    return texto_contexto.strip()[:30000]

CONTEXTO_BOT = obtener_contexto_estatico()

@app.route("/chat", methods=["POST"])
def chat():
    if not request.is_json:
        return jsonify({"reply": "Error: Se esperaba formato JSON."}), 400

    user_message = request.json.get("message")
    if not user_message or not str(user_message).strip():
        return jsonify({"reply": "Por favor, escribe un mensaje válido."}), 400

    try:
        # Prompt estructurado según las directrices de Gemini
        prompt_completo = f"""
Eres el asistente oficial Erasmus de una universidad.

Reglas estrictas:
1. Responde siempre en español.
2. Usa ÚNICAMENTE la información proporcionada en el contexto oficial inferior.
3. Si la respuesta no se encuentra explícitamente en el contexto, di exactamente: 'Lo siento, no dispongo de esa información en los documentos oficiales.'
4. Sé claro, directo y estructurado.

CONTEXTO OFICIAL EXTRAÍDO DE LOS PDF:
{CONTEXTO_BOT}

PREGUNTA DEL USUARIO:
{user_message}
"""

        # Llamada simplificada compatible con todas las versiones de google-genai
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt_completo,
            config={
                "temperature": 0.1,
                "max_output_tokens": 800  # Evita respuestas eternas que rompen el JSON de Flask
            }
        )
        
        # Extracción segura de la respuesta
        if response and response.text:
            return jsonify({"reply": response.text.strip()})
        else:
            return jsonify({"reply": "Lo siento, el asistente no pudo procesar la respuesta adecuadamente."}), 500
        
    except Exception as e:
        print(f"❌ ERROR CRÍTICO EN /CHAT: {str(e)}")
        return jsonify({"reply": f"Fallo interno del servidor: {str(e)}"}), 500

@app.route("/")
def home():
    return "Chatbot Erasmus funcionando con Gemini"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)