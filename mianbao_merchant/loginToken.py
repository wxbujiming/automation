import requests
import re
import math
import time
import os
import threading
from config import *
from loging import *

# ==============================================
# 配置区
# ==============================================

LOOP_MINUTES = TOKEN_REFRESH_MINUTES  # 复用刷新间隔配置

# 当前平台标识（默认使用 merchant）
CURRENT_PLATFORM = "merchant"

def set_current_platform(platform_key):
    """
    设置当前要登录的平台
    
    Args:
        platform_key: 平台标识 (merchant/platform)
        
    Returns:
        bool: 设置是否成功
    """
    global CURRENT_PLATFORM
    if platform_key in PLATFORM_CONFIGS:
        old_platform = CURRENT_PLATFORM
        CURRENT_PLATFORM = platform_key
        config = get_current_config()
        logger.info(f"✅ 平台已切换：{PLATFORM_CONFIGS[old_platform]['name']} → {config['name']}")
        logger.info(f"   使用账号：{config['login_info']['account']}")
        return True
    else:
        logger.error(f"❌ 无效的平台标识：{platform_key}，可用平台：{list(PLATFORM_CONFIGS.keys())}")
        return False

def get_current_config():
    """获取当前平台的配置"""
    config = PLATFORM_CONFIGS.get(CURRENT_PLATFORM, PLATFORM_CONFIGS["merchant"])
    logger.debug(f"当前平台配置：{CURRENT_PLATFORM} | 账号：{config['login_info']['account']}")
    return config

def get_browser_headers():
    """动态获取当前平台的请求头"""
    config = get_current_config()
    base_url = config["base_url"]
    return {
        **BASE_HEADERS,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Origin": base_url,
        "Referer": f"{base_url}/",
    }

