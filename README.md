# CatShare LineageOS 刷入包 (支持 addon.d OTA 自动恢复)

本项目基于 **MindTheGapps** 的官方安装架构与 LineageOS 的 **addon.d (ADDOND_VERSION=3)** 机制制作，用于将 **CatShare**（互传联盟第三方适配客户端）刷入为系统的特权应用（`priv-app`），使其能够顺利获取 **Wi-Fi Direct P2P MAC 地址**。

---

## 📦 生成的刷机包

- **安装包（刷入 CatShare）**：
  - 文件：[`CatShare-addon.d-arm64.zip`](file:///home/worker/Projects/CatShare/CatShare-addon.d-arm64.zip)
  - 功能：安装 CatShare 为系统特权应用，写入权限白名单，并配置 LineageOS OTA 自动存活脚本。
- **卸载包（移除 CatShare）**：
  - 文件：[`CatShare-uninstaller-arm64.zip`](file:///home/worker/Projects/CatShare/CatShare-uninstaller-arm64.zip)
  - 功能：安全移除 CatShare 应用、特权权限白名单以及 `addon.d` 存活脚本，恢复干净系统。
- **目标架构**：`arm64`（兼容现代主流 Android / LineageOS 设备）

---

## 🛠 核心技术机制

### 1. 特权应用与权限白名单 (`privapp-permissions`)
CatShare 需要获取系统的本地 Wi-Fi Direct MAC 地址，其在清单中声明了：
- `android.permission.LOCAL_MAC_ADDRESS`（系统特权权限 `signature|privileged`）
- `android.permission.INTERACT_ACROSS_USERS_FULL`
- `android.permission.DUMP`

在 Android 8.0+（尤其是 LineageOS 等官方 ROM）中，开启了 `enforce` 特权权限白名单机制。如果特权应用没有在系统配置中明确列入白名单，系统启动时将抛出异常甚至导致开机卡死。
本刷机包自动配置了 `/product/etc/permissions/privapp-permissions-catshare.xml`：
```xml
<?xml version="1.0" encoding="utf-8"?>
<permissions>
    <privapp-permissions package="moe.reimu.catshare">
        <permission name="android.permission.LOCAL_MAC_ADDRESS"/>
        <permission name="android.permission.INTERACT_ACROSS_USERS_FULL"/>
        <permission name="android.permission.DUMP"/>
    </privapp-permissions>
</permissions>
```
这使得 CatShare 作为系统特权应用运行时能直接获取真实的 Wi-Fi P2P MAC 地址。

### 2. LineageOS addon.d 自动持久化机制
在 LineageOS 进行系统全量更新或 OTA 升级时，`/system` 和 `/product` 分区通常会被全量抹除并重新刷入。
LineageOS 自带的 `backuptool.sh` 机制会在更新时执行 `/system/addon.d/` 下的存活脚本：
- **更新前 (`backup`)**：执行 `70-catshare.sh backup`，自动备份：
  - `product/priv-app/CatShare/CatShare.apk`
  - `product/etc/permissions/privapp-permissions-catshare.xml`
- **更新后 (`restore`)**：执行 `70-catshare.sh restore` 将文件还原回对应分区。
- **还原后 (`post-restore`)**：自动修复权限为 `0644`、目录为 `0755`，属主设为 `root:root`，并重置 SELinux 上下文为 `system_file`。
- **免手动重刷**：每次 LineageOS 升级后，CatShare 仍然自动存在且特权权限完整保留。

### 3. 动态分区（Dynamic Partitions）与 System-as-Root 支持
安装与卸载脚本直接继承了 MindTheGapps 对 Android 现代分区的适配：
- 自动识别并探测 `/dev/block/mapper` 下的逻辑分区以及 A/B 槽位（`_a` / `_b`）。
- 对动态只读块设备自动执行 `blockdev --setrw`。
- 自动兼容独立 `/product` 分区与单 `system` 分区回退。

---

## 📲 刷入与卸载教程

### 方式 A：LineageOS Recovery（推荐）
1. 手机进入 **LineageOS Recovery**。
2. 选择 **Apply update** -> **Apply from ADB**。
3. 电脑连接手机，执行命令刷入（需要安装刷入安装包，需要卸载则刷入卸载包）：
   - **安装 CatShare**：
     ```bash
     adb sideload CatShare-addon.d-arm64.zip
     ```
   - **卸载 CatShare**：
     ```bash
     adb sideload CatShare-uninstaller-arm64.zip
     ```
4. 如果 Recovery 提示 `Signature verification failed. Install anyway?`（签名验证提示），直接点击 **Yes** 继续。
5. 操作完成后选择 **Reboot system now** 重启手机。

### 方式 B：第三方 Recovery（如 TWRP / OrangeFox）
1. 将安装包或卸载包传入手机存储（或 OTG U 盘）。
2. 进入 Recovery，点击 **Install**（安装），选中对应的 zip 包滑动刷入并重启。

---

## 🔄 后续升级 CatShare APK 与项目维护

本项目完全独立自治，不再依赖任何外部的 MindTheGapps 参考目录（你可以安全删除它）。

### 升级 APK 步骤：
1. 用新版本的 APK 替换根目录的 `catshare.apk`。
2. 运行打包脚本：
   ```bash
   python3 build_package.py
   ```
即可一键重新生成最新的 `CatShare-addon.d-arm64.zip`。

### 源码结构说明 (`package_src/`)：
如果需要对卡刷脚本或权限配置进行定制，可直接在 [`package_src/`](file:///home/worker/Projects/CatShare/package_src) 目录中编辑：
- `META-INF/com/google/android/update-binary`: Recovery 安装执行脚本
- `system/addon.d/addond_head` & `addond_tail`: LineageOS 备份存活脚本模板
- `system/product/etc/permissions/privapp-permissions-catshare.xml`: 特权权限白名单配置
- `toybox`: 静态编译的通用 arm64 工具集
- `build.prop`: 架构与安装包元信息

