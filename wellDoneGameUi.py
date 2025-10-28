from PySide6 import QtCore, QtGui, QtWidgets
from shiboken6 import wrapInstance
import maya.OpenMayaUI as omui
import importlib
import sys, os
import time

# Support running as a package (relative import) or as a standalone script
try:
    from . import wellDoneGameUtil as wdutil
except Exception:
    import wellDoneGameUtil as wdutil
try:
    importlib.reload(wdutil)
except Exception:
    pass

SOURCE_PATH = os.path.join(os.path.dirname(__file__), "source_image", "image")

class GameMenu(QtWidgets.QWidget):
    def __init__(self, stacked_widget, parent=None):
        super().__init__(parent)
        self.stacked_widget = stacked_widget

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.bg = QtWidgets.QLabel(self)
        self.bg.setPixmap(QtGui.QPixmap(f"{SOURCE_PATH}/background.png"))
        self.bg.setScaledContents(True)
        self.bg.lower()

        self.menuLayout = QtWidgets.QVBoxLayout()
        self.menuLayout.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.menuLayout.setContentsMargins(90, 90, 0, 0)

        self.startButton = QtWidgets.QPushButton('START')
        self.startButton.clicked.connect(lambda: stacked_widget.setCurrentIndex(2))
        self.startButton.setStyleSheet("""
            QPushButton {
                background-color: rgba(216, 110, 14, 0);
                color: #7f7b71;
                border-radius: 2px;
                font-size: 40px;
                font-family: "Showcard Gothic";
                padding: 2px;
            }
            QPushButton:hover {
                background-color: rgba(216, 110, 14, 180);
                color: #e1e8e4;
            }
            QPushButton:pressed {
                background-color: rgba(75, 53, 42, 255);
                color: white;
            }
        """)

        self.howtoplayButton = QtWidgets.QPushButton('HOW TO PLAY')
        self.howtoplayButton.clicked.connect(lambda: stacked_widget.setCurrentIndex(1))
        self.howtoplayButton.setStyleSheet("""
            QPushButton {
                background-color: rgba(216, 110, 14, 0);
                color: #7f7b71;
                border-radius: 2px;
                font-size: 22px;
                font-family: "Showcard Gothic";
                padding: 8px;
            }
            QPushButton:hover {
                background-color: rgba(216, 110, 14, 180);
                color: #e1e8e4;
            }
            QPushButton:pressed {
                background-color: rgba(75, 53, 42, 255);
                color: white;
            }
        """)


        self.exitButton = QtWidgets.QPushButton('EXIT')
        self.exitButton.clicked.connect(self.close_main_window)
        self.exitButton.setStyleSheet("""
            QPushButton {
                background-color: rgba(216, 110, 14, 0);
                color: #7f7b71;
                border-radius: 2px;
                font-size: 28px;
                font-family: "Showcard Gothic";
                padding: 8px;
            }
            QPushButton:hover {
                background-color: rgba(216, 110, 14, 180);
                color: #e1e8e4;
            }
            QPushButton:pressed {
                background-color: rgba(75, 53, 42, 255);
                color: white;
            }
        """)


        for b in [self.startButton, self.howtoplayButton, self.exitButton]:
            b.setFixedWidth(300)
            self.menuLayout.addWidget(b)

        self.layout.addLayout(self.menuLayout)

    def resizeEvent(self, event):
        if self.bg and self.bg.pixmap():
            self.bg.setGeometry(self.rect()) 
        super().resizeEvent(event)


    def close_main_window(self):
        main_window = self.window()
        if main_window:
            main_window.hide()
            main_window.deleteLater()