# ==============================================
# 1. 获取验证码 + uuid
# ==============================================
def get_captcha_info():
    config = get_current_config()
    url = f"{config['base_url']}/gateway/hucs-minivan/captcha/image"
    headers = get_browser_headers()
    logger.debug(f"请求验证码{url}, {headers}")
    try:
        response = requests.get(url, headers=headers, allow_redirects=True, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        res_json = response.json()
        uuid = res_json["data"]["uuid"]
        img_base64 = res_json["data"]["img"]
        base64_image = f"data:image/jpeg;base64,{img_base64}"
        logger.info(f"✅ 获取验证码成功 | UUID: {uuid}")
        return uuid, base64_image
    except Exception as e:
        logger.error(f"❌ 获取验证码失败：{e}")
        return None, None

# ==============================================
# 2. OCR 识别
# ==============================================
def ocr_recognize(base64_image):
    ocr_url = "https://api.ocr.space/parse/image"
    payload = {
        "apiKey": OCR_API_KEY,
        "base64Image": base64_image,
        "language": "eng",
        "scale": "true",
        "OCREngine": 2,
        "detectOrientation": "true"
    }
    logger.debug(f"OCR 请求：{ocr_url}, apiKey: {payload['apiKey']}, base64Image: {payload['base64Image']}")
    try:
        response = requests.post(ocr_url, data=payload, timeout=15)
        response.raise_for_status()
        logger.debug(response.json())
        return response.json()
    except Exception as e:
        logger.error(f"OCR 请求失败：{e}")
        return None

# ==============================================
# 3. 验证码处理
# ==============================================
def process_captcha_expr(ocr_text):
    if not ocr_text:
        return None

    logger.debug(f"识别到原始内容：{ocr_text}")
    expr = ocr_text.strip()
    expr = expr[:3]
    logger.debug(f"✅ 截断前 3 位后：{expr}")

    # ======================
    # 仅容错：S 替换成 5
    # ======================
    expr = expr.replace("S", "5")
    expr = expr.replace("s", "5")
    expr = expr.replace("~", "-")
    expr = expr.replace("——", "-")
    expr = expr.replace("_", "-")

    expr = re.sub(r'×|x|X', '*', expr)
    expr = re.sub(r'÷', '/', expr)
    expr = re.sub(r'=', '', expr)
    expr = re.sub(r'\s+', '', expr)
    expr = re.sub(r'[()]', '/', expr)
    expr = re.sub(r'[^0-9+\-*/]', '', expr)

    logger.info(f"专用清洗后表达式：{expr}")

    try:
        result = eval(expr)
        if isinstance(result, float):
            result = int(result) if result.is_integer() else math.floor(result)
        else:
            result = int(result)

        logger.info(f"✅ 计算结果：{result}")
        return result
    except Exception as e:
        logger.error(f"❌ 计算失败：{e}")
        return None

# ==============================================
# 4. 登录 + 保存 token（支持多平台）
# ==============================================
def login(uuid, code):
    """
    执行登录请求并保存 token
    
    Args:
        uuid: 验证码 UUID
        code: 验证码计算结果
        
    Returns:
        str | None: 登录成功返回 accessToken，失败返回 None
    """
    config = get_current_config()
    platform_name = config.get("name", CURRENT_PLATFORM)
    
    url = f"{config['base_url']}/gateway/hucs-minivan/system/auth/loginByUser"
    headers = get_browser_headers()
    payload = {
        "account": config["login_info"]["account"],
        "password": config["login_info"]["password"],
        "uuid": uuid,
        "code": str(code),
        "sysKey": config["login_info"]["sysKey"]
    }
    
    # 脱敏显示账号信息（仅显示前 3 位）
    account_display = config["login_info"]["account"][:3] + "***"
    logger.info(f"🔐 正在登录 [{platform_name}] | 账号：{account_display}")
    logger.debug(f"登录 URL: {url}")
    logger.debug(f"请求 Payload: {payload}")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
        res_json = response.json()
        logger.info(f"🔐 登录响应 | 状态码：{response.status_code}")
        logger.debug(f"响应数据：{res_json}")
        
        if res_json.get("code") == 200:
            access_token = res_json["data"].get("accessToken", "")
            if access_token:
                logger.info(f"✅ [{platform_name}] 登录成功！accessToken = {access_token[:20]}...")

                # 使用带平台标识的 token 文件路径
                platform_token_file = TOKEN_FILE.replace(".txt", f"_{CURRENT_PLATFORM}.txt")
                with open(platform_token_file, "w", encoding="utf-8") as f:
                    f.write(access_token)
                logger.info(f"✅ Token 已保存至：{platform_token_file}")

                os.environ["accessToken"] = access_token
                return access_token
            else:
                logger.error(f"❌ 登录成功但未获取到 accessToken: {res_json}")
                return None
        else:
            logger.error(f"❌ [{platform_name}] 登录失败 | 错误码：{res_json.get('code')} | 消息：{res_json.get('msg', '未知错误')}")
            return None

    except Exception as e:
        logger.error(f"❌ 登录请求异常：{type(e).__name__} - {e}", exc_info=True)
        return None

# ==============================================
# 单次执行
# ==============================================
def run_once():
    logger.info("=" * 60)
    logger.info(f"执行时间：{time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*60)

    uuid, base64_img = get_captcha_info()
    if not uuid or not base64_img:
        return

    ocr_res = ocr_recognize(base64_img)
    if not ocr_res or ocr_res.get("IsErroredOnProcessing"):
        logger.error("❌ OCR 识别失败")
        return

    parsed_results = ocr_res.get("ParsedResults", [])
    if not parsed_results:
        logger.warning("⚠️  无 OCR 识别内容")
        return
    ocr_text = parsed_results[0].get("ParsedText", "")

    captcha_result = process_captcha_expr(ocr_text)
    if captcha_result is None:
        logger.error("❌ 验证码计算失败")
        return None


    login(uuid, captcha_result)


# ==============================================
# 循环执行
# ==============================================
def run_loop():
    logger.info(f"🚀 自动任务启动：每 {LOOP_MINUTES} 分钟执行一次")
    while True:
        run_once()
        logger.info(f"⏳ 等待 {LOOP_MINUTES} 分钟后继续...")
        time.sleep(LOOP_MINUTES * 60)


# ==============================================
# Token 管理接口（供 main.py 调用）
# ==============================================

def get_latest_token():
    """
    读取最新 token
    
    从 TOKEN_FILE 中读取最新的 accessToken。
    
    Returns:
        str | None: 有效的 token 字符串，如果不存在或读取失败则返回 None
    """
    # 使用带平台标识的 token 文件路径
    platform_token_file = TOKEN_FILE.replace(".txt", f"_{CURRENT_PLATFORM}.txt")
    try:
        with open(platform_token_file, "r", encoding="utf-8") as f:
            token = f.read().strip()
            if token:
                return token
            else:
                logger.warning(f"⚠️  Token 文件为空：{platform_token_file}")
                return None
    except FileNotFoundError:
        logger.warning(f"⚠️  Token 文件不存在：{platform_token_file}")
        return None
    except Exception as e:
        logger.error(f"❌ 读取 token 失败：{type(e).__name__} - {e}", exc_info=True)
        return None


def start_token_refresh_thread():
    """
    启动后台 token 刷新线程
    
    创建并启动守护线程，用于自动刷新 token。
    
    Returns:
        threading.Thread: 启动的线程对象
    """
    thread = threading.Thread(
        target=run_loop,
        daemon=True,
        name="TokenRefreshThread"
    )
    thread.start()
    logger.info(f"✅ 后台 token 刷新线程已启动 (线程名：{thread.name})")
    return thread


def wait_for_valid_token(timeout=600, interval=30):
    """
    等待有效 token 生成
    
    带超时机制的等待函数，避免无限期阻塞。
    
    Args:
        timeout: 最大等待秒数，默认 300 秒（5 分钟）
        interval: 检查间隔秒数，默认 2 秒
    
    Returns:
        str: 有效的 token 字符串
    
    Raises:
        TimeoutError: 当等待超时时抛出异常
    """
    logger.info(f"⏳ 等待获取有效 token (超时时间：{timeout}秒)...")
    start_time = time.time()
    check_count = 0
    
    while time.time() - start_time < timeout:
        token = get_latest_token()
        check_count += 1
        
        if token:
            elapsed = time.time() - start_time
            logger.info(f"✅ 成功获取 token，耗时：{elapsed:.2f}秒，检查次数：{check_count}")
            return token
        
        time.sleep(interval)
    
    # 超时处理
    final_elapsed = time.time() - start_time
    logger.error(f"❌ 等待 token 超时 (耗时：{final_elapsed:.2f}秒，检查次数：{check_count})")
    raise TimeoutError(f"获取 token 超时 ({timeout}秒)")


def clear_old_token():
    """
    清除旧的 token 数据
    
    在第一次启动时清除 token 文件中上次执行的 token 数据，
    确保每次启动都是从全新的状态开始。
    """
    # 使用带平台标识的 token 文件路径
    platform_token_file = TOKEN_FILE.replace(".txt", f"_{CURRENT_PLATFORM}.txt")
    try:
        if os.path.exists(platform_token_file):
            with open(platform_token_file, "w", encoding="utf-8") as f:
                f.write("")  # 清空文件内容
            logger.info(f"✅ 已清除旧 token 数据：{platform_token_file}")
        else:
            logger.info(f"ℹ️  Token 文件不存在，无需清除：{platform_token_file}")
    except Exception as e:
        logger.warning(f"⚠️  清除 token 失败：{type(e).__name__} - {e}")




if __name__ == "__main__":
    import sys
    
    print("\n" + "=" * 60)
    print("LoginToken 模块 - 调试模式")
    print("=" * 60)
    
    # 提供调试选项
    print("\n请选择调试模式：")
    print("1. 运行完整登录循环（run_loop）")
    print("2. 测试 Token 管理接口（get_latest_token / start_token_refresh_thread / wait_for_valid_token）")
    print("3. 单次执行登录（run_once）")
    
    choice = input("\n请输入选项 (1/2/3): ").strip()
    
    if choice == "1":
        # 运行完整登录循环
        print("\n✅ 启动完整登录循环...")
        run_loop()
        
    elif choice == "2":
        # 测试 Token 管理接口
        print("\n✅ 开始测试 Token 管理接口...\n")
        
        # 测试 1: get_latest_token
        print("-" * 40)
        print("测试 1: get_latest_token() - 读取最新 token")
        print("-" * 40)
        token = get_latest_token()
        if token:
            print(f"✅ 成功读取 token: {token[:20]}... (长度：{len(token)})")
        else:
            print("⚠️  未找到有效 token")
        
        # 测试 2: start_token_refresh_thread + wait_for_valid_token
        print("\n" + "-" * 40)
        print("测试 2: start_token_refresh_thread() + wait_for_valid_token()")
        print("-" * 40)
        
        try:
            # 启动后台刷新线程
            thread = start_token_refresh_thread()
            
            # 等待有效 token 生成
            valid_token = wait_for_valid_token(timeout=60, interval=30)
            print(f"✅ 获取到有效 token: {valid_token[:20]}...")
            
            # 让线程运行一会儿，观察刷新效果
            print("\n⏳ 等待 10 秒观察后台刷新...")
            time.sleep(10)
            
            # 再次检查 token
            print("\n📌 再次检查最新 token:")
            latest = get_latest_token()
            if latest:
                print(f"✅ 最新 token: {latest[:20]}...")
            
        except TimeoutError as e:
            print(f"❌ 等待超时：{e}")
        except Exception as e:
            print(f"❌ 测试失败：{type(e).__name__} - {e}")
        
        print("\n✅ Token 管理接口测试完成")
        
    elif choice == "3":
        # 单次执行登录
        print("\n✅ 执行单次登录...")
        run_once()
        
    else:
        print("\n❌ 无效选项，程序退出")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("调试完成")
    print("=" * 60 + "\n")