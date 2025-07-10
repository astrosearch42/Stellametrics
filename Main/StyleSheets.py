fontsize = 8.2  # Default font size for all stylesheets

# --- Définition de plusieurs stylesheets ---
# DARK 
txt_color_darkcss = "#F0EBE3"
bg_dark = "#232629"
bg_input_dark = "#2b2f31"
bg_btn_dark = "#353b3c"
border_dark = "#444"
bg_combo_dark= "#2b2f31"
bg_titlebar_dark = "#181a1b"
# StyleSheet
dark_stylesheet = f"""
    QWidget {{ background-color: {bg_dark}; color: {txt_color_darkcss}; font-family: 'Century Gothic', Arial, 'Liberation Sans', sans-serif; font-size: {fontsize}pt; }}
    QMenuBar, QMenu, QToolBar {{ background-color: {bg_dark}; color: {txt_color_darkcss}; font-family: 'Century Gothic', Arial, 'Liberation Sans', sans-serif; font-size: {fontsize}pt; }}
    QPushButton {{ background-color: {bg_btn_dark}; color: {txt_color_darkcss}; border: 1px solid {border_dark}; border-radius: 4px; padding: 4px; font-family: 'Century Gothic', Arial, 'Liberation Sans', sans-serif; font-size: {fontsize}pt; }}
    QPushButton:hover {{ background-color: #3e4446; }}
    QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
        background-color: {bg_input_dark}; color: {txt_color_darkcss}; border: 1px solid {border_dark}; border-radius: 4px; font-family: 'Century Gothic', Arial, 'Liberation Sans', sans-serif; font-size: {fontsize}pt;
    }}
    QDateEdit {{
        background-color: {bg_input_dark}; color: {txt_color_darkcss}; border: 1px solid {border_dark}; border-radius: 4px; font-family: 'Century Gothic', Arial, 'Liberation Sans', sans-serif; font-size: {fontsize}pt;
    }}
    QGroupBox {{
        border: 1.5px solid {border_dark}; border-radius: 6px; margin-top: 6px; font-family: 'Century Gothic', Arial, 'Liberation Sans', sans-serif; font-size: {fontsize}pt;
    }}
    QGroupBox:title {{
        color: {txt_color_darkcss}; background: transparent; subcontrol-origin: margin; left: 10px; padding: 0 4px; font-family: 'Century Gothic', Arial, 'Liberation Sans', sans-serif; font-size: {fontsize}pt;
    }}
    QLabel {{ color: {txt_color_darkcss}; font-family: 'Century Gothic', Arial, 'Liberation Sans', sans-serif; font-size: {fontsize}pt; }}
    QCheckBox, QRadioButton {{ color: {txt_color_darkcss}; font-family: 'Century Gothic', Arial, 'Liberation Sans', sans-serif; font-size: {fontsize}pt; }}
    QPushButton#open_btn {{ font-size: 11pt; font-weight: bold; }}      
    QPushButton#load_btn {{ margin-bottom: 20px; }}  
    QGroupBox#skyfield_group {{ margin-bottom: 20px; }}  
    QLabel#real_length_label {{ font-size: 11pt; font-weight: bold; margin-bottom: 12px; }}      
    QLabel#length_label {{ font-size: 11pt; font-weight: bold; }}      
    QPushButton#save_object_btn {{ font-size: 12pt; font-weight: bold; }}  
    QTabWidget::pane {{ border: 1px solid {border_dark}; font-family: 'Century Gothic', Arial, 'Liberation Sans', sans-serif; font-size: {fontsize}pt; }}
    QTabBar::tab {{ background: {bg_dark}; color: {txt_color_darkcss}; border: 1px solid {border_dark}; border-bottom: none; padding: 6px; font-family: 'Century Gothic', Arial, 'Liberation Sans', sans-serif; font-size: {fontsize}pt; }}
    QTabBar::tab:selected {{ background: #353b3c; }}
    QWidget#FramelessImageViewer {{ border-radius: 10px; border: 1.2px solid #353b3c; background-color: #232629; }}
    QWidget#CustomTitleBar {{ background-color: {bg_titlebar_dark}; }}
    QWidget#CustomTitleBar QLabel {{ color: {txt_color_darkcss}; }}
    QComboBox#themeComboBox {{
        background-color: {bg_combo_dark};
        color: {txt_color_darkcss};
        border: 1.2px solid #353b3c;
        border-radius: 6px;
        padding: 2px 18px 2px 8px;
        min-width: 90px;
        font-weight: bold;
    }}
    QComboBox#themeComboBox QAbstractItemView {{
        background-color: #232629;
        color: {txt_color_darkcss};
        border: 1.2px solid #353b3c;
        selection-background-color: #353b3c;
        selection-color: {txt_color_darkcss};
    }}
"""

