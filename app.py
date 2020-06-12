from flask import Flask, render_template, request, redirect, url_for
from flask_mysqldb import MySQL
import yaml


app = Flask(__name__)

# Configure db
with open('db.yaml') as f:
    
    db = yaml.load(f, Loader=yaml.FullLoader)

app.config['MYSQL_HOST'] = db['mysql_host']
app.config['MYSQL_USER'] = db['mysql_user']
app.config['MYSQL_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DB'] = db['mysql_database']


mysql = MySQL(app)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/', methods=['POST'])
def recommend():
    course_details = request.form
    filter_sub_query = get_filter_sub_query(course_details)

    cur = mysql.connection.cursor()

    sql_fetch_query = "select * from datasets_udemy_courses where course_title REGEXP \'"+course_details['Name']+"\' and "+filter_sub_query

    print(course_details['Name'])
    print(sql_fetch_query)

    result_value = cur.execute(sql_fetch_query)
    if result_value > 0:
        course_details = cur.fetchall()
        cur.close()
        return render_template('home.html', course_details = course_details)
    


    return 'No data found'


def get_filter_sub_query(course_details):
    course_price = course_details['Price']
    course_level = course_details.getlist('Level')
    course_duration = course_details.getlist('Duration')

    filter_sub_query = ' and '

    filters_list=[]

    if course_price is not None: 
       filters_list.append(get_price_type_sub_query(course_price))
        
    if course_level is not None: 
        if len(course_level) > 0:
            filters_list.append(get_level_sub_query(course_level))

    if course_duration is not None: 
        if len(course_duration) > 0:
            filters_list.append(get_duration_sub_query(course_duration))

    filter_sub_query = filter_sub_query.join(filters_list)
        
    print(filter_sub_query)

    return filter_sub_query

def get_price_type_sub_query(course_price):
        if course_price == 'Paid':
            sub_query= "is_paid = \'True\'"
        else:
            sub_query= "is_paid = \'False\'"

        return sub_query

def get_level_sub_query(course_level):
        sub_query= "level in ("

        length = len(course_level) 
        
        i = 0

        while i < length: 
            if i< length-1:
                 sub_query += "\'"+course_level[i]+"\',"
            else:
                sub_query += "\'"+course_level[i]+"\')"
            i += 1

        return sub_query

def get_duration_sub_query(course_duration):
        sub_query= "("

        length = len(course_duration) 
        i = 0

        while i < length: 
            if i< length-1:
                sub_query += "content_duration "+course_duration[i]+" or "
            else:
                sub_query += "content_duration "+course_duration[i]+")"
            i += 1

        return sub_query        


if __name__ == '__main__':
    app.run(debug=True)