class HowToPlayPage(QtWidgets.QWidget):
    def __init__(self, stacked_widget, parent=None):
        super().__init__(parent)
        self.stacked_widget = stacked_widget
        layout = QtWidgets.QHBoxLayout(self)
        back = QtWidgets.QPushButton("⬅️")
        back.setFixedSize(80, 60)
        back.clicked.connect(lambda: stacked_widget.setCurrentIndex(0))
        img = QtWidgets.QLabel()
        img.setPixmap(QtGui.QPixmap(f"{SOURCE_PATH}/howtoplay.webp"))
        img.setScaledContents(True)
        img.setFixedSize(1200, 675)
        layout.addWidget(back, alignment=QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        layout.addWidget(img, alignment=QtCore.Qt.AlignCenter)

class GameWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setStyleSheet("background-color: #8BC34A;")  # สีพื้นสนาม
        self.objects = []


        # สร้างวัตถุในฉาก
        self.create_game_objects()

        # ตัวละคร (เชฟ)
        self.has_item = False
        self.current_item = None
        self.held_icon = None

        self.placed_items = []

        self.pot_icons = []  # เก็บ QLabel ของวัตถุดิบบน pot
        self.pot_contents = [] # ข้อมูลวัตถุดิบ

        self.chef = QtWidgets.QLabel(self)
        chef_pixmap = QtGui.QPixmap(f"{SOURCE_PATH}/chef.png")

        # ให้รองรับ transparency และไม่ขึ้นสีพื้น
        self.chef.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.chef.setStyleSheet("background: transparent;")

        self.chef.setPixmap(chef_pixmap)
        self.chef.setScaledContents(True)
        self.chef.resize(111.875, 133.33)
        self.chef.move(200, 400)
        self.chef_speed = 8


        # ตัวจับเวลาเดินอัตโนมัติ
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_position)
        self.timer.start(16)
        self.pressed_keys = set()

    def create_image_object(self, x, y, w, h, image_name):
        """สร้าง QLabel ที่มีภาพ"""
        obj = QtWidgets.QLabel(self)
        obj.setGeometry(x, y, w, h)
        obj.setStyleSheet("background: transparent;")
        pix = QtGui.QPixmap(f"{SOURCE_PATH}/{image_name}")
        obj.setPixmap(pix)
        obj.setScaledContents(True)
        self.objects.append(obj)
        return obj

    def create_game_objects(self):
        # เตา (stove)
        self.pot = self.create_image_object(310, 154, 90, 106, "pot.png")
        self.pot_icons = []
        self.pot_contents = []

        self.chopping_board = self.create_image_object(467, 185, 70, 50, "chopping_board.png")
        self.chopping_board_icons = []

        # จุดเสิร์ฟ (serve)
        self.serve_station = self.create_image_object(1158, 163, 160, 229, "serve_station.png")
        self.plate_station = self.create_image_object(1167, 353, 100, 85, "plate_station.png")
        self.trash_bin = self.create_image_object(1045, 172, 90, 90, "trash_bin.png")

        # โต๊ะ (table)
        self.create_image_object(150, 500, 1240, 715, "table.png")

        # วัตถุดิบ (ingredients)
        self.ingredients = []  # ✅ เก็บรายการวัตถุดิบ

        tomato = self.create_image_object(920, 477, 80, 80, "tomato.png")
        lettuce = self.create_image_object(853, 460, 90, 130, "lettuce.png")
        cucamber = self.create_image_object(980, 475, 90, 80, "cucamber.png")

        # ใส่ใน list เพื่อใช้ตรวจชน
        self.ingredients = [
            {"name": "tomato", "widget": tomato},
            {"name": "lettuce", "widget": lettuce},
            {"name": "cucamber", "widget": cucamber},
        ]


    def keyPressEvent(self, event):
        key = event.key()
        self.pressed_keys.add(key)

        # 🎯 ปุ่ม F = ใช้ทำหลายอย่าง (หยิบ, ใส่จาน, ทิ้ง, รับจาน)
        if key == QtCore.Qt.Key_F:

            # ----- 1️⃣ กรณีถืออะไรอยู่ -----
            if self.has_item:
                # ถ้าอยู่ใกล้ถังขยะ → ทิ้งของ
                if wdutil.is_near_trash(self):
                    wdutil.try_throw_item_to_trash(self)

                # ถ้าอยู่ใกล้จาน → ใส่วัตถุดิบลงจาน
                # ถ้าอยู่ใกล้ plate station → ใส่ลงจานที่ station
                elif hasattr(self, "plate_station") and wdutil.is_near_object(self.chef, self.plate_station):
                    wdutil.add_item_to_plate(self, self.current_item)
                    # ล้างของในมือ
                    self.has_item = False
                    self.current_item = None
                    if getattr(self, "held_icon", None):
                        self.held_icon.deleteLater()
                        self.held_icon = None

                elif getattr(self, "dropped_plates", None) and any(
                    wdutil.is_near_object(self.chef, plate_dict.get("label"))
                    for plate_dict in self.dropped_plates
                    if plate_dict.get("label") is not None
                ):
                    # หา plate ที่อยู่ใกล้ที่สุดและใส่ของลงไปบนจานที่พื้น
                    for plate_dict in list(self.dropped_plates):
                        plate_label = plate_dict.get("label")
                        if plate_label and wdutil.is_near_object(self.chef, plate_label):
                            wdutil.add_item_to_dropped_plate(self, plate_dict, self.current_item)
                            break

                    # ล้างของในมือ
                    self.has_item = False
                    self.current_item = None
                    if getattr(self, "held_icon", None):
                        self.held_icon.deleteLater()
                        self.held_icon = None

                # ถ้าเราถือจานอยู่และถือวัตถุดิบด้วย → ใส่ลงในจานที่ถือ
                elif getattr(self, "has_plate", False):
                    wdutil.add_item_to_held_plate(self, self.current_item)
                    # ล้างของในมือ
                    self.has_item = False
                    self.current_item = None
                    if getattr(self, "held_icon", None):
                        self.held_icon.deleteLater()
                        self.held_icon = None

                # ถ้าไม่เข้าเงื่อนไขอื่น ๆ → วางของ (drop)
                else:
                    wdutil.drop_item(self)

            # ----- 2️⃣ ถ้าไม่มีวัตถุดิบ แต่ถือจานอยู่ -----
            elif getattr(self, "has_plate", False):
                # ถ้าอยู่ใกล้ถังขยะ → ทิ้งจาน
                if wdutil.is_near_trash(self):
                    wdutil.throw_plate_to_trash(self)
                # ถ้าอยู่ใกล้จุดเสิร์ฟ → เสิร์ฟจาน
                elif wdutil.try_serve_plate(self):
                    # เสิร์ฟเสร็จแล้ว ฟังก์ชันจะจัดการ state ให้
                    return
                else:
                    pass  # ยังไม่วาง (ใช้ปุ่ม G วางแทน)

            # ----- 3️⃣ ถ้าไม่มีของในมือเลย -----
            else:
                # พยายามหยิบจานก่อน (เพราะจานมี priority สูงกว่า item)
                if wdutil.try_pickup_plate(self):
                    return
                # ถ้าไม่เจอจาน → พยายามหยิบวัตถุดิบแทน
                wdutil.try_pick_item(self)

        # 🎯 ปุ่ม G = วางของ/จานบนพื้น
        elif key == QtCore.Qt.Key_G:
            if getattr(self, "has_plate", False):
                wdutil.drop_plate(self)
            elif self.has_item:
                wdutil.drop_item(self)

        # 🔪 ปุ่ม Space = ใช้ทำ action เช่น หั่นของ
        elif key == QtCore.Qt.Key_Space:
            wdutil.process_space_action(self)

    def keyReleaseEvent(self, event):
        key = event.key()
        if key in self.pressed_keys:
            self.pressed_keys.remove(key)

    def update_position(self):
        dx = dy = 0
        if QtCore.Qt.Key_Left in self.pressed_keys:
            dx -= self.chef_speed
        if QtCore.Qt.Key_Right in self.pressed_keys:
            dx += self.chef_speed
        if QtCore.Qt.Key_Up in self.pressed_keys:
            dy -= self.chef_speed
        if QtCore.Qt.Key_Down in self.pressed_keys:
            dy += self.chef_speed

        new_x = max(0, min(self.chef.x() + dx, self.width() - self.chef.width()))
        new_y = max(0, min(self.chef.y() + dy, self.height() - self.chef.height()))
        self.chef.move(new_x, new_y)

        if getattr(self, "held_icon", None):
            icon_x = new_x + (self.chef.width() - self.held_icon.width()) // 2
            icon_y = new_y - self.held_icon.height() - 5
            self.held_icon.move(icon_x, icon_y)

        if getattr(self, "has_plate", False) and hasattr(self, "held_plate"):
            wdutil.update_plate_position(self, self.chef, self.held_plate)