# DARK Windows 11 Style (neumorphism-inspired, soft, modern, no font-size or color imposed)
txt_color_darkcss = "#F0EBE3"
bg_dark = "#232629"
bg_input_dark = "#2b2f31"
bg_btn_dark = "#353b3c"
border_dark = "#444"
bg_combo_dark= "#2b2f31"
bg_titlebar_dark = "#181a1b"
# StyleSheet
dark_stylesheet_w = f"""
    QWidget {{ background-color: {bg_dark}; color: {txt_color_darkcss}; font-family: 'Century Gothic', Arial, 'Liberation Sans', sans-serif; font-size: {fontsize}pt; }}
    QMenuBar, QMenu, QToolBar {{ background-color: {bg_dark}; color: {txt_color_darkcss}; font-family: 'Century Gothic', Arial, 'Liberation Sans', sans-serif; font-size: {fontsize}pt; }}
    QPushButton {{
        border: none;
        border-radius: 7px;
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f3f6fa, stop:1 #e2e6ea);
        box-shadow: 2px 2px 6px #babecc, -2px -2px 6px #ffffff;
        padding: 6px 14px;
        min-width: 60px;
        min-height: 24px;
    }}
    
    QPushButton:hover {{ background-color: #3e4446; }}
    QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
        background: #f7faff;
        border: 1px solid #babecc;
        border-radius: 6px;
        padding: 4px;
    }}
    QDateEdit {{
        background-color: {bg_input_dark}; color: {txt_color_darkcss}; border: 1px solid {border_dark}; border-radius: 4px; font-family: 'Century Gothic', Arial, 'Liberation Sans', sans-serif; font-size: {fontsize}pt;
    }}
    QGroupBox {{
        border: 1.5px solid {border_dark}; border-radius: 6px; margin-top: 6px; font-family: 'Century Gothic', Arial, 'Liberation Sans', sans-serif; font-size: {fontsize}pt;
    }}
    QGroupBox:title {{
        color: {txt_color_darkcss}; background: transparent; subcontrol-origin: margin; left: 10px; padding: 0 4px; font-family: 'Century Gothic', Arial, 'Liberation Sans', sans-serif; font-size: {fontsize}pt;
    }}
    QLabel {{ color: {txt_color_darkcss}; font-family: 'Century Gothic', Arial, 'Liberation Sans', sans-serif; font-size: {fontsize}pt; }}
    QCheckBox, QRadioButton {{ color: {txt_color_darkcss}; font-family: 'Century Gothic', Arial, 'Liberation Sans', sans-serif; font-size: {fontsize}pt; }}
    QPushButton#open_btn {{ font-size: 11pt; font-weight: bold; }}      
    QPushButton#load_btn {{ margin-bottom: 20px; }}  
    QGroupBox#skyfield_group {{ margin-bottom: 20px; }}  
    QLabel#real_length_label {{ font-size: 11pt; font-weight: bold; margin-bottom: 12px; }}      
    QLabel#length_label {{ font-size: 11pt; font-weight: bold; }}      
    QPushButton#save_object_btn {{ font-size: 12pt; font-weight: bold; }}  
    QTabWidget::pane {{ border: 1px solid {border_dark}; font-family: 'Century Gothic', Arial, 'Liberation Sans', sans-serif; font-size: {fontsize}pt; }}
    QTabBar::tab {{ background: {bg_dark}; color: {txt_color_darkcss}; border: 1px solid {border_dark}; border-bottom: none; padding: 6px; font-family: 'Century Gothic', Arial, 'Liberation Sans', sans-serif; font-size: {fontsize}pt; }}
    QTabBar::tab:selected {{ background: #353b3c; }}
    QWidget#FramelessImageViewer {{ border-radius: 10px; border: 1.2px solid #353b3c; background-color: #232629; }}
    QWidget#CustomTitleBar {{ background-color: {bg_titlebar_dark}; }}
    QWidget#CustomTitleBar QLabel {{ color: {txt_color_darkcss}; }}
    QComboBox#themeComboBox {{
        background-color: {bg_combo_dark};
        color: {txt_color_darkcss};
        border: 1.2px solid #353b3c;
        border-radius: 6px;
        padding: 2px 18px 2px 8px;
        min-width: 90px;
        font-weight: bold;
    }}
    QComboBox#themeComboBox QAbstractItemView {{
        background-color: #232629;
        color: {txt_color_darkcss};
        border: 1.2px solid #353b3c;
        selection-background-color: #353b3c;
        selection-color: {txt_color_darkcss};
    }}
"""


