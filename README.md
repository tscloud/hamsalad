hamsalad
========

Swiss army type utility for ham radio activities.  It basically does a bunch of things with a list of callsigns.  The callsigns can be gathered a few different ways: space seperated list at cmdline or file or via query to logging application.  Only cqrlog presently supported.  Data can be retrieved from this source via arbitrary query.

Started out needing a way to do better labels.  Found this excellent little Python program that fit the bill (thanks Martin, AA6E. Wanted to learn Python too, 73. http://www.aa6e.net/wiki/Qrz.py).  Changed it to handle the labels I had at the time.  Worked like charm.  Decided I wanted to learn a little more Python so I put some more functions in it.

What it does:
- Print adresses on 3x10 and 2x10 Avery labels

Call http://qrz.com service to get address information via callsign.  Output is piped to mpage.  See hamsalad help page for example.  This should work for just about anybody.  See man page for mpage if things need to be tweeked.
- Print QSO lists

I use cqrlog (thanks Petr, OK2CQR.  Great Linux logging prog, 73.  http://HamQTH.com/ok2cqr http://www.ok2cqr.com).   It'll print out QSOs for provided calls on the 2 label sizes or to stderr (stderr is a legecy from the origin label   code).
- ADIF file

Write an ADIF file to specified file name.  This file can posted to http://eQSL.cc.
- Raw output

Output to stderr results of http://qrz.com service call.
- Output call list to stderr

- Make map file

Make a KML file used by Google Earth or an html file for Google Maps.  Algorythm uses calls to 1) http://qrz.com and 2) http://hamqth.com, 3) log grid entries and 4) cty.dat file to determine the most accurate location.  The display of folders and icons can (almost) be arbitrarilly configured, e.g. QSOs grouped in folders per band or mode, colors of points based on QSL status, etc.

Would also like to thank Fabian Kurz, DJ1YFK and Jeff Laughlin, N1YWB for cty.dat file processing routines, Jerome Renard for distance and bearing routines, Yifei Jiang for Google Maps javascript generation routines and those previously mentioned.
