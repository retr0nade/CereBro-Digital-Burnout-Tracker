
// Type definition for Tauri window object
declare global {
    interface Window {
        __TAURI__: {
            invoke?: (command: string, args?: any) => Promise<any>;
            core?: {
                invoke: (command: string, args?: any) => Promise<any>;
            };
            event?: {
                listen: <T>(event: string, handler: (event: { payload: T }) => void) => Promise<() => void>;
            };
        };
    }
}

/**
 * Safely invokes a Tauri command, handling differences between Tauri v1 and v2.
 * @param command The command name to invoke
 * @param args Optional arguments for the command
 * @returns Promise resolving to the command result
 */
export const invoke = async <T = any>(command: string, args?: any): Promise<T> => {
    if (typeof window === 'undefined') {
        throw new Error('Window object is not available');
    }

    // Check for Tauri v2 (window.__TAURI__.core.invoke)
    if (window.__TAURI__?.core?.invoke) {
        return window.__TAURI__.core.invoke(command, args);
    }

    // Check for Tauri v1 (window.__TAURI__.invoke)
    if (window.__TAURI__?.invoke) {
        return window.__TAURI__.invoke(command, args);
    }

    throw new Error('Tauri API is not available. Make sure you are running in a Tauri environment.');
};

/**
 * Safely listens to a Tauri event.
 * @param event The event name to listen to
 * @param handler The event handler callback
 * @returns Promise resolving to an unlisten function
 */
export const listen = async <T = any>(event: string, handler: (event: { payload: T }) => void): Promise<() => void> => {
    if (typeof window === 'undefined') {
        console.warn('Window object is not available, cannot listen to event:', event);
        return () => { };
    }

    // Check for Tauri event API
    if (window.__TAURI__?.event?.listen) {
        return window.__TAURI__.event.listen(event, handler);
    }

    // Fallback or error if not found (Tauri v1 might have it directly on __TAURI__ or different path, 
    // but v2 usually has it under event)
    // For v1 it was window.__TAURI__.event.listen too usually if allowed.

    console.warn('Tauri Event API is not available.');
    return () => { };
};

/**
 * Checks if the Tauri API is available.
 */
export const isTauriAvailable = (): boolean => {
    return typeof window !== 'undefined' &&
        !!(window.__TAURI__?.core?.invoke || window.__TAURI__?.invoke);
};
