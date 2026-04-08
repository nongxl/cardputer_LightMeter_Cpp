# M5Cardputer 跨设备键盘兼容性技术指南

本文档总结了在开发中实现 **M5Cardputer V1.1** (GPIO 扫描键盘) 与 **Cardputer ADV** (I2C 键盘) 完美兼容的技术要点。

---

## 1. 核心挑战：硬件驱动差异
*   **V1.1 (GPIO 矩阵)**: 通过 ESP32-S3 引脚直接扫描。
*   **ADV (I2C 网络)**: 通过 TCA8418 键盘扩展芯片通信（I2C 地址 0x34）。
*   **痛点**: 旧版库只支持 GPIO 模式，且系统自带的 `isChange()` 状态位在 ADV 硬件上有时触发不稳定。

---

## 2. 软件适配方案

### A. 环境配置 (PlatformIO)
必须使用支持自动检测硬件版本的库。锁定旧版本会导致代码在 ADV 上由于无法识别 I2C 键盘而完全失灵。
```ini
lib_deps = 
    m5stack/M5GFX@^0.2.4
    m5stack/M5Unified@^0.2.8
    m5stack/M5Cardputer@^1.2.0  ; 关键：1.2.0+ 对应 ADV 支持
```

### B. 逻辑重构：手动边沿检测 (Edge Detection)
由于 `M5Cardputer.Keyboard` 暂未提供类似物理按键的 `wasPressed()` 方法，且驱动层面的 `isChange()` 可能受各种宏定义影响，**手动维护状态位**是最稳健的做法。

**核心逻辑公式：**
`当前按下 (true)` + `上一帧松开 (false)` = **一次有效且唯一的点击事件**。

```cpp
void handleInput() {
    // 1. 获取当前实时状态
    bool curr_tab = M5Cardputer.Keyboard.isKeyPressed(KEY_TAB);
    
    // 2. 静态变量追踪历史
    static bool prev_tab = false;

    // 3. 计算单次点击边沿 (当前为真 且 历史为假)
    bool pressed_tab = curr_tab && !prev_tab;

    // 4. 更新历史状态供下一帧使用
    prev_tab = curr_tab;

    // 5. 业务逻辑应用
    if (pressed_tab) {
        // 执行切换模式逻辑...
    }
}
```

---

## 3. 开发规范建议
1.  **心跳统一**：只在 `loop()` 中调用一次 `M5Cardputer.update()`，它会自动处理所有底层刷新。
2.  **避免重复调用**：不要手动调用 `updateKeysState()`，除非你需要读取详细的 `KeysState`（如录入长字符串）。
3.  **UI 性能提示**：在 PlatformIO 中，推荐使用 `FreeSansBold` 矢量字体，它比 `DejaVu` 在这种高 PPI 屏幕上渲染得更加精致。

---

> [!IMPORTANT]
> **关键结论**: 跨设备兼容的本质是 **“用稳定的状态轮询取代不稳定的变化检测”**。只要按照上述“边沿检测”模板编写，您的代码无需任何修改即可在所有 Cardputer 版本上流畅运行。
