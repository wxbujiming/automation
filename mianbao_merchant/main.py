"""
主程序入口模块

负责调用 loginToken 模块的 token 管理接口，执行后续业务逻辑。
支持多平台自动遍历测试。
"""

import sys
import os
import time
import requests
import json
from datetime import datetime
import loginToken
from config import *
import excel_read
from loging import setup_logger
from report_generator import generate_html_report

# 初始化日志记录器
logger = setup_logger(__name__)


def print_startup_info():
    """打印程序启动信息"""
    separator = "=" * 60
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    logger.info(separator)
    logger.info(f"程序启动时间：{current_time}")
    logger.info(f"配置信息：刷新间隔={TOKEN_REFRESH_MINUTES}分钟")
    logger.info(separator)


def _get_nested_value(data, key_path):
    """
    从嵌套的 JSON 数据中获取值
    
    支持点分隔的路径，如 "data.user.name"
    
    Args:
        data: JSON 数据（dict 或 list）
        key_path: 键路径，用点分隔，如 "data.user.name"
        
    Returns:
        找到的值，如果路径不存在则返回 None
    """
    if not data or not key_path:
        return None
    
    keys = key_path.split('.')
    current = data
    
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
        elif isinstance(current, list):
            try:
                index = int(key)
                current = current[index] if 0 <= index < len(current) else None
            except (ValueError, IndexError):
                return None
        else:
            return None
        
        if current is None:
            return None
    
    return current


def _validate_assertion(response_data, assertion):
    """
    验证响应数据是否符合断言
    
    Args:
        response_data: API 响应的 JSON 数据
        assertion: 断言字典，键为 JSONPath（点分隔），值为期望值
        
    Returns:
        tuple: (是否通过，错误信息列表)
    """
    errors = []
    
    if not assertion:
        return True, []
    
    for key_path, expected_value in assertion.items():
        actual_value = _get_nested_value(response_data, key_path)
        
        if actual_value is None and expected_value is not None:
            error_msg = f"字段 '{key_path}' 不存在或未返回"
            errors.append(error_msg)
            logger.warning(f"⚠️  {error_msg}")
        elif actual_value != expected_value:
            error_msg = f"字段 '{key_path}' 断言失败：期望={expected_value}, 实际={actual_value}"
            errors.append(error_msg)
            logger.warning(f"⚠️  {error_msg}")
    
    return len(errors) == 0, errors


