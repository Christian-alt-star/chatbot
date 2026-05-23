(function () {
  const chatHTML = `
  <div id="chatbot-box" style="
    position:fixed;
    bottom:15px;
    right:15px;
    width:280px;
    background:white;
    border-radius:10px;
    box-shadow:0 4px 15px rgba(0,0,0,0.15);
    font-family:sans-serif;
    z-index: 99999;
    display:flex;
    flex-direction:column;
    transition: all 0.3s ease;
  ">
    <div id="chatbot-header" style="
      background:#003366;
      color:white;
      padding:10px;
      border-radius:10px 10px 0 0;
      font-weight:bold;
      display:flex;
      justify-content:space-between;
      align-items:center;
      cursor:pointer;
    ">
      <span style="flex:1; pointer-events:none;">🤖 Erasmus Bot</span>
      <button id="chatbot-toggle-btn" style="background:none; border:none; color:white; cursor:pointer; font-size:12px; padding:0 5px; font-weight:bold;">[-]</button>
    </div>
    
    <div id="chatbot-body" style="display:flex; flex-direction:column;">
      <div id="messages" style="height:180px; overflow-y:auto; padding:10px; font-size:13px; background:#f9f9f9;"></div>
      <div style="display:flex; border-top:1px solid #eee;">
        <input id="chat-input" placeholder="Pregunta algo..." style="flex:1; border:none; padding:10px; font-size:13px; outline:none; border-radius:0 0 0 10px;">
        <button id="send-btn" style="background:none; border:none; padding:10px; cursor:pointer; color:#003366; font-size:14px;">➤</button>
      </div>
    </div>
  </div>
  `;

  document.body.insertAdjacentHTML("beforeend", chatHTML);

  const chatbotBox = document.getElementById("chatbot-box");
  const chatbotHeader = document.getElementById("chatbot-header");
  const chatbotBody = document.getElementById("chatbot-body");
  const toggleBtn = document.getElementById("chatbot-toggle-btn");
  const input = document.getElementById("chat-input");
  const button = document.getElementById("send-btn");
  const messagesContainer = document.getElementById("messages");

  let isMinimized = false;

  function toggleChat() {
    if (!isMinimized) {
      chatbotBody.style.display = "none";
      chatbotBox.style.width = "140px";
      toggleBtn.innerText = "💬 Abrir";
      isMinimized = true;
    } else {
      chatbotBody.style.display = "flex";
      chatbotBox.style.width = "280px";
      toggleBtn.innerText = "[-]";
      isMinimized = false;
    }
  }

  chatbotHeader.addEventListener("click", toggleChat);

  async function sendMessage() {
    const msg = input.value.trim();
    if (!msg) return;

    if (isMinimized) toggleChat();

    messagesContainer.innerHTML += `<p style="margin:4px 0; font-size:13px;"><b>Tú:</b> ${msg}</p>`;
    input.value = "";
    messagesContainer.scrollTop = messagesContainer.scrollHeight; 

    try {
      const res = await fetch("https://chatbot-eygx.onrender.com/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg })
      });

      if (!res.ok) throw new Error(`Error en servidor (Código ${res.status})`);

      const data = await res.json();
      messagesContainer.innerHTML += `<p style="margin:4px 0; color:#003366; font-size:13px;"><b>Bot:</b> ${data.reply}</p>`;
    } catch (error) {
      messagesContainer.innerHTML += `<p style="margin:4px 0; color:red; font-size:12px;"><b>Fallo:</b> ${error.message}</p>`;
    }

    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  button.addEventListener("click", sendMessage);
  input.addEventListener("keypress", (e) => {
    if (e.key === "Enter") sendMessage();
  });
})();