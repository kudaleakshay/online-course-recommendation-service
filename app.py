from flask import Flask, render_template, request, redirect, url_for
from flaskext.mysql import MySQL
import pandas as pd
import yaml
import random
import re
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import sigmoid_kernel


app = Flask(__name__)

# Configure db
with open('db.yaml') as f:

    db = yaml.load(f, Loader=yaml.FullLoader)

app.config['MYSQL_DATABASE_HOST'] = db['mysql_host']
app.config['MYSQL_DATABASE_USER'] = db['mysql_user']
app.config['MYSQL_DATABASE_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DATABASE_DB'] = db['mysql_database']

db_table = db['mysql_table']
print(db_table)

header_list = ['course_id', 'course_title', 'Category_1', 'Category_2', 'url', 'num_reviews', 'is_paid',
               'price', 'num_subscribers', 'num_lectures', 'level', 'content_duration', 'published_timestamp', 'rating']

mysql = MySQL(app)
mysql.init_app(app)
course_df = ''


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/', methods=['POST'])
def recommend_courses():
    input_details = request.form
    input_name = input_details['Name'].strip()

    conn = mysql.connect()
    cur = conn.cursor()

    sql_get_match_courses = f'select * from {db_table} where course_title = \'{input_name}\' OR course_title LIKE \'% {input_name}\' OR course_title LIKE \'{input_name} %\' OR course_title LIKE \'% {input_name} %\''

    match_courses = cur.execute(sql_get_match_courses)
    if match_courses > 0:
        dataset = cur.fetchall()
        cur.close()

        match_categories = []
        for var in dataset:
            match_categories.append(dataset[dataset.index(var)][3].strip())

        print("Most frequent: ")
        print(most_frequent(match_categories))

        global course_df
        course_df = pd.DataFrame(dataset, columns=header_list)
        course_df = course_df.drop_duplicates()

        category = most_frequent(match_categories)
        match_categories = list(set(match_categories))
        match_categories.remove(category)

        match_courses_data = get_match_courses()

        similar_courses = ''

        try:
            similar_courses = get_categorywise_similar_courses(category)
        except:
            print("Oops! Error occurred.")

        return render_template('home.html', title=input_name.upper(), match_courses_data=match_courses_data,
                               similar_courses=similar_courses, categories=match_categories
                               )

    else:
        return render_template('home.html')


@app.route('/category', methods=['POST'])
def recommend_categorywise_courses():
    input_details = request.form
    input_category = input_details['Category'].strip()

    conn = mysql.connect()
    cur = conn.cursor()

    sql_get_match_courses = f'select * from {db_table} where Category_1 like \'%{input_category}%\' or Category_2 like \'%{input_category}%\' ORDER BY RAND()'

    match_courses = cur.execute(sql_get_match_courses)
    if match_courses > 0:
        dataset = cur.fetchall()
        cur.close()

        global course_df
        course_df = pd.DataFrame(dataset, columns=header_list)
        course_df = course_df.drop_duplicates()

        category = input_category

        match_courses_data = get_match_courses()
        similar_courses = ''

        return render_template('home.html', title=category.upper(), match_courses_data=match_courses_data,
                               similar_courses=similar_courses
                               )

    else:
        return render_template('home.html')


def most_frequent(List):
    # return max(set(List), key=List.count)
    occurence_count = Counter(List)
    return occurence_count.most_common(1)[0][0]


def get_categorywise_similar_courses(category):
    conn = mysql.connect()
    cur = conn.cursor()

    global course_df
    sql_get_match_categories = f'select * from {db_table} where Category_1 = \'%{category}%\' or Category_2 like \'%{category}%\''

    match_courses = cur.execute(sql_get_match_categories)
    if match_courses > 0:
        category_dataset = cur.fetchall()
        cur.close()

        category_df = pd.DataFrame(category_dataset, columns=header_list)
        category_df = category_df.drop_duplicates()

        category_df = pd.concat([category_df,
                                 course_df]).drop_duplicates(keep=False)

        category_df = category_df.head(40)
        return [tuple(course) for course in category_df.values]


def get_match_courses():
    global course_df
    selected_course_df = course_df.sort_values(
        'rating', ascending=False).head(20)
    course_df = pd.concat([course_df,
                           selected_course_df]).drop_duplicates(keep=False)

    return [tuple(course) for course in selected_course_df.values]


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=True)
