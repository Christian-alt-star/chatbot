from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from google import genai
from google.genai import types

app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": "*", "methods": ["POST", "GET", "OPTIONS"], "allow_headers": ["Content-Type"]}})

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else None

def obtener_contexto_estatico():
    texto_contexto = ""
    ruta_base = os.path.dirname(os.path.abspath(__file__))
    ruta_data = os.path.join(ruta_base, "data")
    
    if not os.path.exists(ruta_data):
        return "No hay documentos disponibles en el servidor."
        
    archivos = [f for f in os.listdir(ruta_data) if f.lower().endswith(".pdf")]
    if not archivos:
        return "La carpeta de documentos oficiales está vacía."

    for file in archivos:
        ruta_completa = os.path.join(ruta_data, file)
        try:
            from pypdf import PdfReader
            reader = PdfReader(ruta_completa)
            for page in reader.pages:
                txt = page.extract_text()
                if txt:
                    texto_contexto += txt + "\n"
        except Exception as e:
            print(f"❌ Error al leer {file}: {str(e)}")
                
    return texto_contexto.strip()[:15000]

CONTEXTO_BOT = obtener_contexto_estatico()

@app.route("/chat", methods=["POST", "OPTIONS"])
def chat():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    if not request.is_json:
        return jsonify({"reply": "Error interno: Formato inválido."}), 400

    user_message = request.json.get("message")
    if not user_message or not str(user_message).strip():
        return jsonify({"reply": "Por favor, escribe una pregunta válida."}), 400

    if not client:
        return jsonify({"reply": "Error: La clave de la IA no está configurada en Render."}), 500

    try:
        prompt_completo = f"""
Eres el asistente oficial Erasmus de una universidad.

Reglas estrictas:
1. Responde siempre en español de forma resumida.
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
                max_output_tokens=500
            )
        )
        
        if response and response.text:
            return jsonify({"reply": response.text.strip()})
        else:
            return jsonify({"reply": "Lo siento, la IA no generó texto. Inténtalo de nuevo."}), 500
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ DETALLE DEL ERROR: {error_msg}")
        
        if "429" in error_msg or "quota" in error_msg.lower() or "exhausted" in error_msg.lower():
            return jsonify({"reply": "⏳ El servidor está procesando muchas consultas. Por favor, espera 10 segundos y vuelve a enviar tu pregunta."})
            
        return jsonify({"reply": "Fallo de conexión con la IA. Por favor, reintenta en unos instantes."}), 500

@app.route("/")
def home():
    return f"Chatbot Erasmus activo. Servidor funcionando correctamente."

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

