(function () {
  // Eliminamos DOMContentLoaded para asegurar que inyecte el HTML de inmediato
  const chatHTML = `
  <div id="chatbot-box" style="
    position:fixed;
    bottom:20px;
    right:20px;
    width:300px;
    background:white;
    border-radius:10px;
    box-shadow:0 0 10px rgba(0,0,0,0.2);
    font-family:sans-serif;
    z-index: 99999; /* Asegura que el chat quede por encima de todo */
  ">
    <div style="background:#003366;color:white;padding:10px;border-radius:10px 10px 0 0;font-weight:bold;">
      Erasmus Bot
    </div>
    <div id="messages" style="height:200px;overflow-y:auto;padding:10px;font-size:14px;"></div>
    <div style="display:flex;border-top:1px solid #eee;">
      <input id="chat-input" placeholder="Escribe un mensaje..." style="flex:1;border:none;padding:10px;border-radius:0 0 0 10px;outline:none;">
      <button id="send-btn" style="background:none;border:none;padding:10px;cursor:pointer;color:#003366;font-size:16px;">➤</button>
    </div>
  </div>
  `;

  document.body.insertAdjacentHTML("beforeend", chatHTML);

  const input = document.getElementById("chat-input");
  const button = document.getElementById("send-btn");
  const messagesContainer = document.getElementById("messages");

  async function sendMessage() {
    const msg = input.value.trim();
    if (!msg) return;

    // Mostrar mensaje del usuario en pantalla
    messagesContainer.innerHTML += `<p style="margin:5px 0;"><b>Tú:</b> ${msg}</p>`;
    input.value = "";
    messagesContainer.scrollTop = messagesContainer.scrollHeight; 

    try {
      // 🚀 CORREGIDO: Añadida la ruta /chat al final de la URL de tu Render
      const res = await fetch("https://chatbot-eygx.onrender.com/chat", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({message: msg})
      });

      if (!res.ok) throw new Error("Error en el servidor");

      const data = await res.json();
      
      messagesContainer.innerHTML += `<p style="margin:5px 0;color:#003366;"><b>Bot:</b> ${data.reply}</p>`;
    } catch (error) {
      messagesContainer.innerHTML += `<p style="margin:5px 0;color:red;"><b>Error:</b> No se pudo conectar con el bot.</p>`;
    }

    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  // Asignación de eventos directa y segura
  button.addEventListener("click", sendMessage);
  
  input.addEventListener("keypress", (e) => {
    if (e.key === "Enter") sendMessage();
  });
})();
