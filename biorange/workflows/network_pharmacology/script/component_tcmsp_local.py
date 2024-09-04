import json
import re
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from biorange.core.logger import get_logger
from biorange.core.utils.package_fileload import get_data_file_path

logger = get_logger(__name__)


class TCMSPComponentLocalScraper:
    def __init__(self, use_remote: bool = False, remote_url: Optional[str] = None):
        """
        初始化草药查询器，提供本地或远程的 Playwright 环境配置选项。

        Args:
            use_remote (bool): 是否使用远程 Playwright 服务器。
            remote_url (Optional[str]): 远程服务器的 WebSocket URL（如果使用远程）。
        """
        self.use_remote = use_remote
        self.remote_url = remote_url or "ws://127.0.0.1:1985"
        self._setup_playwright()

    def _setup_playwright(self):
        """
        为用户提供配置 Playwright 环境的提示。
        """
        if self.use_remote:
            logger.info(
                "使用远程 Playwright 服务。确保你已在远程运行：playwright run-server --host 0.0.0.0 --port 1985"
            )
            logger.info(
                f"或docker run -it --rm -p 1985:1985 --ipc=host august777/playwright-server:v1.46.0-jammy"
            )
        else:
            logger.info("使用本地 Playwright。确保你已安装：pip install playwright")
            logger.info("并运行：playwright install chromium")

    def get_search_result_url(self, search_term: str) -> str:
        """
        使用 Playwright 在指定网页中搜索并获取结果的 URL。

        Args:
            search_term (str): 搜索词。

        Returns:
            str: 搜索结果的 URL。
        """
        with sync_playwright() as p:
            if self.use_remote:
                browser = p.chromium.connect(self.remote_url)
            else:
                browser = p.chromium.launch(headless=True)

            page = browser.new_page()
            page.goto("https://old.tcmsp-e.com/browse.php?qc=herbs")

            # 在搜索框中输入搜索词
            page.fill("#inputVarTcm", search_term)
            page.click("#searchBtTcm")

            # 等待搜索结果加载
            page.wait_for_selector(
                "#grid > div.k-grid-content > table > tbody > tr > td:nth-child(3)"
            )

            # 获取搜索结果的href
            href = page.get_attribute(
                "#grid > div.k-grid-content > table > tbody > tr > td:nth-child(3) > a",
                "href",
            )
            browser.close()

            if href:
                result_url = f"https://old.tcmsp-e.com/{href}"
                logger.info(f"成功获取搜索结果的URL: {result_url}")
                return result_url
            else:
                logger.error("未能获取搜索结果的URL")
                raise ValueError("未能获取搜索结果的URL")

    def fetch_webpage_content(self, url: str) -> str:
        """
        获取指定URL的网页内容。

        Args:
            url (str): 目标网页的URL。

        Returns:
            str: 网页的HTML内容。
        """
        try:
            response = requests.get(url)
            response.raise_for_status()
            logger.info(f"成功获取网页内容: {url}")
            return response.text
        except requests.RequestException as e:
            logger.error(f"获取网页内容时出错: {e}")
            raise

    def extract_json_data(self, html_content: str) -> Optional[List[Dict[str, Any]]]:
        """
        从HTML内容中提取JSON数据。

        Args:
            html_content (str): 网页的HTML内容。

        Returns:
            Optional[List[Dict[str, Any]]]: 解析后的JSON数据列表，如果未找到则返回None。
        """
        soup = BeautifulSoup(html_content, "html.parser")
        script_tag = soup.select_one("#tabstrip > script:nth-child(6)")

        if not script_tag or not script_tag.string:
            logger.warning("未找到目标script标签")
            return None

        pattern = re.compile(r"data:\s*(\[\{.*?\}\])", re.DOTALL)
        match = pattern.search(script_tag.string)

        if not match:
            logger.warning("未找到data字段的JSON数组")
            return None

        try:
            json_data = json.loads(match.group(1))
            logger.info("成功提取并解析JSON数据")
            return json_data
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析错误: {e}")
            return None

    def convert_to_dataframe(self, data: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        将JSON数据转换为pandas DataFrame。

        Args:
            data (List[Dict[str, Any]]): JSON数据列表。

        Returns:
            pd.DataFrame: 转换后的DataFrame。
        """
        try:
            df = pd.DataFrame(data)
            logger.info("成功将数据转换为DataFrame")
            return df
        except Exception as e:
            logger.error(f"数据转换为DataFrame时出错: {e}")
            raise

    # 缓存
    from functools import lru_cache

    @lru_cache(maxsize=128)
    def search_herb(self, herb_name: str) -> pd.DataFrame:
        """
        查询指定草药名，返回结果的DataFrame。

        Args:
            herb_name (str): 草药名。

        Returns:
            pd.DataFrame: 查询结果的DataFrame，即使未找到结果也返回空的DataFrame。
        """
        try:
            # 获取搜索结果的URL
            webpage_url = self.get_search_result_url(herb_name)

            # 获取网页内容
            html_content = self.fetch_webpage_content(webpage_url)

            # 从HTML中提取JSON数据
            data = self.extract_json_data(html_content)

            if data:
                # 将数据转换为pandas DataFrame
                data = self.convert_to_dataframe(data)
                logger.info("数据已成功提取并转换为DataFrame")

                logger.info(f"合并离线数据{get_data_file_path('TCMSP_mol.csv')}")
                csv_table = pd.read_csv(get_data_file_path("TCMSP_mol.csv"))
                data = pd.merge(
                    data["MOL_ID"],
                    csv_table,
                    left_on="MOL_ID",
                    right_on="MOL_ID",
                    how="inner",
                )

                return data
            else:
                logger.warning("无法提取数据，返回空的DataFrame")
                return pd.DataFrame()

        except Exception as e:
            logger.exception("处理过程中发生错误:")
            return pd.DataFrame()  # 返回空的DataFrame以确保函数返回类型一致


if __name__ == "__main__":
    scraper = TCMSPComponentLocalScraper(use_remote=True)
    df = scraper.search_herb("陈皮")
    df.to_csv("out.csv")
    print(df)
