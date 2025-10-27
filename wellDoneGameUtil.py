import os
from PySide6 import QtWidgets, QtCore, QtGui

SOURCE_PATH = os.path.join(os.path.dirname(__file__), "source_image")

# ------------------- การหยิบของ -------------------
def try_pick_item(game_widget, threshold=50):
    if getattr(game_widget, "has_item", False):
        print("เชฟถือของอยู่แล้ว 🧺")
        return

    chef_geom = game_widget.chef.geometry()
    chef_center = QtCore.QPoint(
        chef_geom.x() + chef_geom.width() // 2,
        chef_geom.y() + chef_geom.height() // 2
    )

    found = False

    # 1️⃣ ตรวจสอบ ingredients
    for ing in getattr(game_widget, "ingredients", []):
        name = ing["name"]
        ing_widget = ing["widget"]
        ing_geom = ing_widget.geometry()
        ing_center = QtCore.QPoint(
            ing_geom.x() + ing_geom.width() // 2,
            ing_geom.y() + ing_geom.height() // 2
        )
        dx = chef_center.x() - ing_center.x()
        dy = chef_center.y() - ing_center.y()
        distance = (dx**2 + dy**2) ** 0.5
        if distance <= threshold:
            game_widget.has_item = True
            game_widget.current_item = name
            print(f"✅ หยิบวัตถุดิบ: {name}")
            show_pick_feedback(game_widget, name)
            found = True
            break

    # 2️⃣ ตรวจสอบ placed_items (บนพื้น)
    if not found and hasattr(game_widget, "placed_items"):
        for item_label in list(game_widget.placed_items):  # ใช้ list() เพื่อแก้ไขระหว่าง loop
            name = getattr(item_label, "item_name", None)
            if not name:
                continue

            item_geom = item_label.geometry()
            item_center = QtCore.QPoint(
                item_geom.x() + item_geom.width() // 2,
                item_geom.y() + item_geom.height() // 2
            )
            dx = chef_center.x() - item_center.x()
            dy = chef_center.y() - item_center.y()
            distance = (dx**2 + dy**2) ** 0.5

            if distance <= threshold:
                game_widget.has_item = True
                game_widget.current_item = name
                print(f"✅ หยิบวัตถุดิบจากพื้น: {name}")

                show_pick_feedback(game_widget, name)

                # เอา icon ของวัตถุดิบบนพื้นออก
                item_label.deleteLater()
                game_widget.placed_items.remove(item_label)
                found = True
                break

    if not found:
        print("❌ ไม่ได้อยู่ใกล้วัตถุดิบใด ๆ")

# ------------------- icon ติดตามเชฟ -------------------
def show_pick_feedback(game_widget, item_name):
    pix_path = os.path.join(SOURCE_PATH, "image", f"{item_name}_icon.png")
    pix = QtGui.QPixmap(pix_path)
    if pix.isNull():
        return

    if getattr(game_widget, "held_icon", None):
        game_widget.held_icon.deleteLater()
        game_widget.held_icon = None

    icon_label = QtWidgets.QLabel(game_widget)
    icon_label.setPixmap(pix)
    icon_label.setScaledContents(True)
    icon_label.resize(40, 40)

    icon_label.setAttribute(QtCore.Qt.WA_TranslucentBackground)
    icon_label.setStyleSheet("background: transparent;")

    icon_label.show()
    game_widget.held_icon = icon_label

    update_held_icon_position(game_widget)

def update_held_icon_position(game_widget):
    if getattr(game_widget, "held_icon", None):
        drop_x = game_widget.chef.x() + (game_widget.chef.width() - 40) // 2
        drop_y = game_widget.chef.y() - 40 - 5
        game_widget.held_icon.move(drop_x, drop_y)