# LIGHT 
txt_color_lightcss = "#292826"
bg_light = "#f5f5f5"
bg_input_light = "#fff"
bg_btn_light = "#e0e0e0"
border_light = "#bbb"
bg_combo_light = "#f0f0f0"
bg_titlebar_light = "#979797"
# StyleSheet
light_stylesheet = f"""
    QWidget {{ background-color: {bg_light}; color: {txt_color_lightcss}; font-family: 'Century Gothic', Arial, 'Liberation Sans', sans-serif; font-size: {fontsize}pt; }}
    QMenuBar, QMenu, QToolBar {{ background-color: {bg_light}; color: {txt_color_lightcss}; font-family: 'Century Gothic', Arial, 'Liberation Sans', sans-serif; font-size: {fontsize}pt; }}
    QPushButton {{ background-color: {bg_btn_light}; color: {txt_color_lightcss}; border: 1px solid {border_light}; border-radius: 4px; padding: 4px; font-family: 'Century Gothic', Arial, 'Liberation Sans', sans-serif; font-size: {fontsize}pt; }}
    QPushButton:hover {{ background-color: #3e4446; }}
    QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
        background-color: {bg_input_light}; color: {txt_color_lightcss}; border: 1px solid {border_light}; border-radius: 4px; font-family: 'Century Gothic', Arial, 'Liberation Sans', sans-serif; font-size: {fontsize}pt;
    }}
    QDateEdit {{
        background-color: {bg_input_light}; color: {txt_color_lightcss}; border: 1px solid {border_light}; border-radius: 4px; font-family: 'Century Gothic', Arial, 'Liberation Sans', sans-serif; font-size: {fontsize}pt;
    }}
    QGroupBox {{
        border: 1.5px solid {border_light}; border-radius: 6px; margin-top: 6px; font-family: 'Century Gothic', Arial, 'Liberation Sans', sans-serif; font-size: {fontsize}pt;
    }}
    QGroupBox:title {{
        color: {txt_color_lightcss}; background: transparent; subcontrol-origin: margin; left: 10px; padding: 0 4px; font-family: 'Century Gothic', Arial, 'Liberation Sans', sans-serif; font-size: {fontsize}pt;
    }}
    QLabel {{ color: {txt_color_lightcss}; font-family: 'Century Gothic', Arial, 'Liberation Sans', sans-serif; font-size: {fontsize}pt; }}
    QCheckBox, QRadioButton {{ color: {txt_color_lightcss}; font-family: 'Century Gothic', Arial, 'Liberation Sans', sans-serif; font-size: {fontsize}pt; }}
    QPushButton#open_btn {{ font-size: 11pt; font-weight: bold; }}      
    QPushButton#load_btn {{ margin-bottom: 20px; }}  
    QGroupBox#skyfield_group {{ margin-bottom: 20px; }}  
    QLabel#real_length_label {{ font-size: 11pt; font-weight: bold; margin-bottom: 12px; }}      
    QLabel#length_label {{ font-size: 11pt; font-weight: bold; }}      
    QPushButton#save_object_btn {{ font-size: 12pt; font-weight: bold; }}  
    QTabWidget::pane {{ border: 1px solid {border_light}; font-family: 'Century Gothic', Arial, 'Liberation Sans', sans-serif; font-size: {fontsize}pt; }}
    QTabBar::tab {{ background: {bg_light}; color: {txt_color_lightcss}; border: 1px solid {border_light}; border-bottom: none; padding: 6px; font-family: 'Century Gothic', Arial, 'Liberation Sans', sans-serif; font-size: {fontsize}pt; }}
    QTabBar::tab:selected {{ background: #353b3c; }}
    QWidget#FramelessImageViewer {{ border-radius: 10px; border: 1.2px solid #353b3c; background-color: #232629; }}
    QWidget#CustomTitleBar {{ background-color: {bg_titlebar_light}; }}
    QWidget#CustomTitleBar QLabel {{ color: {txt_color_lightcss}; }}
    QComboBox#themeComboBox {{
        background-color: {bg_combo_light};
        color: {txt_color_lightcss};
        border: 1.2px solid #353b3c;
        border-radius: 6px;
        padding: 2px 18px 2px 8px;
        min-width: 90px;
        font-weight: bold;
    }}
    QComboBox#themeComboBox QAbstractItemView {{
        background-color: {bg_light};
        color: {txt_color_lightcss};
        border: 1.2px solid #353b3c;
        selection-background-color: #abb3ba;
        selection-color: {txt_color_lightcss};
    }}
"""

