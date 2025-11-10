pip install esptool==3.3 -i https://pypi.tuna.tsinghua.edu.cn/simple

cd /d %~dp0

esptool -b 115200  erase_flash || esptool.py -b 115200  erase_flash
esptool --chip esp8266 --baud 115200 write_flash --flash_size=detect 0 1_22_2-20251110.bin || esptool.py --chip esp8266 --baud 115200 write_flash --flash_size=detect 0 1_22_2-20251110.bin

esptool run || esptool.py run

pause
