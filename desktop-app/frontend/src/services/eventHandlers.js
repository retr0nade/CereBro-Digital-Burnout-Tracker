export const createToastStore = () => {
    let listeners = [];
    let queue = [];
    const notify = (type, message) => {
        const item = { id: Date.now() + Math.random(), type, message };
        queue.push(item);
        listeners.forEach(l => l(queue));
        setTimeout(() => dismiss(item.id), 3000);
    };
    const dismiss = (id) => {
        queue = queue.filter(q => q.id !== id);
        listeners.forEach(l => l(queue));
    };
    const subscribe = (cb) => {
        listeners.push(cb);
        cb(queue);
        return () => { listeners = listeners.filter(l => l !== cb); };
    };
    return { notify, dismiss, subscribe };
};

export const toast = createToastStore();

// Event types for the WebSocket
export const EVENT_TYPES = {
    ACTIVITY_UPDATE: 'activity_update',
    IDLE_UPDATE: 'idle_update',
    SCREEN_TIME_UPDATE: 'screen_time_update',
    FOCUS_SESSION_UPDATE: 'focus_session_update',
    BREAK_UPDATE: 'break_update',
};

// Event handlers for different types of events
const eventHandlers = {
    [EVENT_TYPES.ACTIVITY_UPDATE]: (data) => {
        // Handle activity update
        // console.log('Activity update received:', data);
    },
    [EVENT_TYPES.IDLE_UPDATE]: (data) => {
        // Handle idle update
        // console.log('Idle update received:', data);
    },
    [EVENT_TYPES.SCREEN_TIME_UPDATE]: (data) => {
        // Handle screen time update
        // console.log('Screen time update received:', data);
    },
    [EVENT_TYPES.FOCUS_SESSION_UPDATE]: (data) => {
        // Handle focus session update
        // console.log('Focus session update received:', data);
    },
    [EVENT_TYPES.BREAK_UPDATE]: (data) => {
        // Handle break update
        // console.log('Break update received:', data);
    },
};

// Register event handlers with socket
export const registerSocketEvents = (socket) => {
    socket.on('event', (eventData) => {
        const { type, data } = eventData;
        const handler = eventHandlers[type];
        if (handler) {
            handler(data);
        } else {
            console.warn('Unknown event type received:', type);
        }
    });
};
