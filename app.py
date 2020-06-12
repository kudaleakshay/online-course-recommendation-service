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

@app.route('/', methods=['GET','POST'])
def index():
    if request.method == 'POST':
        # Fetch form Data
        course_details = request.form
        name = course_details['course']

        return redirect(url_for('.Home', name=name))
    
    return render_template('index.html')


@app.route('/home')
def Home():
    name = request.args['name']
    print(name)
    cur = mysql.connection.cursor()

    sql_fetch_query = """select * from datasets_udemy_courses where course_title REGEXP %s"""
    course_id = name

    result_value = cur.execute(sql_fetch_query,(course_id,))
    if result_value > 0:
        course_details = cur.fetchall()
        cur.close()
        return render_template('home.html', course_details = course_details)
    
    
if __name__ == '__main__':
    app.run(debug=True)