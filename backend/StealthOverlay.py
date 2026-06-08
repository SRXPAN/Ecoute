import customtkinter as ctk
import ctypes
import threading
from typing import Optional
import queue

# Windows API constants for screen capture exclusion and taskbar hiding
WDA_EXCLUDEFROMCAPTURE = 0x00000011
WDA_NONE = 0x00000000
GWL_EXSTYLE = -20
WS_EX_APPWINDOW = 0x00040000
WS_EX_TOOLWINDOW = 0x00000080

class StealthOverlay:
    """
    Stealth Mode Overlay Window for Interview Assistance

    Features:
    - Frameless window (no title bar, borders)
    - Always on top of all applications
    - Semi-transparent background
    - Draggable by clicking anywhere
    - Screen capture exclusion (invisible in Zoom, Teams, OBS)
    - Real-time AI suggestion streaming
    - Ultra-clean, professional design
    """

    def __init__(self):
        self.root = ctk.CTkToplevel()
        self.root.withdraw()  # Hide initially

        # Window configuration
        self.root.title("Assistant")
        self.root.geometry("450x350+100+100")

        # Remove window decorations (frameless)
        self.root.overrideredirect(True)

        # Always on top
        self.root.attributes('-topmost', True)

        # Semi-transparent background for subtlety
        self.root.attributes('-alpha', 0.92)

        # Premium dark background
        self.root.configure(fg_color="#0F172A")

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
        """Create the overlay UI components - Ultra-premium minimalist design"""

        # Main container with subtle border
        main_frame = ctk.CTkFrame(
            self.root,
            fg_color="#1E293B",
            corner_radius=12,
            border_width=1,
            border_color="#334155"
        )
        main_frame.pack(fill="both", expand=True, padx=0, pady=0)

        # Minimalist header bar
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent", height=36)
        header_frame.pack(fill="x", padx=8, pady=8)
        header_frame.pack_propagate(False)

        # Title with minimal styling
        title_label = ctk.CTkLabel(
            header_frame,
            text="Assistant",
            font=("Segoe UI", 11, "bold"),
            text_color="#64748B"
        )
        title_label.pack(side="left", padx=12)

        # Hotkey hint
        hotkey_hint = ctk.CTkLabel(
            header_frame,
            text="[F9: Hide/Show]",
            font=("Segoe UI", 9),
            text_color="#475569"
        )
        hotkey_hint.pack(side="left", padx=8)

        # Ultra-minimal close button (only visible on hover)
        close_button = ctk.CTkButton(
            header_frame,
            text="×",
            width=28,
            height=28,
            fg_color="transparent",
            hover_color="#EF4444",
            text_color="#64748B",
            font=("Segoe UI", 16),
            corner_radius=6,
            command=self.close_overlay
        )
        close_button.pack(side="right", padx=6)

        # Scrollable frame to hold Q&A cards
        self.cards_container = ctk.CTkScrollableFrame(
            main_frame,
            fg_color="transparent"
        )
        self.cards_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))

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

                # Hide from Taskbar and Alt+Tab
                ex_style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                new_style = (ex_style & ~WS_EX_APPWINDOW) | WS_EX_TOOLWINDOW
                ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)

                # Force window to update its style
                self.root.withdraw()
                self.root.deiconify()

                print("[INFO] Overlay hidden from Taskbar and Alt+Tab")
            else:
                print("[WARNING] Could not get window handle for screen capture exclusion")

        except Exception as e:
            print(f"[ERROR] Failed to apply screen capture exclusion: {e}")
            print("[WARNING] Overlay will be visible in screen sharing")

    def add_qa_card(self, question_text: str) -> ctk.CTkTextbox:
        """
        Create a new Q&A card with question header and dismissable close button.
        Returns the answer textbox for streaming responses.

        Args:
            question_text: The interviewer's question

        Returns:
            CTkTextbox: The answer textbox for streaming AI response
        """
        # Card container
        card = ctk.CTkFrame(
            self.cards_container,
            fg_color="#1E293B",
            corner_radius=10,
            border_width=1,
            border_color="#334155"
        )
        card.pack(fill="x", padx=5, pady=5)

        # Header container (question + close button)
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=(12, 8))

        # Question label (bold, truncated if too long)
        question_display = question_text if len(question_text) <= 80 else question_text[:80] + "..."
        question_label = ctk.CTkLabel(
            header,
            text=f"Q: {question_display}",
            font=("Segoe UI", 13, "bold"),
            text_color="#38BDF8",
            anchor="w",
            wraplength=340
        )
        question_label.pack(side="left", fill="x", expand=True)

        # Close button
        close_btn = ctk.CTkButton(
            header,
            text="×",
            width=24,
            height=24,
            fg_color="transparent",
            hover_color="#EF4444",
            text_color="#64748B",
            font=("Segoe UI", 16),
            corner_radius=4,
            command=card.destroy
        )
        close_btn.pack(side="right", padx=(8, 0))

        # Answer textbox (for streaming response)
        answer_box = ctk.CTkTextbox(
            card,
            font=("Segoe UI", 15),
            text_color="#E2E8F0",
            fg_color="#0F172A",
            wrap="word",
            height=150,
            spacing1=8,
            spacing3=8
        )
        answer_box.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        answer_box.insert("0.0", "🤔 Thinking...")
        answer_box.configure(state="disabled")

        return answer_box

    def update_text(self, text: str, clear: bool = False):
        """
        Legacy method - kept for backward compatibility
        Now creates a new card for each question

        Args:
            text: Text to display
            clear: If True, clear existing text before adding new text
        """
        self.text_queue.put((text, clear))

    def update_text_from_queue(self):
        """Process text updates from queue (runs in main thread) - Legacy support"""
        try:
            while not self.text_queue.empty():
                text, clear = self.text_queue.get_nowait()
                # Legacy behavior - ignore for new card-based system
                pass

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
        """Close the overlay window without destroying it"""
        self.hide()

    def hide_overlay(self):
        """Hide the overlay window (for panic button)"""
        self.root.withdraw()

    def show_overlay(self):
        """Show the overlay window (for panic button)"""
        self.root.deiconify()
        self.root.lift()

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
