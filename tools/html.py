#!/usr/bin/env python
#coding: utf-8
################################################################################
#
# Copyright (c) 2017 Baidu.com, Inc. All Rights Reserved
#
################################################################################
"""
This class is used to run remote command

Authors: guochaorong(guochaorong@baidu.com)
Date: 2018/07/11
"""

#from common import config
import time
from datetime import datetime, timedelta
#CONF = config.CommonConf()

class Html(object):
    """html"""
    def __init__(self, html_name_only="index.html"):
        self.html_name = html_name_only
        pass    

    def html_create_logs(self):
        """html create"""        
        f = open(self.html_name, 'w') 
        message = """ 
        <!DOCTYPE html> 
        <html> 
        <head> 
        </head> 
        <body> 
        <table border="1" align="center"> 
          <tr> 
           <th width="200px">timestamp</th> 
           <th>file no</th> 
           <th width="400px">class name</th> 
           <th width="200px">log type</th> 
           <th width="600px">log detail</th> 
          </tr> 
        </table> 
        </body> 
        </html> 
        """ 
        f.write(message) 
        f.close()

    def html_create(self, period):
        begin = (datetime.now() - timedelta(days=period)).strftime('%Y-%m-%d %H:%M:%S')
        dd_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        """html create"""        
        f = open(self.html_name, 'w') 
        message = """ 
        <!DOCTYPE html> 
        <html> 
        <head> 
        <font size="5"> 
        Report for PaddlePaddle CE tasks. </font>
        <br>
        <font size="3">
        %s ---- %s
        </font><br><br>
        </head> 
        <body> 
        <table border="1" align="center"> 
          <tr> 
           <th width="200px">models</th> 
           <th>result of model's kpis</th> 
           <th width="600px">msg</th> 
          </tr> 
        </table> 
        </body> 
        </html> 
        """ % (begin, dd_str)
        f.write(message) 
        f.close()

    def html_add_script(self):
        """html add script"""
        file = open(self.html_name, 'r')
        content = file.read()

        pos = content.find("</head>")
        if pos != -1:
            contentadd = """
        <script>
        </script>
        """
        content = content[:pos] + contentadd + content[pos:]
        file = open(self.html_name, "w")
        file.write(content)
        file.close()

    def html_add_logs(self, asctime, filenum, classname, logtype, info):
        """html add param"""
        file = open(self.html_name, 'r')
        content = file.read()
        contentadd = """<tr>
        <td>""" + asctime + """</td>
        <td>""" + filenum + """</td>
        <td>""" + classname + """</td>
        <td>""" + logtype + """</td>
        <td>""" + info + """</td>
        </tr> 
        """ 
        print (contentadd)
        pos = content.find("</table>")
        if pos != -1:
            content = content[:pos] + contentadd + content[pos:]
            file = open(self.html_name, "w")
            file.write(content)
            file.close()

    def html_add_param(self, case, result, log):
        """html add param"""
        file = open(self.html_name, 'r')
        content = file.read()
        contentadd = """<tr>
        <td>""" + case + """</td>
        <td>""" + str(result) + """</td>
        <td><a href="http://ce.paddlepaddle.org/commit/draw_scalar?task=%s">%s</a></td>
        </tr> 
        """ % (log, log)
        pos = content.find("</table>")
        if pos != -1:
            content = content[:pos] + contentadd + content[pos:]
            file = open(self.html_name, "w")
            file.write(content)
            file.close()

    def html_add_scene(self, scene="create and delete blb"):
        """html add scene"""
        file = open(self.html_name, 'r')
        content = file.read()
        contentadd = """<tr>
        <th colspan="3">scene name :""" + scene + """</th>
        </tr>
        """
        pos = content.find("</table>")
        if pos != -1:
            content = content[:pos] + contentadd + content[pos:]
            file = open(self.html_name, "w")
            file.write(content)
            file.close()

    def html_add_describe(self):
        """html add describe"""
        #region = CONF.get_conf("region", "sandbox")
        now = time.strftime('%y-%m-%d %H:%M:%S', time.localtime(time.time()))

        file = open(self.html_name, 'r')
        content = file.read()
        contentadd = """<tr>
        <th>region :""" + region + """</th>
        <th colspan="2">data :""" + now + """</th>
        </tr>
        """
        pos = content.find("</table>")
        if pos != -1:
            content = content[:pos] + contentadd + content[pos:]
            file = open(self.html_name, "w")
            file.write(content)
            file.close()

    def html_Statistics(self):
        """html atatistics"""
        ok_count = 0
        fail_count = 0
        with open(self.html_name, 'r') as f:
            alllines = f.readlines()
        for line in alllines:
            if 'OK' in line:
                ok_count += 1
            if 'Fail' in line:
                fail_count += 1
        if((ok_count + fail_count) != 0):
            count = float(ok_count) / (ok_count + fail_count)
        else:
            count = 0
        contentadd = """<tr>
        <th>ok_count:""" + str(ok_count) + """</th>
        <th>fail_count:""" + str(fail_count) + """</th>
        <th>percent:""" + str('%.3f' % count) + """</th>
        </tr>
        """
        file = open(self.html_name, 'r')
        content = file.read()
        pos = content.find("</table>")
        if pos != -1:
            content = content[:pos] + contentadd + content[pos:]
            file = open(self.html_name, "w")
            file.write(content)
            file.close() 

