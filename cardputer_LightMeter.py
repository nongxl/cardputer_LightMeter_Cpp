import M5
from M5 import Power, Lcd, Widgets
from hardware import MatrixKeyboard, I2C, Pin
from unit import DLightUnit
import math
import time

# --- 常量定义 ---
UP_KEY_STR = '.'
DOWN_KEY_STR = ';'

# --- 优化后的颜色方案 ---
COLOR_DEFAULT = 0xffffff  # 白色
COLOR_FOCUSED = 0x33ff33  # 绿色 (焦点)
COLOR_INVALID = 0xff0000  # 红色 (无效选项 - 焦点)
COLOR_BACKGROUND = 0x000000  # 黑色
COLOR_TITLE_BG = 0x0000FF  # 标题背景色
COLOR_GRADIENT_1 = 0xCCCCCC  # 渐变色1 (亮灰色)
COLOR_GRADIENT_2 = 0x555555  # 渐变色2 (暗灰色)
# [新增] 无效选项的渐变色
COLOR_INVALID_GRADIENT_1 = 0xCC3333  # 无效渐变1 (暗红色)
COLOR_INVALID_GRADIENT_2 = 0x883333  # 无效渐变2 (更暗的红色)

PARAMETER_LIST_SIZE = 5  # 参数选择列表显示的行数，必须为奇数
LIST_ITEM_HEIGHT = 20  # 列表项的高度


