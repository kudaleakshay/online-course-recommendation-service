from flask import Flask, render_template, request, redirect, url_for
from flaskext.mysql import MySQL
import pandas as pd
import yaml
import random
import re
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
    input_name = input_details['Name']

    conn = mysql.connect()
    cur = conn.cursor()

    sql_get_match_courses = f'select * from {db_table} where course_title = \'{input_name}\' OR course_title LIKE \'% {input_name}\' OR course_title LIKE \'{input_name} %\' OR course_title LIKE \'% {input_name} %\''

    match_courses = cur.execute(sql_get_match_courses)
    if match_courses > 0:
        dataset = cur.fetchall()
        cur.close()

        global course_df
        course_df = pd.DataFrame(dataset, columns=header_list)
        course_df = course_df.drop_duplicates()

        category = dataset[0][2]  # Category column

        match_courses_data = get_match_courses()
        sort_rating_courses = get_rating_courses()
        sort_popular_courses = get_popular_courses()

        similar_courses = ''
        # Data should be more than 2 for computing similar courses based on sigmoid_kernel.
        if match_courses > 2:
            try:
                similar_courses = get_similar_courses(dataset, category)
            except:
                print("Oops! Error occurred.")

        return render_template('home.html', title=input_name, match_courses_data=match_courses_data,
                               rating_courses=sort_rating_courses,
                               popular_courses=sort_popular_courses,
                               similar_courses=similar_courses
                               )

    else:
        return render_template('home.html')


@app.route('/category', methods=['POST'])
def recommend_categorywise_courses():
    input_details = request.form
    input_category = input_details['Category']

    conn = mysql.connect()
    cur = conn.cursor()

    sql_get_match_courses = f'select * from {db_table} where Category_1 = \'{input_category}\' ORDER BY RAND()'

    match_courses = cur.execute(sql_get_match_courses)
    if match_courses > 0:
        dataset = cur.fetchall()
        cur.close()

        global course_df
        course_df = pd.DataFrame(dataset, columns=header_list)
        course_df = course_df.drop_duplicates()

        category = input_category

        match_courses_data = get_match_courses()
        sort_rating_courses = get_rating_courses()
        sort_popular_courses = get_popular_courses()

        similar_courses = ''
        # Data should be more than 2 for computing similar courses based on sigmoid_kernel.
        if match_courses > 2:
            try:
                similar_courses = get_similar_courses(dataset, category)
            except:
                print("Oops! Error occurred.")

        return render_template('home.html', title=category, match_courses_data=match_courses_data,
                               rating_courses=sort_rating_courses,
                               popular_courses=sort_popular_courses,
                               similar_courses=similar_courses
                               )

    else:
        return render_template('home.html')


def get_match_courses():
    # course_df = course_df.head(10)
    global course_df
    print(len(course_df))
    selected_course_df = course_df.head(10)
    course_df = pd.concat([course_df,
                           selected_course_df]).drop_duplicates(keep=False)

    print("get_match_courses: ")
    print(len(course_df))
    return [tuple(course) for course in selected_course_df.values]


def get_rating_courses():
    global course_df
    print(len(course_df))
    selected_course_df = course_df.sort_values(
        'rating', ascending=False).head(5)

    course_df = pd.concat([course_df,
                           selected_course_df]).drop_duplicates(keep=False)
    print("get_rating_courses: ")
    print(len(course_df))
    return [tuple(course) for course in selected_course_df.values]


def get_popular_courses():
    global course_df
    print(len(course_df))
    selected_course_df = course_df.sort_values(
        'num_subscribers', ascending=False).head(5)

    course_df = pd.concat([course_df,
                           selected_course_df]).drop_duplicates(keep=False)

    print("get_popular_courses: ")
    print(len(course_df))
    return [tuple(course) for course in selected_course_df.values]


def get_similar_courses(dataset, category):
    course_df = pd.DataFrame(dataset, columns=header_list)

    print(len(course_df))
    course_df = course_df.drop_duplicates()
    print(len(course_df))

    course_cleaned_df = course_df
    course_cleaned_df.head()

    course_cleaned_df.info()

    tfv = TfidfVectorizer(min_df=3,
                          max_features=None,
                          strip_accents='unicode',
                          analyzer='word',
                          token_pattern=r'\w{1,}',
                          ngram_range=(1, 3),
                          stop_words='english')

    tfv_matrix = tfv.fit_transform(course_cleaned_df['course_title'])

    # Compute the sigmoid kernel
    sig = sigmoid_kernel(tfv_matrix, tfv_matrix)
    indices = pd.Series(course_cleaned_df.index,
                        index=course_cleaned_df['Category_1']).drop_duplicates()

    # Get the index corresponding to original_title
    idx = indices[category]

    # Get the pairwsie similarity scores
    sig_scores = list(enumerate(sig[idx]))

    # Sort the Course
    sig_scores = sorted(sig_scores, key=lambda x: x[1].all(), reverse=True)

    # Scores of the 10 most similar movies
    sig_scores = sig_scores[1:11]

    # Course indices
    course_indices = [i[0] for i in sig_scores]

    # Top 10 most similar Course
    print(course_cleaned_df['Category_1'].iloc[course_indices])

    # return course_cleaned_df['course_title'].iloc[course_indices]
    df1 = course_cleaned_df.iloc[course_indices]
    print(course_cleaned_df.iloc[course_indices])
    return [tuple(course) for course in df1.values]


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=True)
