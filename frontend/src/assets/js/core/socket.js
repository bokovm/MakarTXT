import { io } from 'socket.io-client'

export function setupSocket(app) {
  const socket = io('http://localhost:8080', {
    path: '/socket.io',
    transports: ['websocket'],
    reconnectionAttempts: 5
  })

  // Глобальное предоставление сокета
  app.provide('socket', socket)

  socket.on('connect', () => {
    console.log('Socket connected')
  })

  socket.on('disconnect', () => {
    console.log('Socket disconnected')
  })
}

export function setupProgressHandlers(socket) {
  socket.on('download_progress', (data) => {
    const progressBar = document.querySelector(`#progress-${data.task_id}`);
    if (progressBar) {
      progressBar.style.width = `${Math.round((data.current/data.total)*100)}%`;
    }

    socket.emit('get_progress', taskId);
    
    socket.on('progress_update', (data) => {
        const progressBar = document.getElementById('progress-bar');
        progressBar.style.width = `${data.progress}%`;
    });
    
    socket.on('download_complete', (data) => {
        showToast(`Файл ${data.filename} готов!`);
    });
  });
}