# ------------------- วางของ -------------------
def drop_item(game_widget):
    """ฟังก์ชันวางของจากมือเชฟลงในจุดต่าง ๆ (เขียง, หม้อ, พื้น, ถังขยะ)"""
    if not getattr(game_widget, "has_item", False):
        print("❌ ไม่มีของในมือ")
        return

    item_name = game_widget.current_item

    # ✅ ถ้าอยู่ใกล้ถังขยะ → ทิ้งของ
    if is_near_trash(game_widget):
        try_throw_item_to_trash(game_widget)
        return

    # --- ตรวจสอบว่ามี object จำเป็นหรือไม่ ---
    if not hasattr(game_widget, "chef"):
        print("⚠️ ไม่มี chef ในเกม")
        return

    # --- เตรียมตำแหน่งวาง ---
    drop_x = game_widget.chef.x() + (game_widget.chef.width() - 40) // 2
    drop_y = game_widget.chef.y() + game_widget.chef.height() - 10

    # --- สร้าง QLabel แสดงของ ---
    item_label = QtWidgets.QLabel(game_widget)
    pix_path = os.path.join(SOURCE_PATH, "image", f"{item_name}_icon.png")
    if not os.path.exists(pix_path):
        print(f"⚠️ ไม่พบภาพ: {pix_path}")
        return

    pix = QtGui.QPixmap(pix_path)
    item_label.setPixmap(pix)
    item_label.setScaledContents(True)
    item_label.resize(40, 40)
    item_label.move(drop_x, drop_y)
    item_label.setAttribute(QtCore.Qt.WA_TranslucentBackground)
    item_label.setStyleSheet("background: transparent;")
    item_label.show()

    # ตั้งชื่อไอเทมทั้งเป็น attribute และ Qt property เพื่อให้ฟังก์ชันอื่นเรียกใช้ได้
    try:
        item_label.item_name = item_name
    except Exception:
        pass
    try:
        item_label.setProperty("item_name", item_name)
    except Exception:
        pass

    # --- คำนวณตำแหน่งศูนย์กลางของเชฟ ---
    chef_center = QtCore.QPoint(
        game_widget.chef.x() + game_widget.chef.width() // 2,
        game_widget.chef.y() + game_widget.chef.height() // 2
    )

    placed = False  # flag ตรวจว่าของถูกวางตรงไหนแล้วหรือยัง

    # 🪵 เขียง (chopping board)
    if hasattr(game_widget, "chopping_board"):
        board_geom = game_widget.chopping_board.geometry()
        board_center = QtCore.QPoint(
            board_geom.x() + board_geom.width() // 2,
            board_geom.y() + board_geom.height() // 2
        )
        dx = chef_center.x() - board_center.x()
        dy = chef_center.y() - board_center.y()
        distance_board = (dx ** 2 + dy ** 2) ** 0.5

        if distance_board <= 50:
            if not hasattr(game_widget, "chopping_board_icons"):
                game_widget.chopping_board_icons = []
            # ตั้งชื่อไอเทมเพื่อให้ process_space_action หาเจอ
            try:
                item_label.item_name = item_name
            except Exception:
                pass
            try:
                item_label.setProperty("item_name", item_name)
            except Exception:
                pass
            game_widget.chopping_board_icons.append(item_label)
            print(f"🔪 วาง {item_name} บน chopping board")
            placed = True

    # 🍲 หม้อ (pot)
    if not placed and hasattr(game_widget, "pot"):
        pot_geom = game_widget.pot.geometry()
        pot_center = QtCore.QPoint(
            pot_geom.x() + pot_geom.width() // 2,
            pot_geom.y() + pot_geom.height() // 2
        )
        dx = chef_center.x() - pot_center.x()
        dy = chef_center.y() - pot_center.y()
        distance_pot = (dx ** 2 + dy ** 2) ** 0.5

        if distance_pot <= 50:
            if not hasattr(game_widget, "pot_icons"):
                game_widget.pot_icons = []
            if not hasattr(game_widget, "pot_contents"):
                game_widget.pot_contents = []

            game_widget.pot_icons.append(item_label)
            game_widget.pot_contents.append(item_name)
            # ตั้งชื่อไอเทมบน icon ด้วย
            try:
                item_label.item_name = item_name
            except Exception:
                pass
            try:
                item_label.setProperty("item_name", item_name)
            except Exception:
                pass
            print(f"🥘 วาง {item_name} ลงหม้อ")

            count = game_widget.pot_contents.count(item_name)
            if count == 3:
                print(f"🎉 {item_name.replace('_chopped', '')} ต้มเสร็จแล้ว!")
                for _ in range(3):
                    game_widget.pot_contents.remove(item_name)
                for icon in game_widget.pot_icons[:3]:
                    icon.deleteLater()
                    game_widget.pot_icons.remove(icon)
            placed = True

    # 🌾 ถ้าไม่อยู่ใกล้ที่ไหนเลย → วางบนพื้น
    if not placed:
        print(f"📦 วาง {item_name} บนพื้น")
        item_label.item_name = item_name
        if not hasattr(game_widget, "placed_items"):
            game_widget.placed_items = []
        game_widget.placed_items.append(item_label)

    # 🧺 ล้างของในมือเชฟ
    if getattr(game_widget, "held_icon", None):
        game_widget.held_icon.deleteLater()
        game_widget.held_icon = None

    game_widget.has_item = False
    game_widget.current_item = None


