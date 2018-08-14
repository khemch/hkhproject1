import requests
import csv
import MySQLdb
import json
import time
import pandas as pd
import numpy as np

db = MySQLdb.connect(host="localhost", user="root", passwd="root", db="hkhproject1")

cur = db.cursor()

# CSV Loop
i = 0
csvfile = open('books.csv', "r")
read = csv.reader(csvfile)
for row in read:
    while True:
        try:
            i += 1
            print(i)
            print(row[0])
            res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "gHWyultZ5tIMpAo6M0hQ", "isbns": "{}".format(row[0])})
            o = json.loads(res.text)

            books = o['books'][0]
            goodreadsid = books['id']
            isbn = books['isbn']
            isbn13 = books['isbn13']
            ratings_count = books['ratings_count']
            reviews_count = books['reviews_count']
            text_reviews_count = books['text_reviews_count']
            work_ratings_count = books['work_ratings_count']
            work_reviews_count = books['work_reviews_count']
            work_text_reviews_count = books['work_text_reviews_count']
            average_rating = books['average_rating']

            cur.execute('INSERT INTO goodreads(goodreadsid, isbn, isbn13, ratings_count, reviews_count, text_reviews_count, work_ratings_count, work_reviews_count, work_text_reviews_count, average_rating) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', [goodreadsid, isbn, isbn13, ratings_count, reviews_count, text_reviews_count, work_ratings_count, work_reviews_count, work_text_reviews_count, average_rating])
        except:
            print("Exception")
            time.sleep(3)
            pass
        break
#close the connection to the database.
# Commit to DB
db.commit()
db.close()
print("Done")
