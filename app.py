from flask import Flask, render_template, request, redirect
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
        print(name)
        return redirect('/home')
    return render_template('index.html')


@app.route('/home')
def Home():
    cur = mysql.connection.cursor()
    result_value = cur.execute("select * from datasets_udemy_courses limit 10")
    if result_value > 0:
        course_details = cur.fetchall()
        cur.close()
        return render_template('home.html', course_details = course_details)
    
    
if __name__ == '__main__':
    app.run(debug=True)