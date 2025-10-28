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

    # 3️⃣ ตรวจสอบ chopping_board_icons (ไอเทมบนเขียง)
    if not found and hasattr(game_widget, "chopping_board_icons"):
        for icon_label in list(game_widget.chopping_board_icons):
            name = icon_label.property("item_name") or getattr(icon_label, "item_name", None)
            if not name:
                continue

            icon_geom = icon_label.geometry()
            icon_center = QtCore.QPoint(
                icon_geom.x() + icon_geom.width() // 2,
                icon_geom.y() + icon_geom.height() // 2
            )
            dx = chef_center.x() - icon_center.x()
            dy = chef_center.y() - icon_center.y()
            distance = (dx**2 + dy**2) ** 0.5

            if distance <= threshold:
                game_widget.has_item = True
                game_widget.current_item = name
                print(f"🔪 หยิบวัตถุดิบจากเขียง: {name}")

                show_pick_feedback(game_widget, name)

                # เอา icon ของวัตถุดิบบนเขียงออก
                try:
                    game_widget.chopping_board_icons.remove(icon_label)
                except ValueError:
                    pass
                icon_label.deleteLater()
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
    """Start a chopping action that takes 3 seconds on the nearest chopping-board icon.

    If a chop is already in progress (game_widget.is_chopping), this call is ignored.
    """
    # ignore if already chopping
    if getattr(game_widget, 'is_chopping', False):
        print("⏳ กำลังหั่นอยู่ โปรดรอ")
        return

    # find nearest chopping_board icon to the chef
    if not hasattr(game_widget, 'chopping_board_icons') or not game_widget.chopping_board_icons:
        print("🔪 ไม่มีของบนเขียงให้หั่น")
        return

    chef_geom = game_widget.chef.geometry()
    chef_center = QtCore.QPoint(
        chef_geom.x() + chef_geom.width() // 2,
        chef_geom.y() + chef_geom.height() // 2
    )

    nearest = None
    nearest_dist = None
    for icon_label in list(game_widget.chopping_board_icons):
        try:
            icon_geom = icon_label.geometry()
        except Exception:
            continue
        icon_center = QtCore.QPoint(
            icon_geom.x() + icon_geom.width() // 2,
            icon_geom.y() + icon_geom.height() // 2
        )
        dx = chef_center.x() - icon_center.x()
        dy = chef_center.y() - icon_center.y()
        dist = (dx**2 + dy**2) ** 0.5
        if nearest is None or dist < nearest_dist:
            nearest = icon_label
            nearest_dist = dist

    if nearest is None:
        print("🔪 ไม่พบไอเทมบนเขียง")
        return

    # require reasonable proximity (use 80 px)
    if nearest_dist is None or nearest_dist > 120:
        print(f"🚫 ไกลเกินไป (ระยะ {int(nearest_dist or 999)})")
        return

    # start chopping
    game_widget.is_chopping = True
    target = nearest
    try:
        orig_name = target.property('item_name') or getattr(target, 'item_name', None)
    except Exception:
        orig_name = None

    print(f"🔪 เริ่มหั่น {orig_name} — ใช้เวลา 3 วินาที")

    def _finish_chop():
        try:
            if not getattr(game_widget, 'chopping_board_icons', None):
                return
            # target may have been deleted — check
            if target not in game_widget.chopping_board_icons:
                # maybe it was picked up or removed
                return
            name = target.property('item_name') or getattr(target, 'item_name', None)
            if not name:
                return
            # don't append _chopped twice
            if name.endswith('_chopped'):
                print(f"ℹ️ {name} ถูกหั่นแล้ว")
                return
            chopped_name = f"{name}_chopped"
            pix_path = os.path.join(SOURCE_PATH, "image", f"{chopped_name}_icon.png")
            pix = QtGui.QPixmap(pix_path)
            if not pix.isNull():
                target.setPixmap(pix)
                target.setScaledContents(True)
                target.setProperty('item_name', chopped_name)
                try:
                    target.item_name = chopped_name
                except Exception:
                    pass
                print(f"✅ หั่นวัตถุดิบเสร็จ: {chopped_name}")
        except Exception:
            pass
        finally:
            game_widget.is_chopping = False

    # 3 seconds delay
    QtCore.QTimer.singleShot(3000, _finish_chop)

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
    # เก็บของบน plate station (ไม่ใช่จานที่ถือ)
    if not hasattr(game_widget, "station_plate_items"):
        game_widget.station_plate_items = []
    game_widget.station_plate_items.append(item_name)
    print(f"🍽️ ใส่ {item_name} ลงจานที่ station: {game_widget.station_plate_items}")

    # อัปเดตรูปที่แสดงบน plate_station
    try:
        update_plate_image(game_widget, target_label=game_widget.plate_station, items=game_widget.station_plate_items)
    except Exception:
        pass


