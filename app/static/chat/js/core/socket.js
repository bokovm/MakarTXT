// app\static\chat\js\core\socket.js
export function setupSocketHandlers(socket) {
  socket.on('message_update', (msg) => {
      const container = document.getElementById('messages-container');
      if (container) {
          const messageDiv = document.createElement('div');
          messageDiv.className = 'message user';
          messageDiv.innerHTML = `
              <div class="message-content">${msg.content}</div>
              <span class="message-time">${msg.time}</span>
          `;
          container.appendChild(messageDiv);
      }
  });
}