class Overlay(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 150);")
        layout = QtWidgets.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignCenter)

        # Message shown in overlay (used for Pause and Game Over)
        self.message_label = QtWidgets.QLabel("", self)
        self.message_label.setStyleSheet("color: white; font-size: 34px; font-weight: bold;")
        self.message_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.message_label)

        # Buttons area
        self.continue_btn = QtWidgets.QPushButton("Continue")
        self.quit_btn = QtWidgets.QPushButton("Quit")
        for btn in (self.continue_btn, self.quit_btn):
            btn.setFixedSize(150, 50)
            btn.setStyleSheet("font-size: 20px;")
            layout.addWidget(btn)

        # state flag (True when overlay is showing game-over)
        self.is_game_over = False

    def set_paused(self):
        self.is_game_over = False
        self.message_label.setText("Paused")
        self.continue_btn.setText("Continue")

    def set_game_over(self, score):
        self.is_game_over = True
        self.message_label.setText(f"Game Over\nScore: {score}")
        self.continue_btn.setText("Restart")


class GamePage(QtWidgets.QWidget):
    """แทน MainWindow เดิม แต่เป็น QWidget"""
    def __init__(self, stacked_widget, parent=None):
        super().__init__(parent)
        self.stacked_widget = stacked_widget

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.bg_label = QtWidgets.QLabel(self)
        self.bg_label.setScaledContents(True)  # ให้ขยายเต็มพื้นที่ widget
        self.bg_pixmap = QtGui.QPixmap(f"{SOURCE_PATH}/bg_kitchen.png")
        self.bg_label.setPixmap(self.bg_pixmap)
        self.bg_label.lower()

        self.game_widget = GameWidget()
        layout.addWidget(self.game_widget)
        # ให้ game widget ได้รับ focus เพื่อรับ key events (เช่น Space)
        self.game_widget.setFocus()

        # Score / Time / Orders labels (create early so helpers can use them)
        self.score_label = QtWidgets.QLabel("Score: 0", self)
        self.score_label.setGeometry(10, 655, 150, 30)
        self.score_label.setStyleSheet("font-size: 18px; background-color: white;")

        self.time_label = QtWidgets.QLabel("Time: 120", self)
        self.time_label.setGeometry(1150, 655, 150, 30)
        self.time_label.setStyleSheet("font-size: 18px; background-color: white;")

        self.order_label = QtWidgets.QLabel("Orders:", self)
        self.order_label.setGeometry(10, 10, 400, 40)
        self.order_label.setStyleSheet("font-size: 20px; background-color: white; text-align: center;")

        # Game clock
        self.remaining_time = 120
        self.time_label.setText(f"Time: {self.remaining_time}")
        self.game_clock = QtCore.QTimer(self)
        self.game_clock.timeout.connect(self._tick_game_clock)
        self.game_clock.start(1000)

        # Orders: scan available plate combo images
        try:
            files = os.listdir(os.path.join(os.path.dirname(__file__), "source_image", "image"))
            combos = [f[len("plate_"):-4] for f in files if f.startswith("plate_") and f.lower().endswith('.png')]
        except Exception:
            combos = []
        if not combos:
            combos = ["tomato_chopped", "lettuce_chopped", "cucamber_chopped"]

        import random
        # maintain a queue of 3 orders
        self.orders = [random.choice(combos) for _ in range(3)]
        self._refresh_orders_label()


        # ปุ่ม Pause
        self.pause_btn = QtWidgets.QPushButton("Pause", self)
        self.pause_btn.setGeometry(1200, 10, 100, 40)
        self.pause_btn.clicked.connect(self.show_overlay)
        self.pause_btn.setStyleSheet("font-size: 16px; background-color: #FFF;")

        # Overlay
        self.overlay = Overlay(self)
        self.overlay.setGeometry(0, 0, 1200, 675)
        self.overlay.hide()
        # connect to a handler that can decide between resume or restart
        self.overlay.continue_btn.clicked.connect(self._overlay_continue_clicked)
        self.overlay.quit_btn.clicked.connect(self.back_to_menu)
        

    def resizeEvent(self, event):
        self.bg_label.setGeometry(0, 0, self.width(), self.height())
        self.overlay.setGeometry(0, 0, self.width(), self.height())
        super().resizeEvent(event)

    def showEvent(self, event):
        # เมื่อหน้า GamePage ปรากฎ ให้โฟกัสที่ game_widget เพื่อรับ key events (เช่น Space)
        try:
            self.game_widget.setFocus()
        except Exception:
            pass
        super().showEvent(event)

    def show_overlay(self):
        # pause game timers
        try:
            self.game_clock.stop()
        except Exception:
            pass
        try:
            self.game_widget.timer.stop()
        except Exception:
            pass
        # Set overlay to paused mode and show
        try:
            self.overlay.set_paused()
        except Exception:
            pass
        self.overlay.show()

    def hide_overlay(self):
        self.overlay.hide()
        # resume game timers
        try:
            self.game_clock.start(1000)
        except Exception:
            pass
        try:
            self.game_widget.timer.start(16)
        except Exception:
            pass

    def _tick_game_clock(self):
        self.remaining_time -= 1
        if self.remaining_time < 0:
            self.remaining_time = 0
        self.time_label.setText(f"Time: {self.remaining_time}")
        if self.remaining_time <= 0:
            # time up -> show overlay and stop timers
            try:
                self.game_clock.stop()
            except Exception:
                pass
            try:
                self.game_widget.timer.stop()
            except Exception:
                pass
            # show game-over overlay with final score
            try:
                # parse numeric score from label
                text = self.score_label.text()
                score = int(text.split(":")[-1].strip())
            except Exception:
                score = 0
            try:
                self.overlay.set_game_over(score)
            except Exception:
                pass
            self.overlay.show()

    def _overlay_continue_clicked(self):
        """Called when overlay continue/restart button is clicked."""
        try:
            if getattr(self.overlay, 'is_game_over', False):
                self.restart_game()
            else:
                self.hide_overlay()
        except Exception:
            try:
                self.hide_overlay()
            except Exception:
                pass

    def restart_game(self):
        """Reset game state to allow a fresh playthrough."""
        # reset time and score
        self.remaining_time = 120
        self.time_label.setText(f"Time: {self.remaining_time}")
        self.score_label.setText("Score: 0")

        # clear items from the game widget
        gw = self.game_widget
        try:
            for lbl in list(getattr(gw, 'placed_items', [])):
                try:
                    lbl.deleteLater()
                except Exception:
                    pass
            gw.placed_items = []
        except Exception:
            gw.placed_items = []

        try:
            for lbl in list(getattr(gw, 'pot_icons', [])):
                try:
                    lbl.deleteLater()
                except Exception:
                    pass
            gw.pot_icons = []
            gw.pot_contents = []
        except Exception:
            gw.pot_icons = []
            gw.pot_contents = []

        try:
            for lbl in list(getattr(gw, 'chopping_board_icons', [])):
                try:
                    lbl.deleteLater()
                except Exception:
                    pass
            gw.chopping_board_icons = []
        except Exception:
            gw.chopping_board_icons = []

        try:
            for pd in list(getattr(gw, 'dropped_plates', [])):
                try:
                    lab = pd.get('label')
                    if lab:
                        lab.deleteLater()
                except Exception:
                    pass
            gw.dropped_plates = []
        except Exception:
            gw.dropped_plates = []

        try:
            if getattr(gw, 'held_plate', None):
                gw.held_plate.deleteLater()
            gw.held_plate = None
        except Exception:
            gw.held_plate = None

        try:
            if getattr(gw, 'held_icon', None):
                gw.held_icon.deleteLater()
            gw.held_icon = None
        except Exception:
            gw.held_icon = None

        gw.has_item = False
        gw.current_item = None
        gw.has_plate = False
        gw.plate_items = []
        gw.station_plate_items = []

        # regenerate orders
        try:
            files = os.listdir(os.path.join(os.path.dirname(__file__), "source_image", "image"))
            combos = [f[len("plate_"):-4] for f in files if f.startswith("plate_") and f.lower().endswith('.png')]
        except Exception:
            combos = []
        if not combos:
            combos = ["tomato_chopped", "lettuce_chopped", "cucamber_chopped"]
        import random
        self.orders = [random.choice(combos) for _ in range(3)]
        self._refresh_orders_label()

        # hide overlay and restart timers
        try:
            self.overlay.set_paused()
        except Exception:
            pass
        try:
            self.overlay.hide()
        except Exception:
            pass
        try:
            self.game_clock.start(1000)
        except Exception:
            pass
        try:
            self.game_widget.timer.start(16)
        except Exception:
            pass

    def _refresh_orders_label(self):
        # display orders nicely
        disp = " | ".join(self.orders)
        self.order_label.setText(f"Orders: {disp}")

    def back_to_menu(self):
        self.overlay.hide()
        self.stacked_widget.setCurrentIndex(0)

class WellDoneGame(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Well Done! 🧑‍🍳")
        self.resize(1200, 675)

        self.stacked = QtWidgets.QStackedWidget()
        self.page1 = GameMenu(self.stacked)
        self.page2 = HowToPlayPage(self.stacked)
        self.page3 = GamePage(self.stacked)

        self.stacked.addWidget(self.page1)
        self.stacked.addWidget(self.page2)
        self.stacked.addWidget(self.page3)
        self.setCentralWidget(self.stacked)


def run():
    global ui
    try:
        ui.close()
        ui.deleteLater()
    except:
        pass

    ptr = wrapInstance(int(omui.MQtUtil.mainWindow()), QtWidgets.QWidget)
    ui = WellDoneGame(parent=ptr)
    ui.show()