import customtkinter as ctk
import ctypes
import threading
from typing import Optional
import queue

# Windows API constants for screen capture exclusion
WDA_EXCLUDEFROMCAPTURE = 0x00000011
WDA_NONE = 0x00000000

class StealthOverlay:
    """
    Stealth Mode Overlay Window for Interview Assistance

    Features:
    - Frameless window (no title bar, borders)
    - Always on top of all applications
    - Semi-transparent background (70% opacity)
    - Draggable by clicking anywhere
    - Screen capture exclusion (invisible in Zoom, Teams, OBS)
    - Real-time AI suggestion streaming
    - Discrete close button
    """

    def __init__(self):
        self.root = ctk.CTkToplevel()
        self.root.withdraw()  # Hide initially

        # Window configuration
        self.root.title("AI Assistant")
        self.root.geometry("400x300+100+100")  # width x height + x + y

        # Remove window decorations (frameless)
        self.root.overrideredirect(True)

        # Always on top
        self.root.attributes('-topmost', True)

        # Semi-transparent background (70% opacity = 0.7 alpha)
        self.root.attributes('-alpha', 0.85)

        # Dark background color
        self.root.configure(fg_color="#1a1a1a")

        # Dragging variables
        self.drag_start_x = 0
        self.drag_start_y = 0

        # Text update queue
        self.text_queue = queue.Queue()

        self.create_ui()
        self.setup_dragging()
        self.apply_screen_capture_exclusion()

        # Start text update loop
        self.update_text_from_queue()

    def create_ui(self):
        """Create the overlay UI components"""

        # Main container
        main_frame = ctk.CTkFrame(
            self.root,
            fg_color="#1a1a1a",
            corner_radius=10,
            border_width=2,
            border_color="#2ecc71"
        )
        main_frame.pack(fill="both", expand=True, padx=2, pady=2)

        # Header with title and close button
        header_frame = ctk.CTkFrame(main_frame, fg_color="#2a2a2a", height=30)
        header_frame.pack(fill="x", padx=5, pady=5)
        header_frame.pack_propagate(False)

        title_label = ctk.CTkLabel(
            header_frame,
            text="💡 AI Assistant (Stealth Mode)",
            font=("Arial", 12, "bold"),
            text_color="#2ecc71"
        )
        title_label.pack(side="left", padx=10)

        close_button = ctk.CTkButton(
            header_frame,
            text="✕",
            width=30,
            height=25,
            fg_color="#e74c3c",
            hover_color="#c0392b",
            font=("Arial", 14, "bold"),
            command=self.close_overlay
        )
        close_button.pack(side="right", padx=5)

        # Text display area
        self.text_display = ctk.CTkTextbox(
            main_frame,
            font=("Arial", 16, "bold"),
            text_color="#2ecc71",
            fg_color="#1a1a1a",
            wrap="word",
            activate_scrollbars=True
        )
        self.text_display.pack(fill="both", expand=True, padx=5, pady=(0, 5))

        # Initial message
        self.text_display.insert("0.0", "Waiting for interviewer's question...\n\n")
        self.text_display.configure(state="disabled")

    def setup_dragging(self):
        """Enable window dragging by clicking and holding anywhere"""

        def start_drag(event):
            self.drag_start_x = event.x
            self.drag_start_y = event.y

        def do_drag(event):
            x = self.root.winfo_x() + (event.x - self.drag_start_x)
            y = self.root.winfo_y() + (event.y - self.drag_start_y)
            self.root.geometry(f"+{x}+{y}")

        # Bind to root window and all child widgets
        self.root.bind("<Button-1>", start_drag)
        self.root.bind("<B1-Motion>", do_drag)

        for widget in self.root.winfo_children():
            widget.bind("<Button-1>", start_drag)
            widget.bind("<B1-Motion>", do_drag)

    def apply_screen_capture_exclusion(self):
        """
        Apply Windows API flag to exclude window from screen capture.
        This makes the window invisible in Zoom, Teams, OBS, etc.
        """
        try:
            # Wait for window to be created
            self.root.update()

            # Get window handle
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())

            if hwnd:
                # Apply WDA_EXCLUDEFROMCAPTURE flag
                result = ctypes.windll.user32.SetWindowDisplayAffinity(
                    hwnd,
                    WDA_EXCLUDEFROMCAPTURE
                )

                if result:
                    print("[INFO] Stealth mode activated - Window excluded from screen capture")
                else:
                    print("[WARNING] Failed to apply screen capture exclusion")
            else:
                print("[WARNING] Could not get window handle for screen capture exclusion")

        except Exception as e:
            print(f"[ERROR] Failed to apply screen capture exclusion: {e}")
            print("[WARNING] Overlay will be visible in screen sharing")

    def update_text(self, text: str, clear: bool = False):
        """
        Update the overlay text (thread-safe)

        Args:
            text: Text to display
            clear: If True, clear existing text before adding new text
        """
        self.text_queue.put((text, clear))

    def update_text_from_queue(self):
        """Process text updates from queue (runs in main thread)"""
        try:
            while not self.text_queue.empty():
                text, clear = self.text_queue.get_nowait()

                self.text_display.configure(state="normal")

                if clear:
                    self.text_display.delete("0.0", "end")

                self.text_display.insert("end", text)

                # Auto-scroll to bottom
                self.text_display.see("end")

                self.text_display.configure(state="disabled")

        except queue.Empty:
            pass

        # Schedule next update
        self.root.after(100, self.update_text_from_queue)

    def stream_text(self, text_generator):
        """
        Stream text from a generator (e.g., LLM streaming response)

        Args:
            text_generator: Generator that yields text tokens
        """
        def stream_worker():
            self.update_text("", clear=True)
            self.update_text("🤔 Thinking...\n\n", clear=False)

            # Small delay to show "Thinking..." message
            threading.Event().wait(0.3)

            self.update_text("", clear=True)

            for token in text_generator:
                self.update_text(token, clear=False)

        threading.Thread(target=stream_worker, daemon=True).start()

    def show(self):
        """Show the overlay window"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def hide(self):
        """Hide the overlay window"""
        self.root.withdraw()

    def close_overlay(self):
        """Close the overlay window"""
        self.root.destroy()

    def is_visible(self):
        """Check if overlay is currently visible"""
        return self.root.state() == "normal"


class StealthOverlayManager:
    """
    Manager class to control the stealth overlay from the main application
    """

    def __init__(self):
        self.overlay: Optional[StealthOverlay] = None
        self.enabled = True

    def create_overlay(self):
        """Create and show the stealth overlay"""
        if self.overlay is None:
            self.overlay = StealthOverlay()
            self.overlay.show()
            print("[INFO] Stealth overlay created and shown")

    def update_suggestions(self, text: str, clear: bool = False):
        """Update the overlay with new AI suggestions"""
        if self.overlay and self.enabled:
            self.overlay.update_text(text, clear=clear)

    def stream_suggestions(self, text_generator):
        """Stream AI suggestions to the overlay"""
        if self.overlay and self.enabled:
            self.overlay.stream_text(text_generator)

    def toggle_visibility(self):
        """Toggle overlay visibility"""
        if self.overlay:
            if self.overlay.is_visible():
                self.overlay.hide()
            else:
                self.overlay.show()

    def close(self):
        """Close the overlay"""
        if self.overlay:
            self.overlay.close_overlay()
            self.overlay = None


# Test the overlay
if __name__ == "__main__":
    import time

    print("Testing Stealth Overlay...")
    print("The overlay should appear on your screen.")
    print("Try screen sharing with Zoom/Teams - the overlay should be invisible!")

    # Create root window (required for CTkToplevel)
    root = ctk.CTk()
    root.withdraw()

    # Create overlay
    overlay = StealthOverlay()
    overlay.show()

    # Simulate streaming text
    def simulate_stream():
        time.sleep(2)

        test_suggestions = [
            "• ", "Optimized ", "database ", "queries ", "- ", "reduced ", "latency ", "60%\n",
            "• ", "Implemented ", "caching ", "layer ", "with ", "Redis\n",
            "• ", "Collaborated ", "with ", "DevOps ", "on ", "infrastructure\n",
            "• ", "Result: ", "handled ", "10x ", "traffic ", "spike\n"
        ]

        overlay.update_text("", clear=True)

        for token in test_suggestions:
            overlay.update_text(token, clear=False)
            time.sleep(0.05)

    threading.Thread(target=simulate_stream, daemon=True).start()

    root.mainloop()
