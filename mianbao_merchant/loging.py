"""
日志输出模块

提供统一的日志记录功能，仅输出到文件，
包含不同级别的日志方法和装饰器。
"""

import logging
import os
from datetime import datetime
from functools import wraps
from config import LOG_DIR

# ==========================
# 日志配置
# ==========================
LOG_LEVEL = logging.DEBUG  # 可选：DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE = os.path.join(LOG_DIR, f"app_{datetime.now().strftime('%Y%m%d')}.log")


# ==========================
# 日志格式配置
# ==========================
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logger(name: str = __name__, level: int = LOG_LEVEL) -> logging.Logger:
    """
    设置并返回日志记录器
    
    创建或获取一个配置好的日志记录器，仅支持文件输出。
    如果日志目录不存在会自动创建。
    
    Args:
        name: 日志记录器名称，通常使用 __name__
        level: 日志级别，默认使用 LOG_LEVEL
        
    Returns:
        logging.Logger: 配置好的日志记录器实例
        
    Examples:
        >>> logger = setup_logger(__name__)
        >>> logger.info("程序启动")
    """
    # 确保日志目录存在
    os.makedirs(LOG_DIR, exist_ok=True)
    
    # 获取或创建 logger
    logger = logging.getLogger(name)
    
    # 如果已经配置过，直接返回
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # 创建 formatter
    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    
    # 创建文件处理器
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger


# 创建默认 logger
logger = setup_logger(__name__)


# ==========================
# 便捷日志函数
# ==========================
def debug(msg: str, *args, **kwargs):
    """记录 DEBUG 级别日志"""
    logger.debug(msg, *args, **kwargs)


def info(msg: str, *args, **kwargs):
    """记录 INFO 级别日志"""
    logger.info(msg, *args, **kwargs)


def warning(msg: str, *args, **kwargs):
    """记录 WARNING 级别日志"""
    logger.warning(msg, *args, **kwargs)


def error(msg: str, *args, **kwargs):
    """记录 ERROR 级别日志"""
    logger.error(msg, *args, **kwargs)


def critical(msg: str, *args, **kwargs):
    """记录 CRITICAL 级别日志"""
    logger.critical(msg, *args, **kwargs)


def exception(msg: str, *args, exc_info=True, **kwargs):
    """记录异常日志，包含堆栈信息"""
    logger.exception(msg, *args, exc_info=exc_info, **kwargs)


# ==========================
# 日志装饰器
# ==========================
def log_function_call(logger_obj: logging.Logger = None):
    """
    装饰器：记录函数调用信息
    
    自动记录函数的调用时间、参数、返回值和异常信息。
    
    Args:
        logger_obj: 日志记录器，默认使用模块级 logger
        
    Returns:
        装饰器函数
        
    Examples:
        @log_function_call()
        def my_function(a, b):
            return a + b
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            log = logger_obj or logger
            func_name = func.__name__
            
            # 记录函数调用
            log.info(f"▶️ 调用函数：{func_name}")
            log.debug(f"   参数：args={args}, kwargs={kwargs}")
            
            start_time = datetime.now()
            try:
                result = func(*args, **kwargs)
                elapsed = (datetime.now() - start_time).total_seconds()
                log.info(f"✅ {func_name} 执行成功 | 耗时：{elapsed:.3f}s")
                log.debug(f"   返回值：{result}")
                return result
            except Exception as e:
                elapsed = (datetime.now() - start_time).total_seconds()
                log.error(f"❌ {func_name} 执行失败 | 耗时：{elapsed:.3f}s | 错误：{e}")
                log.exception(f"   异常堆栈：")
                raise
        return wrapper
    return decorator


def log_enter_exit(logger_obj: logging.Logger = None, log_level: str = "INFO"):
    """
    装饰器：记录函数进入和退出
    
    在函数开始和结束时记录日志，适合追踪执行流程。
    
    Args:
        logger_obj: 日志记录器，默认使用模块级 logger
        log_level: 日志级别，可选 "DEBUG", "INFO", "WARNING", "ERROR"
        
    Returns:
        装饰器函数
        
    Examples:
        @log_enter_exit()
        def process_data(data):
            return data.strip()
    """
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR
    }
    log_level = level_map.get(log_level.upper(), logging.INFO)
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            log = logger_obj or logger
            
            # 记录进入函数
            log.log(log_level, f"⬇️  进入：{func.__name__}")
            
            try:
                result = func(*args, **kwargs)
                # 记录退出函数
                log.log(log_level, f"⬆️  退出：{func.__name__}")
                return result
            except Exception as e:
                log.log(log_level, f"⚠️  异常退出：{func.__name__} | {e}")
                raise
        return wrapper
    return decorator


# ==========================
# 日志工具函数
# ==========================
def get_log_file_path() -> str:
    """获取当前日志文件路径"""
    return LOG_FILE


def get_log_dir_path() -> str:
    """获取日志目录路径"""
    return LOG_DIR


def set_log_level(level: int):
    """
    动态设置日志级别
    
    Args:
        level: 日志级别，如 logging.DEBUG, logging.INFO 等
    """
    global LOG_LEVEL
    LOG_LEVEL = level
    for handler in logger.handlers:
        handler.setLevel(level)
    logger.setLevel(level)
    # 注意：此消息仅写入日志文件，不会在控制台显示
    info(f"日志级别已设置为：{logging.getLevelName(level)}")


def enable_debug_mode():
    """启用调试模式（DEBUG 级别日志）"""
    set_log_level(logging.DEBUG)


def enable_production_mode():
    """启用生产模式（WARNING 级别日志）"""
    set_log_level(logging.WARNING)


# ==========================
# 测试代码
# ==========================
if __name__ == "__main__":
    print("=" * 60)
    print("日志模块测试")
    print("=" * 60)
    
    # 测试各级别日志
    debug("这是一条 DEBUG 日志")
    info("这是一条 INFO 日志")
    warning("这是一条 WARNING 日志")
    error("这是一条 ERROR 日志")
    critical("这是一条 CRITICAL 日志")
    
    # 测试异常日志
    try:
        1 / 0
    except ZeroDivisionError:
        exception("发生除零异常")
    
    # 测试装饰器
    @log_function_call()
    def test_function(a, b):
        return a + b
    
    @log_enter_exit()
    def test_function2(data):
        return data.upper()
    
    print("\n" + "-" * 60)
    print("测试装饰器日志：\n")
    
    result1 = test_function(10, 20)
    print(f"test_function 结果：{result1}\n")
    
    result2 = test_function2("hello")
    print(f"test_function2 结果：{result2}\n")
    
    # 显示日志文件位置
    print("-" * 60)
    print(f"📁 日志文件路径：{get_log_file_path()}")
    print(f"📂 日志目录：{get_log_dir_path()}")
    print("=" * 60)
    print("✅ 日志模块测试完成")