# ------------------- หั่น -------------------
def process_space_action(game_widget):
    for icon_label in game_widget.chopping_board_icons:
        # สมมติเราจำชื่อใน property name
        chopped_name = icon_label.property("item_name")
        if not chopped_name:
            continue
        chopped_name = f"{chopped_name}_chopped"
        pix_path = os.path.join(SOURCE_PATH, "image", f"{chopped_name}_icon.png")
        pix = QtGui.QPixmap(pix_path)
        if not pix.isNull():
            icon_label.setPixmap(pix)
            icon_label.setScaledContents(True)
            icon_label.setProperty("item_name", chopped_name)
            print(f"✅ หั่นวัตถุดิบ: {chopped_name}")

# ------------------- ทิ้งของลงถังขยะ ------------------

def try_throw_item_to_trash(game_widget, threshold=80):
    """
    ถ้าอยู่ใกล้ trash_bin → ทิ้งของในมือ (หรือของที่พื้นใกล้ถัง)
    """
    if not hasattr(game_widget, "trash_bin"):
        print("❌ ไม่มี trash_bin ในเกม")
        return

    chef_geom = game_widget.chef.geometry()
    trash_geom = game_widget.trash_bin.geometry()

    chef_center = QtCore.QPoint(
        chef_geom.x() + chef_geom.width() // 2,
        chef_geom.y() + chef_geom.height() // 2
    )
    trash_center = QtCore.QPoint(
        trash_geom.x() + trash_geom.width() // 2,
        trash_geom.y() + trash_geom.height() // 2
    )

    dx = chef_center.x() - trash_center.x()
    dy = chef_center.y() - trash_center.y()
    distance = (dx**2 + dy**2) ** 0.5

    if distance > threshold:
        print(f"🚫 ยังไม่ใกล้ถังพอ ({int(distance)} px)")
        return

    # ถ้ามีของในมือ → ทิ้ง
    if getattr(game_widget, "has_item", False):
        item_name = game_widget.current_item
        print(f"🗑️ ทิ้งของ: {item_name}")
        game_widget.has_item = False
        game_widget.current_item = None

        if getattr(game_widget, "held_icon", None):
            game_widget.held_icon.deleteLater()
            game_widget.held_icon = None
        return

    # ถ้าไม่มีของในมือ → ลบของที่พื้นใกล้ถัง
    if hasattr(game_widget, "placed_items"):
        for item_label in list(game_widget.placed_items):
            item_geom = item_label.geometry()
            item_center = QtCore.QPoint(
                item_geom.x() + item_geom.width() // 2,
                item_geom.y() + item_geom.height() // 2
            )
            dx = trash_center.x() - item_center.x()
            dy = trash_center.y() - item_center.y()
            dist_item = (dx**2 + dy**2) ** 0.5

            if dist_item <= threshold:
                print(f"🗑️ เก็บ {item_label.item_name} ทิ้งถังขยะ")
                item_label.deleteLater()
                game_widget.placed_items.remove(item_label)

    print("🧹 ทำความสะอาดเรียบร้อย!")

