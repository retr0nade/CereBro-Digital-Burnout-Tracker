use serde::{Deserialize, Serialize};
use std::process::Command;
use std::sync::{Arc, Mutex};
use tauri::Manager;

#[derive(Debug, Serialize, Deserialize)]
struct BackendStatus {
    running: bool,
    port: u16,
    error: Option<String>,
}

struct BackendState {
    status: Arc<Mutex<BackendStatus>>,
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let backend_state = BackendState {
        status: Arc::new(Mutex::new(BackendStatus {
            running: false,
            port: 5005,
            error: None,
        })),
    };

    tauri::Builder::default()
        .manage(backend_state)
        .setup(|app| {
            if cfg!(debug_assertions) {
                app.handle().plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Info)
                        .build(),
                )?;
            }
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            start_backend_command,
            stop_backend_command,
            get_backend_status,
            check_backend_health,
            get_system_metrics
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

#[tauri::command]
async fn start_backend_command(app: tauri::AppHandle) -> Result<(), String> {
    let backend_state = app.state::<BackendState>();
    
    // Update status to running
    {
        let mut status = backend_state.status.lock().unwrap();
        status.running = true;
        status.error = None;
    }
    
    // Start backend in a separate thread
    let status_arc = Arc::clone(&backend_state.status);
    std::thread::spawn(move || {
        // Start Python backend
        let result = Command::new("python")
            .arg("app_service.py")
            .current_dir("../../backend")
            .output();

        // Update status based on result
        let mut status = status_arc.lock().unwrap();
        match result {
            Ok(_) => {
                status.running = false;
                status.error = Some("Backend stopped".to_string());
            }
            Err(e) => {
                status.running = false;
                status.error = Some(format!("Failed to start backend: {}", e));
            }
        }
    });
    
    Ok(())
}

#[tauri::command]
async fn stop_backend_command(app: tauri::AppHandle) -> Result<(), String> {
    let backend_state = app.state::<BackendState>();
    let mut status = backend_state.status.lock().unwrap();
    status.running = false;
    status.error = Some("Backend stopped by user".to_string());
    Ok(())
}

#[tauri::command]
async fn get_backend_status(app: tauri::AppHandle) -> Result<BackendStatus, String> {
    let backend_state = app.state::<BackendState>();
    let status = backend_state.status.lock().unwrap();
    Ok(BackendStatus {
        running: status.running,
        port: status.port,
        error: status.error.clone(),
    })
}

#[tauri::command]
async fn check_backend_health() -> Result<bool, String> {
    let client = reqwest::Client::new();
    match client.get("http://localhost:5005/api/health").send().await {
        Ok(response) => Ok(response.status().is_success()),
        Err(_) => Ok(false),
    }
}

#[tauri::command]
async fn get_system_metrics() -> Result<serde_json::Value, String> {
    let client = reqwest::Client::new();
    match client.get("http://localhost:5005/api/metrics").send().await {
        Ok(response) => {
            if response.status().is_success() {
                response.json().await.map_err(|e| e.to_string())
            } else {
                Err("Backend returned error status".to_string())
            }
        }
        Err(e) => Err(format!("Failed to connect to backend: {}", e)),
    }
}
