// Prevents additional console window on Windows in release
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::Manager;

// Custom commands that can be called from the frontend
#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

#[tauri::command]
fn get_app_version() -> String {
    env!("CARGO_PKG_VERSION").to_string()
}

#[tauri::command]
fn open_external(url: &str) {
    let _ = webbrowser::open(url);
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![greet, get_app_version, open_external])
        .setup(|app| {
            // Setup window
            let window = app.get_window("main").unwrap();
            
            // Set minimum size
            let _ = window.set_min_size(Some(tauri::LogicalSize::new(1200, 700)));
            
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}