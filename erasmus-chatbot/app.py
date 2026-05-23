from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from openai import OpenAI

app = Flask(__name__)
# CORS configurado de forma segura pero abierta para tu entorno web
CORS(app, resources={r"/*": {"origins": "*"}}) 

# 🔐 API KEY (Se lee directamente desde el entorno seguro de Render)
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")

# Inicialización segura del cliente OpenAI
if not OPENAI_KEY:
    print("⚠️ CRÍTICO: La variable de entorno OPENAI_API_KEY no está configurada.")
client = OpenAI(api_key=OPENAI_KEY)

# 🔹 Cargar texto de tus 3 documentos de forma directa
def obtener_contexto_estatico():
    texto_contexto = ""
    # Forzamos una ruta absoluta para evitar fallos de lectura en servidores Linux (Render)
    ruta_base = os.path.dirname(os.path.abspath(__file__))
    ruta_data = os.path.join(ruta_base, "data")
    
    if not os.path.exists(ruta_data):
        print(f"Advertencia: La carpeta '{ruta_data}' no existe. Creándola vacía...")
        os.makedirs(ruta_data, exist_ok=True)
        return "No hay documentos disponibles."
        
    for file in os.listdir(ruta_data):
        if file.lower().endswith(".pdf"):
            ruta_completa = os.path.join(ruta_data, file)
            try:
                from pypdf import PdfReader
                reader = PdfReader(ruta_completa)
                for page in reader.pages:
                    texto_extraido = page.extract_text()
                    if texto_extraido:
                        texto_contexto += texto_extraido + "\n"
                print(f"✅ Documento cargado con éxito: {file}")
            except Exception as e:
                print(f"❌ Error al leer el archivo {file}: {e}")
                
    # Reducimos ligeramente el límite para asegurar que el modelo procese bien las reglas
    return texto_contexto[:25000] 

# Cargamos los datos de tus PDFs en la memoria inicial del servidor
CONTEXTO_BOT = obtener_contexto_estatico()

@app.route("/chat", methods=["POST"])
def chat():
    # Validación de seguridad para evitar caídas por peticiones mal formadas
    if not request.is_json:
        return jsonify({"reply": "Error: La petición debe ser JSON."}), 400

    user_message = request.json.get("message")
    if not user_message or not str(user_message).strip():
        return jsonify({"reply": "Por favor, escribe un mensaje válido."}), 400

    try:
        # Llamada directa a la API de OpenAI con la estructura corregida
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.1, # Bajamos a 0.1 para que sea más estricto con tus normas
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Eres el asistente oficial Erasmus de una universidad.\n"
                        "Reglas estrictas:\n"
                        "- Responde siempre en español.\n"
                        "- Usa ÚNICAMENTE la información proporcionada en el contexto inferior.\n"
                        "- Si la respuesta no se encuentra en el contexto, di exactamente: 'Lo siento, no dispongo de esa información en los documentos oficiales.'\n"
                        "- Sé claro, directo y estructurado.\n\n"
                        f"CONTEXTO OFICIAL EXTRAÍDO DE LOS PDF:\n{CONTEXTO_BOT}"
                    )
                },
                {"role": "user", "content": str(user_message)}
            ]
        )
        return jsonify({"reply": response.choices[0].message.content})
    except Exception as e:
        print(f"Error en OpenAI API: {e}")
        return jsonify({"reply": f"Error en el servidor de IA: {str(e)}"}), 500

@app.route("/")
def home():
    return "Chatbot Erasmus funcionando perfectamente en modo ligero"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
