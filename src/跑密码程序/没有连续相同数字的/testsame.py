#power by fengmm521.taobao.com
#wechat:woodmage

def saveStr2File(ks,pth):
    outstr = ''
    for i,v in enumerate(ks):
        outstr += v + '\n'
    with open(pth,'w') as f:
        f.write(outstr)

sameKeys = []
nosameKeys = []
#把一个数字转换成指字长度的字符串,长度不够时前边补0
def conventNumber2String(n,numlenth):
    tmpstr = str(n)
    lth = len(tmpstr)
    tmpstr = (numlenth-lth)*'0' + tmpstr
    return tmpstr
#检查是否有连续相同数字出现
def chickSameKey(strnum):
    slen = len(strnum)
    for i in range(slen-1):
        if strnum[i] == strnum[i+1]:
            return True
#发送对应数字的输入,默认密码长度为6位
def sendNumber(n,numlenth = 4):
    strn = conventNumber2String(n,numlenth)
    print(strn)
    if chickSameKey(strn):
        sameKeys.append(strn)
    else:
        nosameKeys.append(strn)

#主函数,点击器程序从这里开始运行
def main():
    for i in range(0,10000):
        sendNumber(i)        #发送对数的密码数字
    saveStr2File(sameKeys,'samekey.txt')
    saveStr2File(nosameKeys,'nosamekey.txt')

if __name__ == '__main__':  
    main()
    