def add_item_to_held_plate(game_widget, item_name):
    """เพิ่มวัตถุดิบลงในจานที่ถืออยู่ (held_plate)"""
    if not getattr(game_widget, "has_plate", False):
        print("❌ ไม่มีจานในมือ")
        return

    if not hasattr(game_widget, "held_plate") or game_widget.held_plate is None:
        print("❌ ไม่มี held_plate")
        return

    if not hasattr(game_widget, "plate_items"):
        game_widget.plate_items = []

    game_widget.plate_items.append(item_name)
    print(f"🍽️ ใส่ {item_name} ลงจานที่ถืออยู่: {game_widget.plate_items}")

    try:
        update_plate_image(game_widget, target_label=game_widget.held_plate, items=game_widget.plate_items)
    except Exception:
        pass


def add_item_to_dropped_plate(game_widget, plate_dict, item_name):
    """เพิ่มวัตถุดิบลงในจานที่วางบนพื้น (plate_dict เหมือนใน dropped_plates)"""
    lbl = plate_dict.get("label")
    if lbl is None:
        print("❌ plate label ไม่ถูกต้อง")
        return

    items = plate_dict.get("items", [])
    items.append(item_name)
    plate_dict["items"] = items
    print(f"🍽️ ใส่ {item_name} ลงจานที่พื้น: {items}")

    try:
        update_plate_image(game_widget, target_label=lbl, items=items)
    except Exception:
        pass


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
        # ✅ หยิบจานใหม่จาก station (พร้อมของที่อยู่บน station ถ้ามี)
        game_widget.has_plate = True
        game_widget.current_item = "plate"

        # ย้ายของจาก station ไปยัง plate_items
        game_widget.plate_items = list(getattr(game_widget, "station_plate_items", []))
        # ล้างของบน station
        game_widget.station_plate_items = []
        try:
            # อัปเดตรูปบน station ให้เป็นจานเปล่า
            update_plate_image(game_widget, target_label=game_widget.plate_station, items=[])
        except Exception:
            pass

        held_plate = QtWidgets.QLabel(game_widget)
        img_path = os.path.join(SOURCE_PATH, "image", "plate_icon.png")
        if os.path.exists(img_path):
            held_plate.setPixmap(QtGui.QPixmap(img_path))
        held_plate.setScaledContents(True)
        held_plate.resize(64, 64)
        held_plate.setStyleSheet("background: transparent;")
        held_plate.show()

        update_plate_position(game_widget, game_widget.chef, held_plate)
        game_widget.held_plate = held_plate

        # อัปเดตรูปของ held plate ให้แสดงของทั้งหมด
        try:
            update_plate_image(game_widget, target_label=held_plate, items=game_widget.plate_items)
        except Exception:
            pass

        print(f"✅ หยิบจานเรียบร้อย! มีของ: {game_widget.plate_items}")
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


