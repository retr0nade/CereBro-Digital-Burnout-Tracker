use std::process::{Command, Stdio};
use std::io::{BufRead, BufReader};
use tauri::Emitter;

// ... (keep existing structs)

#[tauri::command]
async fn start_backend_command(app: tauri::AppHandle) -> Result<(), String> {
    let backend_state = app.state::<BackendState>();
    
    // Check if already running
    {
        let child_guard = backend_state.child_process.lock().unwrap();
        if child_guard.is_some() {
            return Ok(()); // Already running
        }
    }

    // Ensure port 5005 is free by killing any process using it
    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        let _ = Command::new("cmd")
            .args(&["/C", "for /f \"tokens=5\" %a in ('netstat -aon ^| findstr :5005') do taskkill /f /pid %a"])
            .creation_flags(0x08000000) // CREATE_NO_WINDOW
            .output();
    }

    // Try to find the backend directory
    let possible_paths = vec![
        "../../backend",
        "../../../backend",
        "../../../../backend",
        "../backend",
        "./backend",
        "backend"
    ];

    let mut backend_dir = "../../backend"; // Default fallback
    for path in &possible_paths {
        let full_path = std::path::Path::new(path).join("app_service.py");
        if full_path.exists() {
            backend_dir = path;
            break;
        }
    }

    // Try python first, then python3
    let mut command = Command::new("python");
    command.arg("app_service.py").current_dir(backend_dir);
    
    // Configure for Windows to hide console window
    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        const CREATE_NO_WINDOW: u32 = 0x08000000;
        command.creation_flags(CREATE_NO_WINDOW);
    }

    // Pipe stdout and stderr
    command.stdout(Stdio::piped());
    command.stderr(Stdio::piped());

    let child_result = command.spawn();

    match child_result {
        Ok(mut child) => {
            // Handle stdout
            if let Some(stdout) = child.stdout.take() {
                let app_handle = app.clone();
                std::thread::spawn(move || {
                    let reader = BufReader::new(stdout);
                    for line in reader.lines() {
                        if let Ok(line) = line {
                            println!("Backend: {}", line);
                            let _ = app_handle.emit("backend-log", format!("STDOUT: {}", line));
                            if line.contains("PORT_BUSY") {
                                let _ = app_handle.emit("backend-error", "Port 5005 is busy");
                            }
                        }
                    }
                });
            }

            // Handle stderr
            if let Some(stderr) = child.stderr.take() {
                let app_handle = app.clone();
                std::thread::spawn(move || {
                    let reader = BufReader::new(stderr);
                    for line in reader.lines() {
                        if let Ok(line) = line {
                            eprintln!("Backend Err: {}", line);
                            let _ = app_handle.emit("backend-log", format!("STDERR: {}", line));
                        }
                    }
                });
            }

            // Store the child process
            let mut child_guard = backend_state.child_process.lock().unwrap();
            *child_guard = Some(child);
            
            // Update status
            let mut status = backend_state.status.lock().unwrap();
            status.running = true;
            status.error = None;
            Ok(())
        },
        Err(e) => {
            // Try python3 fallback
            let mut command3 = Command::new("python3");
            command3.arg("app_service.py").current_dir(backend_dir);
            
            #[cfg(windows)]
            {
                use std::os::windows::process::CommandExt;
                const CREATE_NO_WINDOW: u32 = 0x08000000;
                command3.creation_flags(CREATE_NO_WINDOW);
            }

            // Pipe stdout and stderr for fallback too
            command3.stdout(Stdio::piped());
            command3.stderr(Stdio::piped());

            match command3.spawn() {
                Ok(mut child) => {
                    // Handle stdout
                    if let Some(stdout) = child.stdout.take() {
                        let app_handle = app.clone();
                        std::thread::spawn(move || {
                            let reader = BufReader::new(stdout);
                            for line in reader.lines() {
                                if let Ok(line) = line {
                                    println!("Backend: {}", line);
                                    let _ = app_handle.emit("backend-log", format!("STDOUT: {}", line));
                                    if line.contains("PORT_BUSY") {
                                        let _ = app_handle.emit("backend-error", "Port 5005 is busy");
                                    }
                                }
                            }
                        });
                    }

                    // Handle stderr
                    if let Some(stderr) = child.stderr.take() {
                        let app_handle = app.clone();
                        std::thread::spawn(move || {
                            let reader = BufReader::new(stderr);
                            for line in reader.lines() {
                                if let Ok(line) = line {
                                    eprintln!("Backend Err: {}", line);
                                    let _ = app_handle.emit("backend-log", format!("STDERR: {}", line));
                                }
                            }
                        });
                    }

                    let mut child_guard = backend_state.child_process.lock().unwrap();
                    *child_guard = Some(child);
                    
                    let mut status = backend_state.status.lock().unwrap();
                    status.running = true;
                    status.error = None;
                    Ok(())
                },
                Err(e2) => {
                    let mut status = backend_state.status.lock().unwrap();
                    status.running = false;
                    status.error = Some(format!("Failed to start backend: {} / {}", e, e2));
                    Err(format!("Failed to start backend: {} / {}", e, e2))
                }
            }
        }
    }
}

#[tauri::command]
async fn stop_backend_command(app: tauri::AppHandle) -> Result<(), String> {
    let backend_state = app.state::<BackendState>();
    
    // First try to call the shutdown endpoint gracefully
    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(2))
        .build()
        .unwrap_or_else(|_| reqwest::Client::new());
        
    let _ = client.post("http://127.0.0.1:5005/api/shutdown").send().await;

    // Give it a moment to shut down
    std::thread::sleep(std::time::Duration::from_millis(1000));

    // Then ensure the process is killed if we have a handle
    let mut child_guard = backend_state.child_process.lock().unwrap();
    if let Some(mut child) = child_guard.take() {
        // Kill the process
        let _ = child.kill();
        let _ = child.wait(); // Prevent zombie process
    }

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
    
    let is_running = match client.get("http://127.0.0.1:5005/api/health").send().await {
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
    match client.get("http://127.0.0.1:5005/api/health").send().await {
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
    
    match client.get("http://127.0.0.1:5005/api/metrics").send().await {
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
        .post(&format!("http://127.0.0.1:5005/api/service/{}/start", name))
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
        .post(&format!("http://127.0.0.1:5005/api/service/{}/stop", name))
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
        .get("http://127.0.0.1:5005/api/status")
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

