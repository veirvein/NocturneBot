import os
import ctypes
import keyboard
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QPlainTextEdit,
    QListWidget, QListWidgetItem, QFileDialog, QMessageBox,
    QGraphicsDropShadowEffect, QApplication, QSlider,
    QDialog, QGraphicsOpacityEffect, QCheckBox, QScrollArea,
    QComboBox, QLineEdit, QKeySequenceEdit
)
from PySide6.QtCore import (
    Qt, Signal, QPropertyAnimation, QEasingCurve,
    QSize, QPoint, QTimer, Property, QEvent, QSequentialAnimationGroup,
    QPauseAnimation, QAbstractAnimation
)
from PySide6.QtGui import (
    QFontDatabase, QColor, QFont, QPainter,
    QDragEnterEvent, QDropEvent, QCursor, QKeySequence
)


def apply_dark_titlebar(widget):
    try:
        hwnd = int(widget.winId())
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, 20, ctypes.byref(ctypes.c_int(1)), ctypes.sizeof(ctypes.c_int)
        )
    except Exception:
        pass


class PillSlider(QSlider):
    def __init__(self, min_val=0, max_val=100, parent=None):
        super().__init__(Qt.Horizontal, parent)
        self.setMinimum(min_val)
        self.setMaximum(max_val)
        self.setFocusPolicy(Qt.NoFocus)
        self.setFixedHeight(20)

        self._handle_color = QColor("#E080B0")
        self._handle_hover_color = QColor("#F090C0")
        self._anim = None

        self.setStyleSheet("""
            QSlider { background: transparent; }
            QSlider::groove:horizontal { height: 6px; background: #2A1E2E; border-radius: 3px; }
            QSlider::sub-page:horizontal { background: #C06090; border-radius: 3px; }
            QSlider::add-page:horizontal { background: #2A1E2E; border-radius: 3px; }
            QSlider::handle:horizontal { width: 16px; height: 16px; border-radius: 8px; margin: -5px 0; }
        """)
        self._update_handle_color(self._handle_color)

    def _update_handle_color(self, color):
        self.setStyleSheet(self.styleSheet() + f"""
            QSlider::handle:horizontal {{ background: {color.name()}; }}
        """)

    def _get_handle_color(self):
        return self._handle_color

    def _set_handle_color(self, c):
        self._handle_color = QColor(c)
        self._update_handle_color(self._handle_color)

    handleColor = Property(QColor, _get_handle_color, _set_handle_color)

    def enterEvent(self, e):
        if self._anim:
            self._anim.stop()
        self._anim = QPropertyAnimation(self, b"handleColor")
        self._anim.setDuration(300)
        self._anim.setStartValue(self._handle_color)
        self._anim.setEndValue(self._handle_hover_color)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.start()
        super().enterEvent(e)

    def leaveEvent(self, e):
        if self._anim:
            self._anim.stop()
        self._anim = QPropertyAnimation(self, b"handleColor")
        self._anim.setDuration(400)
        self._anim.setStartValue(self._handle_color)
        self._anim.setEndValue(self._handle_color)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.start()
        super().leaveEvent(e)


class AnimatedColorButton(QPushButton):
    FULL_ALPHA = 150
    DIM_ALPHA = 40

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._color = QColor("#5A8A6A")
        self._normal = QColor("#5A8A6A")
        self._hover = QColor("#6A9A7A")
        self._disabled = QColor("#4A3A4C")
        self._glow = None
        self._anim = None
        self._glow_anim = None
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setFocusPolicy(Qt.NoFocus)

    def setColors(self, normal, hover, disabled):
        self._normal = QColor(normal)
        self._hover = QColor(hover)
        self._disabled = QColor(disabled)
        self._color = QColor(self._normal if self.isEnabled() else self._disabled)
        self.update()

    def setGlow(self, effect):
        self._glow = effect
        alpha = self.FULL_ALPHA if self.isEnabled() else self.DIM_ALPHA
        gc = QColor(self._color)
        gc.setAlpha(alpha)
        self._glow.setColor(gc)

    def _get_color(self):
        return self._color

    def _set_color(self, c):
        self._color = QColor(c)
        self.update()

    bgColor = Property(QColor, _get_color, _set_color)

    def _animate_to(self, target_rgb, glow_alpha, duration):
        if self._anim:
            self._anim.stop()
        self._anim = QPropertyAnimation(self, b"bgColor")
        self._anim.setDuration(duration)
        self._anim.setStartValue(self._color)
        self._anim.setEndValue(QColor(target_rgb))
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.start()

        if self._glow:
            gc = QColor(target_rgb)
            gc.setAlpha(glow_alpha)
            if self._glow_anim:
                self._glow_anim.stop()
            self._glow_anim = QPropertyAnimation(self._glow, b"color")
            self._glow_anim.setDuration(duration)
            self._glow_anim.setStartValue(self._glow.color())
            self._glow_anim.setEndValue(gc)
            self._glow_anim.setEasingCurve(QEasingCurve.OutCubic)
            self._glow_anim.start()

    def enterEvent(self, e):
        if self.isEnabled():
            self._animate_to(self._hover, self.FULL_ALPHA, 450)
        super().enterEvent(e)

    def leaveEvent(self, e):
        if self.isEnabled():
            self._animate_to(self._normal, self.FULL_ALPHA, 500)
        super().leaveEvent(e)

    def changeEvent(self, e):
        if e.type() == QEvent.EnabledChange:
            if self.isEnabled():
                self._animate_to(self._normal, self.FULL_ALPHA, 600)
            else:
                self._animate_to(self._disabled, self.DIM_ALPHA, 600)
        super().changeEvent(e)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen)
        p.setBrush(self._color)
        p.drawRoundedRect(self.rect().adjusted(2, 2, -2, -2), 14, 14)
        p.setPen(QColor("#F0E0F0") if self.isEnabled() else QColor("#9A8A9A"))
        f = self.font()
        f.setBold(True)
        f.setPointSize(11)
        p.setFont(f)
        p.drawText(self.rect(), Qt.AlignCenter, self.text())
        p.end()


class AnimatedListItemWidget(QWidget):
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self._padding = 0
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(0)
        self.label = QLabel(text)
        self.label.setStyleSheet("color: #EAE0EA; font-size: 12px; background: transparent;")
        layout.addWidget(self.label)
        self.setLayout(layout)
        self._anim = None

    def _get_padding(self):
        return self._padding

    def _set_padding(self, v):
        self._padding = v
        self.layout().setContentsMargins(12 + v, 10, 12, 10)
        self.update()

    leftPadding = Property(int, _get_padding, _set_padding)

    def enterEvent(self, event):
        if self._anim:
            self._anim.stop()
        self._anim = QPropertyAnimation(self, b"leftPadding")
        self._anim.setDuration(250)
        self._anim.setStartValue(self._padding)
        self._anim.setEndValue(10)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.start()

    def leaveEvent(self, event):
        if self._anim:
            self._anim.stop()
        self._anim = QPropertyAnimation(self, b"leftPadding")
        self._anim.setDuration(300)
        self._anim.setStartValue(self._padding)
        self._anim.setEndValue(0)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.start()


class AnimatedListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)

    def add_animated_item(self, text, data=None):
        item = QListWidgetItem()
        widget = AnimatedListItemWidget(text)
        if data is not None:
            item.setData(Qt.UserRole, data)
        item.setSizeHint(widget.sizeHint())
        self.addItem(item)
        self.setItemWidget(item, widget)
        return item


class SettingsDialog(QDialog):
    HUMANIZE_PRESETS = {
        "Machine":       {'humanize': False, 'stddev': 1,  'release_variance': 0,  'tap_shortening': 0},
        "Near Perfect":  {'humanize': True,  'stddev': 3,  'release_variance': 1,  'tap_shortening': 2},
        "Expert":        {'humanize': True,  'stddev': 5,  'release_variance': 4,  'tap_shortening': 8},
        "Advanced":      {'humanize': True,  'stddev': 7,  'release_variance': 6,  'tap_shortening': 10},
        "Skilled":       {'humanize': True,  'stddev': 9,  'release_variance': 8,  'tap_shortening': 14},
        "Intermediate":  {'humanize': True,  'stddev': 12, 'release_variance': 12, 'tap_shortening': 20},
        "Casual":        {'humanize': True,  'stddev': 14, 'release_variance': 14, 'tap_shortening': 22},
        "Human":         {'humanize': True,  'stddev': 17, 'release_variance': 16, 'tap_shortening': 28},
        "Unsteady":      {'humanize': True,  'stddev': 19, 'release_variance': 22, 'tap_shortening': 30},
        "Sloppy":        {'humanize': True,  'stddev': 22, 'release_variance': 22, 'tap_shortening': 33},
        "Erratic":       {'humanize': True,  'stddev': 24, 'release_variance': 26, 'tap_shortening': 34},
        "Careless":      {'humanize': True,  'stddev': 27, 'release_variance': 27, 'tap_shortening': 37},
        "Chaotic":       {'humanize': True,  'stddev': 30, 'release_variance': 30, 'tap_shortening': 40},
    }

    def __init__(self, config, logger, theme_colors, font_family, bot, parent=None):
        super().__init__(parent)
        self.config = config
        self.logger = logger
        self.c = theme_colors
        self.font_family = font_family
        self.bot = bot
        self._applying_preset = False

        self.setWindowTitle("Settings")
        self.setFixedSize(440, 760)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        self._build_ui()
        self._apply_theme()
        apply_dark_titlebar(self)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        header = QFrame()
        header.setObjectName("settingsHeader")
        header.setFixedHeight(56)
        hl = QVBoxLayout(header)
        hl.setContentsMargins(24, 16, 24, 12)
        title = QLabel("Settings")
        title.setObjectName("settingsTitle")
        hl.addWidget(title)
        root.addWidget(header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        sw = QWidget()
        sl = QVBoxLayout(sw)
        sl.setContentsMargins(24, 8, 24, 24)
        sl.setSpacing(18)

        self._add_section(sl, "HOTKEYS (REBIND)")
        hf = self._card()
        hhl = QVBoxLayout(hf)
        hhl.setContentsMargins(16, 16, 16, 16)
        hhl.setSpacing(10)
        hk_g = QGridLayout()
        hk_g.setHorizontalSpacing(12)
        hk_g.setVerticalSpacing(8)
        current_hks = self.config.get('hotkeys', {})

        hk_g.addWidget(QLabel("Start bot"), 0, 0)
        self.hk_start = QKeySequenceEdit(QKeySequence(current_hks.get('start', 'F6')))
        self.hk_start.setFixedHeight(32)
        hk_g.addWidget(self.hk_start, 0, 1)

        hk_g.addWidget(QLabel("Stop bot"), 1, 0)
        self.hk_stop = QKeySequenceEdit(QKeySequence(current_hks.get('stop', 'F7')))
        self.hk_stop.setFixedHeight(32)
        hk_g.addWidget(self.hk_stop, 1, 1)

        hk_g.addWidget(QLabel("Toggle Humanize"), 2, 0)
        self.hk_humanize = QKeySequenceEdit(QKeySequence(current_hks.get('humanize', 'F8')))
        self.hk_humanize.setFixedHeight(32)
        hk_g.addWidget(self.hk_humanize, 2, 1)
        hk_g.setColumnStretch(1, 1)
        hhl.addLayout(hk_g)

        hint = QLabel("Click the field and press any key/combination to bind.")
        hint.setStyleSheet("font-size: 10px; margin-top: 4px; color: #9A8A9A;")
        hhl.addWidget(hint)
        sl.addWidget(hf)

        self._add_section(sl, "KEYBINDS (GAMEPLAY)")
        kf = self._card()
        khl = QVBoxLayout(kf)
        khl.setContentsMargins(16, 16, 16, 16)
        khl.setSpacing(12)
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Keymode:"))
        self.keymode_combo = QComboBox()
        for i in range(1, 11):
            self.keymode_combo.addItem(f"{i}K")
        self.keymode_combo.setCurrentIndex(self.bot.keys - 1)
        self.keymode_combo.currentIndexChanged.connect(self._update_keybind_ui)
        mode_layout.addWidget(self.keymode_combo)
        mode_layout.addStretch()
        khl.addLayout(mode_layout)

        self.keybinds_layout = QVBoxLayout()
        self.keybinds_layout.setSpacing(8)
        khl.addLayout(self.keybinds_layout)
        self.key_edits = []
        self._update_keybind_ui()
        sl.addWidget(kf)

        self._add_section(sl, "TIMING")
        ttf = self._card()
        ttl = QVBoxLayout(ttf)
        ttl.setContentsMargins(16, 16, 16, 16)
        ttl.setSpacing(12)
        g = QGridLayout()
        g.setContentsMargins(0, 0, 0, 0)
        g.setHorizontalSpacing(12)
        g.setVerticalSpacing(10)

        g.addWidget(self._lbl("Global offset"), 0, 0)
        self.offset_slider = PillSlider(-1000, 1000)
        self.offset_slider.setValue(self.config.get('offset', 0))
        g.addWidget(self.offset_slider, 0, 1)
        self.offset_label = QLabel(f"{self.offset_slider.value()} ms")
        self.offset_label.setFixedWidth(60)
        self.offset_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        g.addWidget(self.offset_label, 0, 2)

        g.addWidget(self._lbl("Tap duration"), 1, 0)
        self.tap_slider = PillSlider(5, 50)
        self.tap_slider.setValue(self.config.get('tap_duration', 20))
        g.addWidget(self.tap_slider, 1, 1)
        self.tap_label = QLabel(f"{self.tap_slider.value()} ms")
        self.tap_label.setFixedWidth(60)
        self.tap_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        g.addWidget(self.tap_label, 1, 2)
        g.setColumnStretch(1, 1)
        ttl.addLayout(g)
        sl.addWidget(ttf)

        self._add_section(sl, "HUMANIZE")
        huf = self._card()
        hul = QVBoxLayout(huf)
        hul.setContentsMargins(16, 16, 16, 16)
        hul.setSpacing(12)

        preset_row = QHBoxLayout()
        preset_row.addWidget(self._lbl("Preset:"))
        self.preset_combo = QComboBox()
        self.preset_combo.addItem("— Custom —")
        self.preset_combo.addItems(list(self.HUMANIZE_PRESETS.keys()))
        self.preset_combo.currentTextChanged.connect(self._apply_preset)
        preset_row.addWidget(self.preset_combo, 1)
        hul.addLayout(preset_row)

        self.humanize_check = QPushButton()
        self.humanize_check.setCheckable(True)
        self.humanize_check.setChecked(self.config.get('humanize', False))
        self.humanize_check.setFixedHeight(34)
        self.humanize_check.setCursor(QCursor(Qt.PointingHandCursor))
        self.humanize_check.setFocusPolicy(Qt.NoFocus)
        self._update_humanize_btn_text()
        self.humanize_check.toggled.connect(lambda _: self._update_humanize_btn_text())
        hul.addWidget(self.humanize_check)

        sg = QGridLayout()
        sg.setContentsMargins(0, 0, 0, 0)
        sg.setHorizontalSpacing(12)
        sg.addWidget(self._lbl("Std deviation"), 0, 0)
        self.stddev_slider = PillSlider(1, 30)
        self.stddev_slider.setValue(self.config.get('stddev', 10))
        sg.addWidget(self.stddev_slider, 0, 1)
        self.stddev_label = QLabel(f"{self.stddev_slider.value()} ms")
        self.stddev_label.setFixedWidth(60)
        self.stddev_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        sg.addWidget(self.stddev_label, 0, 2)
        sg.setColumnStretch(1, 1)
        hul.addLayout(sg)

        std_hint = QLabel("Controls timing spread & miss chance (bigger = more human-like mistakes)")
        std_hint.setStyleSheet("font-size: 10px; color: #9A8A9A;")
        std_hint.setWordWrap(True)
        hul.addWidget(std_hint)

        release_grid = QGridLayout()
        release_grid.setContentsMargins(0, 8, 0, 0)
        release_grid.setHorizontalSpacing(12)
        release_grid.addWidget(self._lbl("Release Variance"), 0, 0)
        self.release_slider = PillSlider(0, 30)
        self.release_slider.setValue(self.config.get('release_variance', 10))
        release_grid.addWidget(self.release_slider, 0, 1)
        self.release_label = QLabel(f"{self.release_slider.value()} ms")
        self.release_label.setFixedWidth(60)
        self.release_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        release_grid.addWidget(self.release_label, 0, 2)
        release_grid.setColumnStretch(1, 1)
        hul.addLayout(release_grid)

        tap_grid = QGridLayout()
        tap_grid.setContentsMargins(0, 8, 0, 0)
        tap_grid.setHorizontalSpacing(12)
        tap_grid.addWidget(self._lbl("Tap Shortening"), 0, 0)
        self.tap_short_slider = PillSlider(0, 40)
        self.tap_short_slider.setValue(self.config.get('tap_shortening', 20))
        tap_grid.addWidget(self.tap_short_slider, 0, 1)
        self.tap_short_label = QLabel(f"{self.tap_short_slider.value()} ms")
        self.tap_short_label.setFixedWidth(60)
        self.tap_short_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        tap_grid.addWidget(self.tap_short_label, 0, 2)
        tap_grid.setColumnStretch(1, 1)
        hul.addLayout(tap_grid)

        sl.addWidget(huf)
        sl.addStretch()

        self.scroll.setWidget(sw)
        root.addWidget(self.scroll, 1)

        bb = QFrame()
        bb.setObjectName("btnBar")
        br = QHBoxLayout(bb)
        br.setContentsMargins(24, 12, 24, 16)
        br.setSpacing(10)

        cb = QPushButton("Cancel")
        cb.setObjectName("cancelBtn")
        cb.setFixedHeight(40)
        cb.setCursor(QCursor(Qt.PointingHandCursor))
        cb.setFocusPolicy(Qt.NoFocus)
        cb.clicked.connect(self.reject)
        br.addWidget(cb)

        sb = QPushButton("Save")
        sb.setObjectName("saveBtn")
        sb.setFixedHeight(40)
        sb.setCursor(QCursor(Qt.PointingHandCursor))
        sb.setFocusPolicy(Qt.NoFocus)
        sb.clicked.connect(self._save)

        save_glow = QGraphicsDropShadowEffect(self)
        save_glow.setBlurRadius(16)
        gc = QColor(self.c['primary'])
        gc.setAlpha(110)
        save_glow.setColor(gc)
        save_glow.setOffset(0, 3)
        sb.setGraphicsEffect(save_glow)

        br.addWidget(sb)
        root.addWidget(bb)

        self.offset_slider.valueChanged.connect(lambda v: self.offset_label.setText(f"{v} ms"))
        self.tap_slider.valueChanged.connect(lambda v: self.tap_label.setText(f"{v} ms"))
        self.stddev_slider.valueChanged.connect(lambda v: self.stddev_label.setText(f"{v} ms"))
        self.release_slider.valueChanged.connect(lambda v: self.release_label.setText(f"{v} ms"))
        self.tap_short_slider.valueChanged.connect(lambda v: self.tap_short_label.setText(f"{v} ms"))

        self.stddev_slider.valueChanged.connect(self._mark_custom)
        self.release_slider.valueChanged.connect(self._mark_custom)
        self.tap_short_slider.valueChanged.connect(self._mark_custom)
        self.humanize_check.toggled.connect(self._mark_custom)
        self._sync_preset_combo()

    def _apply_preset(self, name):
        p = self.HUMANIZE_PRESETS.get(name)
        if not p:
            return
        self._applying_preset = True
        self.humanize_check.setChecked(p['humanize'])
        self.stddev_slider.setValue(p['stddev'])
        self.release_slider.setValue(p['release_variance'])
        self.tap_short_slider.setValue(p['tap_shortening'])
        self._applying_preset = False

    def _mark_custom(self, *args):
        if self._applying_preset:
            return
        self.preset_combo.blockSignals(True)
        self.preset_combo.setCurrentIndex(0)
        self.preset_combo.blockSignals(False)

    def _sync_preset_combo(self):
        cur = {
            'humanize': self.humanize_check.isChecked(),
            'stddev': self.stddev_slider.value(),
            'release_variance': self.release_slider.value(),
            'tap_shortening': self.tap_short_slider.value(),
        }
        for name, p in self.HUMANIZE_PRESETS.items():
            if p == cur:
                self.preset_combo.blockSignals(True)
                self.preset_combo.setCurrentText(name)
                self.preset_combo.blockSignals(False)
                return
        self.preset_combo.setCurrentIndex(0)

    def _update_keybind_ui(self):
        def _clear_layout(layout):
            if layout is None:
                return
            while layout.count():
                item = layout.takeAt(0)
                if item.layout() is not None:
                    _clear_layout(item.layout())
                elif item.widget() is not None:
                    item.widget().setParent(None)
                    item.widget().deleteLater()

        _clear_layout(self.keybinds_layout)
        self.key_edits.clear()

        mode = self.keymode_combo.currentIndex() + 1
        binds = self.config.get('key_binds', {})
        layout = binds.get(str(mode), self.bot.LAYOUTS.get(mode, []))

        for i in range(mode):
            row = QHBoxLayout()
            row.addWidget(QLabel(f"Key {i+1}:"))
            edit = QLineEdit(str(layout[i]) if i < len(layout) else "")
            edit.setMaxLength(15)
            edit.setFixedWidth(120)
            row.addWidget(edit)
            row.addStretch()
            self.keybinds_layout.addLayout(row)
            self.key_edits.append(edit)

    def _card(self):
        f = QFrame()
        f.setObjectName("card")
        return f

    def _lbl(self, t):
        return QLabel(t)

    def _add_section(self, l, t):
        x = QLabel(t)
        x.setObjectName("section")
        l.addWidget(x)

    def _update_humanize_btn_text(self):
        self.humanize_check.setText(
            "Disable Humanize" if self.humanize_check.isChecked() else "Enable Humanize"
        )

    def _save(self):
        self.config.set('offset', self.offset_slider.value())
        self.config.set('tap_duration', self.tap_slider.value())
        self.config.set('stddev', self.stddev_slider.value())
        self.config.set('humanize', self.humanize_check.isChecked())
        self.config.set('release_variance', self.release_slider.value())
        self.config.set('tap_shortening', self.tap_short_slider.value())

        mode = self.keymode_combo.currentIndex() + 1
        new_layout = [edit.text().strip().lower() for edit in self.key_edits]

        if len(new_layout) != mode or any(not k for k in new_layout):
            QMessageBox.warning(self, "Keybinds", f"All {mode} key fields must be filled.")
            return
        if len(set(new_layout)) != len(new_layout):
            QMessageBox.warning(self, "Keybinds", "Duplicate keys — each column needs its own key.")
            return
        unknown = [k for k in new_layout if k not in self.bot.SUPPORTED_KEYS]
        if unknown:
            QMessageBox.warning(self, "Keybinds", "Unsupported keys: " + ", ".join(unknown))
            return

        binds = self.config.get('key_binds', {})
        binds[str(mode)] = new_layout
        self.config.set('key_binds', binds)

        hotkeys = {
            'start': self.hk_start.keySequence().toString().lower(),
            'stop': self.hk_stop.keySequence().toString().lower(),
            'humanize': self.hk_humanize.keySequence().toString().lower()
        }
        self.config.set('hotkeys', hotkeys)

        if self.bot.map_data:
            map_keys = self.bot.map_data.get('keys', self.bot.keys)
            if map_keys != mode:
                QMessageBox.information(
                    self, "Keymode",
                    f"Saved binds for {mode}K.\nCurrent map is {map_keys}K — these binds will apply to {mode}K maps."
                )
            else:
                self.bot.keys = mode
                self.bot._events_ready = False
        else:
            self.bot.keys = mode
            self.bot._events_ready = False

        self.accept()

    def _apply_theme(self):
        c = self.c
        self.setStyleSheet(f"""
            QDialog {{ background-color: {c['bg']}; font-family: '{self.font_family}', 'Segoe UI', sans-serif; }}
            QLabel {{ color: {c['text']}; font-size: 12px; background: transparent; }}
            QLabel#section {{ color: {c['primary']}; font-size: 11px; font-weight: 700; letter-spacing: 1px; }}
            QFrame#settingsHeader {{ background-color: {c['bg']}; }}
            QLabel#settingsTitle {{ color: {c['primary']}; font-size: 20px; font-weight: 700; }}
            QFrame#card {{ background-color: {c['bg_secondary']}; border-radius: 10px; border: 1px solid {c['border']}; }}
            QPushButton {{ background-color: {c['bg_card']}; color: {c['text']}; border: none; border-radius: 8px; font-size: 12px; font-weight: 500; }}
            QPushButton:hover {{ background-color: {c['border']}; }}
            QPushButton:checked {{ background-color: {c['primary']}; color: white; }}
            QScrollArea {{ background: transparent; border: none; }}
            QScrollArea > QWidget > QWidget {{ background: transparent; }}
            QScrollBar:vertical {{ background: transparent; width: 8px; margin: 4px 2px; }}
            QScrollBar::handle:vertical {{ background: {c['border']}; border-radius: 4px; min-height: 30px; }}
            QScrollBar::handle:vertical:hover {{ background: {c['primary']}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
            QFrame#btnBar {{ background-color: {c['bg']}; border-top: 1px solid {c['border']}; border-radius: 0; }}
            QPushButton#saveBtn {{ background-color: {c['primary']}; color: white; font-weight: 600; }}
            QPushButton#saveBtn:hover {{ background-color: {c['primary_hover']}; }}
            QPushButton#cancelBtn {{ background-color: {c['bg_secondary']}; color: {c['text']}; }}
            QPushButton#cancelBtn:hover {{ background-color: {c['border']}; }}
            QComboBox, QLineEdit, QKeySequenceEdit {{ background-color: {c['bg']}; color: {c['text']}; border: 1px solid {c['border']}; border-radius: 6px; padding: 4px 8px; }}
        """)


class ModsDialog(QDialog):
    def __init__(self, config, logger, theme_colors, font_family, parent=None):
        super().__init__(parent)
        self.config = config
        self.logger = logger
        self.c = theme_colors
        self.font_family = font_family

        self.setWindowTitle("Mods")
        self.setFixedSize(440, 400)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        self._build_ui()
        self._apply_theme()
        apply_dark_titlebar(self)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 20)
        root.setSpacing(16)

        t = QLabel("GAMEPLAY MODS")
        t.setObjectName("modsTitle")
        root.addWidget(t)

        f = QFrame()
        f.setObjectName("modsCard")
        fl = QVBoxLayout(f)
        fl.setContentsMargins(18, 16, 18, 16)
        fl.setSpacing(14)

        self.dt = QCheckBox("Double Time / Nightcore (1.5x)")
        self.dt.setChecked(self.config.get('mod_dt', False))
        self.dt.setCursor(QCursor(Qt.PointingHandCursor))
        fl.addWidget(self.dt)

        self.ht = QCheckBox("Half Time (0.75x)")
        self.ht.setChecked(self.config.get('mod_ht', False))
        self.ht.setCursor(QCursor(Qt.PointingHandCursor))
        fl.addWidget(self.ht)

        self.dt.toggled.connect(lambda on: self.ht.setChecked(False) if on else None)
        self.ht.toggled.connect(lambda on: self.dt.setChecked(False) if on else None)

        self.mi = QCheckBox("Mirror (flip columns)")
        self.mi.setChecked(self.config.get('mod_mirror', False))
        self.mi.setCursor(QCursor(Qt.PointingHandCursor))
        fl.addWidget(self.mi)

        self.ra = QCheckBox("Random (shuffle columns)")
        self.ra.setChecked(self.config.get('mod_random', False))
        self.ra.setCursor(QCursor(Qt.PointingHandCursor))
        fl.addWidget(self.ra)

        root.addWidget(f)
        root.addStretch()

        btnbar = QFrame()
        btnbar.setObjectName("modsBtnBar")
        bbl = QHBoxLayout(btnbar)
        bbl.setContentsMargins(10, 10, 10, 10)
        bbl.setSpacing(10)
        bbl.addStretch()

        cb = QPushButton("Cancel")
        cb.setObjectName("mCancelBtn")
        cb.setFixedHeight(38)
        cb.setMinimumWidth(112)
        cb.setCursor(QCursor(Qt.PointingHandCursor))
        cb.setFocusPolicy(Qt.NoFocus)
        cb.clicked.connect(self.reject)
        bbl.addWidget(cb)

        sb = QPushButton("Save")
        sb.setObjectName("mSaveBtn")
        sb.setFixedHeight(38)
        sb.setMinimumWidth(112)
        sb.setCursor(QCursor(Qt.PointingHandCursor))
        sb.setFocusPolicy(Qt.NoFocus)
        sb.clicked.connect(self._save)
        bbl.addWidget(sb)

        save_glow = QGraphicsDropShadowEffect(self)
        save_glow.setBlurRadius(16)
        gc = QColor(self.c['primary'])
        gc.setAlpha(110)
        save_glow.setColor(gc)
        save_glow.setOffset(0, 3)
        sb.setGraphicsEffect(save_glow)

        root.addWidget(btnbar)

    def _save(self):
        self.config.set('mod_dt', self.dt.isChecked())
        self.config.set('mod_ht', self.ht.isChecked())
        self.config.set('mod_mirror', self.mi.isChecked())
        self.config.set('mod_random', self.ra.isChecked())
        self.accept()

    def _apply_theme(self):
        c = self.c
        self.setStyleSheet(f"""
            QDialog {{ background-color: {c['bg']}; font-family: '{self.font_family}', 'Segoe UI', sans-serif; }}
            QLabel {{ color: {c['text']}; font-size: 12px; background: transparent; }}
            QLabel#modsTitle {{ color: {c['primary']}; font-size: 11px; font-weight: 700; letter-spacing: 1px; background: transparent; }}
            QFrame#modsCard {{ background-color: {c['bg_secondary']}; border-radius: 12px; border: 1px solid {c['border']}; }}
            QFrame#modsBtnBar {{ background-color: {c['bg_card']}; border-radius: 12px; border: 1px solid {c['border']}; }}
            QCheckBox {{ color: {c['text']}; font-size: 12px; spacing: 8px; background: transparent; }}
            QCheckBox::indicator {{ width: 18px; height: 18px; border-radius: 4px; border: 2px solid {c['border']}; background: {c['bg']}; }}
            QCheckBox::indicator:hover {{ border-color: {c['primary']}; }}
            QCheckBox::indicator:checked {{ background: {c['primary']}; border-color: {c['primary']}; }}
            QPushButton#mCancelBtn {{ background-color: transparent; color: {c['text_muted']}; border: 1px solid {c['border']}; border-radius: 9px; font-size: 12px; font-weight: 600; }}
            QPushButton#mCancelBtn:hover {{ background-color: {c['border']}; color: {c['text']}; }}
            QPushButton#mSaveBtn {{ background-color: {c['primary']}; color: white; border: none; border-radius: 9px; font-size: 12px; font-weight: 700; }}
            QPushButton#mSaveBtn:hover {{ background-color: {c['primary_hover']}; }}
        """)


