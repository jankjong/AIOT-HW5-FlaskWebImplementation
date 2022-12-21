# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

myserver ="localhost"
myuser="test123"
mypassword="test123"
mydb="aiotdb"

import pymysql.cursors
conn = pymysql.connect(host=myserver,user=myuser, passwd=mypassword, db=mydb)
c = conn.cursor()
            
c.execute('update sensors set status=1')
conn.commit()


######### cursor close, conn close
c.close()
conn.close()

