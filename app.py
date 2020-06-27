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

# Headers for dataset
header_list = ['course_id', 'course_title', 'Category_1', 'Category_2', 'url', 'num_reviews', 'is_paid',
               'price', 'num_subscribers', 'num_lectures', 'level', 'content_duration', 'published_timestamp', 'rating', 'language', 'is_subtitle']


mysql = MySQL(app)
mysql.init_app(app)
course_df = ''


# If user hit URL from browser this function will call
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


# If user enter keyword on home page this function will call
@app.route('/', methods=['POST'])
def recommend_courses():

    # get data from form
    input_details = request.form

    # get keyword from form data
    input_name = input_details['Name'].strip()

    # connnect to mysql DB
    conn = mysql.connect()
    cur = conn.cursor()

    # SQL query for fetching data from DB
    sql_get_match_courses = f'select * from {db_table} where course_title = \'{input_name}\' OR course_title LIKE \'% {input_name}\' OR course_title LIKE \'{input_name} %\' OR course_title LIKE \'% {input_name} %\''

    # If any course match with Keyword
    match_courses = cur.execute(sql_get_match_courses)
    if match_courses > 0:

        # fetch all data from SQL query
        dataset = cur.fetchall()
        cur.close()

        # get distinct categories from dataset
        match_categories = []
        for var in dataset:
            match_categories.append(dataset[dataset.index(var)][3].strip())

        # Convert data into pandas as a globl variable
        global course_df
        course_df = pd.DataFrame(dataset, columns=header_list)

        # remove duplicate data from dataframe
        course_df = course_df.drop_duplicates()

        # get most frequent category map to keyword
        category = most_frequent_category(match_categories)

        # get list of categories map to keyword
        match_categories = list(set(match_categories))

        # remove most frequent category from category list
        match_categories.remove(category)

        # get matching courses for keyword
        match_courses_data = get_match_courses()

        # similaar courses in most frequent category
        similar_courses_in_category = get_similar_courses_in_category(
            category)

        # send data to html file for rendering
        return render_template('home.html', title=input_name.upper(), match_courses_data=match_courses_data,
                               similar_courses_in_category=similar_courses_in_category, categories=match_categories
                               )

    else:
        return render_template('home.html')


# This function will return courses in specific category
@app.route('/category', methods=['POST'])
def recommend_categorywise_courses():

    # get data from form
    input_details = request.form

    # get keyword from form data
    input_category = input_details['Category'].strip()

    # connnect to mysql DB
    conn = mysql.connect()
    cur = conn.cursor()

    # SQL query for fetching data from DB
    sql_get_match_courses = f'select * from {db_table} where Category_1 like \'%{input_category}%\' or Category_2 like \'%{input_category}%\' ORDER BY RAND()'

    # If any course match with Category
    match_courses = cur.execute(sql_get_match_courses)
    if match_courses > 0:

        # fetch all data from SQL query
        dataset = cur.fetchall()
        cur.close()

        # Convert data into pandas as a globl variable
        global course_df
        course_df = pd.DataFrame(dataset, columns=header_list)

        # remove duplicate data from dataframe
        course_df = course_df.drop_duplicates()

        category = input_category

        # get match course in specific category
        match_courses_data = get_match_courses()

        # send data to html file for rendering
        return render_template('home.html', title=category.upper(), match_courses_data=match_courses_data)

    else:
        return render_template('home.html')