class InfoDialog(QDialog):
    def __init__(self, theme_colors, font_family, parent=None):
        super().__init__(parent)
        self.c = theme_colors
        self.font_family = font_family
        self.setWindowTitle("Info")
        self.setFixedSize(400, 470)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self._build_ui()
        self._apply_theme()
        apply_dark_titlebar(self)

        self.glow_anim = QPropertyAnimation(self.wordmark_glow, b"blurRadius")
        self.glow_anim.setDuration(2400)
        self.glow_anim.setStartValue(20.0)
        self.glow_anim.setKeyValueAt(0.5, 38.0)
        self.glow_anim.setEndValue(20.0)
        self.glow_anim.setEasingCurve(QEasingCurve.InOutSine)
        self.glow_anim.setLoopCount(-1)
        self.glow_anim.start()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 36, 32, 24)
        root.setSpacing(0)

        self.wordmark = QLabel("Nocturne!")
        self.wordmark.setObjectName("wordmark")
        self.wordmark.setAlignment(Qt.AlignCenter)
        root.addWidget(self.wordmark)

        sub = QLabel("bot")
        sub.setObjectName("wordmarkSub")
        sub.setAlignment(Qt.AlignCenter)
        root.addWidget(sub)

        root.addSpacing(10)

        vb_row = QHBoxLayout()
        vb_row.addStretch()
        version_badge = QLabel("v1.0.0")
        version_badge.setObjectName("versionBadge")
        vb_row.addWidget(version_badge)
        vb_row.addStretch()
        root.addLayout(vb_row)

        root.addSpacing(22)
        root.addWidget(self._divider())
        root.addSpacing(22)

        role = QLabel("CREATED & DESIGNED BY")
        role.setObjectName("roleLabel")
        role.setAlignment(Qt.AlignCenter)
        root.addWidget(role)

        name = QLabel("veirvein")
        name.setObjectName("nameLabel")
        name.setAlignment(Qt.AlignCenter)
        root.addWidget(name)

        root.addSpacing(22)
        root.addWidget(self._divider())
        root.addSpacing(18)

        for role_text, name_text in [
            ("CORE LOGIC", "veirvein"),
            ("INTERFACE", "veirvein"),
            ("HUMANIZE ENGINE", "veirvein"),
        ]:
            row = QHBoxLayout()
            r = QLabel(role_text)
            r.setObjectName("creditRole")
            n = QLabel(name_text)
            n.setObjectName("creditName")
            row.addWidget(r)
            row.addStretch()
            row.addWidget(n)
            root.addLayout(row)
            root.addSpacing(10)

        root.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setObjectName("infoCloseBtn")
        close_btn.setFixedHeight(38)
        close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        close_btn.setFocusPolicy(Qt.NoFocus)
        close_btn.clicked.connect(self.accept)
        root.addWidget(close_btn)

        self.wordmark_glow = QGraphicsDropShadowEffect(self)
        self.wordmark_glow.setBlurRadius(20)
        gc = QColor(self.c['primary'])
        gc.setAlpha(160)
        self.wordmark_glow.setColor(gc)
        self.wordmark.setGraphicsEffect(self.wordmark_glow)

    def _divider(self):
        d = QFrame()
        d.setObjectName("divider")
        d.setFixedHeight(1)
        return d

    def _apply_theme(self):
        c = self.c
        self.setStyleSheet(f"""
            QDialog {{ background-color: {c['bg']}; font-family: '{self.font_family}', 'Segoe UI', sans-serif; }}
            QLabel {{ background: transparent; }}
            QLabel#wordmark {{ color: {c['primary']}; font-size: 40px; font-weight: 800; letter-spacing: 1px; }}
            QLabel#wordmarkSub {{ color: {c['text']}; font-size: 14px; font-weight: 600; letter-spacing: 5px; margin-top: 2px; }}
            QLabel#versionBadge {{ color: {c['text_muted']}; font-size: 9px; letter-spacing: 1px; background: transparent; border: none; padding: 0; margin-top: 10px; }}
            QLabel#roleLabel {{ color: {c['accent']}; font-size: 10px; font-weight: 700; letter-spacing: 3px; }}
            QLabel#nameLabel {{ color: {c['text']}; font-size: 24px; font-weight: 700; margin-top: 6px; }}
            QLabel#creditRole {{ color: {c['text_muted']}; font-size: 10px; font-weight: 600; letter-spacing: 2px; }}
            QLabel#creditName {{ color: {c['text']}; font-size: 12px; font-weight: 600; }}
            QFrame#divider {{ background-color: {c['border']}; border: none; }}
            QPushButton#infoCloseBtn {{ background-color: {c['bg_card']}; color: {c['text']}; border: 1px solid {c['border']}; border-radius: 9px; font-size: 12px; font-weight: 600; }}
            QPushButton#infoCloseBtn:hover {{ background-color: {c['border']}; }}
        """)


