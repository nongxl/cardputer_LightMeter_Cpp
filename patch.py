import re
with open('main.cpp', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Includes and Definitions
code = code.replace('#include <M5Cardputer.h>', '''#ifdef TARGET_STICKS3
#include <M5Unified.h>
#define DISPLAY_CLASS M5.Display
#define POWER_CLASS M5.Power
#define UPDATE_CLASS M5.update()
#else
#include <M5Cardputer.h>
#define DISPLAY_CLASS M5Cardputer.Display
#define POWER_CLASS M5Cardputer.Power
#define UPDATE_CLASS M5Cardputer.update()
#endif''')

# 2. Add ev_locked globally
code = code.replace('bool is_initialized = false;', 'bool is_initialized = false;\nbool ev_locked = false;')

# 3. Replace M5Cardputer instances
code = code.replace('M5Cardputer.Display', 'DISPLAY_CLASS')
code = code.replace('M5Cardputer.Power', 'POWER_CLASS')
code = code.replace('M5Cardputer.update()', 'UPDATE_CLASS')

# 4. Hardware init
hw_init_orig = '''void init_hardware() {
  // 初始化DLight传感器
  dlight_0 = new M5_DLight(0x23);
  
  try {
    dlight_0->begin(&Wire, 2, 1, 100000); // sda=引脚(2), scl=引脚(1), 频率=100kHz'''
hw_init_new = '''void init_hardware() {
  // 初始化DLight传感器
  dlight_0 = new M5_DLight(0x23);
  
  try {
#ifdef TARGET_STICKS3
    dlight_0->begin(&Wire, 8, 0, 100000); // HAT DLight sda=8, scl=0, 频率=100kHz
#else
    dlight_0->begin(&Wire, 2, 1, 100000); // sda=引脚(2), scl=引脚(1), 频率=100kHz
#endif'''
code = code.replace(hw_init_orig, hw_init_new)

# 5. Debug Title (adding lock display)
title_orig = '''  // 绘制标题
  DISPLAY_CLASS.setCursor(TITLE_TEXT_X, TITLE_TEXT_Y);
  DISPLAY_CLASS.print("LightMeter");'''

title_new = '''  // 绘制标题
  DISPLAY_CLASS.setCursor(TITLE_TEXT_X, TITLE_TEXT_Y);
  if (ev_locked) {
    DISPLAY_CLASS.print("LightMeter [LOCK]");
  } else {
    DISPLAY_CLASS.print("LightMeter       ");
  }'''
code = code.replace(title_orig, title_new)

# 6. Setup function
setup_orig = '''void setup() {
  M5Cardputer.begin();
  // 设置屏幕旋转为1（正确方向）
  DISPLAY_CLASS.setRotation(1);
  DISPLAY_CLASS.setBrightness(160);
  
  // 使用我们定义的字体常量而不是硬编码值
  //DISPLAY_CLASS.setTextSize(TITLE_BAR_FONT_SIZE);
  //DISPLAY_CLASS.setTextColor(COLOR_DEFAULT, COLOR_BACKGROUND);
  //DISPLAY_CLASS.setFont(TITLE_BAR_FONT);
  
  // 初始化键盘
  M5Cardputer.Keyboard.begin();'''
  
setup_new = '''void setup() {
#ifdef TARGET_STICKS3
  auto cfg = M5.config();
  M5.begin(cfg);
  DISPLAY_CLASS.setRotation(3);
  DISPLAY_CLASS.setBrightness(160);
  M5.Imu.begin();
#else
  M5Cardputer.begin();
  DISPLAY_CLASS.setRotation(1);
  DISPLAY_CLASS.setBrightness(160);
  M5Cardputer.Keyboard.begin();
#endif'''
code = code.replace(setup_orig, setup_new)

# 7. handleInput function
input_orig = '''void handleInput() {
  // --- 1. 获取当前所有目标按键的状态 ---
  bool curr_i = M5Cardputer.Keyboard.isKeyPressed('i');
  bool curr_a = M5Cardputer.Keyboard.isKeyPressed('a');
  bool curr_s = M5Cardputer.Keyboard.isKeyPressed('s');
  bool curr_tab = M5Cardputer.Keyboard.isKeyPressed(KEY_TAB);
  bool curr_up = M5Cardputer.Keyboard.isKeyPressed(UP_KEY_STR);
  bool curr_down = M5Cardputer.Keyboard.isKeyPressed(DOWN_KEY_STR);

  // --- 2. 使用静态变量追踪上一帧的状态 ---
  static bool prev_i = false;
  static bool prev_a = false;
  static bool prev_s = false;
  static bool prev_tab = false;
  static bool prev_up = false;
  static bool prev_down = false;

  // --- 3. 计算单次按下边沿 (当前为 true 且 上一帧为 false) ---
  bool pressed_i = curr_i && !prev_i;
  bool pressed_a = curr_a && !prev_a;
  bool pressed_s = curr_s && !prev_s;
  bool pressed_tab = curr_tab && !prev_tab;
  bool pressed_up = curr_up && !prev_up;
  bool pressed_down = curr_down && !prev_down;

  // --- 4. 更新上一帧状态等待下一次循环 ---
  prev_i = curr_i;
  prev_a = curr_a;
  prev_s = curr_s;
  prev_tab = curr_tab;
  prev_up = curr_up;
  prev_down = curr_down;

  // --- 5. 处理具体的触发逻辑 ---
  // 检查模式切换键
  if (pressed_i) {
    current_mode = 'i';
    update_parameter_colors();
    update_and_recalculate();
  } else if (pressed_a) {
    current_mode = 'a';
    priority_mode = 'A';
    update_parameter_colors();
    update_and_recalculate();
  } else if (pressed_s) {
    current_mode = 's';
    priority_mode = 'S';
    update_parameter_colors();
    update_and_recalculate();
  } else if (pressed_tab) {
    // Tab键循环切换i, a, s模式
    if (current_mode == 'i') {
      current_mode = 'a';
      priority_mode = 'A';
    } else if (current_mode == 'a') {
      current_mode = 's';
      priority_mode = 'S';
    } else if (current_mode == 's') {
      current_mode = 'i';
    }
    update_parameter_colors();
    update_and_recalculate();
  }
  
  // 检查滚动键 - 为匹配Python版本，仅使用点/分号进行滚动
  if (pressed_up) {
    scroll_list(-1);  // 向上滚动
  } else if (pressed_down) {
    scroll_list(1);  // 向下滚动
  }
}'''

input_new = '''void handleInput() {
#ifdef TARGET_STICKS3
  bool curr_tab = M5.BtnB.isPressed();
  static bool prev_tab = false;
  bool pressed_tab = curr_tab && !prev_tab;
  prev_tab = curr_tab;
  
  if (pressed_tab) {
    if (current_mode == 'i') { current_mode = 'a'; priority_mode = 'A'; }
    else if (current_mode == 'a') { current_mode = 's'; priority_mode = 'S'; }
    else if (current_mode == 's') { current_mode = 'i'; }
    update_parameter_colors();
    update_and_recalculate();
  }
  
  bool curr_lock = M5.BtnA.isPressed();
  static bool prev_lock = false;
  if(curr_lock && !prev_lock) {
     ev_locked = !ev_locked;
     update_debug_title();
  }
  prev_lock = curr_lock;

  float accelX = 0, accelY = 0, accelZ = 0;
  M5.Imu.getAccel(&accelX, &accelY, &accelZ);
  
  static unsigned long last_scroll_time = 0;
  // 倾斜阈值0.4，越过且距离上次>300ms才滚动
  if(millis() - last_scroll_time > 300) {
      if(accelY > 0.4) {
          scroll_list(1);
          last_scroll_time = millis();
      } else if (accelY < -0.4) {
          scroll_list(-1);
          last_scroll_time = millis();
      }
  }
#else
  bool curr_i = M5Cardputer.Keyboard.isKeyPressed('i');
  bool curr_a = M5Cardputer.Keyboard.isKeyPressed('a');
  bool curr_s = M5Cardputer.Keyboard.isKeyPressed('s');
  bool curr_tab = M5Cardputer.Keyboard.isKeyPressed(KEY_TAB);
  bool curr_up = M5Cardputer.Keyboard.isKeyPressed(UP_KEY_STR);
  bool curr_down = M5Cardputer.Keyboard.isKeyPressed(DOWN_KEY_STR);

  static bool prev_i = false;
  static bool prev_a = false;
  static bool prev_s = false;
  static bool prev_tab = false;
  static bool prev_up = false;
  static bool prev_down = false;

  bool pressed_i = curr_i && !prev_i;
  bool pressed_a = curr_a && !prev_a;
  bool pressed_s = curr_s && !prev_s;
  bool pressed_tab = curr_tab && !prev_tab;
  bool pressed_up = curr_up && !prev_up;
  bool pressed_down = curr_down && !prev_down;

  prev_i = curr_i;
  prev_a = curr_a;
  prev_s = curr_s;
  prev_tab = curr_tab;
  prev_up = curr_up;
  prev_down = curr_down;

  if (pressed_i) { current_mode = 'i'; update_parameter_colors(); update_and_recalculate(); } 
  else if (pressed_a) { current_mode = 'a'; priority_mode = 'A'; update_parameter_colors(); update_and_recalculate(); } 
  else if (pressed_s) { current_mode = 's'; priority_mode = 'S'; update_parameter_colors(); update_and_recalculate(); } 
  else if (pressed_tab) {
    if (current_mode == 'i') { current_mode = 'a'; priority_mode = 'A'; } 
    else if (current_mode == 'a') { current_mode = 's'; priority_mode = 'S'; } 
    else if (current_mode == 's') { current_mode = 'i'; }
    update_parameter_colors();
    update_and_recalculate();
  }
  
  if (pressed_up) { scroll_list(-1); } 
  else if (pressed_down) { scroll_list(1); }
#endif
}'''
code = code.replace(input_orig, input_new)


# 8. Loop logic inside loop()
loop_orig = '''          // 始终更新传感器值
          float previous_lux = last_lux_value;
          last_lux_value = current_lux;
          // 更新调试信息，包含LUX值和调试信息'''
          
loop_new = '''          // 始终更新传感器值
          float previous_lux = last_lux_value;
          if (!ev_locked) {
            last_lux_value = current_lux;
          }
          current_lux = last_lux_value; // 让界面显示锁定的计算值
          // 更新调试信息，包含LUX值和调试信息'''
code = code.replace(loop_orig, loop_new)

with open('main.cpp', 'w', encoding='utf-8') as f:
    f.write(code)
print("Patch applied to main.cpp")
