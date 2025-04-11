#!/usr/bin/env python3
import os
import platform
import subprocess
import requests
import zipfile
import io
import shutil
from pathlib import Path

def download_chromedriver_mac_arm():
    """为Mac ARM架构下载正确的ChromeDriver"""
    print("正在为Mac ARM架构下载ChromeDriver...")
    
    # 创建驱动目录
    driver_dir = Path.home() / "chromedriver-mac-arm64"
    if driver_dir.exists():
        print(f"删除旧的驱动目录: {driver_dir}")
        shutil.rmtree(driver_dir)
    
    driver_dir.mkdir(exist_ok=True)
    
    # 获取Chrome版本
    try:
        chrome_version_cmd = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--version"]
        chrome_version = subprocess.check_output(chrome_version_cmd).decode('utf-8')
        chrome_version = chrome_version.strip().split(' ')[-1].split('.')[0]  # 提取主版本号
        print(f"检测到Chrome版本: {chrome_version}")
    except:
        print("无法检测Chrome版本，使用默认版本114")
        chrome_version = "114"
    
    # 下载对应版本的ChromeDriver
    download_url = f"https://storage.googleapis.com/chrome-for-testing-public/{chrome_version}.0.6000.0/mac-arm64/chromedriver-mac-arm64.zip"
    
    try:
        print(f"从 {download_url} 下载ChromeDriver...")
        response = requests.get(download_url)
        response.raise_for_status()
        
        # 解压驱动
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            z.extractall(driver_dir)
        
        # 设置可执行权限
        chromedriver_path = driver_dir / "chromedriver-mac-arm64" / "chromedriver"
        os.chmod(chromedriver_path, 0o755)
        
        print(f"ChromeDriver已下载并解压到: {chromedriver_path}")
        print(f"请将以下路径添加到yuanbao_crawler.py中:")
        print(str(chromedriver_path))
        
        return str(chromedriver_path)
    except Exception as e:
        print(f"下载ChromeDriver时出错: {e}")
        print("请手动下载ChromeDriver并更新路径")
        return None

if __name__ == "__main__":
    system = platform.system()
    machine = platform.machine()
    
    if system == "Darwin" and machine == "arm64":
        driver_path = download_chromedriver_mac_arm()
    else:
        print(f"此脚本用于Mac ARM架构，当前系统是: {system} {machine}") 