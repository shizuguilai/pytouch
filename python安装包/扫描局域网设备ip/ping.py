import sys
import subprocess

def ping_range(start_ip, end_ip, timeout=200):
    # 循环遍历指定范围的IP地址
    for i in range(start_ip, end_ip + 1):
        ip = f"192.168.88.{i}"

        # 执行ping命令
        command = ["ping", "-n", "1", "-w", str(timeout), ip]
        try:
            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"IP地址 {ip} 可以ping通=----------------------")
        except subprocess.CalledProcessError:
            print(f"IP地址 {ip} 无法ping通")



def main(start_ip,end_ip):
    # 设置起始和结束的IP地址
    # 执行ping操作，timeout默认为200毫秒
    ping_range(start_ip, end_ip, timeout=200)


#测试
#工能,把目录下的所有文件找出来并重命名
if __name__ == '__main__':
    args = sys.argv
    fpth = ''
    if len(args) == 3 :
        main(int(args[1]),int(args[2]))
    elif len(args) == 2:
        main(int(args[1]),254)
    else:
        print("没有ip开始参数的结束参数,将从1 ping到 254")
        main(1,254)
    