# ============================================================
# 🧺 ฟังก์ชันเกี่ยวกับ "จาน (Plate)"
# ============================================================

def add_item_to_plate(game_widget, item_name):
    """เพิ่มวัตถุดิบลงในจานและอัปเดตภาพ"""
    if not hasattr(game_widget, "plate_station"):
        print("❌ ไม่มี plate_station ในเกม")
        return

    if not hasattr(game_widget, "plate_items"):
        game_widget.plate_items = []

    # ตรวจว่าอยู่ใกล้จานไหม (ใช้ plate_station)
    plate_obj = getattr(game_widget, "plate_station", None)
    if plate_obj is None or not is_near_object(game_widget.chef, plate_obj, mode="center"):
        print("❌ ไม่ได้อยู่ใกล้จาน")
        return

    # เพิ่มของลงจาน
    game_widget.plate_items.append(item_name)
    print(f"🍽️ ใส่ {item_name} ลงจาน")

    update_plate_image(game_widget)


def update_plate_image(game_widget, target_label=None, items=None):
    """อัปเดตภาพจาน (ทั้งในมือ บนพื้น หรือใน station)"""
    if target_label is None:
        target_label = getattr(game_widget, "plate_station", None)
        if target_label is None:
            print("❌ ไม่มี target_label สำหรับจาน")
            return

    if items is None:
        items = sorted(getattr(game_widget, "plate_items", []))
    else:
        items = sorted(items)

    combo_name = "_".join(items)
    combo_image_name = f"plate_{combo_name}.png"
    combo_path = os.path.join(SOURCE_PATH, "image", combo_image_name)

    if not os.path.exists(combo_path):
        combo_path = os.path.join(SOURCE_PATH, "image", "plate.png")

    pix = QtGui.QPixmap(combo_path)
    target_label.setPixmap(pix)
    target_label.setScaledContents(True)

