from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from groq import Groq

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*", "methods": ["POST", "GET", "OPTIONS"], "allow_headers": ["Content-Type"]}})

GROQ_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=GROQ_KEY) if GROQ_KEY else None

def obtener_contexto_estatico():
    return """
    CONVOCATORIA ERASMUS+ 2026 - DATOS OFICIALES DE ORIENTACIÓN:
    
    1. PLAZOS DE ENTREGA:
    - El plazo de entrega para las solicitudes electrónicas es desde el 27 de enero hasta el 16 de febrero de 2026.
    - Cualquier solicitud presentada fuera de este plazo (incluso 3 días tarde por problemas médicos) será excluida automáticamente sin excepción.
    
    2. CUANTÍAS ECONÓMICAS DE LAS BECAS (MENSUAL):
    - GRUPO 1 (Coste de vida alto: Alemania, Austria, Bélgica, Francia, Italia, Países Bajos, Suecia, etc): Estudios: 350 €/mes | Prácticas: 500 €/mes.
    - GRUPO 2 (Coste de vida medio: Chequia, España, Grecia, Portugal, etc): Estudios: 300 €/mes | Prácticas: 450 €/mes.
    - GRUPO 3 (Coste de vida bajo: Bulgaria, Croacia, Hungría, Polonia, Rumanía, Turquía): Estudios: 250 €/mes | Prácticas: 400 €/mes.
    
    3. REQUISITOS DE IDIOMA:
    - Se exige un nivel B2 obligatorio de inglés por defecto si la universidad de destino no especifica uno concreto.
    - Los estudiantes con un nivel B1 de inglés no cumplen el requisito por defecto y perderán la opción de acceder a esos destinos. Sin embargo, se les podrán ofrecer plazas vacantes que no requieran certificados.
    
    4. CÓMO ENVIAR LA SOLICITUD:
    - Debe grabarse telemáticamente en la secretaría virtual (SIGMA) seleccionando la modalidad. Se pueden elegir hasta 10 opciones en orden de preferencia.
    - Tras grabarla, se debe descargar el formulario, firmarlo y enviarlo por correo electrónico a la Oficina de Relaciones Internacionales (ori@lasallecampus.es) dentro del plazo.
    """

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
        return jsonify({"reply": "Error: La clave GROQ_API_KEY no está configurada en Render."}), 500

    try:
        prompt_completo = f"""
Eres el asistente oficial Erasmus de una universidad.

Reglas estrictas:
- Responde siempre en español de forma directa y resumida.
- Usa ÚNICAMENTE la información proporcionada en el contexto.

CONTEXTO OFICIAL:
{CONTEXTO_BOT}
"""

        
        response = client.chat.completions.create(
            model="groq/compound-mini",
            messages=[
                {"role": "system", "content": prompt_completo},
                {"role": "user", "content": str(user_message)}
            ],
            temperature=0.1,
            max_tokens=400
        )
        
        if response and response.choices:
            return jsonify({"reply": response.choices[0].message.content.strip()})
        else:
            return jsonify({"reply": "El asistente no pudo procesar la respuesta. Reintenta."}), 500
        
    except Exception as e:
        print(f"❌ ERROR CRÍTICO EN GROQ: {str(e)}")
        return jsonify({"reply": f"Fallo en los sistemas del asistente: {str(e)}"}), 500

@app.route("/")
def home():
    return "Backend Erasmus activo con Groq"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