def run_business_logic(token, api_list):
    """
    执行业务逻辑：循环请求 Excel 中的 API 接口
    
    遍历 API 列表，使用 token 对每个接口发送请求并输出结果。
    
    Args:
        token: 认证 token
        api_list: API 接口信息列表（来自 excel_read.read_excel_api_list）
        
    Returns:
        list: 测试结果列表，用于生成报告
    """
    if not token:
        logger.error("❌ Token 为空，无法执行接口请求")
        return []
    
    if not api_list:
        logger.warning("⚠️  API 列表为空，无需执行请求")
        return []
    
    # 获取当前平台标识
    platform_key = loginToken.CURRENT_PLATFORM
    platform_name = PLATFORM_CONFIGS.get(platform_key, {}).get("name", platform_key)
    
    logger.info(f"\n✅ 开始执行接口测试 [{platform_name}]，共 {len(api_list)} 个接口...")
    logger.info("=" * 60)
    
    # 从 PLATFORM_CONFIGS 中获取当前平台的 base_url
    base_url = PLATFORM_CONFIGS.get(platform_key, {}).get("base_url", "http://localhost:8080")
    
    success_count = 0
    fail_count = 0
    test_results = []  # 收集测试结果用于生成报告
    
    for index, api in enumerate(api_list, 1):
        api_name = api.get('api_name', '未知接口')
        method = (api.get('method', 'GET') or 'GET').upper()
        path = api.get('path', '')
        params = api.get('params', {})
        headers = api.get('headers', {})
        body = api.get('body')
        group = api.get('group', platform_key)  # 获取分组信息（Sheet 名称）
        
        # 拼接完整 URL
        if path.startswith('http'):
            url = path
        else:
            url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
        
        # 添加 Authorization 的 token 赋值
        headers['Authorization'] = f'Bearer {token}'
        
        logger.info(f"  [{index}/{len(api_list)}] {api_name}")
        logger.info(f"    请求：{method} {url}")
        logger.debug(f"    Params: {params}")
        logger.debug(f"    Body: {body}")
        logger.debug(f"    Headers: {headers}")
        
        start_time = time.time()
        assertion = api.get('assertion')
        status = "pass"
        error_message = None
        response_data = None
        
        try:
            logger.debug("发送 HTTP 请求...")
            response = requests.request(
                method=method,
                url=url,
                params=params if params else None,
                json=body if body else None,
                headers=headers,
                timeout=30
            )
            
            status_code = response.status_code
            
            try:
                response_data = response.json()
                logger.debug(f"响应数据：{str(response_data)[:200]}...")
            except (json.JSONDecodeError, ValueError):
                response_data = None
                logger.debug("响应不是 JSON 格式")
            
            if assertion:
                passed, errors = _validate_assertion(response_data, assertion)
                if passed:
                    logger.info(f"    ✅ 状态码：{status_code} | 断言验证通过")
                    success_count += 1
                else:
                    logger.error(f"    ❌ 状态码：{status_code} | 断言验证失败")
                    for err in errors:
                        logger.error(f"       - {err}")
                    fail_count += 1
                    status = "fail"
                    error_message = "; ".join(errors)
            else:
                # 无断言配置，仅检查状态码
                if 200 <= status_code < 300:
                    logger.info(f"    ✅ 状态码：{status_code}")
                    success_count += 1
                else:
                    logger.warning(f"    ⚠️  状态码：{status_code}")
                    logger.debug(f"    响应：{response.text[:200]}")
                    fail_count += 1
                    status = "fail"
                    error_message = f"HTTP {status_code}"
                
        except requests.exceptions.Timeout:
            logger.error(f"    ❌ 请求超时（>30 秒）")
            fail_count += 1
            status = "fail"
            error_message = "请求超时"
        except requests.exceptions.ConnectionError as e:
            logger.error(f"    ❌ 连接失败：{str(e)[:100]}")
            fail_count += 1
            status = "fail"
            error_message = f"连接失败：{str(e)[:50]}"
        except Exception as e:
            logger.error(f"    ❌ 请求异常：{type(e).__name__} - {str(e)[:100]}")
            fail_count += 1
            status = "fail"
            error_message = f"{type(e).__name__}: {str(e)[:50]}"
        
        elapsed_time = time.time() - start_time
        
        # 收集测试结果
        test_result = {
            "api_name": api_name,
            "method": method,
            "url": url,
            "status_code": status_code if 'status_code' in locals() else None,
            "status": status,
            "success": status == "pass",  # 添加 success 字段供报告生成器使用
            "error_message": error_message,
            "duration": round(elapsed_time * 1000, 2),  # 转换为毫秒，字段名与 report_generator.py 保持一致
            "request_params": params,
            "request_body": body,
            "response_data": response_data,
            "assertion": assertion,
            "group": group
        }
        test_results.append(test_result)
        
        time.sleep(0.5)
    
    logger.info("\n" + "=" * 60)
    logger.info(f"📊 [{platform_name}] 测试完成统计：")
    logger.info(f"    总接口数：{len(api_list)}")
    logger.info(f"    ✅ 成功：{success_count}")
    logger.info(f"    ❌ 失败：{fail_count}")
    logger.info(f"    通过率：{success_count / len(api_list) * 100:.1f}%" if api_list else "    通过率：N/A")
    logger.info("=" * 60)
    
    return test_results


def cleanup():
    """程序退出前的清理工作"""
    logger.info("\n🧹 执行程序清理工作...")
    logger.info("✅ 清理工作完成")


