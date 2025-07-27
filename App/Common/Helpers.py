# App/Common/Helpers.py

from io import BytesIO
from PIL import Image
from copy import deepcopy

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QPainter, QIcon, QColor
from PySide6.QtWidgets import QApplication

from qfluentwidgets import ComboBox


#region ComboBoxes
def patch_combo_setCurrentIndex(combo: ComboBox):
    old_setCurrentIndex = combo.setCurrentIndex

    def new_setCurrentIndex(index):
        if not 0 <= index < combo.count():
            return
        text = combo.itemText(index)
        displayText = text.replace('&', '&&')
        combo._currentIndex = index
        combo.setText(displayText)
        combo.currentIndexChanged.emit(index)
        combo.currentTextChanged.emit(text)

    combo.setCurrentIndex = new_setCurrentIndex


def populate_combo_box(combo, builtin_list, user_list, target_obj=None, add_none=False):
    combo.clear()

    if add_none:
        combo.addItem("None", userData=None)

    for item in builtin_list:
        combo.addItem(item.name, userData=item)

    for item in user_list:
        combo.addItem(item.name, userData=item)

    patch_combo_setCurrentIndex(combo)

    if target_obj is not None:
        index = combo.findData(target_obj)
        if index >= 0:
            combo.setCurrentIndex(index)
#endregion


#region Image Helpers
def load_image_and_resize_image(path: str, target_size, keep_aspect=True, upscale=False, max_dim=1080) -> QPixmap:
    try:
        with Image.open(path) as img:
            if max(img.size) > max_dim:
                img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

            if keep_aspect:
                img.thumbnail(target_size, Image.Resampling.LANCZOS)
            else:
                if not upscale and (img.width < target_size[0] and img.height < target_size[1]):
                    pass
                else:
                    img = img.resize(target_size, Image.Resampling.LANCZOS)

            buffer = BytesIO()
            img.save(buffer, format='PNG')

            pixmap = QPixmap()
            pixmap.loadFromData(buffer.getvalue())
            return pixmap
    except Exception as e:
        print(f'Error loading image file: {e}')
        return QPixmap()


def apply_opacity_to_pixmap(pixmap: QPixmap, opacity: float) -> QPixmap:
    if opacity >= 1.0:
        return pixmap

    result = QPixmap(pixmap.size())
    result.fill(Qt.GlobalColor.transparent)

    painter = QPainter(result)
    painter.setOpacity(opacity)
    painter.drawPixmap(0, 0, pixmap)
    painter.end()
    return result
#endregion


#region QSS Helpers
def apply_group_box_style(is_dark: bool):
    text_color = '#FFFFFF' if is_dark else '#000000'
    border_color = '#444444' if is_dark else '#CCCCCC'

    qss = f"""
        QGroupBox {{
            color: {text_color};
            border: 1px solid {border_color};
            border-radius: 6px;
            margin-top: 6px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 3px;
        }}
    """

    QApplication.instance().setStyleSheet(qss)
#endregion


#region Misc
def make_dot_icon(color=QColor('#DA3C3C'), diameter=8):
    pixmap = QPixmap(diameter, diameter)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(color)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(0, 0, diameter, diameter)
    painter.end()

    return QIcon(pixmap)
#endregion


#region Alignment
def align_to_16(n: int) -> int:
    return (n + 0xF) & ~0xF

def pad_to_16(b: bytes) -> bytes:
    return b + (b'\x00' * (align_to_16(len(b)) - len(b)))
#endregion

#region Object Copying
def clone_bank(original, new_name: str = '', game=''):
    """ Clones an audiobank while preserving original references. """
    from App.Common.Audiobank import Audiobank
    new_entry = deepcopy(original.tableEntry)

    cloned = Audiobank(
        name=new_name or original.name,
        game=game or original.game,
        tableEntry=new_entry
    )

    cloned.instruments = list(original.instruments)
    cloned.drums = list(original.drums)
    cloned.effects = list(original.effects)

    return cloned

def clone_preset(original, new_name: str = ''):
    from App.Common.Structs import Instrument, Drum, Effect, Sample, Envelope

    name = new_name or original.name
    match original:
        case Instrument():
            return Instrument(
                name=name,
                is_relocated=original.is_relocated,
                key_region_low=original.key_region_low,
                key_region_high=original.key_region_high,
                decay_index=original.decay_index,
                envelope=original.envelope,
                low_sample=original.low_sample,
                prim_sample=original.prim_sample,
                high_sample=original.high_sample
            )
        case Drum():
            return Drum(
                name=name,
                decay_index=original.decay_index,
                pan=original.pan,
                is_relocated=original.is_relocated,
                drum_sample=original.drum_sample,
                envelope=original.envelope
            )
        case _:
            raise TypeError(f'Unsupported preset type: {type(original).__name__}')

def generate_copy_name(base_name: str, existing_names: set[str]) -> str:
    if base_name not in existing_names:
        return base_name

    copy_name = f'{base_name} Copy'
    if copy_name not in existing_names:
        return copy_name

    i = 1
    while True:
        numbered_copy = f'{base_name} Copy {i}'
        if numbered_copy not in existing_names:
            return numbered_copy
        i += 1
#endregion