# BLUE 
txt_color_bluecss = "#B8E1F1"
bg_blue = "#041229"
bg_input_blue = "#080B2E"
bg_btn_blue = "#030845"
border_blue = "#0B104A"
bg_titlebar_blue = "#181a1b"
# StyleSheet
blue_stylesheet = f"""
    QWidget {{ background-color: {bg_blue}; color: {txt_color_bluecss}; font-family: 'Century Gothic', Arial, 'Liberation Sans', sans-serif; font-size: {fontsize}pt; }}
    QMenuBar, QMenu, QToolBar {{ background-color: {bg_blue}; color: {txt_color_bluecss}; font-family: 'Century Gothic', Arial, 'Liberation Sans', sans-serif; font-size: {fontsize}pt; }}
    QPushButton {{ background-color: {bg_btn_blue}; color: {txt_color_bluecss}; border: 1px solid {border_blue}; border-radius: 4px; padding: 4px; font-family: 'Century Gothic', Arial, 'Liberation Sans', sans-serif; font-size: {fontsize}pt; }}
    QPushButton:hover {{ background-color: #3e4446; }}
    QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
        background-color: {bg_input_blue}; color: {txt_color_bluecss}; border: 1px solid {border_blue}; border-radius: 4px; font-family: 'Century Gothic', Arial, 'Liberation Sans', sans-serif; font-size: {fontsize}pt;
    }}
    QDateEdit {{
        background-color: {bg_input_blue}; color: {txt_color_bluecss}; border: 1px solid {border_blue}; border-radius: 4px; font-family: 'Century Gothic', Arial, 'Liberation Sans', sans-serif; font-size: {fontsize}pt;
    }}
    QGroupBox {{
        border: 1.5px solid {border_blue}; border-radius: 6px; margin-top: 6px; font-family: 'Century Gothic', Arial, 'Liberation Sans', sans-serif; font-size: {fontsize}pt;
    }}
    QGroupBox:title {{
        color: {txt_color_bluecss}; background: transparent; subcontrol-origin: margin; left: 10px; padding: 0 4px; font-family: 'Century Gothic', Arial, 'Liberation Sans', sans-serif; font-size: {fontsize}pt;
    }}
    QLabel {{ color: {txt_color_bluecss}; font-family: 'Century Gothic', Arial, 'Liberation Sans', sans-serif; font-size: {fontsize}pt; }}
    QCheckBox, QRadioButton {{ color: {txt_color_bluecss}; font-family: 'Century Gothic', Arial, 'Liberation Sans', sans-serif; font-size: {fontsize}pt; }}
    QPushButton#open_btn {{ font-size: 11pt; font-weight: bold; }}      
    QPushButton#load_btn {{ margin-bottom: 20px; }}  
    QGroupBox#skyfield_group {{ margin-bottom: 20px; }}  
    QLabel#real_length_label {{ font-size: 11pt; font-weight: bold; margin-bottom: 12px; }}      
    QLabel#length_label {{ font-size: 11pt; font-weight: bold; }}      
    QPushButton#save_object_btn {{ font-size: 12pt; font-weight: bold; }}  
    QTabWidget::pane {{ border: 1px solid {border_blue}; font-family: 'Century Gothic', Arial, 'Liberation Sans', sans-serif; font-size: {fontsize}pt; }}
    QTabBar::tab {{ background: {bg_blue}; color: {txt_color_bluecss}; border: 1px solid {border_blue}; border-bottom: none; padding: 6px; font-family: 'Century Gothic', Arial, 'Liberation Sans', sans-serif; font-size: {fontsize}pt; }}
    QTabBar::tab:selected {{ background: #353b3c; }}
    QWidget#FramelessImageViewer {{ border-radius: 10px; border: 1.2px solid #353b3c; background-color: #232629; }}
    QWidget#CustomTitleBar {{ background-color: {bg_titlebar_blue}; }}
    QWidget#CustomTitleBar QLabel {{ color: {txt_color_bluecss}; }}
    QComboBox#themeComboBox {{
        background-color: #181a1b;
        color: {txt_color_bluecss};
        border: 1.2px solid #353b3c;
        border-radius: 6px;
        padding: 2px 18px 2px 8px;
        min-width: 90px;
        font-weight: bold;
    }}
    QComboBox#themeComboBox QAbstractItemView {{
        background-color: {bg_blue};
        color: {txt_color_bluecss};
        border: 1.2px solid #353b3c;
        selection-background-color: #353b3c;
        selection-color: {txt_color_bluecss};
    }}
"""


