CRAWLER_DIR=$(cd "$(dirname "$0")"; pwd)
XVFB=/usr/bin/Xvfb
if [ ! -x "$myPath"]
then 
    count=`ps -ef | grep Xvfb | grep -v "grep" | wc -l`
    echo $count
    if [ $count -eq 0 ]
    then
        Xvfb :2 -screen 0 640x480x16 -nolisten tcp &
    fi
fi

cd $CRAWLER_DIR
if [ $2 ]
then
    ps -ef|grep $1_$2.json|awk '{print$2}'|xargs -i kill -9 {}
else
    ps -ef|grep $1.json|awk '{print$2}'|xargs -i kill -9 {}
fi
if [ $2 ]
then
JSON_DIR=/tmp/$2
if [ ! -d "$JSON_DIR" ]
then
mkdir "$JSON_DIR"
fi
scrapy crawl $1 --set FEED_URI=$JSON_DIR/.$1_$2.json.tmp --set FEED_FORMAT=json
else
JSON_DIR=/tmp
scrapy crawl $1 --set FEED_URI=$JSON_DIR/.$1.json.tmp --set FEED_FORMAT=json
fi
if [ $2 ]
then
    /usr/bin/python $CRAWLER_DIR/check_json_file.py $JSON_DIR/.$1_$2.json.tmp $JSON_DIR/$1_$2.json
else
    /usr/bin/python $CRAWLER_DIR/check_json_file.py $JSON_DIR/.$1.json.tmp $JSON_DIR/$1.json
fi
