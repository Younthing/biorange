import os
import pickle
import threading
import time
from abc import ABC, abstractmethod
from typing import Any, Optional

import redis

from biorange.core.logger import get_logger


# CacheManager 接口
class CacheManager(ABC):
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        pass

    @abstractmethod
    def save(self, key: str, value: Any, ttl: Optional[int] = None):
        pass

    @abstractmethod
    def delete(self, key: str):
        pass


# 内存缓存实现
class InMemoryCacheManager(CacheManager):
    def __init__(self):
        self.cache = {}
        self.lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        with self.lock:
            entry = self.cache.get(key)
            if entry and (entry["ttl"] is None or entry["ttl"] > time.time()):
                return entry["value"]
            elif entry:
                del self.cache[key]
        return None

    def save(self, key: str, value: Any, ttl: Optional[int] = None):
        with self.lock:
            self.cache[key] = {
                "value": value,
                "ttl": time.time() + ttl if ttl else None,
            }

    def delete(self, key: str):
        with self.lock:
            if key in self.cache:
                del self.cache[key]


# 文件缓存实现
class FileCacheManager(CacheManager):
    def __init__(self, cache_dir: str):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        self.logger = get_logger(__name__)

    def _get_cache_path(self, key: str) -> str:
        return os.path.join(self.cache_dir, f"{key}.pkl")

    def get(self, key: str) -> Optional[Any]:
        cache_path = self._get_cache_path(key)
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "rb") as f:
                    entry = pickle.load(f)
                    if entry["ttl"] is None or entry["ttl"] > time.time():
                        return entry["value"]
                    else:
                        self.delete(key)
            except (OSError, pickle.PickleError) as e_file:
                self.logger.error(f"Failed to read cache for key {key}: {e_file}")
        return None

    def save(self, key: str, value: Any, ttl: Optional[int] = None):
        cache_path = self._get_cache_path(key)
        entry = {"value": value, "ttl": time.time() + ttl if ttl else None}
        try:
            with open(cache_path, "wb") as f:
                pickle.dump(entry, f)
        except (OSError, pickle.PickleError) as e_save:
            self.logger.error("Failed to write cache for key %s: %s", key, e_save)

    def delete(self, key: str):
        cache_path = self._get_cache_path(key)
        if os.path.exists(cache_path):
            try:
                os.remove(cache_path)
            except OSError as e:
                self.logger.error(f"Failed to delete cache for key {key}: {e}")


class RedisCacheManager(CacheManager):
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        self.client = redis.StrictRedis(host=host, port=port, db=db)
        self.logger = get_logger(__name__)

    def get(self, key: str) -> Optional[Any]:
        try:
            data = self.client.get(key)
            if data and isinstance(data, bytes):
                return pickle.loads(data)
        except (redis.RedisError, pickle.PickleError) as e_redis:
            self.logger.error(
                f"Failed to get cache for key {key} from Redis: {e_redis}"
            )
        return None

    def save(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        try:
            data = pickle.dumps(value)
            if ttl:
                self.client.setex(key, ttl, data)
            else:
                self.client.set(key, data)
        except (redis.RedisError, pickle.PickleError) as e:
            self.logger.error(f"Failed to save cache for key {key} to Redis: {e}")

    def delete(self, key: str) -> None:
        try:
            self.client.delete(key)
        except redis.RedisError as e:
            self.logger.error(f"Failed to delete cache for key {key} from Redis: {e}")


# 通用缓存管理器
class GeneralCacheManager(CacheManager):
    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager

    def get(self, key: str) -> Optional[Any]:
        return self.cache_manager.get(key)

    def save(self, key: str, value: Any, ttl: Optional[int] = None):
        self.cache_manager.save(key, value, ttl)

    def delete(self, key: str):
        self.cache_manager.delete(key)


# 工厂方法创建缓存管理器
class CacheManagerFactory:
    @staticmethod
    def create_cache_manager(
        cache_type: str = "memory",
        cache_dir: str = "./.cache",  # 默认缓存目录
        redis_config: Optional[dict] = None,
    ) -> CacheManager:
        if cache_type == "redis":
            redis_config = redis_config or {"host": "localhost", "port": 6379, "db": 0}
            return RedisCacheManager(**redis_config)
        elif cache_type == "file":
            return FileCacheManager(cache_dir)
        elif cache_type == "memory":
            return InMemoryCacheManager()
        else:
            raise ValueError("Invalid cache type")


# 使用示例
if __name__ == "__main__":
    try:
        cache_manager = CacheManagerFactory.create_cache_manager(cache_type="redis")
    except ValueError as e:
        print(f"Error: {e}")

    general_cache_manager = GeneralCacheManager(cache_manager)
    general_cache_manager.save("test_key", "test_value", ttl=60)
    print(general_cache_manager.get("test_key"))
    general_cache_manager.delete("test_key")
    print(general_cache_manager.get("test_key"))