# This function will return similar courses for selected course
@app.route('/suggestions', methods=['POST'])
def suggest_courses():

    # get data from form
    input_details = request.form

    # get selected_course from form data
    input_course_id = input_details['selected_course']

    # connnect to mysql DB
    conn = mysql.connect()
    cur = conn.cursor()

    # SQL query for fetching data from DB
    sql_get_selected_course = f'select * from {db_table} where course_id = \'{input_course_id}\''

    # If any course match with selected_course
    if cur.execute(sql_get_selected_course) > 0:

        # fetch all data from SQL query
        dataset = cur.fetchall()

        # set values for filtering
        title = dataset[0][1]
        category = dataset[0][3]
        level = dataset[0][10]
        rating = dataset[0][13]
        language = dataset[0][14]
        is_subtitle = dataset[0][15]

        # SQL query for fetching data from DB
        sql_get_similar_course = f'select * from {db_table} where Category_1 like \'%{category}%\' or Category_2 like \'%{category}%\''

        # If any course match with similar courses
        if cur.execute(sql_get_similar_course) > 0:

            # fetch all data from SQL query
            course_dataset = cur.fetchall()
            cur.close()

            # Convert data into pandas
            course_df = pd.DataFrame(course_dataset, columns=header_list)
            course_df = course_df.drop_duplicates()

            # Convert data into pandas
            other_languge_df = pd.DataFrame(
                course_dataset, columns=header_list)
            other_languge_df = course_df.drop_duplicates()

            # Convert data into pandas
            other_level_df = pd.DataFrame(course_dataset, columns=header_list)
            other_level_df = course_df.drop_duplicates()

            # filter data with query
            course_df.query(
                f'language == \'{language}\' and is_subtitle == \'{is_subtitle}\' and level == \'{level}\'', inplace=True)

            other_languge_df.query(
                f'language != \'{language}\' and is_subtitle == \'{is_subtitle}\' and level == \'{level}\'', inplace=True)

            other_level_df.query(
                f'language != \'{language}\' and is_subtitle == \'{is_subtitle}\' and level != \'{level}\'', inplace=True)

            # Add rating boundries
            lower = rating - 1
            upper = rating + 1
            course_df.query(
                f'rating > {lower} and rating < {upper}', inplace=True)

            # If only 2 courses are there then remove filters
            if len(course_df) <= 2:

                # Convert data into pandas
                course_df = pd.DataFrame(course_dataset, columns=header_list)
                course_df = course_df.drop_duplicates()

                # convert into tuples
                similar_courses = [tuple(course)
                                   for course in course_df.values]

                # send data to html file for rendering
                return render_template('recommendations.html', title=title.upper(),
                                       match_courses_data=similar_courses
                                       )

            similar_courses = [tuple(course) for course in course_df.values]

            similar_courses_other_language = [
                tuple(course) for course in other_languge_df.values]

            similar_courses_other_levels = [
                tuple(course) for course in other_level_df.values]

            print(similar_courses_other_language)

            # send data to html file for rendering
            return render_template('recommendations.html', title=title.upper(),
                                   match_courses_data=similar_courses,
                                   similar_courses_other_language=similar_courses_other_language,
                                   similar_courses_other_levels=similar_courses_other_levels
                                   )

    return render_template('home.html')


# This function will return matching courses for specific keyword
def get_match_courses():
    global course_df

    # sort courses by popularity (num_subscribers)
    selected_course_df = course_df.sort_values(
        'num_subscribers', ascending=False).head(20)

    # delete data selected courses from course_df, so these courses won't showing again
    course_df = pd.concat([course_df,
                           selected_course_df]).drop_duplicates(keep=False)

    return [tuple(course) for course in selected_course_df.values]


# This function will return categorywise similar courses for specific keyword
def get_similar_courses_in_category(category):

    # connnect to mysql DB
    conn = mysql.connect()
    cur = conn.cursor()

    global course_df

    # SQL query for fetching data from DB
    sql_get_match_categories = f'select * from {db_table} where Category_1 = \'%{category}%\' or Category_2 like \'%{category}%\''

    # In any course match with category
    match_courses = cur.execute(sql_get_match_categories)
    if match_courses > 0:

        # fetch all data from SQL query
        category_dataset = cur.fetchall()
        cur.close()

        # Convert data into pandas as a globl variable
        category_df = pd.DataFrame(category_dataset, columns=header_list)
        category_df = category_df.drop_duplicates()

        # delete data selected category courses from course_df, so these courses won't showing again
        category_df = pd.concat([category_df,
                                 course_df]).drop_duplicates(keep=False)

        category_df = category_df.head(40)

    return [tuple(course) for course in category_df.values]


# This function will return most frequent category for specific keyword
def most_frequent_category(List):
    occurence_count = Counter(List)
    return occurence_count.most_common(1)[0][0]


# This is main function
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=True)
