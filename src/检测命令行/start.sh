#!/bin/bash

SCRIPT="./run.py"    # 要执行的脚
echo "正在启动1个终端进程..."

# 使用gnome-terminal启动新终端运行test.sh
gnome-terminal --title="Process $SCRIPT" -- bash -c "python $SCRIPT; exec bash"
# 上面命令中，'exec bash' 是为了让终端在test.sh执行完毕后仍然保持打开状态，如果不需要可以去掉。
# 如果去掉，则变成： gnome-terminal --title="Process $i" -- bash -c "$SCRIPT"
echo "启动终端进程"
echo "所有终端进程已启动，launcher.sh 退出"