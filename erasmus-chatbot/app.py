from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from openai import OpenAI

app = Flask(__name__)
# Permitimos el acceso total de CORS para tu entorno localhost sin restricciones
CORS(app, resources={r"/*": {"origins": "*"}}) 

# 🔐 API KEY (Se lee directamente desde el entorno seguro de Render)
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_KEY)

# 🔹 Cargar texto de tus 3 documentos de forma directa (Sin gastar memoria)
def obtener_contexto_estatico():
    texto_contexto = ""
    ruta_data = "data"
    
    if not os.path.exists(ruta_data):
        print("Advertencia: La carpeta 'data' no se encuentra en el servidor.")
        return "No hay documentos disponibles."
        
    for file in os.listdir(ruta_data):
        if file.endswith(".pdf"):
            try:
                from pypdf import PdfReader
                reader = PdfReader(os.path.join(ruta_data, file))
                for page in reader.pages:
                    texto_contexto += page.extract_text() + "\n"
                print(f"Documento cargado con éxito: {file}")
            except Exception as e:
                print(f"Error al leer el archivo {file}: {e}")
                
    return texto_contexto[:15000] # Limitamos los caracteres para no saturar el prompt

# Cargamos los datos de tus PDFs en la memoria inicial
CONTEXTO_BOT = obtener_contexto_estatico()

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message")
    if not user_message:
        return jsonify({"reply": "Por favor, escribe un mensaje válido."}), 400

    try:
        # Llamada directa y oficial a los modelos de OpenAI
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
                        f"Contexto disponible extraído de los PDFs:\n{CONTEXTO_BOT}"
                    )
                },
                {"role": "user", "content": user_message}
            ]
        )
        return jsonify({"reply": response.choices[0].message.content})
    except Exception as e:
        print(f"Error en OpenAI API: {e}")
        return jsonify({"reply": f"Error interno en el asistente: {str(e)}"}), 500

@app.route("/")
def home():
    return "Chatbot Erasmus funcionando perfectamente en modo ligero"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