def try_serve_plate(game_widget, threshold=80):
    """Serve a plate when near the serve station.

    If holding a plate, serve it. If a dropped plate is near the serve station, serve it.
    Serving increases the parent's score_label by 10 and removes the plate.
    """
    # must have serve_station
    if not hasattr(game_widget, "serve_station"):
        print("❌ ไม่มี serve_station ในเกม")
        return False

    chef_geom = game_widget.chef.geometry()
    chef_center = QtCore.QPoint(
        chef_geom.x() + chef_geom.width() // 2,
        chef_geom.y() + chef_geom.height() // 2
    )

    serv_geom = game_widget.serve_station.geometry()
    serv_center = QtCore.QPoint(
        serv_geom.x() + serv_geom.width() // 2,
        serv_geom.y() + serv_geom.height() // 2
    )

    dx = chef_center.x() - serv_center.x()
    dy = chef_center.y() - serv_center.y()
    distance = (dx**2 + dy**2) ** 0.5

    if distance > threshold:
        print("🚫 ยังไม่อยู่ใกล้จุดเสิร์ฟพอ")
        return False

    parent = game_widget.parent()

    # If holding a plate, serve it
    if getattr(game_widget, "has_plate", False):
        print(f"✅ ให้บริการจาน: {getattr(game_widget, 'plate_items', [])}")
        # increase score if available
        if parent is not None and hasattr(parent, "score_label"):
            try:
                text = parent.score_label.text()
                num = int(text.split(":")[-1].strip())
            except Exception:
                num = 0

            # determine if served plate matches current order
            served_items = list(getattr(game_widget, 'plate_items', []))
            served_key = "_".join(sorted([s.replace('_chopped', '_chopped') for s in served_items]))
            try:
                current_order = parent.orders[0]
            except Exception:
                current_order = None

            if current_order and served_key == current_order:
                num += 20
                print("🏆 เสิร์ฟตรงตามออร์เดอร์! +20")
                # pop order and add a new random one
                try:
                    import random, os
                    files = os.listdir(os.path.join(os.path.dirname(__file__), "source_image", "image"))
                    combos = [f[len("plate_"):-4] for f in files if f.startswith("plate_") and f.lower().endswith('.png')]
                except Exception:
                    combos = []
                if not combos:
                    combos = ["tomato_chopped", "lettuce_chopped", "cucamber_chopped"]
                try:
                    parent.orders.pop(0)
                    parent.orders.append(random.choice(combos))
                    parent._refresh_orders_label()
                except Exception:
                    pass
            else:
                # served but not matching -> smaller reward or none
                num += 0
                print("⚠️ เสิร์ฟไม่ตรงออร์เดอร์")

            parent.score_label.setText(f"Score: {num}")

        # remove held plate
        if hasattr(game_widget, "held_plate") and game_widget.held_plate:
            game_widget.held_plate.deleteLater()
            game_widget.held_plate = None

        game_widget.has_plate = False
        game_widget.current_item = None
        game_widget.plate_items = []
        return True

    # Otherwise, check dropped plates near serve station
    if hasattr(game_widget, "dropped_plates"):
        for plate_dict in list(game_widget.dropped_plates):
            lbl = plate_dict.get("label")
            if lbl is None:
                continue

            item_geom = lbl.geometry()
            item_center = QtCore.QPoint(
                item_geom.x() + item_geom.width() // 2,
                item_geom.y() + item_geom.height() // 2
            )
            dx = serv_center.x() - item_center.x()
            dy = serv_center.y() - item_center.y()
            dist_item = (dx**2 + dy**2) ** 0.5

            if dist_item <= threshold:
                print(f"✅ ให้บริการจานจากพื้น: {plate_dict.get('items', [])}")
                # increase score
                if parent is not None and hasattr(parent, "score_label"):
                    try:
                        text = parent.score_label.text()
                        num = int(text.split(":")[-1].strip())
                    except Exception:
                        num = 0

                    # evaluate if plate matches current order
                    items_served = list(plate_dict.get('items', []))
                    served_key = "_".join(sorted(items_served))
                    try:
                        current_order = parent.orders[0]
                    except Exception:
                        current_order = None

                    if current_order and served_key == current_order:
                        num += 20
                        print("🏆 เสิร์ฟตรงตามออร์เดอร์! +20")
                        try:
                            import random, os
                            files = os.listdir(os.path.join(os.path.dirname(__file__), "source_image", "image"))
                            combos = [f[len("plate_"):-4] for f in files if f.startswith("plate_") and f.lower().endswith('.png')]
                        except Exception:
                            combos = []
                        if not combos:
                            combos = ["tomato_chopped", "lettuce_chopped", "cucamber_chopped"]
                        try:
                            parent.orders.pop(0)
                            parent.orders.append(random.choice(combos))
                            parent._refresh_orders_label()
                        except Exception:
                            pass
                    else:
                        num += 0
                        print("⚠️ เสิร์ฟไม่ตรงออร์เดอร์")

                    parent.score_label.setText(f"Score: {num}")

                lbl.deleteLater()
                try:
                    game_widget.dropped_plates.remove(plate_dict)
                except Exception:
                    pass
                return True

    print("❌ ไม่มีจานที่จะเสิร์ฟ")
    return False

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