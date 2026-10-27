#!/usr/bin/env python3
import os
import shutil
import stat
import zipfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "package_src")
UNINSTALL_SRC_DIR = os.path.join(BASE_DIR, "uninstaller_src")
APK_PATH = os.path.join(BASE_DIR, "catshare.apk")

INSTALL_ZIP = os.path.join(BASE_DIR, "CatShare-addon.d-arm64.zip")
UNINSTALL_ZIP = os.path.join(BASE_DIR, "CatShare-uninstaller-arm64.zip")
TEMP_BUILD_DIR = os.path.join(BASE_DIR, ".build_tmp")

def pack_directory_to_zip(source_dir, output_zip):
    print(f"Generating flashable zip: {output_zip}...")
    if os.path.exists(output_zip):
        os.remove(output_zip)

    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, source_dir)
                file_stat = os.stat(full_path)
                zinfo = zipfile.ZipInfo(rel_path)
                zinfo.date_time = (2026, 1, 1, 0, 0, 0)
                # Preserve file permissions (executable bits) inside zip
                zinfo.external_attr = (file_stat.st_mode & 0xFFFF) << 16
                with open(full_path, "rb") as f:
                    z.writestr(zinfo, f.read(), compress_type=zipfile.ZIP_DEFLATED)

def build_installer():
    print("\n--- [1/2] Building Installer Package ---")
    if not os.path.isfile(APK_PATH):
        raise FileNotFoundError(f"CatShare APK not found at: {APK_PATH}")
    if not os.path.isdir(SRC_DIR):
        raise FileNotFoundError(f"Source template directory not found at: {SRC_DIR}")

    if os.path.exists(TEMP_BUILD_DIR):
        shutil.rmtree(TEMP_BUILD_DIR)

    # 1. Copy package_src tree
    shutil.copytree(SRC_DIR, TEMP_BUILD_DIR)

    # 2. Place catshare.apk into priv-app/CatShare/CatShare.apk
    target_apk_dir = os.path.join(TEMP_BUILD_DIR, "system", "product", "priv-app", "CatShare")
    os.makedirs(target_apk_dir, exist_ok=True)
    target_apk_path = os.path.join(target_apk_dir, "CatShare.apk")
    print(f"Copying {APK_PATH} -> {target_apk_path}...")
    shutil.copy2(APK_PATH, target_apk_path)

    # 3. Ensure executable permissions
    update_binary_path = os.path.join(TEMP_BUILD_DIR, "META-INF", "com", "google", "android", "update-binary")
    toybox_path = os.path.join(TEMP_BUILD_DIR, "toybox")
    for exec_file in [update_binary_path, toybox_path]:
        if os.path.exists(exec_file):
            current_mode = os.stat(exec_file).st_mode
            os.chmod(exec_file, current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    # 4. Pack zip
    pack_directory_to_zip(TEMP_BUILD_DIR, INSTALL_ZIP)
    shutil.rmtree(TEMP_BUILD_DIR)
    print(f"✓ Installer created: {INSTALL_ZIP}")

def build_uninstaller():
    print("\n--- [2/2] Building Uninstaller Package ---")
    if not os.path.isdir(UNINSTALL_SRC_DIR):
        raise FileNotFoundError(f"Uninstaller source directory not found at: {UNINSTALL_SRC_DIR}")

    if os.path.exists(TEMP_BUILD_DIR):
        shutil.rmtree(TEMP_BUILD_DIR)

    # 1. Copy uninstaller_src tree
    shutil.copytree(UNINSTALL_SRC_DIR, TEMP_BUILD_DIR)

    # 2. Ensure executable permissions
    update_binary_path = os.path.join(TEMP_BUILD_DIR, "META-INF", "com", "google", "android", "update-binary")
    toybox_path = os.path.join(TEMP_BUILD_DIR, "toybox")
    for exec_file in [update_binary_path, toybox_path]:
        if os.path.exists(exec_file):
            current_mode = os.stat(exec_file).st_mode
            os.chmod(exec_file, current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    # 3. Pack zip
    pack_directory_to_zip(TEMP_BUILD_DIR, UNINSTALL_ZIP)
    shutil.rmtree(TEMP_BUILD_DIR)
    print(f"✓ Uninstaller created: {UNINSTALL_ZIP}")

if __name__ == "__main__":
    build_installer()
    build_uninstaller()
    print("\n🎉 Both Installer and Uninstaller packages generated successfully!")
