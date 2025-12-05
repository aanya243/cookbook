from flask import Flask, render_template, request, redirect, session, url_for, send_from_directory, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import Form, StringField, PasswordField, SubmitField, TextAreaField, FileField
from wtforms.validators import DataRequired, Length, Email
from flask_ckeditor import CKEditor
from config import Config
import os
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
app.config.from_object(Config)
app.config["SQLALCHEMY_DATABASE_URI"] = 'mysql+mysqlconnector://root:root@localhost:3306/cookbook'
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["CKEDITOR_FILE_UPLOADER"] = "upload"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB

db = SQLAlchemy(app)
login_manager = LoginManager(app)
ckeditor = CKEditor(app)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    recipes = db.relationship("Recipe", backref="user", lazy=True)
    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    cooking_time = db.Column(db.Integer, nullable=False)
    servings = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    image_url = db.Column(db.String(500), nullable=True)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Register")

class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")
    
class RecipeForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    description = TextAreaField("Description", validators=[DataRequired()])
    cooking_time = StringField("Cooking Time", validators=[DataRequired()])
    servings = StringField("Servings", validators=[DataRequired()])
    image = TextAreaField("Image")
    submit = SubmitField("Upload Recipe")
    # connecting to database
def connect_database(): 
    global mydb
    global mycursor
    try:
        if 'mydb' in globals() and mydb is not None and mydb.is_connected():
            return
    except Exception:
        pass

    try:
        print("\nCreating new db connection...")
        mydb = mysql.connector.connect(host="localhost", user="root", password="root", database="cookbook")
        mycursor = mydb.cursor()
    except mysql.connector.Error as q:
        print("Database Error: " + str(q) + "\n")
def disconnect_database():
    global mydb
    global mycursor
    try:
        if 'mydb' in globals() and mydb is not None and mydb.is_connected():
            try:
                mycursor.close()
            except Exception:
                pass
            mydb.close()
    except Exception:
        print("pass")


@app.route("/", methods=["GET"])
def test():
    return redirect("/index")
    #return render_template("index.html",loadsec=loadsec)

@app.route("/index", methods=["GET"])
#def hello_world():
 #   return "<p>Hello, World!</p>"
def index():
    #featured_recipes = Recipe.query.filter(Recipe.user_id == session['userid']).order_by(Recipe.id.asc()).limit(5)
    #recent_recipes = Recipe.query.order_by(Recipe.id.desc()).limit(3)
    #popular_recipes = Recipe.query.order_by(Recipe.id.desc()).limit(3)
   # return render_template("index.html", featured_recipes=featured_recipes, recent_recipes=recent_recipes, popular_recipes=popular_recipes)
    
    return render_template("index.html")
    
@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    #if form.validate_on_submit():
    if request.method=="POST":
        username = form.username.data
        email = form.email.data
        password = form.password.data
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("login"))
        #return render_template("test.html", id = "loginsec") 
        #return render_template("test.html")
    print("loading registration form")
    return render_template("register.html", form = form) 
   

@app.route("/login", methods=["GET", "POST"])
def login():    
    form = LoginForm()
    loadsec="login"
    if request.method=="POST":
            #print("post")
            username = form.username.data
            password = form.password.data
            user = User.query.filter_by(username=username).first()
            #user2 = db.session.query(User).filter_by(id=user).first()
            session['username']=username
            if user and user.check_password(password):
             #   print("password passed")
                login_user(user)
                session['userid']=user.id
                #print(str(user))
                urlprofile ="profile/"+str(username)
                #print("urlprofile"+ urlprofile)
                return redirect(urlprofile)
            #return render_template("test.html", loadsec="login")
            return render_template("login.html", form=form)
    #return render_template("test.html",loadsec="login")
    return render_template("login.html", form=form)
#call profile (sql connect)
@app.route("/profile/<username>")
@login_required
def profile(username):
    #print(username)
    connect_database()
    #mycursor = mydb.cursor()
    query ="SELECT * FROM user where username = \""+username+ "\" limit 1"
    #print(query)
    mycursor.execute(query)
    user = mycursor.fetchall()
    #user1 = User.query.filter_by(username=username).first()
    #print(user[0])
    query2 ="SELECT * FROM recipe r, user u where r.user_id = u.id and r.user_id = "+str(user[0][0])
    #print(query2)
    mycursor.execute(query2)
    recipes=mycursor.fetchall()
    #print(recipes)
       
    if user:
        return render_template("profile.html", user=user, recipes=recipes)
    return render_template("404.html"), 404

@app.route("/upload_recipe", methods=["GET", "POST"])
#jcn
#check_password_hashsd
@login_required
def upload_recipe():
    form = RecipeForm()
    recipeurl= "profile/"+ str(session['username'])
  
    if form.validate_on_submit():
        # recipe = form.save()
            title = form.title.data
            description = form.description.data
            cooking_time = form.cooking_time.data
            servings =form.servings.data
            user_id=session['userid']
            image_url=form.image.data
            recipe = Recipe(title=title, description=description, cooking_time=cooking_time,servings=servings,user_id=user_id, image_url=image_url)
            db.session.add(recipe)
            db.session.commit()
            print(recipeurl)
            return render_template("recipesuccess.html",title=title,recipeurl=recipeurl)
            #return redirect(url_for('recipesuccess'))
    return render_template("recipe.html", form=form, recipeurl=recipeurl)



           
     
if __name__ == '__main__':
    app.run(debug=True)




