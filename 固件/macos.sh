export PATH=/usr/local/bin/:$PATH
CUR_PATH=`pwd`
basepath=$(cd `dirname $0`; pwd)
echo $CUR_PATH
echo $basepath

cd $basepath

esptool.py -b 115200  erase_flash
esptool.py --chip esp8266 --baud 115200 write_flash --flash_size=detect 0 1_22_2-20251028.bin

esptool.py run
