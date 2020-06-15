from flask import Flask, render_template, request, redirect, url_for
from flaskext.mysql import MySQL
import pandas as pd
import yaml
import random


app = Flask(__name__)

# Configure db
with open('db.yaml') as f:
    
    db = yaml.load(f, Loader=yaml.FullLoader)

app.config['MYSQL_DATABASE_HOST'] = db['mysql_host']
app.config['MYSQL_DATABASE_USER'] = db['mysql_user']
app.config['MYSQL_DATABASE_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DATABASE_DB'] = db['mysql_database']

header_list = ['course_id', 'course_title', 'url', 'is_paid','price', 'num_subscribers', 'num_reviews', 'num_lectures','level', 'content_duration', 'published_timestamp','subject','rating']

mysql = MySQL(app)
mysql.init_app(app)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/', methods=['POST'])
def recommend():
    input_details = request.form

    conn = mysql.connect()
    cur = conn.cursor()

    sql_fetch_query = "select * from datasets_udemy_courses where course_title REGEXP \'" + input_details['Name']  + "\'"
    sql_secondary_query = "select * from datasets_udemy_courses where is_paid = 'True' ORDER BY num_lectures DESC"
    
    result_value = cur.execute(sql_fetch_query)
    if result_value > 0:
        result_details = cur.fetchall()
        cur.close()
        offset = 0
    else:
        cur.execute(sql_secondary_query)
        result_details = cur.fetchall()
        cur.close()
        offset = random.randint(0,4)
    return render_template('home.html', course_details = prediction(result_details, header_list, input_details, offset))
    

def prediction(course_details, headers_list, input_details, offset):
    course_is_paid = input_details['Price']
    course_level = input_details.getlist('Level')
    course_duration = input_details.getlist('Duration')
    
    df = pd.DataFrame(course_details, columns = headers_list)
    df['score'] = 0 

    for ind in df.index: 
        score = 0

        if course_is_paid:
            if df['is_paid'][ind] == course_is_paid:
                score +=1

        if df['rating'][ind] > 4:
                    score+=1
                    
        if course_level:
            for level in course_level:
                if df['level'][ind] == level: 
                    print(level)
                    score +=1

        if course_duration:
            for duration in course_duration:
                lower, upper = duration.split('-')
                if df['content_duration'][ind] > int(lower) and df['content_duration'][ind] < int(upper):
                    print(duration)
                    score += 1
                
        df['score'][ind] = score
 
    df1 = df.sort_values('score',ascending = False).iloc[offset:10]
    records = df1.to_records(index=False)
    result = tuple(records)
    return result


if __name__ == '__main__':
    app.run(debug=True)
