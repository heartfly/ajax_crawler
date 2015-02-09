#encoding=utf8
import sys
import json
import os

print sys.argv
try:
    tmp_json_file = open(sys.argv[1])
    json_data = json.load(tmp_json_file)
    tmp_json_file.close()
    json_file = open(sys.argv[2], 'wb')
    json_file.write(open(sys.argv[1], 'rb', 1).read())
    json_file.close()
    print 'well done!'
except Exception,e:
    print e
    print 'error in load tmp json'

os.remove(sys.argv[1])
