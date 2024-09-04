import os

import pandas as pd
from playwright.sync_api import sync_playwright

from biorange.core.logger import get_logger
from biorange.core.utils.package_fileload import get_data_file_path

logger = get_logger(__name__)


class GenecardsDiseaseScraper:
    def __init__(
        self,
        user_data_dir="./User Data",
        download_path=None,
    ):
        self.user_data_dir = user_data_dir
        default_path = "data/GeneCards-SearchResults.csv"
        self.download_path = (
            download_path
            or (
                not os.path.exists(default_path)
                and get_data_file_path("GeneCards-SearchResults.csv")
            )
            or default_path
        )

        self.playwright = None
        self.browser_context = None
        self.page = None

        if self.download_path == get_data_file_path("GeneCards-SearchResults.csv"):
            # 警告，
            logger.error(
                "不可使用默认文件，你需要自行下载genecards结果文件放入：data/GeneCards-SearchResults.csv"
            )

        # 检查本地文件是否存在，如果存在则不启动Playwright
        if not os.path.exists(self.download_path):
            self.playwright = sync_playwright().start()
            self.browser_context = self.playwright.chromium.launch_persistent_context(
                self.user_data_dir,
                headless=False,
                args=[
                    "--disable-blink-features=AutomationControlled",  # 移除自动化标识
                    "--disable-extensions",  # 禁用扩展
                ],
                viewport={"width": 1280, "height": 800},  # 设置窗口大小
            )
            self.page = (
                self.browser_context.pages[0]
                if self.browser_context.pages
                else self.browser_context.new_page()
            )

    def __del__(self):
        if self.browser_context:
            self.browser_context.close()
        if self.playwright:
            self.playwright.stop()

    def read_local_file(self) -> pd.DataFrame:
        """尝试读取本地文件并返回 DataFrame"""
        if os.path.exists(self.download_path):
            print(f"File already exists: {self.download_path}")
            return pd.read_csv(self.download_path)
        return pd.DataFrame()

    def download_file(self, query_string):
        """在线下载文件并保存到本地"""
        if not self.page:
            print("Playwright is not initialized.")
            return

        try:
            # 设置请求头，以避免检测
            self.page.set_extra_http_headers(
                {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "Accept-Language": "en-US,en;q=0.9",
                }
            )
            # 构建完整的URL并导航
            url = f"https://www.genecards.org/Search/Keyword?queryString={query_string}"
            self.page.goto(url)
            print("Page loaded.")
            # 手动登录
            if self.page.url == "https://www.lifemapsc.com/gcsuite/gc_trial/":
                print("Please login to GeneCards.")
                input("Press Enter after completing login...")
                self.page.goto(url)

            # 悬停在#exportBarLabel上以展开菜单
            export_label = self.page.locator("#exportBarLabel")
            export_label.hover()
            export_label.click()
            print("Hovered over export bar label.")

            # 查找并点击指定的下载链接
            download_link = self.page.locator('a[data-target="excel"]')

            # 监听下载事件
            with self.page.expect_download() as download_info:
                download_link.click()
            download = download_info.value

            # 保存下载文件到指定路径和文件名
            download.save_as(self.download_path)
            print(f"Download completed: {self.download_path}")

        except Exception as e:
            print(f"An error occurred: {e}")

    def search(self, query_string):
        """主方法：尝试读取本地文件，如果不存在则在线下载并返回 DataFrame"""
        df = self.read_local_file()
        if df.empty:
            self.download_file(query_string)
            df = self.read_local_file()
        result = pd.DataFrame()
        if df.empty:
            return pd.DataFrame(cloumns=["disease", "dis_targets", "source"])
        result["dis_targets"] = df["Gene Symbol"].values
        result["disease"] = query_string
        result["source"] = "GeneCards"
        return result


# 使用示例
if __name__ == "__main__":
    downloader = GenecardsDiseaseScraper()
    df = downloader.search("liver cancer")
    print(df)
