# Cardputer Photography Light Meter

[English](#english) | [中文](#中文)

---

<a name="english"></a>

## 📷 Cardputer Photography Light Meter (English)

A feature-rich photography light meter application for the M5Stack Cardputer, developed in MicroPython. It provides both APERure Priority and Shutter Priority modes with a responsive and intuitive user interface.This is a C++ version of nongxl/cardputer_LightMeter.

![App Screenshot](20250805_144436.jpg) 
![App Screenshot](20250729_154934.webp) 
<!-- TODO: Replace this with your own app screenshot -->

### Hardware Requirements

*   M5Stack Cardputer
*   M5Stack DLight Unit (I2C Ambient Light Sensor)

### Features

-   **Dual-Mode Metering**: Supports APERure Priority (`A`) and Shutter Priority (`S`) modes to suit different shooting scenarios.
-   **Real-Time Calculation**: After adjusting any exposure parameter (ISO, APERure, Shutter), the third parameter is calculated and updated instantly without any confirmation needed.
-   **Intuitive UI**:
    *   The left side clearly displays the final exposure combination of ISO, APERure (`APER`), and Shutter Speed (`SSPD`).
    *   The right side features a vertical selection list for the currently adjustable parameter, providing clear context.
    *   The currently focused parameter and the selected value in the list are highlighted in **green** for clear operational focus.
-   **Smart Boundary Detection**:
    *   When an option in the selection list would cause the calculated result to exceed the preset range (e.g., a shutter Speed faster than 1/4000s), that option is marked in **red**.
    *   The application **prevents** the user from selecting red-marked invalid options, ensuring operations stay within a valid exposure range.
-   **Non-Circular Selection**: The parameter list stops scrolling when it reaches the maximum or minimum value, which is more precise and aligns with professional habits.
-   **Hardware Info**: Displays the real-time LUX value from the DLight sensor and the device's battery level.

### How to Use

#### Key Controls

-   **`Tab` key**: Cycles the operational focus between ISO, APERure (`APER`), and Shutter Speed (`SSPD`).
-   **`i` / `a` / `s` keys**: Directly switch operational focus and metering mode.
    -   **`a` key**: Sets to **APERure Priority** mode and moves focus to APERure (`APER`).
    -   **`s` key**: Sets to **Shutter Priority** mode and moves focus to Shutter Speed (`SSPD`).
    -   **`i` key**: Moves focus to ISO. This action **does not** change the current metering mode (A/S).
-   **`.` key (Up Arrow)**: Scrolls up and selects a value for the focused parameter.
-   **`;` key (Down Arrow)**: Scrolls down and selects a value for the focused parameter.

### Installation

#### Method 1: Using M5Burner (.bin firmware)

I have added the compiled .bin firmware and uploaded it to M5Burner. You can now directly download and burn this firmware using M5Burner.

![searchInM5bunner.jpg](searchInM5bunner.jpg)

#### Method 2: Using M5Launcher to load .bin firmware

If you want to keep the ability to run multiple firmwares on your Cardputer, you can use M5Launcher to load the Light Meter firmware:

1.  **Burn M5Launcher Firmware**: First, use M5Burner to burn the [M5Launcher Cardputer](https://github.com/bmorcelli/Launcher) firmware onto your Cardputer.

2.  **Download the Light Meter Firmware**: Use M5Burner to download the Cardputer Photography Light Meter firmware (do not burn it yet).

3.  **Locate the Firmware File**: The downloaded .bin firmware file is stored in M5Burner's installation directory under `packages\firmware`.

4.  **Copy to SD Card**: Copy the .bin firmware file to the root directory of a microSD card.

5.  **Load with M5Launcher**: Insert the microSD card into your Cardputer, power it on, and use M5Launcher to select and load the Light Meter firmware.

#### Method 3: Build from Source (Using VSCode and PlatformIO)

1.  **Install Required Software**:
    *   Download and install [Visual Studio Code](https://code.visualstudio.com/).
    *   Install the [PlatformIO IDE extension](https://platformio.org/platformio-ide) for VSCode.
    *   Ensure you have the necessary USB drivers for your Cardputer installed.

2.  **Clone the Repository**:
    ```bash
    git clone https://github.com/your-username/cardputer_LightMeter_Cpp.git
    cd cardputer_LightMeter_Cpp
    ```

3.  **Open the Project in VSCode**:
    *   Launch VSCode.
    *   Click on "File" > "Open Folder" and select the cloned repository folder.
    *   PlatformIO should automatically detect the project configuration.

4.  **Install Dependencies**:
    *   Wait for PlatformIO to initialize the project.
    *   The dependencies are defined in the `platformio.ini` file and should be installed automatically.
    *   If not, click on the PlatformIO icon in the sidebar, then click on "Install All Libraries" in the "Project Tasks" section.

5.  **Connect Your Device**:
    *   Connect your Cardputer to your computer via a USB-C cable.
    *   Press and hold the **G0** button while connecting to enter download mode if necessary.

6.  **Build and Upload**:
    *   Click on the PlatformIO icon in the sidebar.
    *   Under "Project Tasks" > "m5cardputer" > "General", click on "Upload".
    *   This will build the project and upload the firmware to your Cardputer.

7.  **Monitor Output** (Optional):
    *   To view serial output, click on "Monitor" under the same "General" section.
    *   This will open a serial monitor showing debug information from the device.

---

<a name="中文"></a>

## 📷 Cardputer 摄影测光表 (中文)

这是一款为 M5Stack Cardputer 打造的功能完善的摄影测光表应用，使用 MicroPython 开发。它提供了光圈优先和快门优先两种核心测光模式，并拥有一个响应迅速、交互直观的用户界面。这是一个基于nongxl/cardputer_LightMeter项目重构的C++版本

![应用截图](20250805_144436.jpg)
![应用截图](20250729_154934.webp)

### 硬件需求

*   M5Stack Cardputer
*   M5Stack DLight Unit (I2C 环境光传感器)

### 功能特性

-   **双模式测光**: 支持光圈优先 (`A`) 和快门优先 (`S`) 模式，满足不同拍摄场景的需求。
-   **实时计算**: 调整任何曝光参数（ISO、光圈、快门）后，程序会立即计算出第三个参数的值，无需等待或确认。
-   **直观的用户界面**:
    *   左侧清晰显示 ISO、光圈 (`APER`) 和快门速度 (`SSPD`) 的最终曝光组合。
    *   右侧为当前可调参数的纵向选择列表，提供清晰的上下文。
    *   当前拥有输入焦点的参数和在列表中选中的值，均以**绿色**高亮显示，操作目标明确。
-   **智能边界检测**:
    *   当待选列表中的某个选项会导致计算结果超出预设范围时（例如，计算出的快门速度快于 1/4000s），该选项会在列表中被标为**红色**。
    *   程序会**阻止**用户选择被标为红色的无效选项，确保操作始终在有效曝光组合内。
-   **非循环选择**: 参数列表在选择到最大或最小值后会停止滚动，操作更精确、更符合专业习惯。
-   **硬件信息显示**: 实时显示 DLight 传感器读取的 LUX 值和设备电量。

### 如何使用

#### 按键控制

-   **`Tab` 键**: 在 ISO、光圈 (`APER`) 和快门速度 (`SSPD`) 之间循环切换操作焦点。
-   **`i` / `a` / `s` 键**: 直接切换操作焦点和测光模式。
    -   **`a` 键**: 设定为 **光圈优先** 模式，并将操作焦点切换到光圈 (`APER`)。
    -   **`s` 键**: 设定为 **快门优先** 模式，并将操作焦点切换到快门速度 (`SSPD`)。
    -   **`i` 键**: 将操作焦点切换到 ISO。此操作**不会**改变当前的测光模式（光圈/快门优先）。
-   **`.` 键 (上箭头)**: 向上滚动并选择当前焦点参数的值。
-   **`;` 键 (下箭头)**: 向下滚动并选择当前焦点参数的值。

### 安装与部署

#### 方法一：使用 M5Burner（.bin 固件）

我添加了编译的.bin固件，已经上传到M5bunner，现在可以直接通过M5bunner下载和烧录这个固件。

![searchInM5bunner.jpg](searchInM5bunner.jpg)

#### 方法二：使用 M5Launcher 加载 .bin 固件

如果您想保留在Cardputer上运行多个固件的能力，可以使用M5Launcher加载测光表固件：

1.  **烧录 M5Launcher 固件**：首先，使用M5Burner为您的Cardputer烧录[M5Launcher Cardputer](https://github.com/bmorcelli/Launcher)固件。

2.  **下载测光表固件**：使用M5Burner下载Cardputer摄影测光表固件（暂时不要烧录）。

3.  **找到固件文件**：下载的.bin固件文件存储在M5Burner安装目录下的`packages\firmware`文件夹中。

4.  **复制到SD卡**：将.bin固件文件复制到microSD卡的根目录。

5.  **使用M5Launcher加载**：将microSD卡插入Cardputer，开机后使用M5Launcher选择并加载测光表固件。

#### 方法三：从源码编译（使用 VSCode 和 PlatformIO）

1.  **安装必要软件**：
    *   下载并安装 [Visual Studio Code](https://code.visualstudio.com/)。
    *   为 VSCode 安装 [PlatformIO IDE 扩展](https://platformio.org/platformio-ide)。
    *   确保您已安装 Cardputer 所需的 USB 驱动程序。

2.  **克隆代码库**：
    ```bash
    git clone https://github.com/your-username/cardputer_LightMeter_Cpp.git
    cd cardputer_LightMeter_Cpp
    ```

3.  **在 VSCode 中打开项目**：
    *   启动 VSCode。
    *   点击 "文件" > "打开文件夹"，选择克隆的代码库文件夹。
    *   PlatformIO 应该会自动检测项目配置。

4.  **安装依赖项**：
    *   等待 PlatformIO 初始化项目。
    *   依赖项在 `platformio.ini` 文件中定义，应该会自动安装。
    *   如果没有自动安装，点击侧边栏中的 PlatformIO 图标，然后在 "项目任务" 部分点击 "安装所有库"。

5.  **连接设备**：
    *   使用 USB-C 数据线将您的 Cardputer 连接到电脑。
    *   如有必要，在连接时按住 **G0** 按钮以进入下载模式。

6.  **编译和上传**：
    *   点击侧边栏中的 PlatformIO 图标。
    *   在 "项目任务" > "m5cardputer" > "通用" 下，点击 "Upload"。
    *   这将编译项目并将固件上传到您的 Cardputer。

7.  **监控输出**（可选）：
    *   要查看串行输出，点击同一 "通用" 部分下的 "Monitor"。
    *   这将打开一个串行监视器，显示来自设备的调试信息。
