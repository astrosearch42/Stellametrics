import os
import sys
import glob
import json
import traceback
from pathlib import Path
import webbrowser
import tempfile  # Ajouté pour le chemin temporaire

import numpy as np
import pyqtgraph as pg
from astropy.io import fits
from PIL import Image, ImageOps
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontDatabase, QPen, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QGraphicsDropShadowEffect,
    QGraphicsLineItem,
    QGraphicsPixmapItem
)
from skyfield.api import load

version= "1.0.0"  # Application version in MAJOR.MINOR.PATCH format

# Set environment variables for high DPI scaling
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
os.environ["QT_SCALE_FACTOR"] = "1"
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"

# Root directory (the folder containing 'Main', 'Library', etc.)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller case
        base_path = sys._MEIPASS
    else:
        base_path = PROJECT_ROOT
    return os.path.join(base_path, relative_path)

class CustomToolTipButton(QtWidgets.QPushButton):
    def __init__(self, text='', tooltip='', parent=None):
        super().__init__(text, parent)
        self._tooltip_text = tooltip
        self._tooltip_label = None

    def enterEvent(self, event):
        if self._tooltip_text:
            if not self._tooltip_label:
                self._tooltip_label = QtWidgets.QLabel(self._tooltip_text, self.window())
                self._tooltip_label.setWindowFlags(Qt.ToolTip)
                self._tooltip_label.setObjectName("InstantToolTip")
            pos = self.mapToGlobal(self.rect().bottomLeft())
            self._tooltip_label.move(pos.x(), pos.y())
            self._tooltip_label.adjustSize()
            self._tooltip_label.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self._tooltip_label:
            self._tooltip_label.hide()
        super().leaveEvent(event)

