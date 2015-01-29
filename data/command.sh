#/bin/sh
./qrz_TC.py -l -f calls.dat | mpage -FCourier-Bold -o -t -m20l30t10r30b -L60 -W120 -1P -
./qrz_TC.py -r -f calls2.dat|grep -e call -e lat -e lon|grep -v -e p_call
