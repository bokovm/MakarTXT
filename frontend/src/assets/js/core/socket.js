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