# WINDOWS 11 STYLE (neumorphism-inspired, soft, modern, no font-size or color imposed)
windows11_stylesheet = f"""
    QWidget {{
        background-color: #f3f6fb;
        border: none;
        font-family: 'Segoe UI Variable', 'Segoe UI', 'Century Gothic', Arial, 'Liberation Sans', sans-serif;
    }}
    QPushButton {{
        border: none;
        border-radius: 10px;
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f3f6fb, stop:1 #e7eaf0);
        box-shadow: 0 2px 8px 0 #e3e8f0, 0 1.5px 0 #fff;
        padding: 8px 18px;
        min-width: 70px;
        min-height: 28px;
        transition: background 0.2s, box-shadow 0.2s;
    }}
    QPushButton:hover {{
        background: #e0e6f7;
        box-shadow: 0 4px 16px 0 #d0d8e8;
    }}
    QPushButton:pressed {{
        background: #d1d9e6;
        box-shadow: 0 1px 2px 0 #c0c8d8;
    }}
    QPushButton:focus {{
        outline: 2px solid #2563eb;
        outline-offset: 2px;
    }}
    QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
        background: #f7faff;
        border: 1.5px solid #cfd8e3;
        border-radius: 8px;
        padding: 6px;
        transition: border 0.2s;
    }}
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
        border: 2px solid #2563eb;
        background: #f0f4ff;
    }}
    QGroupBox {{
        border: 1.5px solid #e3e8f0;
        border-radius: 12px;
        margin-top: 8px;
        background: #f3f6fb;
        padding-top: 10px;
    }}
    QGroupBox::title {{
        background: transparent;
        subcontrol-origin: margin;
        left: 14px;
        padding: 0 6px;
        color: #2563eb;
        font-weight: 600;
    }}
    QLabel {{
        color: #222c37;
    }}
    QCheckBox, QRadioButton {{
        padding: 3px;
        color: #222c37;
    }}
    QCheckBox::indicator, QRadioButton::indicator {{
        width: 20px;
        height: 20px;
        border-radius: 10px;
        border: 1.5px solid #cfd8e3;
        background: #fff;
    }}
    QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
        background: #2563eb;
        border: 1.5px solid #2563eb;
    }}
    QComboBox {{
        background: #f7faff;
        border: 1.5px solid #cfd8e3;
        border-radius: 8px;
        padding: 6px 22px 6px 10px;
        min-width: 100px;
    }}
    QComboBox QAbstractItemView {{
        background: #f3f6fb;
        border: 1.5px solid #cfd8e3;
        selection-background-color: #e0e6f7;
        border-radius: 8px;
    }}
    QTabWidget::pane {{
        border: 1.5px solid #e3e8f0;
        border-radius: 12px;
        background: #f3f6fb;
    }}
    QTabBar::tab {{
        background: #e7eaf0;
        color: #222c37;
        border: 1.5px solid #e3e8f0;
        border-bottom: none;
        border-radius: 10px 10px 0 0;
        padding: 8px 18px;
        margin-right: 2px;
    }}
    QTabBar::tab:selected {{
        background: #f3f6fb;
        color: #2563eb;
        font-weight: 600;
    }}
    QWidget#FramelessImageViewer {{
        border-radius: 14px;
        border: 1.5px solid #e3e8f0;
        background-color: #f3f6fb;
    }}
    QWidget#CustomTitleBar {{
        background-color: #f3f6fb;
        border-top-left-radius: 14px;
        border-top-right-radius: 14px;
    }}
    QWidget#CustomTitleBar QLabel {{
        color: #536369;
        font-weight: 600;
    }}
"""

# Tu peux ajouter d'autres palettes ici
STYLESHEETS = {
    "Dark": dark_stylesheet,
    "Light": light_stylesheet,
    "Blue": blue_stylesheet,
    "Windows 11": windows11_stylesheet,
    "Windows Dark 11": dark_stylesheet_w,
}