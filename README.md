### **v2rayN 自动更新节点脚本使用教程**

#### **1. 准备工作**
- **安装 Python**（3.6+ 版本）  
- **安装依赖库**（运行以下命令）：
  ```bash
  pip install requests beautifulsoup4 psutil
  ```
- **下载脚本**：将 `Automatic_cawling_mibei_Nodes.py` 保存到本地（如 `C:\v2ray_auto_update`）。
- **确保 v2rayN 已安装**：脚本会检测 `v2rayN.exe` 是否在相同目录下。

---

#### **2. 运行脚本**
- **方式 1：直接运行**
  ```
  python Automatic_cawling_mibei_Nodes.py
  ```
- **方式 2：定时任务（推荐）**
  - **Windows**：使用“任务计划程序”设置每天自动运行。
  - **Linux/Mac**：使用 `crontab` 定时执行。

---

#### **3. 脚本执行流程**
1. **检查 v2rayN 是否运行** → 若未运行，自动启动。
2. **访问目标网站**（`mibei77.com`）爬取最新节点链接。
3. **下载节点文件**（`.txt`）并保存到 `nodes.txt`。
4. **更新 v2rayN 订阅** → 自动重启 v2rayN 生效。

---

#### **4. 日志查看**
- 脚本运行日志保存在同目录下的 `v2ray_updater.log`，可检查错误信息。

---

#### **5. 注意事项**
- **网络畅通**：确保能访问 `mibei77.com`。
- **杀毒软件**：若拦截 `v2rayN.exe`，请添加信任。
- **手动更新**：若自动失败，可复制 `nodes.txt` 中的订阅链接到 v2rayN 手动更新。

---

✅ **完成！** 脚本会自动保持节点更新，无需手动操作。
