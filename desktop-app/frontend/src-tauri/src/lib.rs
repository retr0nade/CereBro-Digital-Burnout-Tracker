use serde::{Deserialize, Serialize};
use std::process::Command;
use std::sync::{Arc, Mutex};
use tauri::Manager;
use std::collections::HashMap;

#[derive(Debug, Serialize, Deserialize)]
struct BackendStatus {
    running: bool,
    port: u16,
    error: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
struct ServiceStatus {
    name: String,
    status: String,
    start_time: Option<String>,
    last_error: Option<String>,
    restart_count: u32,
    max_restarts: u32,
    uptime: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
struct ServiceControlResponse {
    success: bool,
    message: String,
    service_name: String,
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
        .plugin(tauri_plugin_http::init())
        .plugin(tauri_plugin_shell::init())
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
            get_system_metrics,
            start_service,
            stop_service,
            get_service_status
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
    
    // Check if backend is actually running by calling health endpoint
    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(5))
        .build()
        .map_err(|e| format!("Failed to create HTTP client: {}", e))?;
    
    let is_running = match client.get("http://localhost:5005/api/health").send().await {
        Ok(response) => response.status().is_success(),
        Err(e) => {
            println!("Backend health check failed: {:?}", e);
            false
        }
    };
    
    // Update the status based on actual health check
    let mut status = backend_state.status.lock().unwrap();
    status.running = is_running;
    if !is_running {
        status.error = Some("Backend is not responding".to_string());
    } else {
        status.error = None;
    }
    
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
    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(10))
        .build()
        .map_err(|e| format!("Failed to create HTTP client: {}", e))?;
    
    match client.get("http://localhost:5005/api/metrics").send().await {
        Ok(response) => {
            if response.status().is_success() {
                response.json().await.map_err(|e| format!("Failed to parse JSON: {}", e))
            } else {
                Err(format!("Backend returned error status: {}", response.status()))
            }
        }
        Err(e) => {
            println!("Metrics request failed: {:?}", e);
            Err(format!("Failed to connect to backend: {}", e))
        }
    }
}

#[tauri::command]
async fn start_service(name: String) -> Result<ServiceControlResponse, String> {
    let client = reqwest::Client::new();
    
    // Call the Python backend API to start the service
    let response = client
        .post(&format!("http://localhost:5005/api/service/{}/start", name))
        .send()
        .await
        .map_err(|e| format!("Failed to connect to backend: {}", e))?;

    if response.status().is_success() {
        let result: ServiceControlResponse = response
            .json()
            .await
            .map_err(|e| format!("Failed to parse response: {}", e))?;
        Ok(result)
    } else {
        let error_text = response.text().await.unwrap_or_else(|_| "Unknown error".to_string());
        Err(format!("Backend returned error: {}", error_text))
    }
}

#[tauri::command]
async fn stop_service(name: String) -> Result<ServiceControlResponse, String> {
    let client = reqwest::Client::new();
    
    // Call the Python backend API to stop the service
    let response = client
        .post(&format!("http://localhost:5005/api/service/{}/stop", name))
        .send()
        .await
        .map_err(|e| format!("Failed to connect to backend: {}", e))?;

    if response.status().is_success() {
        let result: ServiceControlResponse = response
            .json()
            .await
            .map_err(|e| format!("Failed to parse response: {}", e))?;
        Ok(result)
    } else {
        let error_text = response.text().await.unwrap_or_else(|_| "Unknown error".to_string());
        Err(format!("Backend returned error: {}", error_text))
    }
}

#[tauri::command]
async fn get_service_status() -> Result<HashMap<String, ServiceStatus>, String> {
    let client = reqwest::Client::new();
    
    // Call the Python backend API to get service status
    let response = client
        .get("http://localhost:5005/api/status")
        .send()
        .await
        .map_err(|e| format!("Failed to connect to backend: {}", e))?;

    if response.status().is_success() {
        let result: serde_json::Value = response
            .json()
            .await
            .map_err(|e| format!("Failed to parse response: {}", e))?;
        
        // Extract services from the response
        if let Some(services) = result.get("services") {
            let services_map: HashMap<String, ServiceStatus> = serde_json::from_value(services.clone())
                .map_err(|e| format!("Failed to parse services: {}", e))?;
            Ok(services_map)
        } else {
            Err("No services found in response".to_string())
        }
    } else {
        let error_text = response.text().await.unwrap_or_else(|_| "Unknown error".to_string());
        Err(format!("Backend returned error: {}", error_text))
    }
}

