# server.py
from mcp.server.fastmcp import FastMCP
import sys
import logging
import touchUtil

logger = logging.getLogger('touchDevice')

# Fix UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stderr.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')

import math
import random

# Create an MCP server
mcp = FastMCP("touchDevice")

touchUtil.openSerial()

cmddict = {1:'x',2:'y',3:'z',4:'1',5:'2'}
# Add an addition tool
@mcp.tool()
def touchDevice(cmd: int) -> dict:
    """当要求滑动屏幕,或者操作手机时,使用这个工具来操作手机,cmd为操作指令,支持下边指令:\n1:向上滑动或者跳过广告\n2:向下滑动\n3:点赞或双击屏幕\n4:返回上一个界面\n5:关闭广告\n"""
    print('Touch device,cmd:',cmd)
    result = touchUtil.sendcmd(cmddict[cmd])
    logger.info(f"touchDevice formula: {cmd}, result: {result}")
    return {"success": True, "result": result}

# Start the server
if __name__ == "__main__":
    mcp.run(transport="stdio")
