from flask import Flask, render_template, request, redirect, url_for
from flaskext.mysql import MySQL
import pandas as pd
import yaml
import random
import re
from collections import Counter


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
               'price', 'num_subscribers', 'num_lectures', 'level', 'content_duration', 'published_timestamp', 'rating', 'language', 'is_subtitle']

# header_list = ['course_id', 'course_title', 'Category_1', 'Category_2', 'url', 'num_reviews', 'is_paid',
#                'price', 'num_subscribers', 'num_lectures', 'level', 'content_duration', 'published_timestamp', 'rating']


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


@app.route('/suggestions', methods=['POST'])
def suggest_courses():
    input_details = request.form
    input_course_id = input_details['selected_course']

    conn = mysql.connect()
    cur = conn.cursor()

    sql_get_selected_course = f'select * from {db_table} where course_id = \'{input_course_id}\''

    if cur.execute(sql_get_selected_course) > 0:
        dataset = cur.fetchall()

        print(type(dataset))
        print(dataset[0][1])

        title = dataset[0][1]
        category = dataset[0][3]
        level = dataset[0][10]
        rating = dataset[0][13]
        language = dataset[0][14]
        is_subtitle = dataset[0][15]

        print(category)
        print(level)
        print(rating)
        print(language)
        print(is_subtitle)

        sql_get_similar_course = f'select * from {db_table} where Category_1 like \'%{category}%\' or Category_2 like \'%{category}%\''

        if cur.execute(sql_get_similar_course) > 0:
            course_dataset = cur.fetchall()
            cur.close()

            print(len(course_dataset))

            course_df = pd.DataFrame(course_dataset, columns=header_list)
            course_df = course_df.drop_duplicates()

            other_languge_df = pd.DataFrame(
                course_dataset, columns=header_list)
            other_languge_df = course_df.drop_duplicates()

            other_level_df = pd.DataFrame(course_dataset, columns=header_list)
            other_level_df = course_df.drop_duplicates()

            course_df.query(
                f'language == \'{language}\' and is_subtitle == \'{is_subtitle}\' and level == \'{level}\'', inplace=True)

            other_languge_df.query(
                f'language != \'{language}\' and is_subtitle == \'{is_subtitle}\' and level == \'{level}\'', inplace=True)

            other_level_df.query(
                f'language != \'{language}\' and is_subtitle == \'{is_subtitle}\' and level != \'{level}\'', inplace=True)

            print(len(course_df))
            lower = rating - 1
            upper = rating + 1
            course_df.query(
                f'rating > {lower}and rating < {upper}', inplace=True)
            print(len(course_df))

            if len(course_df) <= 2:
                course_df = pd.DataFrame(course_dataset, columns=header_list)
                course_df = course_df.drop_duplicates()
                similar_courses = [tuple(course)
                                   for course in course_df.values]
                return render_template('home.html', title=title.upper(),
                                       match_courses_data=similar_courses
                                       )

            similar_courses = [tuple(course) for course in course_df.values]
            similar_courses_other_language = [
                tuple(course) for course in other_languge_df.values]
            similar_courses_other_levels = [
                tuple(course) for course in other_level_df.values]

            print(similar_courses_other_language)

            return render_template('home.html', title=title.upper(),
                                   match_courses_data=similar_courses,
                                   similar_courses_other_language=similar_courses_other_language,
                                   similar_courses_other_levels=similar_courses_other_levels
                                   )

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