def main(api_dict):
    """
    主程序入口函数（多平台支持）
    
    执行流程：
    1. 打印启动信息
    2. 遍历所有平台
    3. 对每个平台：清除旧 token -> 切换平台 -> 登录 -> 执行接口测试
    4. 汇总所有平台的测试结果
    5. 生成 HTML 测试报告
    
    Args:
        api_dict: dict, key 为平台标识 (merchant/platform)，value 为对应的 API 列表
    """
    # 记录脚本开始执行时间
    script_start_time = time.time()
    
    # 1. 打印启动信息
    print_startup_info()
    
    all_test_results = []  # 收集所有平台的测试结果
    platform_stats = {}  # 记录每个平台的统计信息
    
    # 2. 遍历所有平台
    for platform_key, api_list in api_dict.items():
        if not api_list:
            logger.warning(f"⚠️  平台 '{platform_key}' 无接口数据，跳过")
            continue
        
        logger.info(f"\n{'='*60}")
        logger.info(f"🚀 开始处理平台：{platform_key}")
        logger.info(f"{'='*60}")
        
        # 切换平台并清除旧 token
        loginToken.set_current_platform(platform_key)
        loginToken.clear_old_token()
        
        # 启动该平台的 token 刷新线程
        refresh_thread = loginToken.start_token_refresh_thread()
        
        # 等待 token 生成
        try:
            token = loginToken.wait_for_valid_token(timeout=600, interval=30)
        except TimeoutError as e:
            logger.error(f"❌ [{platform_key}] 平台登录失败：{e}")
            platform_stats[platform_key] = {"status": "failed", "error": str(e)}
            continue
        
        logger.info(f"\n✅ [{platform_key}] 平台登录成功！")
        logger.info(f"📝 Token 内容：{token[:20]}... (长度：{len(token)})")
        
        # 执行该平台的接口测试
        test_results = run_business_logic(token, api_list)
        all_test_results.extend(test_results)
        
        # 记录平台统计
        success_count = sum(1 for r in test_results if r["status"] == "pass")
        platform_stats[platform_key] = {
            "total": len(test_results),
            "success": success_count,
            "fail": len(test_results) - success_count,
            "status": "completed"
        }
        
        # 清理工作
        cleanup()
    
    # 3. 生成汇总报告
    if all_test_results:
        # 计算脚本总执行时长（秒）
        script_total_duration = time.time() - script_start_time
        
        # 从 config 读取报告配置并生成路径
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = REPORT_FILENAME_TEMPLATE.replace('{timestamp}', timestamp)
        report_path = os.path.join(REPORT_DIR, report_filename)
        
        # 确保报告目录存在
        os.makedirs(REPORT_DIR, exist_ok=True)
        
        generate_html_report(all_test_results, report_path, script_duration=script_total_duration)
        logger.info(f"\n📄 测试报告已生成：{report_path}")
        
        # 打印总体统计（包含脚本执行时长）
        logger.info("\n" + "=" * 60)
        logger.info("📊 总体测试统计：")
        total_all = len(all_test_results)
        success_all = sum(1 for r in all_test_results if r["status"] == "pass")
        fail_all = total_all - success_all
        logger.info(f"    总接口数：{total_all}")
        logger.info(f"    ✅ 成功：{success_all}")
        logger.info(f"    ❌ 失败：{fail_all}")
        logger.info(f"    通过率：{success_all / total_all * 100:.1f}%" if total_all > 0 else "    通过率：N/A")
        logger.info(f"    ⏱ 脚本总耗时：{script_total_duration:.2f}s ({script_total_duration / 60:.2f}分钟)")
        logger.info("")
        logger.info("📋 分平台统计：")
        for platform, stats in platform_stats.items():
            if stats["status"] == "completed":
                logger.info(f"    {platform}: 总计{stats['total']} | 成功{stats['success']} | 失败{stats['fail']}")
            else:
                logger.info(f"    {platform}: ❌ 失败 - {stats.get('error', '未知错误')}")
        logger.info("=" * 60)
    else:
        logger.warning("⚠️  未生成任何测试结果，跳过报告生成")


if __name__ == "__main__":
    logger.info("📖 正在读取 Excel 配置文件（所有 Sheet 页）...")
    api_dict = excel_read.read_excel_api_list(EXCEL_PATH)
    
    if not api_dict:
        logger.error("❌ 未读取到任何接口数据，程序退出。")
        sys.exit(1)
    
    logger.info(f"✅ 成功加载 {len(api_dict)} 个平台的接口配置\\n")
    
    try:
        main(api_dict)
    except SystemExit:
        pass
    except Exception as e:
        logger.error(f"\n❌ 程序异常终止：{type(e).__name__} - {e}", exc_info=True)
        sys.exit(1)
