#!/usr/local/bin/python3

import pymysql.cursors
import sys
import time

import login_details

def etl():

    # read file - lazy

    try:
        print("read total")
        total = float(open("/data/results.log",'r').read(12).strip())
        print("read total:",total)
    except Exception as e:
        print(e)
        sys.exit(1)

    try:
        print("read ftse100")
        ftse100 = float(open("/data/ftse100.log",'r').read(12).strip())
        print("read ftse100:",ftse100)
    except Exception as e:
        print(e)
        #sys.exit(1)
        ftse100 = -1

    try:
        print("read ftse250")
        ftse250 = float(open("/data/ftse250.log",'r').read(12).strip())
        print("read ftse250:",ftse250)
    except Exception as e:
        print(e)
        #sys.exit(1)
        ftse250 = -1

    pct=100

    now = time.strftime('%Y-%m-%d %H:%M:%S')

    print('iii:', now, total, ftse100, ftse250)

    try:
        db = pymysql.connect(host=login_details.mysqlHost, user=login_details.mysqlUser, password=login_details.mysqlPassword, db=login_details.dbName, 
            charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
        #print("MySQL Client Connected")
    except pymysql.Error as e:
        print(e)
        sys.exit()
    
    #my $query = "INSERT INTO iii (id,cdate,total,ftse100,ftse250,pct) VALUES (DEFAULT, \'$timestamp\', $total,$ftse,$ftse250,$pct )";

    with db.cursor() as cursor:
        try:
            sql = "INSERT INTO `iii` (`id`, `cdate`, `total`, `ftse100`, `ftse250`, `pct`) VALUES (DEFAULT, %s, %s, %s, %s, %s)"
            cursor.execute(sql, (now, total, ftse100, ftse250, pct))
        except pymysql.Error as e:
            print(e)
            sys.exit()
        finally:
            db.commit()

    db.close()

#
# main
#
etl()

print('iii update successful')