def try_pickup_plate(game_widget):
    """ฟังก์ชันให้เชฟหยิบจานจาก station หรือจากพื้น (พร้อมของบนจาน)"""
    # 🧺 ถ้ามือเชฟถือของอื่นอยู่ หยุดเลย
    if getattr(game_widget, "has_item", False):
        print("เชฟถือของอยู่แล้ว 🧺")
        return

    # 🔸 ลบจานเก่าถ้ามี
    if hasattr(game_widget, "held_plate") and game_widget.held_plate:
        game_widget.held_plate.deleteLater()
        game_widget.held_plate = None

    # 📍 หาตำแหน่งศูนย์กลางเชฟ
    chef_geom = game_widget.chef.geometry()
    chef_center = QtCore.QPoint(
        chef_geom.x() + chef_geom.width() // 2,
        chef_geom.y() + chef_geom.height() // 2
    )

    threshold = getattr(game_widget, "pickup_threshold", 80)

    # 1️⃣ ตรวจว่าใกล้ plate_station หรือไม่
    if hasattr(game_widget, "plate_station") and is_near_object(game_widget.chef, game_widget.plate_station, mode="bounds"):
        if getattr(game_widget, "has_plate", False):
            print("⚠️ มีจานอยู่แล้ว")
            return

        # ✅ หยิบจานใหม่จาก station
        game_widget.has_plate = True
        game_widget.current_item = "plate"
        game_widget.plate_items = []

        held_plate = QtWidgets.QLabel(game_widget)
        img_path = os.path.join(SOURCE_PATH, "image", "plate.png")
        if os.path.exists(img_path):
            held_plate.setPixmap(QtGui.QPixmap(img_path))
        held_plate.setScaledContents(True)
        held_plate.resize(64, 64)
        held_plate.setStyleSheet("background: transparent;")
        held_plate.show()

        update_plate_position(game_widget, game_widget.chef, held_plate)
        game_widget.held_plate = held_plate

        print("✅ หยิบจานเรียบร้อย!")
        return

    # 2️⃣ ตรวจ dropped_plates (จานที่วางพื้น)
    if hasattr(game_widget, "dropped_plates"):
        for plate_dict in list(game_widget.dropped_plates):
            lbl = plate_dict.get("label")
            items_on_plate = plate_dict.get("items", [])

            if lbl is None:
                continue

            # หาระยะระหว่างเชฟกับจาน
            item_geom = lbl.geometry()
            item_center = QtCore.QPoint(
                item_geom.x() + item_geom.width() // 2,
                item_geom.y() + item_geom.height() // 2
            )
            dx = chef_center.x() - item_center.x()
            dy = chef_center.y() - item_center.y()
            distance = (dx**2 + dy**2) ** 0.5

            # 📏 ถ้าอยู่ในระยะหยิบได้
            if distance <= threshold:
                # ✅ หยิบทั้งจานและของทั้งหมด
                game_widget.has_plate = True
                game_widget.current_item = "plate"
                game_widget.plate_items = list(items_on_plate)

                # --- 🔹 สร้าง QLabel ของจานที่ถือ ---
                held_plate = QtWidgets.QLabel(game_widget)
                img_path = os.path.join(SOURCE_PATH, "image", "plate_icon.png")
                if os.path.exists(img_path):
                    held_plate.setPixmap(QtGui.QPixmap(img_path))
                held_plate.setScaledContents(True)
                held_plate.resize(64, 64)
                held_plate.setStyleSheet("background: transparent;")
                held_plate.show()

                # --- จัดตำแหน่งให้อยู่บนหัวเชฟ ---
                update_plate_position(game_widget, game_widget.chef, held_plate)
                game_widget.held_plate = held_plate

                # --- อัปเดตรูปให้เห็นของทั้งหมดบนจาน ---
                try:
                    update_plate_image(game_widget, target_label=held_plate, items=game_widget.plate_items)
                except Exception:
                    pass

                # --- ลบจานจากพื้น ---
                lbl.deleteLater()
                try:
                    game_widget.dropped_plates.remove(plate_dict)
                except ValueError:
                    pass

                print(f"✅ หยิบจานพร้อมของทั้งหมดจากพื้น: {game_widget.plate_items}")
                return

    print("❌ ไม่ได้อยู่ใกล้วัตถุดิบใด ๆ")


def is_near_object(obj_a, obj_b, threshold=80, mode="center"):
    """
    ตรวจว่าวัตถุ obj_a อยู่ใกล้ obj_b หรือไม่

    mode:
        - "center" : วัดระยะจากจุดศูนย์กลาง (เหมาะกับ station ทั่วไป)
        - "bounds" : วัดจากระยะขอบของ bounding box (เหมาะกับ trash_bin หรือ collision check)
    """
    if not (obj_a and obj_b):
        return False

    if mode == "center":
        # --- วัดระยะจากจุดศูนย์กลาง ---
        ax = obj_a.x() + obj_a.width() / 2
        ay = obj_a.y() + obj_a.height() / 2
        bx = obj_b.x() + obj_b.width() / 2
        by = obj_b.y() + obj_b.height() / 2
        distance = ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5

    elif mode == "bounds":
        # --- วัดจากขอบกล่อง (เหมือน trash) ---
        a_rect = QtCore.QRect(obj_a.x(), obj_a.y(), obj_a.width(), obj_a.height())
        b_rect = QtCore.QRect(obj_b.x(), obj_b.y(), obj_b.width(), obj_b.height())

        dx = max(b_rect.left() - a_rect.right(), a_rect.left() - b_rect.right(), 0)
        dy = max(b_rect.top() - a_rect.bottom(), a_rect.top() - b_rect.bottom(), 0)
        distance = (dx**2 + dy**2) ** 0.5

    else:
        raise ValueError("mode ต้องเป็น 'center' หรือ 'bounds'")

    return distance < threshold