class CustomTitleBar(QtWidgets.QWidget):
    theme_changed = QtCore.pyqtSignal(str)  # Signal to notify theme change
    def __init__(self, parent=None, icon_path=None, title="Stellametrics", theme_names=None, current_theme=None):
        super().__init__(parent)
        self.setObjectName("CustomTitleBar")
        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self.setFixedHeight(60)
        self.parent = parent
        self.icon_path = icon_path
        self.title = title

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(15)
        # Icon
        self.icon_label = QtWidgets.QLabel()
        if icon_path:
            self.icon_label.setPixmap(QtGui.QPixmap(icon_path).scaled(24, 24, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
        layout.addWidget(self.icon_label)
        # Title
        self.title_label = QtWidgets.QLabel(self.title)
        layout.addWidget(self.title_label)
        # Add theme selector
        if theme_names:
            self.theme_combo = QtWidgets.QComboBox()
            self.theme_combo.setObjectName("theme_combo")
            self.theme_combo.addItems(theme_names)
            if current_theme and current_theme in theme_names:
                self.theme_combo.setCurrentText(current_theme)
            self.theme_combo.setFixedWidth(340)
            self.theme_combo.setToolTip("Change the application theme")
            self.theme_combo.currentTextChanged.connect(self.on_theme_changed)
            layout.addWidget(self.theme_combo)
        layout.addStretch(5)

        self.version_label = self.findChild(QtWidgets.QLabel, "version_label")
        # Hide the left panel at startup
        if self.version_label:
            self.version_label.setText(f"Version: {version}")

        # Minimize
        self.min_btn = QtWidgets.QPushButton("–")
        self.min_btn.setObjectName("minimizeButton")
        self.min_btn.setFixedSize(28, 28)
        self.min_btn.clicked.connect(self.on_minimize)
        layout.addWidget(self.min_btn)
        # Maximize/Restore
        self.max_btn = QtWidgets.QPushButton("□")
        self.max_btn.setObjectName("maximizeButton")
        self.max_btn.setFixedSize(28, 28)
        self.max_btn.clicked.connect(self.on_max_restore)
        layout.addWidget(self.max_btn)
        # Close
        self.close_btn = QtWidgets.QPushButton("✕")
        self.close_btn.setObjectName("closeButton")
        self.close_btn.setFixedSize(28, 28)
        self.close_btn.clicked.connect(self.on_close)
        layout.addWidget(self.close_btn)
        self._drag_pos = None
        self._is_maximized = False


    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.parent.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() == QtCore.Qt.LeftButton:
            self.parent.move(event.globalPos() - self._drag_pos)
            event.accept()

    def mouseDoubleClickEvent(self, event):
        self.on_max_restore()

    def on_minimize(self):
        self.parent.showMinimized()

    def on_max_restore(self):
        if self.parent.isMaximized() or self._is_maximized:
            self.parent.showNormal()
            self._is_maximized = False
        else:
            self.parent.showMaximized()
            self._is_maximized = True

    def on_close(self):
        self.parent.close()

    def on_theme_changed(self, theme_name):
        self.theme_changed.emit(theme_name)

class ImageViewer(QtWidgets.QWidget):
    CONFIG_DIR = os.path.join(PROJECT_ROOT, "Stellametrics_Config")
    LAST_IMAGE_PATH_FILE = os.path.join(CONFIG_DIR, "Stellametrics_last_image.txt")
    LAST_PRESET_PATH_FILE = os.path.join(CONFIG_DIR, "Stellametrics_last_preset.txt")


    def __init__(self):
        # Forcer le support du scaling DPI (avant QApplication si possible)
        QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
        QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)
        super().__init__()
        # Fix UI file path
        uic.loadUi(resource_path(os.path.join("Main", "ImageViewer.ui")), self)
        self.setWindowTitle("Stellametrics")

        # Redimensionner la fenêtre selon la taille de l'écran (80% de la taille)
        screen = QtWidgets.QApplication.primaryScreen()
        size = screen.size()
        self.resize(int(size.width() * 0.8), int(size.height() * 0.8))
        self.move(int(size.width() * 0.1), int(size.height() * 0.1))

        # Forcer la police à s'adapter au DPI
        font = self.font()
        font.setPointSizeF(font.pointSizeF() * (self.logicalDpiY() / 96.0))
        self.setFont(font)

        # Initialize instance variables
        self.segment_mode = False
        self.segment_points = []
        self.segment_line = None
        self.temp_line = None
        self.last_segment_length_px = None
        self.object_items = []
        self.original_img = None
        self.current_img = None
        self.rotation_count = 0
        self.distance_library = []
        self.object_dict = {
            "France": {"image": resource_path(os.path.join("Assets", "Add_Objects", "france.png")), "diameter": 975, "min_km": 10, "max_km": 10000},
            "USA": {"image": resource_path(os.path.join("Assets", "Add_Objects", "usa.png")), "diameter": 4500, "min_km": 100, "max_km": 20000},
            "Earth": {"image": resource_path(os.path.join("Assets", "Add_Objects", "earth.png")), "diameter": 12742, "min_km": 100, "max_km": 2e6},
            "Jupiter": {"image": resource_path(os.path.join("Assets", "Add_Objects", "jupiter.png")), "diameter": 139822, "min_km": 1000, "max_km": 1e8},
        }
        self.last_image_path = self.load_last_image_path() or ""
        self.last_preset_path = self.load_last_preset_path() or ""
        # Load the distance library at startup
        self.load_distance_library()
        # Move loading after all widget initializations

        # Imposer la date d'aujourd'hui dans le QDateEdit skyfield_date_edit
        if hasattr(self, 'skyfield_date_edit'):
            self.skyfield_date_edit.setDate(QtCore.QDate.currentDate())

        # Add pyqtgraph widget to the right panel
        self.graphics_widget = pg.GraphicsLayoutWidget()
        self.graphics_widget.setObjectName("ImageArea")
        self.img_view = self.graphics_widget.addViewBox()
        self.img_item = pg.ImageItem()
        self.img_view.addItem(self.img_item)
        self.img_view.setAspectLocked(True)
        # Synchronize the background color of the image area with the widget background
        bg_color = self.graphics_widget.palette().color(QtGui.QPalette.Window)
        self.img_view.setBackgroundColor(bg_color)
        # Set the background color of the graphics widget to match the widget background
        self.graphics_widget.setBackground(bg_color)
        self.img_view.scene().sigMouseMoved.connect(self.update_mouse_coords)
        self.img_view.scene().installEventFilter(self)
        # Add the pyqtgraph widget to the rightPanel layout
        right_panel = self.findChild(QtWidgets.QWidget, "rightPanel")
        right_layout = right_panel.layout() if right_panel is not None else None
        # Remove the image QLabel if present
        image_label = self.findChild(QtWidgets.QLabel, "image_label")
        if image_label is not None and right_layout is not None:
            right_layout.removeWidget(image_label)
            image_label.deleteLater()
        if right_layout is not None:
            right_layout.addWidget(self.graphics_widget)

        # Add the coordinates label on the pyqtgraph widget
        self.coord_label = QtWidgets.QLabel("X: -, Y: -", self.graphics_widget)
        self.coord_label.setStyleSheet("background: #222; color: #fff; padding: 4px; border-radius: 6px;")
        self.coord_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.coord_label.setFixedWidth(150)
        self.coord_label.setFixedHeight(28)
        self.coord_label.move(20, 20)
        self.coord_label.raise_()
        self.graphics_widget.setMouseTracking(True)
        self.graphics_widget.installEventFilter(self)

        # Set the initial size of the splitter
        main_splitter = self.findChild(QtWidgets.QSplitter, "mainSplitter")
        if main_splitter:
            main_splitter.setSizes([500, 1000])  

        # Get the title bar and connect the toggle button
        self.title_bar = self.findChild(QtWidgets.QWidget, "CustomTitleBar")
        # Update the version label if present
        if self.title_bar:
            version_label = self.title_bar.findChild(QtWidgets.QLabel, "version_label")
            if version_label:
                version_label.setText(f"Version: {version}")

        # Get the toggleLeftPanelButton from the UI
        self.toggleLeftPanelButton = self.findChild(QtWidgets.QPushButton, "toggleLeftPanelButton")
        # Hide the left panel at startup
        left_scroll = self.findChild(QtWidgets.QScrollArea, "leftScroll")
        if left_scroll:
            left_scroll.setVisible(False)
            if self.toggleLeftPanelButton:
                self.toggleLeftPanelButton.setText("☰")

        # Connect buttons to methods
        self.open_btn.clicked.connect(self.open_image)
        self.remove_image_btn.clicked.connect(self.remove_image)
        self.segment_btn.clicked.connect(self.toggle_segment_mode)
        self.save_btn.clicked.connect(self.save_preset)
        self.load_btn.clicked.connect(self.load_preset)
        self.calc_btn.clicked.connect(self.calculer_longueur_reelle)
        self.add_object_btn.clicked.connect(self.add_object_to_scene)
        self.clear_objects_btn.clicked.connect(self.clear_all_objects)
        self.save_object_btn.clicked.connect(self.save_image_with_object)
        self.add_distance_btn.clicked.connect(self.add_distance_to_library)
        self.remove_distance_btn.clicked.connect(self.remove_distance_from_library)
        self.distance_combo.currentIndexChanged.connect(self.select_distance_from_library)
        self.skyfield_fill_btn.clicked.connect(self.fill_distance_with_skyfield)
        self.toggleLeftPanelButton.clicked.connect(self.toggle_left_panel)
        self.link_btn.clicked.connect(lambda: webbrowser.open("https://github.com/astrosearch42"))
        self.real_length_line.setReadOnly(True)
        self.length_line.setReadOnly(True)

        ## Specific replacement of the segment_btn with a custom tooltip button
        # Fix the segment_btn
        segment_btn_new = self.findChild(QtWidgets.QPushButton, "segment_btn")
        if segment_btn_new:
            tooltip = "Draw a segment to measure real length by clicking and dragging on the image"
            new_btn = CustomToolTipButton(segment_btn_new.text(), tooltip, self)
            new_btn.setCheckable(segment_btn_new.isCheckable())
            new_btn.setChecked(segment_btn_new.isChecked())
            setattr(self, "segment_btn", new_btn)
            layout = segment_btn_new.parentWidget().layout() if segment_btn_new.parentWidget() else None
            if layout:
                idx = layout.indexOf(segment_btn_new)
                layout.removeWidget(segment_btn_new)
                segment_btn_new.deleteLater()
                layout.insertWidget(idx, new_btn)
            # Reconnecte le bon signal
            if new_btn.isCheckable():
                new_btn.toggled.connect(self.toggle_segment_mode)
            else:
                new_btn.clicked.connect(self.toggle_segment_mode)
            # Set a new object name for the segment button
            new_btn.setObjectName("segment_btn_custom")
        # Link to the repository
        link_btn = self.findChild(QtWidgets.QPushButton, "link_btn")
        if link_btn:
            tooltip = "Visit the project repository"
            new_link_btn = CustomToolTipButton(link_btn.text(), tooltip, self)
            new_link_btn.setObjectName("link_btn")
            layout = link_btn.parentWidget().layout() if link_btn.parentWidget() else None
            if layout:
                idx = layout.indexOf(link_btn)
                layout.removeWidget(link_btn)
                link_btn.deleteLater()
                layout.insertWidget(idx, new_link_btn)
            setattr(self, "link_btn", new_link_btn)
            # Reconnecte le bon signal
            new_link_btn.clicked.connect(lambda: webbrowser.open("https://github.com/astrosearch42"))
        # Add a new distance
        add_distance_btn = self.findChild(QtWidgets.QPushButton, "add_distance_btn")
        if add_distance_btn:
            tooltip = "Add a new distance measurement to the library"
            new_add_distance_btn = CustomToolTipButton(add_distance_btn.text(), tooltip, self)
            new_add_distance_btn.setObjectName("add_distance_btn")
            layout = add_distance_btn.parentWidget().layout() if add_distance_btn.parentWidget() else None
            if layout:
                idx = layout.indexOf(add_distance_btn)
                layout.removeWidget(add_distance_btn)
                add_distance_btn.deleteLater()
                # Fix for QFormLayout
                if isinstance(layout, QtWidgets.QFormLayout):
                    # Find the row containing the widget
                    for row in range(layout.rowCount()):
                        if layout.itemAt(row, QtWidgets.QFormLayout.FieldRole) and layout.itemAt(row, QtWidgets.QFormLayout.FieldRole).widget() is None:
                            continue
                        if layout.itemAt(row, QtWidgets.QFormLayout.FieldRole) and layout.itemAt(row, QtWidgets.QFormLayout.FieldRole).widget() == new_add_distance_btn:
                            break
                        if layout.itemAt(row, QtWidgets.QFormLayout.FieldRole) and layout.itemAt(row, QtWidgets.QFormLayout.FieldRole).widget() == add_distance_btn:
                            label_item = layout.itemAt(row, QtWidgets.QFormLayout.LabelRole)
                            label_widget = label_item.widget() if label_item else None
                            layout.removeRow(row)
                            layout.insertRow(row, label_widget, new_add_distance_btn)
                            break
                    else:
                        layout.addRow(new_add_distance_btn)
                else:
                    layout.insertWidget(idx, new_add_distance_btn)
            setattr(self, "add_distance_btn", new_add_distance_btn)
            # Reconnecte le bon signal
            new_add_distance_btn.clicked.connect(self.add_distance_to_library)
        # Remove a distance
        remove_distance_btn = self.findChild(QtWidgets.QPushButton, "remove_distance_btn")
        if remove_distance_btn:
            tooltip = "Remove a distance measurement from the library"
            new_remove_distance_btn = CustomToolTipButton(remove_distance_btn.text(), tooltip, self)
            new_remove_distance_btn.setObjectName("remove_distance_btn")
            layout = remove_distance_btn.parentWidget().layout() if remove_distance_btn.parentWidget() else None
            if layout:
                idx = layout.indexOf(remove_distance_btn)
                layout.removeWidget(remove_distance_btn)
                remove_distance_btn.deleteLater()
                # Fix for QFormLayout
                if isinstance(layout, QtWidgets.QFormLayout):
                    for row in range(layout.rowCount()):
                        if layout.itemAt(row, QtWidgets.QFormLayout.FieldRole) and layout.itemAt(row, QtWidgets.QFormLayout.FieldRole).widget() is None:
                            continue
                        if layout.itemAt(row, QtWidgets.QFormLayout.FieldRole) and layout.itemAt(row, QtWidgets.QFormLayout.FieldRole).widget() == new_remove_distance_btn:
                            break
                        if layout.itemAt(row, QtWidgets.QFormLayout.FieldRole) and layout.itemAt(row, QtWidgets.QFormLayout.FieldRole).widget() == remove_distance_btn:
                            label_item = layout.itemAt(row, QtWidgets.QFormLayout.LabelRole)
                            label_widget = label_item.widget() if label_item else None
                            layout.removeRow(row)
                            layout.insertRow(row, label_widget, new_remove_distance_btn)
                            break
                    else:
                        layout.addRow(new_remove_distance_btn)
                else:
                    layout.insertWidget(idx, new_remove_distance_btn)
            setattr(self, "remove_distance_btn", new_remove_distance_btn)
            # Reconnecte le bon signal
            new_remove_distance_btn.clicked.connect(self.remove_distance_from_library)
        
        # Now load preset and image after all widgets are initialized
        self.load_last_preset()
        self.load_last_image()
        self.update_graphics_background()
        # Block value change of QComboBox with the mouse wheel
        for combo in self.findChildren(QtWidgets.QComboBox):
            combo.wheelEvent = lambda event: None

    def toggle_left_panel(self):
        left_scroll = self.findChild(QtWidgets.QScrollArea, "leftScroll")
        if left_scroll:
            left_scroll.setVisible(not left_scroll.isVisible())
            # Change le texte du bouton selon l'état
            if left_scroll.isVisible():
                self.toggleLeftPanelButton.setText("☰") #⯇
            else:
                self.toggleLeftPanelButton.setText("☰") #⯈

            # Réapplique les tailles min/max des widgets du layout
            object_distance = self.findChild(QtWidgets.QLineEdit, "object_distance")
            distance_unit = self.findChild(QtWidgets.QComboBox, "distance_unit")
            distance_combo = self.findChild(QtWidgets.QComboBox, "distance_combo")
            if object_distance:
                object_distance.setMinimumWidth(115)
                object_distance.setMaximumWidth(115)
                object_distance.setMinimumHeight(38)
                object_distance.setMaximumHeight(38)
            if distance_unit:
                distance_unit.setMinimumWidth(70)
                distance_unit.setMaximumWidth(70)
                distance_unit.setMinimumHeight(27)
                distance_unit.setMaximumHeight(27)
            if distance_combo:
                distance_combo.setMinimumWidth(130)
                distance_combo.setMaximumWidth(130)
                distance_combo.setMinimumHeight(27)
                distance_combo.setMaximumHeight(27)
            

        # Ajout de marge dans le leftPanel
        left_Layout = self.findChild(QtWidgets.QWidget, "leftLayout")
        if left_Layout:
            layout = left_Layout.layout()
            if layout is None:
                layout = QtWidgets.QVBoxLayout(left_Layout)
                left_Layout.setLayout(layout)
            layout.setContentsMargins(10, 10, 10, 10)
            layout.setSpacing(12)  # Espacement entre widgets
        # Ajout d'un spacing haut et bas dans le leftPanel
        save_object_btn = self.findChild(QtWidgets.QPushButton, "save_object_btn")
        if save_object_btn:
            save_object_btn.setStyleSheet("margin-bottom: 8px; margin-left: 6px; margin-right: 6px;")
        # Ajout d'un spacing droite et gauche à tous les élements du leftPanel
        for element in self.findChildren((QtWidgets.QPushButton, QtWidgets.QLabel, QtWidgets.QGroupBox, QtWidgets.QComboBox, QtWidgets.QLineEdit, QtWidgets.QDateEdit)):
            # N'applique pas la marge aux boutons save_object_btn et load_preset_btn
            if element is save_object_btn:
                continue
            if isinstance(element, QtWidgets.QPushButton):
                element.setStyleSheet("margin-left: 6px; margin-right: 6px;")
            elif isinstance(element, QtWidgets.QLabel):
                element.setStyleSheet("margin-left: 6px; margin-right: 6px;")
            elif isinstance(element, QtWidgets.QGroupBox):
                element.setStyleSheet("margin-left: 6px; margin-right: 6px;")
            elif isinstance(element, QtWidgets.QComboBox):
                element.setStyleSheet("margin-left: 6px; margin-right: 6px;")
            elif isinstance(element, QtWidgets.QLineEdit):
                element.setStyleSheet("margin-left: 6px; margin-right: 6px;")
            elif isinstance(element, QtWidgets.QDateEdit):
                element.setStyleSheet("margin-left: 6px; margin-right: 6px;")
        # Ajoute un Spacing aux QLabel titres de groupbox
        groupbox_ = [
            "telescope_group",
            "barlow_group",
            "camera_group",
            "distance_group",
            "skyfield_group"
        ]
        for gb_name in groupbox_:
            groupbox = self.findChild(QtWidgets.QGroupBox, gb_name)
            if groupbox:
                layout = groupbox.layout()
                if layout:
                    l, t, r, b = layout.contentsMargins().left(), layout.contentsMargins().top(), layout.contentsMargins().right(), layout.contentsMargins().bottom()
                    layout.setContentsMargins(l, 2, r, b)

        # Barlow/reducer UI
        def on_barlow_checked(state):
            if state == QtCore.Qt.Checked:
                self.barlow_value_label.show()
                self.barlow_value_edit.show()
            else:
                self.barlow_value_label.hide()
                self.barlow_value_edit.hide()
        self.barlow_checkbox.stateChanged.connect(on_barlow_checked)
        self.barlow_value_label.hide()
        self.barlow_value_edit.hide()

        # --- Correction responsive boutons leftPanel ---
        left_panel = self.findChild(QtWidgets.QWidget, "leftPanel")
        if left_panel:
            left_panel.setMinimumSize(0, 0)
            # Correction clé : forcer le leftPanel à suivre la largeur du scroll area
            left_panel.setSizePolicy(QtWidgets.QSizePolicy.Ignored, left_panel.sizePolicy().verticalPolicy())
            # Tip: QSizePolicy.Ignored forces the widget to always take the width imposed by its parent (splitter/scroll area),
            # which ensures it compresses perfectly with no horizontal scroll or overlap, even when reduced to the minimum.

            layout = left_panel.layout()
            if layout:
                layout.setContentsMargins(2, 2, 2, 2)
                
            for child in left_panel.findChildren((QtWidgets.QPushButton, QtWidgets.QLabel, QtWidgets.QGroupBox, QtWidgets.QComboBox, QtWidgets.QLineEdit, QtWidgets.QDateEdit)):
                child.setSizePolicy(QtWidgets.QSizePolicy.Expanding, child.sizePolicy().verticalPolicy())
                child.setMinimumWidth(0)
                child.setMaximumWidth(16777215)
            splitter = left_panel.parent()
            if isinstance(splitter, QtWidgets.QSplitter):
                index = splitter.indexOf(left_panel)
                splitter.setCollapsible(index, True)



##################################################################################################################

        self.apply_button_effects()
    def apply_button_effects(self):
        def set_shadow_color(btn, color):
            effect = btn.graphicsEffect()
            if isinstance(effect, QGraphicsDropShadowEffect):
                effect.setColor(QtGui.QColor(color))

        # Determine the shadow color according to the theme
        theme_name = getattr(self, 'current_theme', None)
        if theme_name is None:
            # Essaye de récupérer depuis la combo
            combo = self.findChild(QtWidgets.QComboBox, "theme_combo")
            if combo:
                theme_name = combo.currentText().lower()
        # Colors by theme
        theme_shadow_colors = {
            "dark": ("#2663eb", "#7700ff"),
            "light": ("#5A384F", "#7700ff"),
        }
        normal_color, pressed_color = theme_shadow_colors.get(theme_name, ("#2663eb", "#7700ff"))

        for btn in self.findChildren(QtWidgets.QPushButton):
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(18)
            shadow.setColor(QtGui.QColor(normal_color))
            shadow.setOffset(0, 4)
            btn.setGraphicsEffect(shadow)
            if btn.isCheckable():
                def on_toggle(checked, b=btn):
                    set_shadow_color(b, pressed_color if checked else normal_color)
                btn.toggled.connect(on_toggle)
            else:
                btn.pressed.connect(lambda b=btn: set_shadow_color(b, pressed_color))
                btn.released.connect(lambda b=btn: set_shadow_color(b, normal_color))

##################################################################################################################
    def update_mouse_coords(self, pos):
        # Display the mouse coordinates in the view
        mouse_point = self.img_view.mapSceneToView(pos)
        x = mouse_point.x()
        y = mouse_point.y()
        self.coord_label.setText(f"X: {x:.1f}, Y: {y:.1f}")
        self.coord_label.move(self.graphics_widget.width() - self.coord_label.width() - 10, self.graphics_widget.height() - self.coord_label.height() - 10)
    
    def eventFilter(self, obj, event):
        # Display coordinates if the mouse moves on the view OR on the scene
        if (obj is self.graphics_widget or obj is self.img_view.scene()) and event.type() == QtCore.QEvent.MouseMove:
            if hasattr(event, "scenePos"):
                pos = event.scenePos()
            else:
                pos = self.img_view.mapToScene(event.pos())
            mouse_point = self.img_view.mapSceneToView(pos)
            x = mouse_point.x()
            y = mouse_point.y()
            self.coord_label.setText(f"X: {x:.1f}, Y: {y:.1f}")
            self.coord_label.move(self.graphics_widget.width() - self.coord_label.width() - 10, self.graphics_widget.height() - self.coord_label.height() - 10)
        return super().eventFilter(obj, event)
    
    def calculer_longueur_reelle(self):
        try:
            D = float(self.object_distance.text().replace(",", "."))
            unit = self.distance_unit.currentText()
            if self.segment_line is not None:
                line = self.segment_line.line()
                x1, y1, x2, y2 = line.x1(), line.y1(), line.x2(), line.y2()
                N = np.hypot(x2 - x1, y2 - y1)
            elif self.last_segment_length_px is not None:
                N = self.last_segment_length_px
            else:
                raise ValueError("No segment drawn.")
            p = float(self.camera_pixel_size.text().replace(",", "."))
            f = float(self.telescope_focal.text().replace(",", "."))
            barlow = float(self.barlow_value_edit.text().replace(",", ".")) if self.barlow_checkbox.isChecked() and self.barlow_value_edit.text() else 1.0
            f_total = f * barlow
            p_mm = p * 0.001
            angle_rad = N * p_mm / f_total

            # Calculation in the input unit
            real_length = D * angle_rad

            # Display in the same unit as input
            if unit == "ly":
                self.real_length_line.setText(f"Real object length: {real_length:.4f} ly")
            elif unit == "pc":
                self.real_length_line.setText(f"Real object length: {real_length:.4f} pc")
            elif unit == "kpc":
                # Affiche en Mpc si > 1e3 kpc, sinon en kpc
                if real_length >= 1e3:
                    real_length_mpc = real_length / 1e3
                    self.real_length_line.setText(f"Real object length: {real_length_mpc:.4f} Mpc")
                else:
                    self.real_length_line.setText(f"Real object length: {real_length:.4f} kpc")
            elif unit == "Mpc":
                # Affiche en kpc si < 1 Mpc, sinon en Mpc
                if real_length < 1:
                    real_length_kpc = real_length * 1e3
                    self.real_length_line.setText(f"Real object length: {real_length_kpc:.4f} kpc")
                else:
                    self.real_length_line.setText(f"Real object length: {real_length:.4f} Mpc")
            else:  # km
                if real_length > 1e9:
                    light_year = 9.461e12
                    real_length_ly = real_length / light_year
                    self.real_length_line.setText(f"Real object length: {real_length_ly:.4f} ly")
                else:
                    self.real_length_line.setText(f"Real object length: {real_length:.2f} km")
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", f"Unable to calculate real length:\n{e}")
        self.update_object_selector()

    def save_preset(self):
        data = {
            "telescope_name": self.telescope_name.text(),
            "telescope_diameter": self.telescope_diameter.text(),
            "telescope_focal": self.telescope_focal.text(),
            "barlow_checked": self.barlow_checkbox.isChecked(),
            "barlow_value": self.barlow_value_edit.text(),
            "camera_pixel_size": self.camera_pixel_size.text(),
        }
        # Récupère le nom du télescope juste avant l'enregistrement
        default_name = self.telescope_name.text().strip() or "default"
        # Save preset directly in the user's Documents folder
        documents_dir = str(Path.home() / "Documents")
        default_path = os.path.join(documents_dir, f"preset_{default_name}.json")
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save preset",
            default_path,
            "Presets JSON (*.json);;All files (*)"
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception as e:
            raise Exception(f"Preset save error: {e}")
        self.last_preset_path = path
        self.save_last_preset_path(path)

    def get_preset_path(self):
        name = self.telescope_name.text().strip() or "default"
        preset_dir = resource_path("Preset")
        os.makedirs(preset_dir, exist_ok=True)
        return os.path.join(preset_dir, f"preset_{name}.json")

    def load_last_preset_path(self):
        try:
            if os.path.exists(self.LAST_PRESET_PATH_FILE):
                with open(self.LAST_PRESET_PATH_FILE, "r", encoding="utf-8") as f:
                    path = f.read().strip()
                    if path:
                        return path
        except Exception as e:
            print(f"Error while loading preset path: {e}")
        return ""

    def load_last_preset(self):
        path = self.last_preset_path
        if not path or not os.path.exists(path):
            # Fallback : preset par défaut dans le dossier du script
            name = self.telescope_name.text().strip() or "default"
            path = resource_path(f"preset_{name}.json")
            if not os.path.exists(path):
                return
            self.last_preset_path = path
            self.save_last_preset_path(path)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.telescope_name.setText(data.get("telescope_name", ""))
            self.telescope_diameter.setText(data.get("telescope_diameter", ""))
            self.telescope_focal.setText(data.get("telescope_focal", ""))
            self.barlow_checkbox.setChecked(data.get("barlow_checked", False))
            self.barlow_value_edit.setText(data.get("barlow_value", ""))
            self.camera_pixel_size.setText(data.get("camera_pixel_size", ""))
        except Exception as e:
            pass

    def load_preset(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Load preset",
            self.last_preset_path or str(Path(__file__).parent),
            "Presets JSON (*.json);;All files (*)"
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.telescope_name.setText(data.get("telescope_name", ""))
            self.telescope_diameter.setText(data.get("telescope_diameter", ""))
            self.telescope_focal.setText(data.get("telescope_focal", ""))
            self.barlow_checkbox.setChecked(data.get("barlow_checked", False))
            self.barlow_value_edit.setText(data.get("barlow_value", ""))
            self.camera_pixel_size.setText(data.get("camera_pixel_size", ""))
            self.last_preset_path = path
            self.save_last_preset_path(path)
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", f"Unable to load preset:\n{e}")

    def save_last_preset_name(self):
        self.last_preset_path = self.get_preset_path()

    def closeEvent(self, event):
        # Sauvegarde du thème courant à la fermeture (robuste)
        try:
            theme_name = None
            # 1. Essayer via self.title_bar.theme_combo
            if hasattr(self, "title_bar") and hasattr(self.title_bar, "theme_combo"):
                theme_name = self.title_bar.theme_combo.currentText()
            # 2. Sinon, chercher le QComboBox par nom d'objet dans toute la fenêtre
            if theme_name is None or not theme_name:
                combo = self.findChild(QtWidgets.QComboBox, "theme_combo")
                if combo:
                    theme_name = combo.currentText()
            # 3. Sauvegarder si trouvé
            if theme_name:
                save_last_theme(theme_name)
            else:
                pass
        except Exception as e:
            raise Exception(f"Theme save error: {e}")
        event.accept()

    def open_image(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open image", self.last_image_path or "",
            "Images (*.fits *.tif *.tiff *.jpg *.jpeg *.png *.bmp *.gif *.webp);;All files (*)"
        )
        if not path:
            return
        if path.lower().endswith('.fits'):
            with fits.open(path) as hdul:
                data = hdul[0].data
            if data.ndim == 3:
                if data.shape[0] == 3:
                    data = np.moveaxis(data, 0, -1)
                elif data.shape[2] == 3:
                    pass
                else:
                    data = data[0]
            if data.ndim == 3 and data.shape[2] == 3:
                img = np.zeros_like(data, dtype=np.float32)
                for i in range(3):
                    channel = data[..., i]
                    img[..., i] = (channel - np.nanmin(channel)) / (np.nanmax(channel) - np.nanmin(channel) + 1e-8)
            else:
                data = data.astype(np.float32)
                img = (data - np.nanmin(data)) / (np.nanmax(data) - np.nanmin(data) + 1e-8)
            # Imposer +90° droite
            img = np.rot90(img, k=-1)
        else:
            try:
                pil_img = Image.open(path)
                pil_img = ImageOps.exif_transpose(pil_img)
                pil_img = pil_img.transpose(Image.ROTATE_270)
                if pil_img.mode in ("RGB", "RGBA", "P"):
                    img = np.array(pil_img.convert("RGB")).astype(np.float32) / 255.0
                else:
                    img = np.array(pil_img.convert("L")).astype(np.float32) / 255.0
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Error", f"Unable to open image:\n{e}")
                return
        self.original_img = img.copy()
        self.current_img = img
        self.img_item.setImage(self.current_img, autoLevels=True)
        self.img_view.setAspectLocked(True)
        self.img_view.autoRange()
        # Ouvre le panneau gauche si une image est chargée
        left_scroll = self.findChild(QtWidgets.QScrollArea, "leftScroll")
        if left_scroll:
            left_scroll.setVisible(True)
            if self.toggleLeftPanelButton:
                self.toggleLeftPanelButton.setText("☰")
        # Enregistre le chemin dans fichier
        self.last_image_path = path
        self.save_last_image_path(path)

    def remove_image(self):
        self.original_img = None
        self.current_img = None
        self.img_item.clear()
        self.img_view.autoRange()
        self.last_image_path = ""
        self.save_last_image_path(self.last_image_path)

    def load_last_image(self):
        if self.last_image_path and os.path.exists(self.last_image_path):
            try:
                self.open_image_from_path(self.last_image_path)
                pass
            except Exception as e:
                pass
        else:
            pass


    def open_image_from_path(self, path):
        if not path:
            return
        if not os.path.exists(path):
            return
        if path.lower().endswith('.fits'):
            try:
                with fits.open(path) as hdul:
                    data = hdul[0].data
                if data.ndim == 3:
                    if data.shape[0] == 3:
                        data = np.moveaxis(data, 0, -1)
                    elif data.shape[2] == 3:
                        pass
                    else:
                        data = data[0]
                if data.ndim == 3 and data.shape[2] == 3:
                    img = np.zeros_like(data, dtype=np.float32)
                    for i in range(3):
                        channel = data[..., i]
                        img[..., i] = (channel - np.nanmin(channel)) / (np.nanmax(channel) - np.nanmin(channel) + 1e-8)
                else:
                    data = data.astype(np.float32)
                    img = (data - np.nanmin(data)) / (np.nanmax(data) - np.nanmin(data) + 1e-8)
                # Imposer +90° droite
                img = np.rot90(img, k=-1)
            except Exception as e:
                raise Exception(f"Unable to open FITS image: {e}")
        else:
            try:
                pil_img = Image.open(path)
                pil_img = ImageOps.exif_transpose(pil_img)
                pil_img = pil_img.transpose(Image.ROTATE_270)  # +90° droite
                if pil_img.mode == "RGB":
                    img = np.array(pil_img).astype(np.float32) / 255.0
                else:
                    img = np.array(pil_img.convert("L")).astype(np.float32) / 255.0
            except Exception as e:
                raise Exception(f"Unable to open image: {e}")

        self.original_img = img.copy()    
        self.current_img = img
        self.img_item.setImage(self.current_img, autoLevels=True)
        self.img_view.setAspectLocked(True)  # Permet l'affichage sans forcer le carré
        self.img_view.autoRange()
        left_scroll = self.findChild(QtWidgets.QScrollArea, "leftScroll")
        if left_scroll:
            left_scroll.setVisible(True)
            if self.toggleLeftPanelButton:
                self.toggleLeftPanelButton.setText("☰")

    def toggle_segment_mode(self):
        self.segment_mode = self.segment_btn.isChecked()
        self.segment_points = []
        if self.segment_line:
            self.img_view.removeItem(self.segment_line)
            self.segment_line = None
        if self.segment_mode:
            self.img_view.scene().sigMouseClicked.connect(self.on_segment_click)
            self.img_view.scene().sigMouseMoved.connect(self.on_segment_move)
        else:
            try:
                self.img_view.scene().sigMouseClicked.disconnect(self.on_segment_click)
            except Exception:
                pass
            try:
                self.img_view.scene().sigMouseMoved.disconnect(self.on_segment_move)
            except Exception:
                pass

    def on_segment_click(self, event):
        if not self.segment_mode:
            return
        pos = event.scenePos()
        mouse_point = self.img_view.mapSceneToView(pos)
        x, y = mouse_point.x(), mouse_point.y()
        self.segment_points.append((x, y))
        if len(self.segment_points) == 1:
            # First click: create temporary line
            if self.temp_line:
                self.img_view.removeItem(self.temp_line)
            pen = QPen(Qt.red, 2)
            self.temp_line = QGraphicsLineItem()
            self.temp_line.setPen(pen)
            self.img_view.addItem(self.temp_line)
        elif len(self.segment_points) == 2:
            # Second click: finalize segment, show distance
            x1, y1 = self.segment_points[0]
            x2, y2 = self.segment_points[1]
            if self.temp_line:
                self.img_view.removeItem(self.temp_line)
                self.temp_line = None
            pen = QPen(Qt.red, 2)
            self.segment_line = QGraphicsLineItem()
            self.segment_line.setPen(pen)
            self.segment_line.setLine(x1, y1, x2, y2)
            self.img_view.addItem(self.segment_line)
            dist = np.hypot(x2 - x1, y2 - y1)
            self.length_line.setText(f"Segment length: {dist:.2f} px\n")
            self.last_segment_length_px = dist
            self.segment_points = []
            self.segment_btn.setChecked(False)
            self.toggle_segment_mode()

    def on_segment_move(self, pos):
        if self.segment_mode and len(self.segment_points) == 1 and self.temp_line:
            mouse_point = self.img_view.mapSceneToView(pos)
            x0, y0 = self.segment_points[0]
            x1, y1 = mouse_point.x(), mouse_point.y()
            self.temp_line.setLine(x0, y0, x1, y1)

    def add_object_to_scene(self):
        obj_name = self.object_selector.currentText()
        obj_info = self.object_dict[obj_name]
        obj_path = obj_info["image"]
        pixmap = QPixmap(obj_path)
        if pixmap.isNull():
            QtWidgets.QMessageBox.warning(self, "Error", f"Could not load {obj_info['image']}")
            return
        obj_diameter_km = obj_info["diameter"]
        if self.last_segment_length_px is None:
            QtWidgets.QMessageBox.warning(self, "Error", "Draw a segment first to set the scale.")
            return
        # Recalcule la taille réelle du segment en km
        D = float(self.object_distance.text().replace(",", "."))
        unit = self.distance_unit.currentText()
        if unit == "km":
            D_km = D
        elif unit == "ly":
            D_km = D * 9.461e12
        elif unit == "pc":
            D_km = D * 3.086e13
        elif unit == "kpc":
            D_km = D * 3.086e16
        elif unit == "Mpc":
            D_km = D * 3.086e19
        else:
            D_km = D
        p = float(self.camera_pixel_size.text().replace(",", "."))
        f = float(self.telescope_focal.text().replace(",", "."))
        barlow = float(self.barlow_value_edit.text().replace(",", ".")) if self.barlow_checkbox.isChecked() and self.barlow_value_edit.text() else 1.0
        f_total = f * barlow
        p_mm = p * 0.001
        N = self.last_segment_length_px
        angle_rad = N * p_mm / f_total
        real_length_km = D_km * angle_rad
        px_per_km = N / real_length_km
        # Pour l'ISS, on utilise le plus grand côté comme référence pour le diamètre
        if obj_name == "ISS":
            max_side = max(pixmap.width(), pixmap.height())
            scale_factor = (obj_diameter_km * px_per_km) / max_side
            scaled_pixmap = pixmap.scaled(int(pixmap.width() * scale_factor), int(pixmap.height() * scale_factor), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            obj_px = max(scaled_pixmap.width(), scaled_pixmap.height())
        else:
            obj_px = obj_diameter_km * px_per_km
            scaled_pixmap = pixmap.scaledToWidth(int(obj_px), Qt.SmoothTransformation)
        # Applique un miroir horizontal puis une rotation de 180°
        mirrored_pixmap = scaled_pixmap.transformed(QtGui.QTransform().scale(-1, 1))
        final_pixmap = mirrored_pixmap.transformed(QtGui.QTransform().rotate(180), Qt.SmoothTransformation)
        item = QGraphicsPixmapItem(final_pixmap)
        item.setZValue(10)
        item.setFlag(QGraphicsPixmapItem.ItemIsMovable, True)
        # Place l'objet au centre de l'image
        center_x = self.img_view.viewRect().center().x() - final_pixmap.width() / 2
        center_y = self.img_view.viewRect().center().y() - final_pixmap.height() / 2
        item.setPos(center_x, center_y)
        self.img_view.addItem(item)
        self.object_items.append(item)

    def clear_all_objects(self):
        for item in self.object_items:
            self.img_view.removeItem(item)
        self.object_items.clear()

    def save_image_with_object(self):
        if self.current_img is None:
            QtWidgets.QMessageBox.warning(self, "Error", "No image loaded.")
            return
        if not self.object_items:
            QtWidgets.QMessageBox.warning(self, "Error", "No object is displayed.")
            return
        # Récupère le chemin de l'image de départ
        orig_path = self.last_image_path
        if not orig_path or not os.path.exists(orig_path):
            QtWidgets.QMessageBox.warning(self, "Error", "Could not determine original image path.")
            return
        orig_dir = os.path.dirname(orig_path)
        orig_name = os.path.splitext(os.path.basename(orig_path))[0]
        orig_ext = os.path.splitext(orig_path)[1].lower()
        if orig_ext not in [".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"]:
            orig_ext = ".png"  # fallback
        save_name = f"{orig_name}_objects_compared{orig_ext}"
        save_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save image with objects",
            os.path.join(orig_dir, save_name),
            "Images (*.png *.jpg *.jpeg *.bmp *.tif *.tiff)"
        )
        if not save_path:
            return
        # Convertit l'image numpy d'origine en QImage
        img = self.original_img
        # Applique une rotation -90° (gauche) pour la sauvegarde
        if img.ndim == 2:
            img = np.rot90(img, k=1)
            img = np.stack([img]*3, axis=-1)
        elif img.ndim == 3:
            img = np.rot90(img, k=1, axes=(0, 1))
        img_uint8 = np.clip(img * 255, 0, 255).astype(np.uint8)
        h, w, c = img_uint8.shape
        qimg = QtGui.QImage(img_uint8.tobytes(), w, h, 3*w, QtGui.QImage.Format_RGB888).copy()
        # Prépare le painter
        painter = QtGui.QPainter(qimg)
        # Dessine chaque objet à la bonne position et taille
        for item in self.object_items:
            obj_pixmap = item.pixmap()
            # Applique un miroir horizontal avant la rotation -180°
            mirrored_pixmap = obj_pixmap.transformed(QtGui.QTransform().scale(-1, 1))
            rotated_pixmap = mirrored_pixmap.transformed(QtGui.QTransform().rotate(180), Qt.SmoothTransformation)
            imgitem_pos = self.img_item.mapFromScene(item.scenePos())
            x, y = imgitem_pos.x(), imgitem_pos.y()
            x_rot = h - y - obj_pixmap.height()
            y_rot = x
            painter.drawPixmap(int(y_rot), int(x_rot), rotated_pixmap)
        painter.end()
        # Sauvegarde
        if not qimg.save(save_path):
            QtWidgets.QMessageBox.warning(self, "Error", "Failed to save image.")
        else:
            QtWidgets.QMessageBox.information(self, "Saved", f"Image saved as:\n{save_path}")

    def get_user_distance_library_path(self):
        # Place le fichier modifiable dans AppData/Local/Temp/Stellametrics/distance_library.json
        temp_dir = os.path.join(tempfile.gettempdir(), "Stellametrics")
        os.makedirs(temp_dir, exist_ok=True)
        return os.path.join(temp_dir, "distance_library.json")

    def get_default_distance_library_path(self):
        # Fichier par défaut dans le bundle
        return resource_path(os.path.join("Library", "distance_library.json"))

    def load_distance_library(self):
        self.distance_library_path = self.get_user_distance_library_path()
        # Si le fichier utilisateur n'existe pas, le copier depuis le bundle
        if not os.path.exists(self.distance_library_path):
            try:
                with open(self.get_default_distance_library_path(), "r", encoding="utf-8") as fsrc:
                    data = fsrc.read()
                with open(self.distance_library_path, "w", encoding="utf-8") as fdst:
                    fdst.write(data)
            except Exception:
                # Si la copie échoue, crée un fichier minimal
                with open(self.distance_library_path, "w", encoding="utf-8") as fdst:
                    json.dump([{"name": "Andromeda", "value": 778000, "unit": "pc"}], fdst)
        # Charger le fichier utilisateur
        try:
            with open(self.distance_library_path, "r", encoding="utf-8") as f:
                self.distance_library = json.load(f)
        except Exception:
            self.distance_library = [
                {"name": "Andromeda", "value": 778000, "unit": "pc"}
            ]
        self.distance_combo.clear()
        for d in self.distance_library:
            self.distance_combo.addItem(f"{d['name']} ({d['value']} {d['unit']})")

    def save_distance_library(self):
        try:
            with open(self.distance_library_path, "w", encoding="utf-8") as f:
                json.dump(self.distance_library, f, indent=2)
            # Affiche le chemin utilisé pour debug
            QtWidgets.QMessageBox.information(self, "Debug", f"distance_library.json enregistré dans :\n{self.distance_library_path}")
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Erreur", f"Impossible d'enregistrer la bibliothèque de distances :\n{e}\nChemin : {self.distance_library_path}")

    def select_distance_from_library(self):
        idx = self.distance_combo.currentIndex()
        if idx >= 0 and idx < len(self.distance_library):
            d = self.distance_library[idx]
            self.object_distance.setText(str(d['value']))
            self.distance_unit.setCurrentText(d['unit'])
        self.update_object_selector()

    def add_distance_to_library(self):
        name, ok = QtWidgets.QInputDialog.getText(self, "Add distance", "Name:")
        if not ok or not name.strip():
            return
        value, ok = QtWidgets.QInputDialog.getDouble(self, "Add distance", "Value:")
        if not ok:
            return
        unit, ok = QtWidgets.QInputDialog.getItem(self, "Add distance", "Unit:", ["km", "ly", "pc", "kpc", "Mpc"], 0, False)
        if not ok:
            return
        self.distance_library.append({"name": name.strip(), "value": value, "unit": unit})
        self.save_distance_library()
        self.load_distance_library()
        self.distance_combo.setCurrentIndex(len(self.distance_library)-1)
        self.update_object_selector()

    def remove_distance_from_library(self):
        idx = self.distance_combo.currentIndex()
        if idx >= 0 and idx < len(self.distance_library):
            reply = QtWidgets.QMessageBox.question(
                self,
                "Remove distance",
                f"Are you sure you want to remove the distance '{self.distance_library[idx]['name']}' from the library?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No
            )
            if reply == QtWidgets.QMessageBox.Yes:
                del self.distance_library[idx]
                self.save_distance_library()
                self.load_distance_library()

    def save_distance_library(self):
        try:
            with open(self.distance_library_path, "w", encoding="utf-8") as f:
                json.dump(self.distance_library, f, indent=2)
        except Exception:
            pass

    def update_object_selector(self):
        try:
            if self.last_segment_length_px is None:
                self.object_selector.clear()
                for name in self.object_dict:
                    self.object_selector.addItem(name)
                return
            D = float(self.object_distance.text().replace(",", "."))
            unit = self.distance_unit.currentText()
            if unit == "km":
                D_km = D
            elif unit == "ly":
                D_km = D * 9.461e12
            elif unit == "pc":
                D_km = D * 3.086e13
            elif unit == "kpc":
                D_km = D * 3.086e16
            elif unit == "Mpc":
                D_km = D * 3.086e19
            else:
                D_km = D
            p = float(self.camera_pixel_size.text().replace(",", ".")) if self.camera_pixel_size.text() else 1.0
            f = float(self.telescope_focal.text().replace(",", ".")) if self.telescope_focal.text() else 1.0
            barlow = float(self.barlow_value_edit.text().replace(",", ".")) if self.barlow_checkbox.isChecked() and self.barlow_value_edit.text() else 1.0
            f_total = f * barlow
            p_mm = p * 0.001
            N = self.last_segment_length_px
            angle_rad = N * p_mm / f_total
            real_length_km = D_km * angle_rad
        except Exception:
            real_length_km = None
        self.object_selector.clear()
        for name, obj in self.object_dict.items():
            min_km = obj.get("min_km", 0)
            max_km = obj.get("max_km", float("inf"))
            if real_length_km is None or (min_km <= real_length_km <= max_km):
                self.object_selector.addItem(name)
        if self.object_selector.count() == 0:
            for name in self.object_dict:
                self.object_selector.addItem(name)        

    def fill_distance_with_skyfield(self):
        obj_name = self.skyfield_object_combo.currentText()
        date_qt = self.skyfield_date_edit.date()
        date_str = date_qt.toString("yyyy-MM-dd")
        # Conversion date pour Skyfield
        try:
            from skyfield.api import load
            ts = load.timescale()
            t = ts.utc(date_qt.year(), date_qt.month(), date_qt.day())
            # Correction du chemin du fichier .bsp
            planets = load(resource_path(os.path.join("Library", "de421.bsp")))
            earth = planets['earth']
            # Mapping Skyfield
            skyfield_map = {
                "Moon": "moon",
                "Sun": "sun",
                "Mercury": "mercury",
                "Venus": "venus",
                "Mars": "mars",
                "Jupiter": "jupiter barycenter",
                "Saturn": "saturn barycenter",
                "Uranus": "uranus barycenter",
                "Neptune": "neptune barycenter",
                "Pluto": "pluto barycenter",
            }
            if obj_name not in skyfield_map:
                QtWidgets.QMessageBox.warning(self, "Error", "Object not supported by Skyfield.")
                return
            target = planets[skyfield_map[obj_name]]
            # Distance Terre-objet (en km)
            if obj_name == "Earth":
                dist_km = 0
            else:
                astrometric = earth.at(t).observe(target)
                dist_au = astrometric.apparent().distance().au
                dist_km = dist_au * 149597870.7
            # Remplit le champ distance et l'unité
            self.object_distance.setText(f"{dist_km:.0f}")
            self.distance_unit.setCurrentText("km")
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Skyfield error", f"Error calculating distance:\n{e}")

    def convert_distance_to_km(self, distance_str):
        # Convertit la distance au format numérique approprié (km)
        if "kpc" in distance_str:
            return float(distance_str.replace("kpc", "").strip()) * 3.086e16
        elif "Mpc" in distance_str:
            return float(distance_str.replace("Mpc", "").strip()) * 3.086e19
        elif "pc" in distance_str:
            return float(distance_str.replace("pc", "").strip()) * 3.086e13
        elif "ly" in distance_str:
            return float(distance_str.replace("ly", "").strip()) * 9.461e12
        else:
            return float(distance_str.replace("km", "").strip())

    def save_last_image_path(self, path):
        try:
            os.makedirs(os.path.dirname(self.LAST_IMAGE_PATH_FILE), exist_ok=True)
            with open(self.LAST_IMAGE_PATH_FILE, "w", encoding="utf-8") as f:
                f.write(path)
        except Exception as e:
            raise Exception(f"Error while saving image path: {e}")

    def load_last_image_path(self):
        try:
            if os.path.exists(self.LAST_IMAGE_PATH_FILE):
                with open(self.LAST_IMAGE_PATH_FILE, "r", encoding="utf-8") as f:
                    path = f.read().strip()
                    if path:
                        return path
        except Exception:
            pass
        return ""

    def save_last_preset_path(self, path):
        try:
            os.makedirs(os.path.dirname(self.LAST_PRESET_PATH_FILE), exist_ok=True)
            with open(self.LAST_PRESET_PATH_FILE, "w", encoding="utf-8") as f:
                f.write(path)
        except Exception as e:
            raise Exception(f"Error while saving preset path: {e}")

    def wrap_right_panel_resize_event(self, old_resize_event):
        def new_resize_event(event):
            if callable(old_resize_event):
                old_resize_event(event)
        return new_resize_event

    def update_graphics_background(self):
        self.graphics_widget.style().polish(self.graphics_widget)
        pal = self.graphics_widget.palette()
        bg_color = pal.color(self.graphics_widget.backgroundRole())
        self.graphics_widget.setBackground(bg_color)
        if hasattr(self, "img_view") and self.img_view is not None:
            self.img_view.setBackgroundColor(bg_color)

class FramelessImageViewer(ImageViewer):
    def __init__(self, icon_path=None, theme_names=None, current_theme=None):
        # Appel du constructeur parent en tout premier
        super().__init__()
        # Initialisation spécifique à FramelessImageViewer
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.Window)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.setObjectName("FramelessImageViewer")
        self._drag_pos = None
        self._resizing = False
        self._resize_margin = 8
    
        # Couleur et épaisseur du bord externe
        # Couleurs de bordure selon le thème
        self._border_colors = {
            "dark": QtGui.QColor("#18195c"),
            "light": QtGui.QColor("#3D314A")
        }
        self._border_color = self._border_colors.get(current_theme.lower() if current_theme else "light", QtGui.QColor("#18195c"))
        self._border_width = 8 
        self._border_style = QtCore.Qt.SolidLine
        self._corner_radius = 20
        self._window_shape = 'rounded'  # 'rectangle', 'rounded', 'circle'
        self._gradient_enabled = True
      
        
        # Récupérer la barre de titre depuis l'UI
        self.title_bar = self.findChild(QtWidgets.QWidget, "CustomTitleBar")
        if self.title_bar:
            # Icone et titre
            icon_label = self.title_bar.findChild(QtWidgets.QLabel, "icon_label")
            if icon_label and icon_path:
                icon_label.setPixmap(QtGui.QPixmap(resource_path(icon_path)).scaled(48, 48, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
            title_label = self.title_bar.findChild(QtWidgets.QLabel, "title_label")
            if title_label:
                title_label.setText("Stellametrics")
            # Combo box des thèmes
            theme_combo = self.title_bar.findChild(QtWidgets.QComboBox, "theme_combo")
            if theme_combo and theme_names:
                theme_combo.clear()
                theme_combo.addItems(theme_names)
                if current_theme and current_theme in theme_names:
                    theme_combo.setCurrentText(current_theme)
                def on_theme_changed(theme_name): 
                    app = QApplication.instance()
                    if app:
                        qss_path = resource_path(os.path.join("Main", "StyleSheets", f"{theme_name.lower()}.qss"))
                        if os.path.exists(qss_path):
                            with open(qss_path, "r", encoding="utf-8") as f:
                                app.setStyleSheet(f.read())
                    # Met à jour la couleur de bordure selon le thème
                    self._border_color = self._border_colors.get(theme_name.lower(), QtGui.QColor("#18195c"))
                    self.current_theme = theme_name.lower()
                    self.apply_button_effects()
                    self.update_graphics_background()
                theme_combo.currentTextChanged.connect(on_theme_changed)
            # Boutons min, max, close
            min_btn = self.title_bar.findChild(QtWidgets.QPushButton, "min_btn")
            if min_btn:
                min_btn.clicked.connect(self.showMinimized)
            max_btn = self.title_bar.findChild(QtWidgets.QPushButton, "max_btn")
            if max_btn:
                def on_max_restore():
                    if self.isMaximized():
                        self.showNormal()
                    else:
                        self.showMaximized()
                max_btn.clicked.connect(on_max_restore)
            close_btn = self.title_bar.findChild(QtWidgets.QPushButton, "close_btn")
            if close_btn:
                close_btn.clicked.connect(self.close)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        rect = self.rect()
        margin = self._border_width / 2
        border_rect = QtCore.QRectF(
            rect.left() + margin,
            rect.top() + margin,
            rect.width() - self._border_width,
            rect.height() - self._border_width
        )

        if self._gradient_enabled:
            theme_gradients = {
                "dark": ("#1a2a49", "#3c4153"),
                "light": ("#C8AD7F", "#fff5db"),
            }
            theme_name = getattr(self, 'current_theme', None)
            if theme_name is None:
                combo = self.findChild(QtWidgets.QComboBox, "theme_combo")
                if combo:
                    theme_name = combo.currentText().lower()
            color1, color2 = theme_gradients.get(theme_name, ("#3c4153", "#1a2a49"))
            gradient = QtGui.QLinearGradient(rect.topLeft(), rect.bottomRight())
            gradient.setColorAt(0, QtGui.QColor(color1))
            gradient.setColorAt(1, QtGui.QColor(color2))
            brush = QtGui.QBrush(gradient)
        else:
            brush = QtGui.QBrush(QtGui.QColor("#222a44"))

        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(brush)

        # Dessine le fond et applique le masque
        if self._window_shape == 'circle':
            radius = min(border_rect.width(), border_rect.height()) / 2
            center = border_rect.center()
            painter.drawEllipse(center, radius, radius)
            # Masque circulaire centré
            mask_rect = QtCore.QRect(
                int(center.x() - radius),
                int(center.y() - radius),
                int(2 * radius),
                int(2 * radius)
            )
            self.setMask(QtGui.QRegion(mask_rect, QtGui.QRegion.Ellipse))
        elif self._window_shape == 'rounded':
            painter.drawRoundedRect(border_rect, self._corner_radius, self._corner_radius)
            mask_rect = QtCore.QRect(
                int(border_rect.left()),
                int(border_rect.top()),
                int(border_rect.width()),
                int(border_rect.height())
            )
            self.setMask(QtGui.QRegion(mask_rect, QtGui.QRegion.Rectangle))
        else:
            painter.drawRect(border_rect)
            self.setMask(QtGui.QRegion(rect, QtGui.QRegion.Rectangle))

        # Dessine le bord externe
        pen = QtGui.QPen(self._border_color, self._border_width, self._border_style)
        painter.setPen(pen)
        painter.setBrush(QtCore.Qt.NoBrush)
        if self._window_shape == 'circle':
            painter.drawEllipse(center, radius, radius)
        elif self._window_shape == 'rounded':
            painter.drawRoundedRect(border_rect, self._corner_radius, self._corner_radius)
        else:
            painter.drawRect(border_rect)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            if self._on_edge(event.pos()):
                self._resizing = True
                self._resize_start = event.globalPos()
                self._resize_geom = self.geometry()
            else:
                self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._resizing:
            diff = event.globalPos() - self._resize_start
            new_geom = QtCore.QRect(self._resize_geom)
            if self._resize_edge == 'right':
                new_geom.setWidth(max(400, self._resize_geom.width() + diff.x()))
            elif self._resize_edge == 'bottom':
                new_geom.setHeight(max(300, self._resize_geom.height() + diff.y()))
            elif self._resize_edge == 'left':
                new_geom.setLeft(min(self._resize_geom.right() - 400, self._resize_geom.left() + diff.x()))
            elif self._resize_edge == 'top':
                new_geom.setTop(min(self._resize_geom.bottom() - 300, self._resize_geom.top() + diff.y()))
            self.setGeometry(new_geom)
        elif self._drag_pos and event.buttons() == QtCore.Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)
        else:
            self._update_cursor(event.pos())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        self._resizing = False
        super().mouseReleaseEvent(event)

    def _on_edge(self, pos):
        rect = self.rect()
        margin = self._resize_margin
        if abs(pos.x() - rect.right()) < margin:
            self._resize_edge = 'right'
            return True
        if abs(pos.x() - rect.left()) < margin:
            self._resize_edge = 'left'
            return True
        if abs(pos.y() - rect.bottom()) < margin:
            self._resize_edge = 'bottom'
            return True
        if abs(pos.y() - rect.top()) < margin:
            self._resize_edge = 'top'
            return True
        self._resize_edge = None
        return False

    def _update_cursor(self, pos):
        if self._on_edge(pos):
            if self._resize_edge in ('left', 'right'):
                self.setCursor(QtCore.Qt.SizeHorCursor)
            elif self._resize_edge in ('top', 'bottom'):
                self.setCursor(QtCore.Qt.SizeVerCursor)
        else:
            self.setCursor(QtCore.Qt.ArrowCursor)

def save_last_theme(theme_name):
    CONFIG_DIR = os.path.join(PROJECT_ROOT, "Stellametrics_Config")
    LAST_THEME_FILE = os.path.join(CONFIG_DIR, "Stellametrics_last_theme.txt")
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(LAST_THEME_FILE, "w", encoding="utf-8") as f:
            f.write(theme_name)
    except Exception:
        pass

def load_last_theme():
    CONFIG_DIR = os.path.join(PROJECT_ROOT, "Stellametrics_Config")
    LAST_THEME_FILE = os.path.join(CONFIG_DIR, "Stellametrics_last_theme.txt")
    try:
        if os.path.exists(LAST_THEME_FILE):
            with open(LAST_THEME_FILE, "r", encoding="utf-8") as f:
                return f.read().strip()
    except Exception:
        pass
    return ""

if __name__ == "__main__":
    try:
        app = QtWidgets.QApplication(sys.argv)
        def load_fonts(font_base_name=None):
            fonts_dir = resource_path(os.path.join("Library", "fonts"))
            font_families = {}
            if font_base_name:
                otf_path = os.path.join(fonts_dir, f"{font_base_name}.otf")
                ttf_path = os.path.join(fonts_dir, f"{font_base_name}.ttf")
                if os.path.exists(otf_path):
                    font_path = otf_path
                elif os.path.exists(ttf_path):
                    font_path = ttf_path
                else:
                    raise RuntimeError(f"Font file not found: {otf_path} or {ttf_path}")
                font_id = QFontDatabase.addApplicationFont(font_path)
                if font_id == -1:
                    raise RuntimeError(f"Failed to load font: {font_path}")
                families = QFontDatabase.applicationFontFamilies(font_id)
                if families:
                    font_families[families[0]] = font_path
            else:
                if os.path.exists(fonts_dir):
                    for file in os.listdir(fonts_dir):
                        if file.lower().endswith((".ttf", ".otf")):
                            font_path = os.path.join(fonts_dir, file)
                            font_id = QFontDatabase.addApplicationFont(font_path)
                            if font_id != -1:
                                families = QFontDatabase.applicationFontFamilies(font_id)
                                if families:
                                    font_families[families[0]] = font_path
                            else:
                                raise RuntimeError(f"Failed to load font: {font_path}")
            return font_families

        # Utilisation :
        FONT_FAMILIES = load_fonts() # charge toutes les polices
        # serena_family = list(load_fonts("Serena").keys())[0] # charge une police précise


        icon_path = resource_path(os.path.join("Assets", "Icon", "icon.png"))
        app.setWindowIcon(QtGui.QIcon(icon_path))

        # Chargement des stylesheets 
        STYLESHEETS = {}
        styles_dir = resource_path(os.path.join("Main", "StyleSheets"))
        for path in glob.glob(os.path.join(styles_dir, "*.qss")):
            theme_name = os.path.splitext(os.path.basename(path))[0].lower()
            with open(path, "r", encoding="utf-8") as f:
                STYLESHEETS[theme_name] = f.read()

        last_theme = load_last_theme()
        current_theme = last_theme if last_theme in STYLESHEETS else "light"
        app.setStyleSheet(STYLESHEETS[current_theme])

        # Création de la fenêtre principale avec sélecteur de thème
        win = FramelessImageViewer(icon_path=icon_path, theme_names=list(STYLESHEETS.keys()), current_theme=current_theme)
        # Connexion du signal de changement de thème
        def on_theme_changed(theme_name):
            if theme_name in STYLESHEETS:
                app.setStyleSheet(STYLESHEETS[theme_name])
                win.graphics_widget.style().polish(win.graphics_widget) 
                win.update_graphics_background() 
                win.graphics_widget.update() 
                save_last_theme(theme_name)
        if hasattr(win, "title_bar") and hasattr(win.title_bar, "theme_changed"):
            win.title_bar.theme_changed.connect(on_theme_changed)
        win.setWindowIcon(QtGui.QIcon(icon_path))
        win.setWindowTitle("Stellametrics")
        win.apply_button_effects()
        win.show()
        sys.exit(app.exec_())
    except Exception:
        traceback.print_exc()