import sys, ConfigParser

config = ConfigParser.RawConfigParser()
config.read('.config_kml.cfg')

print 'Icons:'
print config.items('Icons')
print 'Folders:'
print config.items('Folders')