def update_plate_position(game_widget, chef, plate_label):
    """อัปเดตตำแหน่งจานให้อยู่บนหัวเชฟ"""
    plate_x = chef.x() + (chef.width() - plate_label.width()) // 2
    plate_y = chef.y() - plate_label.height() + 10  # +10 ให้จานลอยเหนือหัวนิดหน่อย
    plate_label.move(plate_x, plate_y)

def drop_plate(game_widget):
    """วางจานลงพื้น"""
    if not getattr(game_widget, "has_plate", False):
        print("❌ ไม่มีจานในมือ")
        return

    chef_x = game_widget.chef.x()
    chef_y = game_widget.chef.y()

    dropped_label = QtWidgets.QLabel(game_widget)
    dropped_label.setGeometry(chef_x + 40, chef_y + 40, 60, 60)
    dropped_label.setStyleSheet("background: transparent;")
    dropped_label.show()

    update_plate_image(game_widget, target_label=dropped_label, items=getattr(game_widget, "plate_items", []))

    if not hasattr(game_widget, "dropped_plates"):
        game_widget.dropped_plates = []
    game_widget.dropped_plates.append({
        "label": dropped_label,
        "items": list(getattr(game_widget, "plate_items", []))
    })

    game_widget.has_plate = False
    game_widget.current_item = None
    game_widget.plate_items = []
    if hasattr(game_widget, "held_plate"):
        game_widget.held_plate.deleteLater()
        game_widget.held_plate = None

    print("🧺 วางจานลงพื้นแล้ว")

def is_near_trash(game_widget, threshold=80):
    """
    ตรวจสอบว่าเชฟอยู่ใกล้ถังขยะหรือไม่
    return: True ถ้าอยู่ในระยะ threshold, False ถ้าไกลเกินไป
    """
    if not hasattr(game_widget, "trash_bin") or game_widget.trash_bin is None:
        print("⚠️ ไม่มี trash_bin ในเกม")
        return False

    chef_geom = game_widget.chef.geometry()
    trash_geom = game_widget.trash_bin.geometry()

    chef_center = QtCore.QPoint(
        chef_geom.x() + chef_geom.width() // 2,
        chef_geom.y() + chef_geom.height() // 2
    )
    trash_center = QtCore.QPoint(
        trash_geom.x() + trash_geom.width() // 2,
        trash_geom.y() + trash_geom.height() // 2
    )

    dx = chef_center.x() - trash_center.x()
    dy = chef_center.y() - trash_center.y()
    distance = (dx ** 2 + dy ** 2) ** 0.5

    return distance <= threshold

def throw_plate_to_trash(game_widget):
    """ทิ้งจานในถังขยะ"""
    if not getattr(game_widget, "has_plate", False):
        print("❌ ไม่มีจานในมือ")
        return
    if not hasattr(game_widget, "trash_bin"):
        print("❌ ไม่มี trash_bin ในเกม")
        return

    if not is_near_trash(game_widget):
        print("🚫 อยู่ไกลเกินไปจากถังขยะ")
        return

    print("🗑️ ทิ้งจานลงถังขยะแล้ว")
    if hasattr(game_widget, "held_plate"):
        game_widget.held_plate.deleteLater()
        game_widget.held_plate = None

    game_widget.has_plate = False
    game_widget.current_item = None
    game_widget.plate_items = []