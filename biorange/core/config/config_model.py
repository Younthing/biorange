"""定义参数字段，需要用到的参数都放这里"""

from pydantic import BaseModel, Field


class APISettings(BaseModel):
    """
    API 设置类，定义了 API 相关的配置参数。

    Args:
        key (str): API 密钥，默认值为 "default_api_key"。
        url (str): API URL，默认值为 "https://api.default.com"。
    """

    key: str = Field(default="default_api_key", description="API 密钥")
    url: str = Field(default="https://api.default.com", description="API URL")


class DatabaseSettings(BaseModel):
    """
    数据库设置类，定义了数据库相关的配置参数。

    Args:
        url (str): 数据库 URL，默认值为 "default_database_url"。
        pool_size (int): 数据库连接池大小，默认值为 5。
    """

    url: str = Field(default="default_database_url", description="数据库 URL")
    pool_size: int = Field(default=5, description="数据库连接池大小")


class Settings(BaseModel):
    """
    配置设置类，定义了应用程序的各种配置参数。

    Args:
        api (APISettings): API 相关的配置参数。
        database (DatabaseSettings): 数据库相关的配置参数。
    """

    api: APISettings = Field(default_factory=APISettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    drug_name: list[str] = Field(default=[], description="药物名称列表")
    disease_name: str = Field(default="", description="疾病名称")
    results_dir: str = Field(default="results", description="结果目录")


# 示例用法
if __name__ == "__main__":
    settings = Settings()
    print(settings.api.key)  # 输出: default_api_key
    print(settings.database.url)  # 输出: default_database_url