# --- 应用程序类 ---
class LightMeterApp:
    def __init__(self):
        # --- 状态变量 ---
        self.current_mode = 'i'
        self.priority_mode = 'A'
        self.last_lux_value = 0

        # --- 动画状态变量 ---
        self.is_animating = False
        self.anim_duration = 120  # 动画时长 (毫秒)
        self.anim_start_time = 0
        self.anim_current_y = 0.0
        self.anim_y_start_pos = None

        # [清理] 长按相关的状态变量已被移除

        # --- 预设值 ---
        self.iso_values = [50, 100, 200, 400, 800, 1000, 1200, 1600, 3200, 6400]
        self.aperture_values = [0.95, 1.0, 1.2, 1.4, 1.8, 2.0, 2.2, 2.8, 4, 5.6, 8, 11, 16, 22]
        self.shutter_values = ["30s", "15s", "8s", "4s", "2s", "1s", "1/2", "1/4", "1/8", "1/15", "1/30", "1/60",
                               "1/125", "1/250", "1/500", "1/1000", "1/2000", "1/4000"]

        # --- 当前预览值的索引 ---
        self.preview_indices = {'ISO': 1, 'Aperture': 4, 'Shutter': 11}

        # [核心修正] 根据初始的 'i' 模式，同步滚动列表的初始视觉位置
        # 这确保了数据状态和视觉状态在启动时就保持一致
        initial_mode_key = 'ISO'
        initial_idx = self.preview_indices[initial_mode_key]
        self.anim_current_y = -initial_idx * LIST_ITEM_HEIGHT

        # --- 硬件和界面元素 ---
        self.kb = None
        self.i2c0 = None
        self.dlight_0 = None
        self.ui_elements = {}
        self.param_list_canvas = None

    # --- 辅助函数 ---
    def _shutter_to_float(self, shutter_str):
        clean_str = shutter_str.strip().rstrip('s')
        if "/" in clean_str:
            parts = clean_str.split('/')
            return float(parts[0]) / float(parts[1])
        else:
            return float(clean_str)

    def _compute_aperture(self, ev, iso, shutter_speed):
        ev_corrected = ev + math.log2(iso / 100)
        f_number_sq = (2 ** ev_corrected) * shutter_speed
        return math.sqrt(f_number_sq) if f_number_sq > 0 else 0


    def _compute_shutter_speed(self, ev, iso, aperture):
        ev_corrected = ev + math.log2(iso / 100)
        denominator = (2 ** ev_corrected)
        return (aperture ** 2) / denominator if denominator != 0 else 0

    # --- 检查选项有效性的辅助函数 ---
    def _is_choice_valid(self, param_key, choice_idx):
        # ISO值永远不会被标记为无效
        if param_key == 'ISO':
            return True

        if not self.dlight_0: return True
        try:
            lux = self.dlight_0.get_lux()
            ev = math.log2(lux / 2.5) if lux > 0 else -100

            # 获取基础参数用于计算
            iso = self.iso_values[self.preview_indices['ISO']]

            if param_key == 'Aperture':
                aperture_to_test = self.aperture_values[choice_idx]
                shutter_float_result = self._compute_shutter_speed(ev, iso, aperture_to_test)
                return self._shutter_to_float(
                    self.shutter_values[-1]) <= shutter_float_result <= self._shutter_to_float(self.shutter_values[0])

            elif param_key == 'Shutter':
                shutter_to_test_str = self.shutter_values[choice_idx]
                shutter_float_to_test = self._shutter_to_float(shutter_to_test_str)
                aperture_float_result = self._compute_aperture(ev, iso, shutter_float_to_test)
                return self.aperture_values[0] <= aperture_float_result <= self.aperture_values[-1]

        except (ValueError, ZeroDivisionError, OSError):
            return False
        return True

    # --- 界面更新与核心逻辑 ---
    def _update_parameter_colors(self):
        """根据当前模式，更新左侧标签的颜色以示高亮"""
        self.ui_elements['iso_text_label'].setColor(COLOR_DEFAULT, COLOR_BACKGROUND)
        self.ui_elements['aperture_text_label'].setColor(COLOR_DEFAULT, COLOR_BACKGROUND)
        self.ui_elements['shutter_text_label'].setColor(COLOR_DEFAULT, COLOR_BACKGROUND)
        mode_map = {'i': 'iso', 'a': 'aperture', 's': 'shutter'}
        focus_label = self.ui_elements[f"{mode_map[self.current_mode]}_text_label"]
        focus_label.setColor(COLOR_FOCUSED, COLOR_BACKGROUND)

    def _draw_parameter_list(self):
        """在离屏画布上绘制参数列表，并推送到屏幕，实现无闪烁动画"""
        self.param_list_canvas.fillScreen(COLOR_BACKGROUND)
        self.param_list_canvas.setFont(Widgets.FONTS.DejaVu18)

        font_h = 18
        mode_map = {'i': 'ISO', 'a': 'Aperture', 's': 'Shutter'}
        param_key = mode_map[self.current_mode]
        values_list = getattr(self, f"{param_key.lower()}_values")

        # 当前选中的数据索引 (唯一的“真理”)
        center_data_idx = self.preview_indices[param_key]

        # 视觉上的中心Y坐标
        center_y_on_canvas = (PARAMETER_LIST_SIZE // 2) * LIST_ITEM_HEIGHT

        # --- [核心重构] ---
        # 遍历整个数据列表，而不是屏幕上的可见项
        for data_idx, value in enumerate(values_list):
            # 计算每个数据项的绝对Y坐标，然后加上当前的动画滚动偏移
            # 再加上一个中心化偏移，使得选中的项对齐到视觉中心
            # [关键修正] 将最终结果转换为整数，以满足绘图函数的要求
            draw_y = int((data_idx * LIST_ITEM_HEIGHT) + self.anim_current_y + center_y_on_canvas)

            # 优化：只绘制在画布可视范围内的项
            if -LIST_ITEM_HEIGHT < draw_y < self.param_list_canvas.height():
                prefix = "f/" if param_key == 'Aperture' else ""
                text_to_draw = f"{prefix}{value}"
                text_w = self.param_list_canvas.textWidth(text_to_draw)
                text_x = (self.param_list_canvas.width() - text_w) // 2

                # 决定颜色
                distance_from_center = abs(data_idx - center_data_idx)
                is_valid = self._is_choice_valid(param_key, data_idx)

                if is_valid:
                    if distance_from_center == 0:
                        text_color = COLOR_FOCUSED
                    elif distance_from_center == 1:
                        text_color = COLOR_GRADIENT_1
                    else:
                        text_color = COLOR_GRADIENT_2
                else:
                    if distance_from_center == 0:
                        text_color = COLOR_INVALID
                    elif distance_from_center == 1:
                        text_color = COLOR_INVALID_GRADIENT_1
                    else:
                        text_color = COLOR_INVALID_GRADIENT_2

                # 绘制文本
                self.param_list_canvas.setTextColor(text_color, COLOR_BACKGROUND)
                self.param_list_canvas.drawString(text_to_draw, text_x, draw_y)

        # --- 绘制固定的中心选择框 ---
        # 这个框永远在画布的中心，不受任何滚动影响
        box_color = COLOR_FOCUSED
        box_padding_x = 6
        box_padding_y = 2
        thickness = 2

        # 临时获取中心项的文本宽度来决定框的宽度
        center_text = f"{'f/' if param_key == 'Aperture' else ''}{values_list[center_data_idx]}"
        center_text_w = self.param_list_canvas.textWidth(center_text)

        box_x = (self.param_list_canvas.width() - center_text_w) // 2 - box_padding_x
        box_y = center_y_on_canvas - box_padding_y
        box_w = center_text_w + (2 * box_padding_x)
        box_h = font_h + (2 * box_padding_y)

        for t in range(thickness):
            top_y = box_y + t
            bottom_y = box_y + box_h - 1 - t
            if top_y >= bottom_y and t > 0: break
            self.param_list_canvas.drawLine(box_x, top_y, box_x + box_w, top_y, box_color)
            self.param_list_canvas.drawLine(box_x, bottom_y, box_x + box_w, bottom_y, box_color)

        # 推送画布到屏幕
        canvas_pos = self.ui_elements['param_list_canvas_pos']
        self.param_list_canvas.push(canvas_pos[0], canvas_pos[1])

    def _scroll_list(self, direction):
        """
        处理列表滚动的核心逻辑
        :param direction: 滚动方向, 1 为上, -1 为下
        """
        if self.is_animating: return

        mode_map = {'i': 'ISO', 'a': 'Aperture', 's': 'Shutter'}
        param_key = mode_map[self.current_mode]
        values_list = getattr(self, f"{param_key.lower()}_values")
        current_idx = self.preview_indices[param_key]
        next_idx = current_idx + direction

        # 只有在目标索引有效时，才允许更新数据和触发动画
        if 0 <= next_idx < len(values_list):
            # 1. 更新数据状态 (唯一的“真理”)
            self.preview_indices[param_key] = next_idx

            # 2. 触发动画
            self.is_animating = True
            self.anim_start_time = time.ticks_ms()

            # 3. 触发UI重绘
            self._update_and_recalculate()
            return True  # 表示滚动成功
        return False  # 表示已到边界

    def _update_and_recalculate(self):
        """根据传感器数据和当前设置，计算并更新所有UI显示"""
        # 动画期间，由动画循环负责调用绘制函数
        if not self.is_animating:
            self._draw_parameter_list()

        # 无论是否动画，左侧面板都需要根据最新数据重绘
        self._draw_left_panel()

    # --- 私有初始化方法 ---
    def _init_hardware(self):
        """初始化键盘和I2C传感器"""
        self.kb = MatrixKeyboard()
        self.kb.set_callback(self.kb_pressed_event)
        self.i2c0 = I2C(0, scl=Pin(1), sda=Pin(2), freq=100000)
        try:
            self.dlight_0 = DLightUnit(self.i2c0)
            print("DLight Unit initialized successfully.")
        except OSError as e:
            self.dlight_0 = None
            print(f"Failed to initialize DLight Unit: {e}")

    def _init_ui(self):
        """初始化所有UI元素，包括左侧的Widgets和右侧的Canvas"""
        Widgets.fillScreen(COLOR_BACKGROUND)

        UNIFIED_FONT = Widgets.FONTS.DejaVu24

        # --- 顶部面板 (保持不变) ---
        self.ui_elements['title'] = Widgets.Title("LightMeter", 3, COLOR_DEFAULT, COLOR_TITLE_BG, UNIFIED_FONT)
        self.ui_elements['battary_label'] = Widgets.Label("B:", 188, 1, 1.0, COLOR_DEFAULT, COLOR_BACKGROUND,
                                                          UNIFIED_FONT)

        # --- 左侧面板 (使用 Widgets 和 新的Canvas) ---
        # [修改] 我们只创建静态的文本标签，数值将画在Canvas上
        lux_y, iso_y, apert_y, speed_y = 28, 54, 82, 110
        label_x = 8

        Widgets.Label("LUX:", label_x, lux_y, 1.0, COLOR_DEFAULT, COLOR_BACKGROUND, UNIFIED_FONT)
        self.ui_elements['iso_text_label'] = Widgets.Label("ISO:", label_x, iso_y, 1.0, COLOR_DEFAULT,
                                                           COLOR_BACKGROUND,
                                                           UNIFIED_FONT)
        self.ui_elements['aperture_text_label'] = Widgets.Label("APER:", label_x, apert_y, 1.0, COLOR_DEFAULT,
                                                                COLOR_BACKGROUND, UNIFIED_FONT)
        self.ui_elements['shutter_text_label'] = Widgets.Label("SSPD:", label_x, speed_y, 1.0, COLOR_DEFAULT,
                                                               COLOR_BACKGROUND, UNIFIED_FONT)

        # [新增] 为左侧面板创建离屏画布
        left_panel_x, left_panel_y = 82, 28  # 从第一个数值标签的位置开始
        left_panel_w, left_panel_h = 88, 110  # 宽度和高度足够容纳所有数值
        self.left_panel_canvas = Lcd.newCanvas(left_panel_w, left_panel_h, 16, False)
        self.ui_elements['left_panel_canvas_pos'] = (left_panel_x, left_panel_y)

        # --- 右侧面板 (保持不变) ---
        list_x, list_y = 172, 40
        list_w, list_h = 72, (PARAMETER_LIST_SIZE * LIST_ITEM_HEIGHT)
        self.param_list_canvas = Lcd.newCanvas(list_w, list_h, 16, False)
        self.ui_elements['param_list_canvas_pos'] = (list_x, list_y)

    def _draw_left_panel(self):
        """在左侧离屏画布上绘制所有动态数值，然后一次性推送到屏幕"""
        self.left_panel_canvas.fillScreen(COLOR_BACKGROUND)
        self.left_panel_canvas.setFont(Widgets.FONTS.DejaVu24)

        # --- 获取所有需要显示的值 ---
        iso = self.iso_values[self.preview_indices['ISO']]
        aperture_val = self.aperture_values[self.preview_indices['Aperture']]
        shutter_str = self.shutter_values[self.preview_indices['Shutter']]

        # 默认颜色
        aperture_color = COLOR_DEFAULT
        shutter_color = COLOR_DEFAULT

        # --- 计算最终要显示的文本和颜色 ---
        lux_text = str(int(self.last_lux_value)) if self.dlight_0 else "N/A"
        iso_text = str(iso)
        aperture_text = f"f/{aperture_val:g}"
        shutter_text = shutter_str

        if self.dlight_0:
            try:
                ev = math.log2(self.last_lux_value / 2.5) if self.last_lux_value > 0 else -100

                if self.priority_mode == 'A':
                    shutter_float_theoretical = self._compute_shutter_speed(ev, iso, aperture_val)
                    min_shutter_val = self._shutter_to_float(self.shutter_values[-1])
                    max_shutter_val = self._shutter_to_float(self.shutter_values[0])
                    if not (min_shutter_val <= shutter_float_theoretical <= max_shutter_val):
                        shutter_color = COLOR_INVALID
                    closest_shutter = min(self.shutter_values,
                                          key=lambda s: abs(self._shutter_to_float(s) - shutter_float_theoretical))
                    shutter_text = str(closest_shutter)

                elif self.priority_mode == 'S':
                    shutter_float = self._shutter_to_float(shutter_str)
                    aperture_float_theoretical = self._compute_aperture(ev, iso, shutter_float)
                    min_aperture_val = self.aperture_values[0]
                    max_aperture_val = self.aperture_values[-1]
                    if not (min_aperture_val <= aperture_float_theoretical <= max_aperture_val):
                        aperture_color = COLOR_INVALID
                    closest_aperture = min(self.aperture_values, key=lambda a: abs(a - aperture_float_theoretical))
                    aperture_text = f"f/{closest_aperture:g}"
            except (ValueError, ZeroDivisionError, OSError):
                pass  # 发生计算错误时，保持默认值

        # --- 在画布上绘制所有文本 ---
        # 坐标是相对于画布左上角(0,0)的
        lux_y, iso_y, apert_y, speed_y = 0, 28, 56, 84

        self.left_panel_canvas.setTextColor(COLOR_DEFAULT, COLOR_BACKGROUND)
        self.left_panel_canvas.drawString(lux_text, 0, lux_y)
        self.left_panel_canvas.drawString(iso_text, 0, iso_y)

        self.left_panel_canvas.setTextColor(aperture_color, COLOR_BACKGROUND)
        self.left_panel_canvas.drawString(aperture_text, 0, apert_y)

        self.left_panel_canvas.setTextColor(shutter_color, COLOR_BACKGROUND)
        self.left_panel_canvas.drawString(shutter_text, 0, speed_y)

        # --- 将完成的画布一次性推送到屏幕 ---
        canvas_pos = self.ui_elements['left_panel_canvas_pos']
        self.left_panel_canvas.push(canvas_pos[0], canvas_pos[1])

    # --- 主流程 ---
    def setup(self):
        M5.begin()
        Lcd.setBrightness(25)
        self._init_hardware()
        self._init_ui()
        self._update_parameter_colors()
        self._update_and_recalculate()

    def kb_pressed_event(self, event_arg):
        """
        键盘事件回调函数，处理所有“按键按下”的瞬时事件。
        """
        # 回调被触发后，我们必须主动调用 get_string() 来获取按键数据。
        key_str = self.kb.get_string()

        # 如果没有事件，或正在动画中，则忽略
        if not key_str or self.is_animating:
            return

        if key_str in ['i', 'a', 's']:
            # --- 处理模式切换 ---
            self.current_mode = key_str
            if key_str == 'a':
                self.priority_mode = 'A'
            elif key_str == 's':
                self.priority_mode = 'S'

            mode_map = {'i': 'ISO', 'a': 'Aperture', 's': 'Shutter'}
            param_key = mode_map[self.current_mode]
            target_idx = self.preview_indices[param_key]
            self.anim_current_y = -target_idx * LIST_ITEM_HEIGHT

            self._update_parameter_colors()
            self._update_and_recalculate()

        elif key_str in [UP_KEY_STR, DOWN_KEY_STR]:
            # --- 处理列表滚动 ---
            direction = 1 if key_str == UP_KEY_STR else -1
            self._scroll_list(direction)

    def loop(self):
        M5.update()
        self.kb.tick()

        if self.is_animating:
            # --- 动画逻辑 ---
            mode_map = {'i': 'ISO', 'a': 'Aperture', 's': 'Shutter'}
            param_key = mode_map[self.current_mode]
            target_idx = self.preview_indices[param_key]
            anim_y_end_pos = -target_idx * LIST_ITEM_HEIGHT
            if self.anim_y_start_pos is None:
                self.anim_y_start_pos = self.anim_current_y
            elapsed_time = time.ticks_diff(time.ticks_ms(), self.anim_start_time)
            if elapsed_time >= self.anim_duration:
                self.anim_current_y = anim_y_end_pos
                self.is_animating = False
                self.anim_y_start_pos = None
            else:
                progress = elapsed_time / self.anim_duration
                self.anim_current_y = self.anim_y_start_pos + (anim_y_end_pos - self.anim_y_start_pos) * progress
            self._draw_parameter_list()

        else:
            # --- 常规更新 ---
            self.ui_elements['battary_label'].setText(str(Power.getBatteryLevel()))
            if self.dlight_0:
                try:
                    current_lux = self.dlight_0.get_lux()
                    if abs(current_lux - self.last_lux_value) > 1:
                        self.last_lux_value = current_lux
                        self._update_and_recalculate()
                except OSError:
                    if self.last_lux_value != 0:
                        self.last_lux_value = 0
                        self._draw_left_panel()

        time.sleep_ms(20)


# --- 程序入口 ---
if __name__ == '__main__':
    app = LightMeterApp()
    try:
        app.setup()
        while True:
            app.loop()
    except (Exception, KeyboardInterrupt) as e:
        try:
            from utility import print_error_msg

            print_error_msg(e)
        except ImportError:
            print("Firmware error or missing utility module.")
            print(e)