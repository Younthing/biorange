import os
import subprocess
import sys


def main():
    """
    主函数：执行smina二进制文件并处理其输出。

    该函数执行以下步骤：
    1. 获取当前脚本的目录。
    2. 构建smina二进制文件的路径。
    3. 执行smina二进制文件，传递命令行参数。
    4. 打印标准输出和标准错误。
    5. 以smina的返回码退出程序。

    Returns:
        None
    """
    # 获取当前脚本的目录
    script_dir = os.path.dirname(os.path.realpath(__file__))
    # 构建二进制文件的路径
    smina_path = os.path.join(script_dir, "smina.static")
    # 执行二进制文件
    result = subprocess.run(
        [smina_path] + sys.argv[1:], capture_output=True, check=False
    )
    # 打印输出
    print(result.stdout.decode())
    print(result.stderr.decode(), file=sys.stderr)
    sys.exit(result.returncode)
