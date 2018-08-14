import csv
import MySQLdb

# Config MySQL

db = MySQLdb.connect(host="localhost", user="root", passwd="root", db="hkhproject1")

cur = db.cursor()

# CSV
csvfile = open('books.csv', "r")
read = csv.reader(csvfile)
for row in read:
    cur.execute('INSERT INTO books(isbn, title, author, year ) VALUES(%s, %s, %s, %s)', [row[0], row[1], row[2], row[3]])

# Commit to DB
db.commit()
db.close()
print("Done")
