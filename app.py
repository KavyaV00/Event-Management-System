from flask import Flask, request, make_response,session,abort,redirect,render_template, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin.form.upload import FileUploadField
from wtforms.validators import ValidationError
import imghdr
from flask_login import login_user, current_user, logout_user, login_required  # issac
from flask_login import UserMixin, LoginManager
from flask_bcrypt import Bcrypt
 #issac-cir
from datetime import datetime #Anna

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///newdb.db' #changed db #Anna
app.config['SECRET_KEY'] = 'abababab'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)  # issac
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message_category = "info"

@login_manager.user_loader #issac
def load_user(user_id):
    return Manager.query.get(int(user_id))
### Database

class Manager(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    # manager_name = db.Column(db.String(25)) #issac
    password = db.Column(db.String(20), nullable=False)
    manager_name = db.Column(db.String(25)) 
    # password = db.Column(db.String(20)) 

class Venue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    venue_name = db.Column(db.String(50))
    capacity = db.Column(db.Integer) 
    From = db.Column(db.DateTime) #Anna
    to = db.Column(db.DateTime)   #Anna
    cost = db.Column(db.Integer)

class Food(db.Model): 
    id = db.Column(db.Integer, primary_key=True)
    cuisine = db.Column(db.String(20))
    food_items = db.Column(db.String(50))
    beverages = db.Column(db.String(50))
    cost_per_head = db.Column(db.Integer) 

class Decoration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    theme_name = db.Column(db.String(50)) 
    url_pic = db.Column(db.String(50))
    pic = db.Column(db.LargeBinary)  ### Add theme photo
    cost = db.Column(db.Integer)

class Band(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    band_name = db.Column(db.String(25))
    genre = db.Column(db.String(20))
    cost = db.Column(db.Integer)

class Bookings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_name = db.Column(db.String(25))
    venue_name = db.Column(db.String(50))
    attendees = db.Column(db.Integer)
    date = db.Column(db.Date)
    _from = db.Column(db.DateTime) #Anna
    _to = db.Column(db.DateTime)   #Anna
    theme = db.Column(db.String(50))
    cuisine = db.Column(db.String(20))
    food_items = db.Column(db.String(50))
    food_type = db.Column(db.String(10))
    band_name = db.Column(db.String(25))
    status = db.Column(db.String(20), default='Pending')
    manager_id = db.Column(db.Integer, db.ForeignKey('manager.id'))

from forms import RegistrationForm, LoginForm #issac
class DecorationAdminView(ModelView):   ### To upload image, but image not getting uploaded. getattr() returning None

    def picture_validation(form, field):
        if field.data:
            filename = field.data.filename
            if filename[-4:] != '.jpg': 
                raise ValidationError('file must be .jpg')
            if imghdr.what(field.data) != 'jpeg':
                raise ValidationError('Enter valid jpeg img')
        field.data = field.data.stream.read()
        return True

    form_columns = ['id', 'theme_name', 'url_pic', 'pic']
    column_labels = dict(id='ID', theme_name="theme_name", url_pic="Picture's URL", pic='Picture')
    # print(column_labels)

    def pic_formatter(view, context, model, name):
        # print(getattr(model, name))
        return 'NULL' if getattr(model, name) == None else 'a picture'
        # return 'a picture'

    column_formatters =  dict(pic=pic_formatter)
    form_overrides = dict(pic= FileUploadField)
    form_args = dict(pic=dict(validators=[picture_validation]))
    # print(column_formatters)
    # print(form_overrides)
    # print(form_args)
   
### Admin Permissions

admin = Admin(app, template_mode='bootstrap4') #Anna changed Admin styling
class SecureModelView(ModelView):
    def is_accessible(self):
        if "logged_in" in session:
            return True
        else:
            abort(403)

admin.add_view(SecureModelView(Venue, db.session))
admin.add_view(SecureModelView(Food, db.session))
# admin.add_view(ModelView(Decoration, db.session))
admin.add_view(SecureModelView(Band, db.session))
admin.add_view(SecureModelView(Bookings, db.session))
admin.add_view(SecureModelView(Manager, db.session))  ### Maybe not show the password, just viewing list of managers
admin.add_view(DecorationAdminView(Decoration, db.session))

@app.route("/alogin",methods=['GET','POST'])
def alogin():
    if request.method=='POST':
        if request.form.get('Username')== "Admin" and request.form.get('Password')=='Admin':
            session['logged_in']=True
            return redirect("/admin")
        else:
            return render_template("/admin/alogin.html",failed=True)
    return render_template("/admin/alogin.html")

@app.route("/alogout")
def alogout():
    session.clear()
    return redirect("/alogin")

@app.route("/register", methods=['GET', 'POST'])  # issac
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        manager = Manager(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(manager)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form) #issac


@app.route("/login", methods=['GET', 'POST'])   #issac
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        manager = Manager.query.filter_by(email=form.email.data).first()
        if manager and bcrypt.check_password_hash(manager.password, form.password.data):
            login_user(manager, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route("/home") #issac
@login_required
def home():
    return "Hello Manager!"
    # render_template('home.html', posts=posts)
@app.route("/logout") #issac
def logout():
    logout_user()
    flash('You have been logged out!', 'success')
    return redirect(url_for('login'))

#Anna
@app.route('/bookings')
@app.route('/theme')
def theme():
    dec = Decoration.query.all()
    return render_template('theme.html',dec=dec)
# @app.route('/addtheme/<id>',methods=['GET','POST'])
@app.route('/bookings/<name>',methods=['GET','POST'])
def bookings(name):
    
    if request.method == 'POST':
        event = request.form['event']
        venue = request.form['venue']
        attendees = request.form['attendees']
        date = request.form['date']
        time = request.form['time']
        totime = request.form['totime']
        cuisine = request.form['cuisine']
        fitems = request.form['fitems']
        ftype = request.form['ftype']
        band = request.form['band']
        db_date = datetime.strptime(date,'%Y-%m-%d')
        time = datetime.strptime(time,'%H:%M')
        totime = datetime.strptime(totime,'%H:%M')

        # finaldate = datetime.strftime(db_date,'%Y%m%d')
        # print(finaldate)
        theme_obj = Bookings(event_name=event,venue_name=venue,attendees=attendees, \
                                date=db_date,_from=time,_to=totime,theme=name,cuisine=cuisine,\
                                food_items=fitems,food_type=ftype,band_name=band)
        db.session.add(theme_obj)
        db.session.commit()
    venue_obj = Venue.query.all()
    food_obj= Food.query.all()
    band = Band.query.all()
    return render_template('bookings.html',venue=venue_obj,food=food_obj,band=band)
#EndAnna


### Admin authorization - A

# class AdminView(ModelView):

#     def is_accessible(self):
#         return db.session.is_authenticated

#     def not_auth(self):
#         # redirect to login page if user doesn't have access
#         # return redirect(url_for('login', next=request.url))
#         return "You are not admin"

### Admin authorization - B

# @app.route('/admin')
# def admin():
#     if request.authorization and request.authorization.username == 'username' and request.authorization.password == 'password':
#         return '<h1>You are logged in</h1>'

#     return make_response('Could not verify!', 401, {'WWW-Authenticate' : 'Basic realm="Login Required"'})

if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)
