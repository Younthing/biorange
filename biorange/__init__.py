"""
模块: __init__.py
描述: 'biorange' 包的初始化模块。
"""

from pyfiglet import figlet_format

# 尝试获取已安装包的版本号
try:
    from importlib.metadata import version as get_version

    __version__ = get_version("biorange")
except ImportError:
    __version__ = "0.0.0"  # 如果获取版本号失败，则使用默认版本号

# 生成斜体的 "BIORANGE" ASCII 艺术字

ascii_art = figlet_format("BioRange", font="slant")

# 显示 ASCII 艺术字和当前包的版本号
print(ascii_art)
