import sys
import os
from pathlib import Path
import numpy as np
from PyQt5 import QtWidgets, QtCore, QtGui, uic
import pyqtgraph as pg
from astropy.io import fits
from PIL import Image, ImageOps
import json
from PyQt5.QtGui import QPen, QPixmap, QFontDatabase
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGraphicsLineItem, QGraphicsPixmapItem, QGraphicsDropShadowEffect
from skyfield.api import load
import glob
import traceback

def resource_path(relative_path):
    """Permet d'accéder aux ressources embarquées avec PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


class CustomTitleBar(QtWidgets.QWidget):
    theme_changed = QtCore.pyqtSignal(str)  # Signal pour notifier le changement de thème
    def __init__(self, parent=None, icon_path=None, title="SkyScale", theme_names=None, current_theme=None):
        super().__init__(parent)
        self.setObjectName("CustomTitleBar")
        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self.setFixedHeight(36)
        self.parent = parent
        self.icon_path = icon_path
        self.title = title
        # SUPPRESSION du setStyleSheet local pour laisser le style global agir
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
        # --- Ajout du sélecteur de thème ---
        if theme_names:
            self.theme_combo = QtWidgets.QComboBox()
            self.theme_combo.setObjectName("themeComboBox")
            self.theme_combo.addItems(theme_names)
            if current_theme and current_theme in theme_names:
                self.theme_combo.setCurrentText(current_theme)
            self.theme_combo.setFixedWidth(140)
            self.theme_combo.setToolTip("Changer le thème de l'application")
            self.theme_combo.currentTextChanged.connect(self.on_theme_changed)
            layout.addWidget(self.theme_combo)
        layout.addStretch(5)
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
    LAST_IMAGE_PATH_FILE = ".last_image_path"
    LAST_PRESET_PATH_FILE = ".last_preset_path"

    def __init__(self):
        super().__init__()
        # Correction du chemin du fichier UI
        uic.loadUi(resource_path(os.path.join("Main", "ImageViewer_testing.ui")), self)
        self.setWindowTitle("SkyScale")
        
        # Connexion des boutons aux méthodes
        self.open_btn.clicked.connect(self.open_image)
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

        # Initialisation des variables nécessaires
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
            "France": {"image": resource_path(os.path.join("objects_png", "france.png")), "diameter": 975, "min_km": 10, "max_km": 10000},
            "USA": {"image": resource_path(os.path.join("objects_png", "usa.png")), "diameter": 4500, "min_km": 100, "max_km": 20000},
            "Earth": {"image": resource_path(os.path.join("objects_png", "earth.png")), "diameter": 12742, "min_km": 100, "max_km": 2e6},
            "Jupiter": {"image": resource_path(os.path.join("objects_png", "jupiter.png")), "diameter": 139822, "min_km": 1000, "max_km": 1e8},
        }

        # Variables pour stocker le dernier chemin d'image et de preset utilisés
        self.last_image_path = self.load_last_image_path()
        self.last_preset_path = self.load_last_preset_path()

        # Ajout du widget pyqtgraph dans le panneau de droite
        self.graphics_widget = pg.GraphicsLayoutWidget()
        self.update_graphics_background()
        self.img_view = self.graphics_widget.addViewBox()
        self.img_item = pg.ImageItem()
        self.img_view.addItem(self.img_item)
        self.img_view.setAspectLocked(True)
        self.img_view.setBackgroundColor(self.graphics_widget.palette().color(QtGui.QPalette.Window).name())
        self.img_view.scene().sigMouseMoved.connect(self.update_mouse_coords)
        self.img_view.scene().installEventFilter(self)
        # Récupère le widget rightPanel et son layout
        right_panel = self.findChild(QtWidgets.QWidget, "rightPanel")
        right_layout = right_panel.layout() if right_panel is not None else None
        # Supprime le QLabel d'image si présent
        image_label = self.findChild(QtWidgets.QLabel, "image_label")
        if image_label is not None and right_layout is not None:
            right_layout.removeWidget(image_label)
            image_label.setParent(None)
        if right_layout is not None:
            right_layout.addWidget(self.graphics_widget)
        # Ajoute le label de coordonnées
        self.coord_label = QtWidgets.QLabel("X: -, Y: -", self.graphics_widget)
        self.coord_label.setStyleSheet("background: #222; color: #fff; padding: 4px; border-radius: 6px;")
        self.coord_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.coord_label.setFixedWidth(150)
        self.coord_label.setFixedHeight(28)
        self.coord_label.move(20, 20)
        self.coord_label.raise_()
        self.graphics_widget.setMouseTracking(True)
        self.graphics_widget.installEventFilter(self)

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

        # Chargement des données au démarrage
        self.load_distance_library()
        self.load_last_preset()  # Will use file-based path
        self.load_last_image()   # Will use file-based path

        self.add_author_bar()  # Ajout de la barre d'auteur

        # --- Correction responsive boutons leftPanel ---
        left_panel = self.findChild(QtWidgets.QWidget, "leftPanel")
        if left_panel:
            left_panel.setMinimumWidth(0)
            left_panel.setMinimumSize(0, 0)
            # Correction clé : forcer le leftPanel à suivre la largeur du scroll area
            left_panel.setSizePolicy(QtWidgets.QSizePolicy.Ignored, left_panel.sizePolicy().verticalPolicy())
            # Astuce : QSizePolicy.Ignored force le widget à toujours prendre la largeur imposée par son parent (splitter/scroll area),
            # ce qui garantit qu'il se compresse parfaitement sans scroll horizontal ni superposition, même réduit à l'extrême.

            layout = left_panel.layout()
            if layout:
                layout.setContentsMargins(2, 2, 2, 2)
                
            # Appliquer Expanding à tous les enfants directs du leftPanel
            for child in left_panel.findChildren((QtWidgets.QPushButton, QtWidgets.QLabel, QtWidgets.QGroupBox, QtWidgets.QComboBox, QtWidgets.QLineEdit, QtWidgets.QDateEdit)):
                child.setSizePolicy(QtWidgets.QSizePolicy.Expanding, child.sizePolicy().verticalPolicy())
                child.setMinimumWidth(0)
                child.setMaximumWidth(16777215)
            # Si le parent direct est un QSplitter, le rendre collapsible
            splitter = left_panel.parent()
            if isinstance(splitter, QtWidgets.QSplitter):
                index = splitter.indexOf(left_panel)
                splitter.setCollapsible(index, True)


##################################################################################################################

        self.apply_button_effects()
    def apply_button_effects(self):
        """
        Applique les effets visuels sur tous les QPushButton de l'UI.
        """
        def set_shadow_color(btn, color):
            effect = btn.graphicsEffect()
            if isinstance(effect, QGraphicsDropShadowEffect):
                effect.setColor(QtGui.QColor(color))

        for btn in self.findChildren(QtWidgets.QPushButton):
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(18)
            shadow.setColor(QtGui.QColor(38, 99, 235, 160))  # couleur normale
            shadow.setOffset(0, 4)
            btn.setGraphicsEffect(shadow)
            if btn.isCheckable():
                def on_toggle(checked, b=btn):
                    set_shadow_color(b, "#7700ff" if checked else "#2663eb")
                btn.toggled.connect(on_toggle)
            else:
                btn.pressed.connect(lambda b=btn: set_shadow_color(b, "#7700ff"))
                btn.released.connect(lambda b=btn: set_shadow_color(b, "#2663eb"))
        # btn = self.findChild(QtWidgets.QPushButton, "open_btn")
        # if btn:
        #     shadow = QGraphicsDropShadowEffect()
        #     shadow.setBlurRadius(18)
        #     shadow.setColor(QtGui.QColor(88, 64, 67, 160))
        #     shadow.setOffset(0, 4)
        #     btn.setGraphicsEffect(shadow)

##################################################################################################################
    def update_mouse_coords(self, pos):
        # Affiche les coordonnées de la souris dans la vue
        mouse_point = self.img_view.mapSceneToView(pos)
        x = mouse_point.x()
        y = mouse_point.y()
        self.coord_label.setText(f"X: {x:.1f}, Y: {y:.1f}")
        self.coord_label.move(self.graphics_widget.width() - self.coord_label.width() - 10, self.graphics_widget.height() - self.coord_label.height() - 10)
    
    def eventFilter(self, obj, event):
        # Affiche les coordonnées si la souris bouge sur la view OU sur la scène
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

            # Calcul dans l'unité d'entrée
            real_length = D * angle_rad

            # Affichage dans la même unité que l'entrée
            if unit == "ly":
                self.real_length_label.setText(f"Real object length: {real_length:.4f} ly")
            elif unit == "pc":
                self.real_length_label.setText(f"Real object length: {real_length:.4f} pc")
            elif unit == "kpc":
                # Affiche en Mpc si > 1e3 kpc, sinon en kpc
                if real_length >= 1e3:
                    real_length_mpc = real_length / 1e3
                    self.real_length_label.setText(f"Real object length: {real_length_mpc:.4f} Mpc")
                else:
                    self.real_length_label.setText(f"Real object length: {real_length:.4f} kpc")
            elif unit == "Mpc":
                # Affiche en kpc si < 1 Mpc, sinon en Mpc
                if real_length < 1:
                    real_length_kpc = real_length * 1e3
                    self.real_length_label.setText(f"Real object length: {real_length_kpc:.4f} kpc")
                else:
                    self.real_length_label.setText(f"Real object length: {real_length:.4f} Mpc")
            else:  # km
                if real_length > 1e9:
                    light_year = 9.461e12
                    real_length_ly = real_length / light_year
                    self.real_length_label.setText(f"Real object length: {real_length_ly:.4f} ly")
                else:
                    self.real_length_label.setText(f"Real object length: {real_length:.2f} km")
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
        # Demande à l'utilisateur où enregistrer le preset
        default_name = self.telescope_name.text().strip() or "default"
        default_path = os.path.join(os.path.abspath("."), f"preset_{default_name}.json")
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save preset",
            self.last_preset_path or default_path,
            "Presets JSON (*.json);;All files (*)"
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception as e:
            print("Preset save error:", e)
        # Mémorise le chemin du dernier preset utilisé dans fichier
        self.last_preset_path = path
        self.save_last_preset_path(path)

    def get_preset_path(self):
        # Retourne le chemin complet du preset courant dans le dossier 'preset' à la racine du projet
        name = self.telescope_name.text().strip() or "default"
        # Récupère le chemin absolu du dossier 'preset' à la racine du projet
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        preset_dir = os.path.join(project_root, "preset")
        os.makedirs(preset_dir, exist_ok=True)
        return os.path.join(preset_dir, f"preset_{name}.json")

    def load_last_preset_path(self):
        # Retourne le chemin du dernier preset depuis la variable de classe
        return self.last_preset_path

    def load_last_preset(self):
        path = self.load_last_preset_path()
        if not path or not os.path.exists(path):
            # Fallback : preset par défaut dans le dossier du script
            name = self.telescope_name.text().strip() or "default"
            path = resource_path(f"preset_{name}.json")
            if not os.path.exists(path):
                # Si aucun preset par défaut, on arrête
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
        except Exception:
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
            # Mémorise le chemin du preset chargé dans fichier
            self.last_preset_path = path
            self.save_last_preset_path(path)
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", f"Unable to load preset:\n{e}")

    def save_last_preset_name(self):
        # Mémorise le chemin du preset courant dans la variable de classe
        self.last_preset_path = self.get_preset_path()

    def closeEvent(self, event):
        # Enregistre automatiquement dans le dernier preset utilisé
        try:
            data = {
                "telescope_name": self.telescope_name.text() if hasattr(self, 'telescope_name') and self.telescope_name is not None else "",
                "telescope_diameter": self.telescope_diameter.text() if hasattr(self, 'telescope_diameter') and self.telescope_diameter is not None else "",
                "telescope_focal": self.telescope_focal.text() if hasattr(self, 'telescope_focal') and self.telescope_focal is not None else "",
                "barlow_checked": self.barlow_checkbox.isChecked() if hasattr(self, 'barlow_checkbox') and self.barlow_checkbox is not None else False,
                "barlow_value": self.barlow_value_edit.text() if hasattr(self, 'barlow_value_edit') and self.barlow_value_edit is not None else "",
                "camera_pixel_size": self.camera_pixel_size.text() if hasattr(self, 'camera_pixel_size') and self.camera_pixel_size is not None else "",
            }
            preset_path = self.last_preset_path or self.get_preset_path()
            self.last_preset_path = preset_path
            self.save_last_preset_path(preset_path)
            with open(preset_path, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception as e:
            print("Preset save error:", e)
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
                pil_img = pil_img.transpose(Image.ROTATE_270)  # +90° droite
                if pil_img.mode == "RGB":
                    img = np.array(pil_img).astype(np.float32) / 255.0
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
        # Enregistre le chemin dans fichier
        self.last_image_path = path
        self.save_last_image_path(path)

    def load_last_image(self):
        # Charge la dernière image depuis fichier
        if self.last_image_path and os.path.exists(self.last_image_path):
            self.open_image_from_path(self.last_image_path)

    def open_image_from_path(self, path):
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
                pil_img = pil_img.transpose(Image.ROTATE_270)  # +90° droite
                if pil_img.mode == "RGB":
                    img = np.array(pil_img).astype(np.float32) / 255.0
                else:
                    img = np.array(pil_img.convert("L")).astype(np.float32) / 255.0
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Error", f"Unable to open image:\n{e}")
                return

        self.original_img = img.copy()    
        self.current_img = img
        self.img_item.setImage(self.current_img, autoLevels=True)
        self.img_view.setAspectLocked(True)  # Permet l'affichage sans forcer le carré
        self.img_view.autoRange()

    # def rotate_image(self):
    #     if self.current_img is not None:
    #         if self.current_img.ndim == 3:
    #             self.current_img = np.rot90(self.current_img, k=-1, axes=(0, 1))
    #         else:
    #             self.current_img = np.rot90(self.current_img, k=-1)
    #         self.img_item.setImage(self.current_img, autoLevels=True)
    #         self.img_view.autoRange()
    #         self.rotation_count = (self.rotation_count + 1) % 4  # Ajoute cette ligne

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
            self.length_label.setText(f"Segment length: {dist:.2f} px\n")
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

    def load_distance_library(self):
        # Correction du chemin du fichier JSON
        self.distance_library_path = resource_path(os.path.join("Library", "distance_library.json"))
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
        # Calcule la taille réelle du segment (en km) pour filtrer les objets pertinents
        try:
            if self.last_segment_length_px is None:
                # Si pas de segment, afficher tous les objets
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
        # Si aucun objet n'est pertinent, on affiche tout de même tous les objets
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
            with open(self.LAST_IMAGE_PATH_FILE, "w", encoding="utf-8") as f:
                f.write(path)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du chemin image : {e}")

    def load_last_image_path(self):
        try:
            if os.path.exists(self.LAST_IMAGE_PATH_FILE):
                with open(self.LAST_IMAGE_PATH_FILE, "r", encoding="utf-8") as f:
                    return f.read().strip()
        except Exception as e:
            print(f"Erreur lors du chargement du chemin image : {e}")
        return ""

    def save_last_preset_path(self, path):
        try:
            with open(self.LAST_PRESET_PATH_FILE, "w", encoding="utf-8") as f:
                f.write(path)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du chemin preset : {e}")

    def load_last_preset_path(self):
        try:
            if os.path.exists(self.LAST_PRESET_PATH_FILE):
                with open(self.LAST_PRESET_PATH_FILE, "r", encoding="utf-8") as f:
                    return f.read().strip()
        except Exception as e:
            print(f"Erreur lors du chargement du chemin preset : {e}")
        return ""

    def add_author_bar(self):
        # Ajoute une barre discrète en bas à gauche du panel droit
        right_panel = self.findChild(QtWidgets.QWidget, "rightPanel")
        if right_panel is not None:
            self.author_bar = QtWidgets.QLabel("Author : AstroSearch42", right_panel)
            self.author_bar.setStyleSheet("background: rgba(30,30,30,0.85); color: #F0EBE3; padding: 4px 12px; border-radius: 8px; font-size: 9pt; font-family: 'Century Gothic', Arial, 'Liberation Sans', sans-serif;")
            self.author_bar.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
            self.author_bar.setFixedHeight(20)
            self.author_bar.setFixedWidth(200)
            self.author_bar.raise_()
            self.position_author_bar()
            # Redéfinir resizeEvent du panel droit
            right_panel.resizeEvent = self.wrap_right_panel_resize_event(right_panel.resizeEvent)

    def position_author_bar(self):
        # Place la barre en bas à gauche du panel droit
        right_panel = self.findChild(QtWidgets.QWidget, "rightPanel")
        if right_panel is not None and hasattr(self, 'author_bar'):
            margin = 12
            x = margin
            y = right_panel.height() - self.author_bar.height() - margin
            self.author_bar.move(x, y)

    def wrap_right_panel_resize_event(self, old_resize_event):
        def new_resize_event(event):
            self.position_author_bar()
            if callable(old_resize_event):
                old_resize_event(event)
        return new_resize_event

    def update_graphics_background(self):
        # Récupère la couleur de fond effective du widget (héritée du stylesheet)
        pal = self.graphics_widget.palette()
        bg_color = pal.color(self.graphics_widget.backgroundRole())
        self.graphics_widget.setBackground(bg_color)
        if hasattr(self, "img_view") and self.img_view is not None:
            self.img_view.setBackgroundColor(bg_color)

class FramelessImageViewer(ImageViewer):
    def __init__(self, icon_path=None):
        super().__init__()
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.Window)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, False)
        self.setObjectName("FramelessImageViewer")  # Pour le style global
        # Supprimer le setStyleSheet local qui bloque le background
        # self.setStyleSheet("border-radius: 10px; background: #232629; border: 1.2px solid #353b3c;")
        # Title bar
        self.title_bar = CustomTitleBar(self, icon_path=icon_path, title="SkyScale")
        # Layout principal vertical
        self._main_layout = QtWidgets.QVBoxLayout()
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)
        self._main_layout.addWidget(self.title_bar)
        # Récupérer le layout existant (chargé par uic.loadUi)
        old_layout = self.layout()
        if old_layout:
            # Créer un widget central et lui donner l'ancien layout
            central_widget = QtWidgets.QWidget()
            central_widget.setLayout(old_layout)
            self._main_layout.addWidget(central_widget)
        self.setLayout(self._main_layout)
        # Pour le drag sur la bordure
        self._drag_pos = None
        self._resizing = False
        self._resize_margin = 8

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
    try:
        with open(".last_theme", "w", encoding="utf-8") as f:
            f.write(theme_name)
    except Exception as e:
        print(f"Erreur lors de la sauvegarde du thème : {e}")

def load_last_theme():
    try:
        if os.path.exists(".last_theme"):
            with open(".last_theme", "r", encoding="utf-8") as f:
                return f.read().strip()
    except Exception as e:
        print(f"Erreur lors du chargement du thème : {e}")
    return None

if __name__ == "__main__":
    try:
        app = QtWidgets.QApplication(sys.argv)
        # Chargement des polices personnalisée
        def load_fonts(font_base_name=None):
            """
            Charge une police précise si font_base_name est donné,
            sinon charge toutes les polices du dossier et retourne un dict {famille: chemin}.
            """
            fonts_dir = os.path.join(os.path.dirname(__file__), "..", "Library", "fonts")
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
                for file in os.listdir(fonts_dir):
                    if file.lower().endswith(('.ttf', '.otf')):
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


        icon_path = resource_path(os.path.join("objects_png/Icon", "icon2.ico"))
        app.setWindowIcon(QtGui.QIcon(icon_path))

        # --- Chargement des stylesheets ---
        STYLESHEETS = {}
        styles_dir = os.path.join(os.path.dirname(__file__), "StyleSheets")
        for path in glob.glob(os.path.join(styles_dir, "*.qss")):
            theme_name = os.path.splitext(os.path.basename(path))[0].capitalize()
            with open(path, "r", encoding="utf-8") as f:
                STYLESHEETS[theme_name] = f.read()

        last_theme = load_last_theme()
        current_theme = last_theme if last_theme in STYLESHEETS else "Light"
        app.setStyleSheet(STYLESHEETS[current_theme])

        # --- Création de la fenêtre principale avec sélecteur de thème ---
        win = FramelessImageViewer(icon_path=icon_path)
        # Remplacer la barre de titre par une version avec sélecteur de thème
        win.title_bar.deleteLater()
        win.title_bar = CustomTitleBar(win, icon_path=icon_path, title="SkyScale", theme_names=list(STYLESHEETS.keys()), current_theme=current_theme)
        win._main_layout.insertWidget(0, win.title_bar)
        # Connexion du signal de changement de thème
        def on_theme_changed(theme_name):
            app.setStyleSheet(STYLESHEETS[theme_name])
            save_last_theme(theme_name)
        win.title_bar.theme_changed.connect(on_theme_changed)
        win.title_bar.theme_changed.connect(lambda _: win.update_graphics_background())
        win.setWindowIcon(QtGui.QIcon(icon_path))
        win.setWindowTitle("SkyScale  - FITS/Image Viewer")
        win.update_graphics_background()
        win.show()
        sys.exit(app.exec_())
    except Exception:
        traceback.print_exc()