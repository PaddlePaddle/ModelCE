array=(guochaorong@baidu.com)
#array=(guochaorong@baidu.com guochaorong123@163.com)
for mail in ${array[@]}
do
    cat index.html | formail -I "Content-type:text/html;charset=gb2312" -I "Subject: CE weekly report." -I "To:"$mail | /usr/sbin/sendmail -t guochaorong123@163.com
done
