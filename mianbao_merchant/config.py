# ==========================
# 【统一配置文件】所有可修改内容都在这里
# ==========================


# --------------------------
# 1. 基础服务配置
# --------------------------

REQUEST_TIMEOUT = 20  # 接口超时时间（秒）



# --------------------------
# 2 平台配置映射表（多平台支持）
# --------------------------
PLATFORM_CONFIGS = {
    "merchant": {
        "name": "运营平台",
        "base_url": "https://tminivan-merchant.huianrong.com",
        "login_info": {
            "account": "72538629",
            "password": "qgcTMg3JWscFy/eQiibizpgZh0BJnofgd/+KKZShJqYHeR+S+LFhN5NP4syR3CWXCxrZiAaq5onaklrXR1s6YTz07+eKoCBG1WCKgbQmHg6CcymzEEQSI+xVUQ0wXPJfjaqMDeut6gWN8C4/Sg4Tja+w6KyCBxh6+/LgaFWHqxw=",
            "sysKey": "merchant"
        }
    },
    "platform": {
        "name": "管理平台",
        "base_url": "https://tminivan-platform.huianrong.com",
        "login_info": {
            "account": "17381912550",
            "password": "IgUxWYxXQDSDco9I+Bn/D5Pkbzstj3Qg0Kb7Pu/B68kS0+AQT725Gej8Q1N2L6JhR49CEVRCZm2SrDYCIEGjfspdRD2JxvbksxBsWYDzjxzD4MCwTIF6/GBhKsD6tnFtiNulZEjbl5gkLThDLBdMnavnZMIGDcD2ESJmc0d000E=",
            "sysKey": "platform"
        }
    },
    "supplier": {
        "name": "供应商平台",
        "base_url": "https://tminivan-supplier.huianrong.com",
        "login_info": {
        "account": "48574231",
        "password": "ARoEDJdolvQHStTI/OlAkfZIddQldWyZT0oX1nZLWB9cPO1u4Uxtv1vv9NGmKZKxPTNZP1WC/bZpMy/3XxxeDjKTDj/u3O6xNcU12P/6rD/TG9/8rU0O2ygVF0TXB+QdSE/asE8QqCWfCF9r6p6JvK/mf+xssi2xIIdrhTFBp40=",
        "sysKey": "supplier"
        }
    }
}

# --------------------------
# 3. Token 刷新配置
# --------------------------
TOKEN_REFRESH_MINUTES = 1  # 2分钟刷新一次
TOKEN_FILE = "D:\\python\\mianbao\\mianbao_merchant\\token.txt"
CHECK_TOKEN_INTERVAL = 60  # Token 检查间隔（秒）


# --------------------------
# 4. OCR 配置
# --------------------------
OCR_API_KEY = "helloworld"

# --------------------------
# 5. 请求头公共配置
# --------------------------
BASE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Content-Type": "application/json;charset=UTF-8"
}

# --------------------------
# 6. excel接口文件路径配置
# --------------------------
EXCEL_PATH=f"D:\python\mianbao\mianbao.xlsx"


# --------------------------
# 7. 日志文件存储路径配置
# --------------------------
LOG_DIR = "D:\\python\\mianbao\\logs"  # 日志存储目录（绝对路径）


# --------------------------
# 8. 测试报告配置
# --------------------------
REPORT_DIR = "D:\\python\\mianbao\\reports"  # 报告存储目录（绝对路径）
REPORT_FILENAME_TEMPLATE = "Rreport_{timestamp}.html"  # 报告文件名模板，{timestamp}会被替换为时间戳


# --------------------------
# 9.
# --------------------------