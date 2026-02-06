import requests
import json

def send_bemfa_message(uid, topic, msg, msg_type=3, wemsg=None, share=False):
    """
    向巴法云发送消息
    
    参数:
    uid: 用户私钥
    topic: 主题名称
    msg: 消息内容
    msg_type: 主题类型，默认3(TCP协议)
    wemsg: 微信推送消息（可选）
    share: 是否为分享设备，默认False
    """
    
    # API地址
    url = "https://apis.bemfa.com/va/postJsonMsg"
    
    # 请求头
    headers = {
        "Content-Type": "application/json; charset=utf-8"
    }
    
    # 请求数据
    data = {
        "uid": uid,
        "topic": topic,
        "type": msg_type,
        "msg": msg
    }
    
    # 可选参数
    if wemsg is not None:
        data["wemsg"] = wemsg
    
    if share:
        data["share"] = share
    
    try:
        # 发送POST请求
        response = requests.post(url, headers=headers, data=json.dumps(data))
        
        # 检查响应状态
        response.raise_for_status()
        
        # 解析响应
        result = response.json()
        
        # 状态码说明
        status_codes = {
            0: "成功",
            10002: "请求参数有误",
            40000: "未知错误",
            40004: "私钥或主题错误"
        }
        
        # 输出结果
        print("请求状态:", response.status_code)
        print("响应内容:", result)
        
        if "code" in result:
            code = result["code"]
            message = result.get("message", "无消息")
            print(f"业务状态码: {code} - {status_codes.get(code, '未知状态码')}")
            print(f"消息: {message}")
            
            if code == 0:
                print("消息发送成功！")
            else:
                print(f"消息发送失败: {message}")
        
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"请求发生错误: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
        return None

# 使用示例
if __name__ == "__main__":
    # 请替换为您的实际参数
    YOUR_UID = "14712ccdbc88a59817d77c64ca2e4c33"  # 您的用户私钥
    YOUR_TOPIC = "fengmm521"  # 您的主题名称
    YOUR_MESSAGE = "测试消息"  # 要发送的消息
    
    # 示例1：基本使用
    print("示例1：发送基本消息")
    result = send_bemfa_message(
        uid=YOUR_UID,
        topic=YOUR_TOPIC,
        msg=YOUR_MESSAGE
    )
    
    # print("\n" + "="*50 + "\n")
    
    # 示例2：发送带有微信推送的消息
    # print("示例2：发送带有微信推送的消息")
    # result = send_bemfa_message(
    #     uid=YOUR_UID,
    #     topic=YOUR_TOPIC,
    #     msg=YOUR_MESSAGE,
    #     wemsg="设备状态已更新：灯已打开"  # 微信推送消息
    # )