import sys
import random
import io
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QListWidgetItem, QLabel, QSizePolicy,
    QColorDialog, QMessageBox # Added QColorDialog, QMessageBox
)
from PySide6.QtCore import Qt, QObject, Signal, QThread, Slot
from PySide6.QtGui import QColor, QBrush, QFont, QPixmap, QIcon # Added QPixmap, QIcon

import pyembroidery # Import pyembroidery

# Default SVG content for initial pattern loading (a simple path)
DEFAULT_SVG_CONTENT = """
<svg width="100" height="100" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
  <path d="M 10 10 L 90 10 L 50 90 Z" fill="none" stroke="#3b82f6" stroke-width="2"/>
</svg>
"""

class EmbroideryThreadListWidget(QWidget):
    """
    A custom widget to display and manage a list of embroidery threads
    from a pyembroidery pattern.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Embroidery Thread List")
        self.setMinimumSize(400, 300)
        
        self.emb_pattern = pyembroidery.EmbPattern() # Initialize with an empty pattern
        self.next_custom_thread_id = 1 # For naming custom added threads

        self._setup_ui()
        self._apply_styles()
        self._load_initial_pattern() # Load a default pattern on startup

    def _setup_ui(self):
        """
        Sets up the user interface components.
        """
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Title Label
        title_label = QLabel("Embroidery Threads")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont("Inter", 16, QFont.Bold)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)

        # Thread List
        self.thread_list_widget = QListWidget()
        self.thread_list_widget.setSelectionMode(QListWidget.SingleSelection)
        self.thread_list_widget.itemSelectionChanged.connect(self._on_item_selection_changed)
        self.thread_list_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(self.thread_list_widget)

        # Current Thread Status Label
        self.current_thread_label = QLabel("Current Thread: None")
        self.current_thread_label.setAlignment(Qt.AlignCenter)
        current_thread_font = QFont("Inter", 12)
        self.current_thread_label.setFont(current_thread_font)
        main_layout.addWidget(self.current_thread_label)

        # Buttons Layout
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        buttons_layout.setAlignment(Qt.AlignCenter)

        self.add_new_thread_btn = QPushButton("Add New Thread")
        self.add_new_thread_btn.clicked.connect(self._add_new_embroidery_thread)
        buttons_layout.addWidget(self.add_new_thread_btn)

        main_layout.addLayout(buttons_layout)

    def _apply_styles(self):
        """
        Applies CSS-like styles to the widget and its components.
        """
        self.setStyleSheet("""
            QWidget {
                background-color: #f8fafc; /* Tailwind gray-50 */
                border-radius: 12px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            }
            QLabel {
                color: #1e293b; /* Tailwind slate-800 */
            }
            QListWidget {
                background-color: #ffffff;
                border: 1px solid #e2e8f0; /* Tailwind gray-200 */
                border-radius: 8px;
                padding: 5px;
                color: #334155; /* Tailwind slate-700 */
            }
            QListWidget::item {
                padding: 8px 10px;
                margin-bottom: 4px;
                border-radius: 6px;
            }
            QListWidget::item:selected {
                background-color: #bfdbfe; /* Tailwind blue-200 */
                color: #1e40af; /* Tailwind blue-800 */
                font-weight: 600;
            }
            QPushButton {
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s ease-in-out;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                background-color: #4f46e5; /* Tailwind indigo-600 */
                color: white;
            }
            QPushButton:hover {
                background-color: #4338ca; /* Darker indigo on hover */
            }
            QPushButton:disabled {
                background-color: #cbd5e1; /* Tailwind slate-300 */
                color: #64748b; /* Tailwind slate-500 */
                box-shadow: none;
            }
        """)

    def _load_initial_pattern(self):
        """
        Loads a default SVG pattern to initialize the thread list.
        """
        try:
            svg_file = io.StringIO(DEFAULT_SVG_CONTENT)
            self.emb_pattern.read_svg(svg_file)
            self.populate_thread_list()
        except Exception as e:
            QMessageBox.warning(self, "Error Loading SVG", f"Could not load initial SVG pattern: {e}")
            print(f"Error loading initial SVG: {e}")

    def populate_thread_list(self):
        """
        Populates the QListWidget with threads from the current embroidery pattern.
        """
        self.thread_list_widget.clear()
        if not self.emb_pattern.thread_list:
            QListWidgetItem("No embroidery threads loaded.").setTextAlignment(Qt.AlignCenter)
            self.thread_list_widget.addItem(QListWidgetItem("No embroidery threads loaded."))
            return

        for i, emb_thread in enumerate(self.emb_pattern.thread_list):
            item_text = emb_thread.name if emb_thread.name else f"Unnamed Thread {i+1}"
            
            list_item = QListWidgetItem(item_text)
            
            # Create a color swatch QPixmap
            color = QColor(emb_thread.red, emb_thread.green, emb_thread.blue)
            pixmap = QPixmap(24, 24) # Size of the color swatch
            pixmap.fill(color)
            list_item.setIcon(QIcon(pixmap))
            
            # Store the actual EmbThread object in the item's data
            list_item.setData(Qt.UserRole, emb_thread)
            
            self.thread_list_widget.addItem(list_item)
        
        # Select the first item by default if available
        if self.thread_list_widget.count() > 0:
            self.thread_list_widget.setCurrentRow(0)

    @Slot()
    def _on_item_selection_changed(self):
        """
        Updates the 'Current Thread' label when the selection in the list changes.
        """
        selected_items = self.thread_list_widget.selectedItems()
        if selected_items:
            selected_item = selected_items[0]
            emb_thread = selected_item.data(Qt.UserRole)
            if emb_thread:
                thread_name = emb_thread.name if emb_thread.name else "Unnamed Thread"
                color_rgb = f"({emb_thread.red}, {emb_thread.green}, {emb_thread.blue})"
                self.current_thread_label.setText(f"Current Thread: {thread_name} {color_rgb}")
            else:
                self.current_thread_label.setText("Current Thread: Invalid")
        else:
            self.current_thread_label.setText("Current Thread: None")

    @Slot()
    def _add_new_embroidery_thread(self):
        """
        Adds a new, custom embroidery thread to the pattern and updates the list.
        """
        # Allow user to pick a color
        color_dialog = QColorDialog(self)
        color_dialog.setWindowTitle("Choose New Thread Color")
        if color_dialog.exec() == QColorDialog.Accepted:
            selected_qcolor = color_dialog.selectedColor()
            
            # Create a new pyembroidery.EmbThread object
            new_emb_thread = pyembroidery.EmbThread()
            new_emb_thread.red = selected_qcolor.red()
            new_emb_thread.green = selected_qcolor.green()
            new_emb_thread.blue = selected_qcolor.blue()
            new_emb_thread.name = f"Custom Thread {self.next_custom_thread_id}"
            self.next_custom_thread_id += 1
            
            # Add to the pattern's thread list
            self.emb_pattern.thread_list.append(new_emb_thread)
            
            # Update the QListWidget
            self.populate_thread_list()
            
            # Select the newly added item
            self.thread_list_widget.setCurrentRow(self.thread_list_widget.count() - 1)
            print(f"Added new embroidery thread: {new_emb_thread.name} {selected_qcolor.getRgb()}")
        else:
            print("Thread color selection cancelled.")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    main_window = QMainWindow()
    embroidery_thread_list_widget = EmbroideryThreadListWidget()
    main_window.setCentralWidget(embroidery_thread_list_widget)
    main_window.setWindowTitle("PySide6 Embroidery Thread Manager")
    main_window.setMinimumSize(450, 400)
    
    main_window.show()
    sys.exit(app.exec())