class App(QMainWindow):
    log_signal = Signal(str)
    start_signal = Signal()
    stop_signal = Signal()
    humanize_signal = Signal()

    THEME = {
        'bg': '#120C16',
        'bg_secondary': '#1C1521',
        'bg_card': '#261F2B',
        'text': '#EAE0EA',
        'text_muted': '#8A7E8A',
        'primary': '#B85A82',
        'primary_hover': '#C96A92',
        'accent': '#D080A0',
        'border': '#3A2E3A',
        'start': '#5A8A6A',
        'start_hover': '#6A9A7A',
        'stop': '#8A5A5A',
        'stop_hover': '#9A6A6A',
        'drop_glow': '#B85A82',
        'log_bg': '#0D0710',
        'log_text': '#B8E8B8',
    }

    def __init__(self, config, logger, bot, sound):
        super().__init__()
        self.config = config
        self.logger = logger
        self.bot = bot
        self.sound = sound
        self.c = self.THEME

        self.log_signal.connect(self._insert_log)
        self.start_signal.connect(self.start_bot)
        self.stop_signal.connect(self.stop_bot)
        self.humanize_signal.connect(self._toggle_humanize_hotkey)

        self._drop_glow_anim = None
        self._log_anim_group = None

        self._load_font()
        self._setup_window()
        self._build_ui()
        self._apply_theme()
        self._apply_dark_titlebar()
        self._setup_hotkeys()

        last = self.config.get('last_map_path', '')
        if last and os.path.exists(last):
            self.load_map(last)
        self._update_recent_maps()

    def _load_font(self):
        p = os.path.join(os.path.dirname(__file__), 'fonts', 'PlusJakartaSans-VariableFont_wght.ttf')
        if os.path.exists(p):
            QFontDatabase.addApplicationFont(p)
            self.font_family = 'Plus Jakarta Sans'
        else:
            self.font_family = 'Segoe UI'

    def _setup_window(self):
        self.setWindowTitle("Nocturne! bot")
        self.resize(540, 720)
        self.setMinimumSize(500, 650)

    def _apply_dark_titlebar(self):
        apply_dark_titlebar(self)

    def _start_drop_glow_pulse(self):
        if not self.drop_shadow:
            return
        if self._drop_glow_anim and self._drop_glow_anim.state() == QAbstractAnimation.Running:
            self._drop_glow_anim.stop()
        self._drop_glow_anim = QPropertyAnimation(self.drop_shadow, b"blurRadius")
        self._drop_glow_anim.setDuration(2000)
        self._drop_glow_anim.setStartValue(25.0)
        self._drop_glow_anim.setKeyValueAt(0.5, 42.0)
        self._drop_glow_anim.setEndValue(25.0)
        self._drop_glow_anim.setEasingCurve(QEasingCurve.InOutSine)
        self._drop_glow_anim.setLoopCount(-1)
        self._drop_glow_anim.start()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(20, 15, 20, 12)
        root.setSpacing(10)

        h = QHBoxLayout()
        self.title_label = QLabel("Nocturne! bot")
        self.title_label.setObjectName("title")
        h.addWidget(self.title_label)
        h.addStretch()

        self.mods_btn = QPushButton("Mods")
        self.mods_btn.setObjectName("modsBtn")
        self.mods_btn.setFixedHeight(32)
        self.mods_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.mods_btn.setFocusPolicy(Qt.NoFocus)
        self.mods_btn.clicked.connect(self._open_mods)
        h.addWidget(self.mods_btn)

        self.settings_btn = QPushButton("Settings")
        self.settings_btn.setObjectName("settingsBtn")
        self.settings_btn.setFixedHeight(32)
        self.settings_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.settings_btn.setFocusPolicy(Qt.NoFocus)
        self.settings_btn.clicked.connect(self._open_settings)
        h.addWidget(self.settings_btn)

        self.info_btn = QPushButton("Info")
        self.info_btn.setObjectName("infoBtn")
        self.info_btn.setFixedHeight(32)
        self.info_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.info_btn.setFocusPolicy(Qt.NoFocus)
        self.info_btn.clicked.connect(self._open_info)
        h.addWidget(self.info_btn)

        root.addLayout(h)

        self.drop_frame = QFrame()
        self.drop_frame.setObjectName("dropFrame")
        self.drop_frame.setAcceptDrops(True)
        self.drop_frame.setFixedHeight(120)
        self.drop_frame.setCursor(QCursor(Qt.PointingHandCursor))
        self.drop_frame.dragEnterEvent = self._drag_enter
        self.drop_frame.dragLeaveEvent = self._drag_leave
        self.drop_frame.dropEvent = self._drop
        self.drop_frame.mousePressEvent = lambda e: self.choose_file()

        dl = QVBoxLayout(self.drop_frame)
        dl.setAlignment(Qt.AlignCenter)
        self.drop_label = QLabel("Drop .osu file here or click to browse")
        self.drop_label.setObjectName("dropLabel")
        self.drop_label.setAlignment(Qt.AlignCenter)
        dl.addWidget(self.drop_label)
        root.addWidget(self.drop_frame)

        self.map_card = QFrame()
        self.map_card.setObjectName("mapCard")
        ml = QVBoxLayout(self.map_card)
        ml.setContentsMargins(16, 14, 16, 14)
        ml.setSpacing(6)
        self.map_title_label = QLabel("No map loaded")
        self.map_title_label.setObjectName("mapTitle")
        self.map_title_label.setWordWrap(True)
        ml.addWidget(self.map_title_label)
        self.map_meta_label = QLabel("")
        self.map_meta_label.setObjectName("mapMeta")
        self.map_meta_label.setWordWrap(True)
        ml.addWidget(self.map_meta_label)
        root.addWidget(self.map_card)

        rh = QLabel("RECENT MAPS")
        rh.setObjectName("sectionTitle")
        root.addWidget(rh)

        self.recent_list = AnimatedListWidget()
        self.recent_list.setObjectName("recentList")
        self.recent_list.setFixedHeight(160)
        self.recent_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.recent_list.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.recent_list.itemClicked.connect(self._on_recent_clicked)
        root.addWidget(self.recent_list)

        bts = QHBoxLayout()
        bts.setSpacing(12)

        self.start_btn = AnimatedColorButton("START")
        self.start_btn.setObjectName("startBtn")
        self.start_btn.setFixedHeight(48)
        self.start_btn.clicked.connect(self.start_bot)
        bts.addWidget(self.start_btn)

        self.stop_btn = AnimatedColorButton("STOP")
        self.stop_btn.setObjectName("stopBtn")
        self.stop_btn.setFixedHeight(48)
        self.stop_btn.clicked.connect(self.stop_bot)
        bts.addWidget(self.stop_btn)
        root.addLayout(bts)

        self.logs_visible = self.config.get('logs_visible', False)
        lh = QHBoxLayout()
        self.logs_toggle_btn = QPushButton("Logs")
        self.logs_toggle_btn.setObjectName("logsToggle")
        self.logs_toggle_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.logs_toggle_btn.setFocusPolicy(Qt.NoFocus)
        self.logs_toggle_btn.clicked.connect(self._toggle_logs)
        lh.addWidget(self.logs_toggle_btn)
        lh.addStretch()
        cb = QPushButton("Clear")
        cb.setObjectName("clearBtn")
        cb.setCursor(QCursor(Qt.PointingHandCursor))
        cb.setFocusPolicy(Qt.NoFocus)
        cb.clicked.connect(self._clear_logs)
        lh.addWidget(cb)
        root.addLayout(lh)

        self.log_container = QFrame()
        self.log_container.setObjectName("logContainer")
        ll = QVBoxLayout(self.log_container)
        ll.setContentsMargins(0, 0, 0, 0)
        self.log_text = QPlainTextEdit()
        self.log_text.setObjectName("logText")
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumBlockCount(500)
        self.log_text.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.log_text.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        ll.addWidget(self.log_text)
        root.addWidget(self.log_container)

        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("statusBar")
        self.status_label.setFixedHeight(28)
        root.addWidget(self.status_label)

        if self.logs_visible:
            self.log_container.setMaximumHeight(200)
            self.logs_toggle_btn.setText("Logs  ▾")
        else:
            self.log_container.setMaximumHeight(0)
            self.logs_toggle_btn.setText("Logs  ▸")

    def _apply_theme(self):
        c = self.c
        qss = f"""
            QMainWindow, QWidget {{ background-color: {c['bg']}; }}
            QLabel#title {{ color: {c['primary']}; font-size: 22px; font-weight: 700; background: transparent; letter-spacing: 0.5px; }}
            QPushButton#modsBtn, QPushButton#settingsBtn, QPushButton#infoBtn {{
                background-color: #2A1E2E; color: {c['text_muted']};
                border: 1px solid {c['border']}; border-radius: 10px; padding: 0 16px;
                font-size: 12px; font-weight: 600;
            }}
            QPushButton#modsBtn:hover, QPushButton#settingsBtn:hover, QPushButton#infoBtn:hover {{
                background-color: #35253A; color: {c['text']};
            }}
            QFrame#dropFrame {{
                background-color: {c['bg_card']};
                border: 1.5px solid {c['primary']};
                border-radius: 18px;
            }}
            QFrame#dropFrame:hover {{
                border-color: {c['primary_hover']};
                background-color: #2D2433;
            }}
            QLabel#dropLabel {{ color: {c['text_muted']}; font-size: 14px; background: transparent; }}
            QFrame#mapCard {{
                background-color: {c['bg_card']};
                border-radius: 16px;
                border: 1px solid transparent;
            }}
            QFrame#mapCard:hover {{ border-color: #3A2E3A; }}
            QLabel#mapTitle {{ color: {c['text']}; font-size: 14px; font-weight: 600; background: transparent; }}
            QLabel#mapMeta {{ color: {c['text_muted']}; font-size: 12px; background: transparent; }}
            QLabel#sectionTitle {{
                color: {c['accent']}; font-size: 11px; font-weight: 700;
                letter-spacing: 1px; padding: 4px 0; background: transparent;
            }}
            QListWidget#recentList {{
                background-color: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 14px;
                color: {c['text']}; font-size: 12px; outline: none;
            }}
            QListWidget#recentList::item {{
                background: transparent;
                border: none;
            }}
            QPushButton#logsToggle {{
                background-color: transparent; color: {c['accent']};
                border: none; font-size: 13px; font-weight: 700; padding: 4px 0;
            }}
            QPushButton#logsToggle:hover {{ color: {c['primary_hover']}; }}
            QPushButton#clearBtn {{ background-color: transparent; color: {c['text_muted']}; border: none; font-size: 12px; }}
            QPushButton#clearBtn:hover {{ color: {c['text']}; }}
            QFrame#logContainer {{ background-color: transparent; border: none; }}
            QPlainTextEdit#logText {{
                background-color: {c['log_bg']}; color: {c['log_text']};
                border: 1px solid {c['border']}; border-radius: 14px;
                font-family: Consolas, monospace; font-size: 11px; padding: 8px;
            }}
            QPlainTextEdit#logText QScrollBar:vertical {{ width: 0px; background: transparent; }}
            QLabel#statusBar {{
                background-color: {c['bg_secondary']};
                color: {c['text_muted']}; border-radius: 10px;
                padding: 0 14px; font-size: 11px;
            }}
        """
        self.setStyleSheet(qss)
        QApplication.instance().setFont(QFont(self.font_family, 10))

        self.drop_shadow = QGraphicsDropShadowEffect(self)
        self.drop_shadow.setBlurRadius(30)
        gc = QColor(c['drop_glow'])
        gc.setAlpha(100)
        self.drop_shadow.setColor(gc)
        self.drop_shadow.setOffset(0, 0)
        self.drop_frame.setGraphicsEffect(self.drop_shadow)
        self._start_drop_glow_pulse()

        self.start_glow = self._make_glow(self.start_btn, blur=25, y=0, alpha=90)
        self.start_btn.setColors(c['start'], c['start_hover'], '#3A2E3A')
        self.start_btn.setGlow(self.start_glow)

        self.stop_glow = self._make_glow(self.stop_btn, blur=25, y=0, alpha=90)
        self.stop_btn.setColors(c['stop'], c['stop_hover'], '#3A2E3A')
        self.stop_btn.setGlow(self.stop_glow)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 3)
        self.recent_list.setGraphicsEffect(shadow)

    def _glow(self, w, color_hex, blur=25, y=0, alpha=120):
        s = QGraphicsDropShadowEffect(self)
        s.setBlurRadius(blur)
        qc = QColor(color_hex)
        qc.setAlpha(alpha)
        s.setColor(qc)
        s.setOffset(0, y)
        w.setGraphicsEffect(s)
        return s

    def _make_glow(self, w, blur=25, y=0, alpha=90):
        s = QGraphicsDropShadowEffect(self)
        s.setBlurRadius(blur)
        s.setOffset(0, y)
        c = QColor(0, 0, 0, 0)
        s.setColor(c)
        w.setGraphicsEffect(s)
        return s

    def _set_drop_glow(self, bright):
        pass

    def _open_settings(self):
        d = SettingsDialog(self.config, self.logger, self.c, self.font_family, self.bot, self)
        if d.exec():
            self._setup_hotkeys()

    def _open_mods(self):
        d = ModsDialog(self.config, self.logger, self.c, self.font_family, self)
        if d.exec():
            self.bot.rebuild_events()
            self.logger.info(f"Mods updated. Active mods: {self.bot.get_active_mods_text()}")

    def _open_info(self):
        d = InfoDialog(self.c, self.font_family, self)
        d.exec()

    def _drag_enter(self, e: QDragEnterEvent):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def _drag_leave(self, e):
        pass

    def _drop(self, e: QDropEvent):
        urls = e.mimeData().urls()
        if urls:
            p = urls[0].toLocalFile()
            if p.lower().endswith('.osu'):
                self.load_map(p)

    def choose_file(self):
        p, _ = QFileDialog.getOpenFileName(self, "Select .osu file", "", "osu files (*.osu);;All files (*.*)")
        if p:
            self.load_map(p)

    def load_map(self, filepath):
        self.logger.info(f"Loading: {os.path.basename(filepath)}")
        if self.bot.load_map(filepath):
            d = self.bot.map_data
            ls = d.get('length_seconds', 0)
            lstr = f"{int(ls // 60)}:{int(ls % 60):02d}"
            bpm = d.get('bpm', 0)
            bstr = f"{bpm:.1f}" if bpm > 0 else "N/A"
            self.map_title_label.setText(f"{d['artist']} - {d['title']}")
            self.map_meta_label.setText(f"[{d['version']}]  •  {d['keys']}K  •  {bstr} BPM  •  {lstr}")
            self.status_label.setText("Map loaded")
            self._add_to_recent(filepath)
        else:
            self.sound.play('error')
            QMessageBox.critical(self, "Error", "Failed to load map.\nCheck logs.")

    def _add_to_recent(self, p):
        r = self.config.get('recent_maps', [])
        if p in r:
            r.remove(p)
        r.insert(0, p)
        self.config.set('recent_maps', r[:30])
        self._update_recent_maps()

    def _update_recent_maps(self):
        self.recent_list.clear()
        for p in self.config.get('recent_maps', []):
            if os.path.exists(p):
                self.recent_list.add_animated_item(os.path.basename(p), data=p)

    def _on_recent_clicked(self, item):
        p = item.data(Qt.UserRole)
        if p and os.path.exists(p):
            self.load_map(p)

    def start_bot(self):
        if not self.bot.map_data:
            QMessageBox.warning(self, "Warning", "Load a map first!")
            return
        if self.bot.playing:
            return
        if self.bot.start():
            self.status_label.setText("Playing...")
            self.start_btn.setEnabled(False)

    def stop_bot(self):
        if self.bot.playing:
            self.bot.stop()
            self.status_label.setText("Stopped")
        self.start_btn.setEnabled(True)

    def _toggle_humanize_hotkey(self):
        is_on = not self.config.get('humanize', False)
        self.config.set('humanize', is_on)
        self.status_label.setText(f"Humanize: {'ON' if is_on else 'OFF'}")
        self.logger.info(f"Humanize set to {is_on}")

    def _toggle_logs(self):
        self.logs_visible = not self.logs_visible
        self.config.set('logs_visible', self.logs_visible)

        if self._log_anim_group and self._log_anim_group.state() == QAbstractAnimation.Running:
            self._log_anim_group.stop()

        anim = QPropertyAnimation(self.log_container, b"maximumHeight")
        anim.setDuration(400)
        anim.setEasingCurve(QEasingCurve.InOutCubic)

        if self.logs_visible:
            anim.setStartValue(0)
            anim.setEndValue(200)
            self.logs_toggle_btn.setText("Logs  ▾")
        else:
            anim.setStartValue(self.log_container.height())
            anim.setEndValue(0)
            self.logs_toggle_btn.setText("Logs  ▸")

        self._log_anim_group = QSequentialAnimationGroup()
        self._log_anim_group.addPause(80)
        self._log_anim_group.addAnimation(anim)
        self._log_anim_group.start()

    def _clear_logs(self):
        self.log_text.clear()

    def append_log(self, msg):
        self.log_signal.emit(msg)

    def _insert_log(self, msg):
        self.log_text.appendPlainText(msg)

    def _setup_hotkeys(self):
        try:
            keyboard.unhook_all()
        except Exception:
            pass

        hk = self.config.get('hotkeys', {})
        hotkey_defs = [
            ('start', self.start_signal),
            ('stop', self.stop_signal),
            ('humanize', self.humanize_signal),
        ]

        registered = 0
        for name, signal in hotkey_defs:
            key = hk.get(name)
            if not key:
                continue
            try:
                keyboard.add_hotkey(key, lambda s=signal: s.emit())
                registered += 1
            except Exception as e:
                self.logger.warning(f"Hotkey '{name}' ({key}) failed: {e}")

        if registered:
            self.logger.info(f"Hotkeys registered: {registered}/3")
        else:
            self.logger.warning("No hotkeys registered. Run as admin.")

    def closeEvent(self, e):
        self.bot.stop()
        try:
            keyboard.unhook_all()
        except:
            pass
        e.accept()