// Learn more about Tauri commands at https://tauri.app/develop/calling-rust/
#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

/// Toggle stealth mode to exclude window from screen capture (Windows only)
///
/// When enabled, the window becomes invisible to screen recording software like Zoom, Teams, OBS.
/// Uses Windows API SetWindowDisplayAffinity with WDA_EXCLUDEFROMCAPTURE flag.
///
/// # Arguments
/// * `window` - The Tauri window handle
/// * `enable` - true to enable stealth mode, false to disable
///
/// # Returns
/// * `Result<String, String>` - Success message or error
#[tauri::command]
fn toggle_stealth(window: tauri::Window, enable: bool) -> Result<String, String> {
    #[cfg(target_os = "windows")]
    {
        use windows::Win32::Foundation::HWND;
        use windows::Win32::UI::WindowsAndMessaging::{SetWindowDisplayAffinity, WDA_EXCLUDEFROMCAPTURE, WDA_NONE};

        // Get the native window handle
        let hwnd = window.hwnd().map_err(|e| format!("Failed to get window handle: {}", e))?;
        let hwnd = HWND(hwnd.0 as *mut std::ffi::c_void);

        // Set the display affinity based on enable flag
        let affinity = if enable {
            WDA_EXCLUDEFROMCAPTURE // 0x00000011 - Excludes window from screen capture
        } else {
            WDA_NONE // 0x00000000 - Normal window behavior
        };

        unsafe {
            SetWindowDisplayAffinity(hwnd, affinity)
                .map_err(|e| format!("Failed to set window display affinity: {}", e))?;
        }

        let status = if enable { "enabled" } else { "disabled" };
        Ok(format!("Stealth mode {}", status))
    }

    #[cfg(not(target_os = "windows"))]
    {
        // Gracefully handle non-Windows platforms
        Err("Stealth mode is only supported on Windows".to_string())
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![greet, toggle_stealth])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
