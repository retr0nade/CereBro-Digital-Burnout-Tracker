import { io } from 'socket.io-client';
import { SOCKET_URL } from '../config';

export const socket = io(SOCKET_URL, {
    autoConnect: true,
    reconnection: true,
    reconnectionAttempts: 5,
    reconnectionDelay: 1000,
});

// Event listeners
socket.on('connect', () => {
    // console.log('Connected to WebSocket server');
});

socket.on('disconnect', () => {
    // console.log('Disconnected from WebSocket server');
});

socket.on('event', (eventData) => {
    // console.log('Received event:', eventData);
    // You can dispatch this event to your state management system (Redux, Context, etc.)
    // or handle it directly in your components
});

// Error handling
socket.on('connect_error', (error) => {
    // console.error('WebSocket connection error:', error);
});

export const disconnectSocket = () => {
    if (socket) socket.disconnect();
};
