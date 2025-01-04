import subprocess
import os
import requests
from src.tool import show_progress
import zipfile
edge_exe_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
parent_file_path = 'driver/edgedriver_win64'
file_path = 'driver/edgedriver_win64.zip'
unzip_file_path = 'driver/edgedriver_win64/msedgedriver.exe'
edgedriver_location = 'driver/msedgedriver.exe'

def is_exist_edgedriver(file_path):
    """
    获取浏览器版本
    :param file_path: 浏览器文件路径
    :return: 浏览器大版本号
    """
    # 判断路径文件是否存在
    if not os.path.isfile(file_path):
        return False


    return True

#获取edge的版本
def get_executable_version(exe_path):
    try:
        # 构建PowerShell命令
        powershell_command = f'(Get-Command "{exe_path}").FileVersionInfo.FileVersion'

        # 使用subprocess运行PowerShell命令
        result = subprocess.run([
            'powershell',
            '-NoProfile',
            '-Command',
            powershell_command
        ], capture_output=True, text=True)

        # 返回命令的输出
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        return None

def download_driver(file_url, file_path):
    print("正在请求下载Downloading......")
    # 发送HEAD请求来获取文件大小
    with requests.head(file_url) as head_response:
        if head_response.status_code != 200:
            print("请求失败，状态码：", head_response.status_code)
            return

        # 获取文件大小
        file_size = int(head_response.headers.get('content-length', 0))

    # 发送GET请求
    with requests.get(file_url, stream=True) as response:
        if response.status_code == 200:
            # 打开文件以写入二进制模式
            with open(file_path, 'wb') as file:
                downloaded = 0
                total_chunks = 0
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:  # 过滤掉保持活动连接的chunk
                        file.write(chunk)
                        downloaded += len(chunk)
                        total_chunks += 1
                        show_progress('edgedriver_win64.zip', downloaded, file_size)

            print("\n驱动文件下载完成")
        else:
            print("请求失败，状态码：", response.status_code)

def unzip_driver(zip_path,extract_to_path) :


    # 要解压的特定文件名（确保文件名是ZIP文件内的相对路径）
    file_to_extract = 'file_inside_zip.txt'

    # 使用 zipfile 模块打开 ZIP 文件
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        # 解压到指定路径
        zip_ref.extractall(extract_to_path)

    print(f"文件 '{zip_path}' 已被解压到 '{extract_to_path}'")

if __name__ == '__main__':
    edge_driver_version = get_executable_version(edgedriver_location)
    edge_version = get_executable_version(edge_exe_path)
    Base_edgedriver_url = f'https://msedgedriver.azureedge.net/{edge_version}/edgedriver_win64.zip'
    if is_exist_edgedriver(edgedriver_location):

        print(f"Microsoft Edge driver版本信息: {edge_driver_version}")
        print(f"Microsoft Edger版本信息: {edge_version}")
        if edge_driver_version == edge_version :
            print("Edge版本已和dirver版本一致")
        else :
            download_driver(Base_edgedriver_url,file_path)
            unzip_driver(file_path, parent_file_path)
            subprocess.run(['powershell', '-Command', f"del {edgedriver_location}"], check=True)

            # 移动文件
            # 使用subprocess.run执行PowerShell命令
            subprocess.run(['powershell', '-Command', f"move {unzip_file_path} {edgedriver_location}"], check=True)

            # 删除zip压缩包
            subprocess.run(['powershell', '-Command', f"rd {file_path}"], check=True)

            # PowerShell命令，用于递归删除目录及其内容
            cmd = f'Remove-Item -Path {parent_file_path} -Recurse -Force'

            # 使用subprocess.run执行PowerShell命令
            subprocess.run(['powershell', '-Command', cmd], check=True)

            print(f"Microsoft驱动 {edge_version} 已更新完毕！")

    else :

        download_driver(Base_edgedriver_url,file_path)
        unzip_driver(file_path,parent_file_path)
        # 移动文件
        #使用subprocess.run执行PowerShell命令
        subprocess.run(['powershell', '-Command', f"move {unzip_file_path} {edgedriver_location}"], check=True)

        # 删除zip压缩包
        subprocess.run(['powershell', '-Command', f"rd {file_path}"], check=True)

        # PowerShell命令，用于递归删除目录及其内容
        cmd = f'Remove-Item -Path {parent_file_path} -Recurse -Force'

        # 使用subprocess.run执行PowerShell命令
        subprocess.run(['powershell', '-Command', cmd], check=True)


        print(f"Microsoft驱动 {edge_version} 已安装完毕！")




