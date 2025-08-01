from datetime import timezone, timedelta, datetime


def get_china_time():
    # 定义中国时区 UTC+8
    china_tz = timezone(timedelta(hours=8))
    # 获取当前UTC时间，转换为中国时间
    now_china = datetime.now(china_tz)
    # 格式化时间：年月日 时分秒
    return now_china.strftime("%Y-%m-%d %H:%M:%S")