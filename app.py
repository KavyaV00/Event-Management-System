from flask import Flask, request, make_response,session,abort,redirect,render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin.form.upload import FileUploadField
from wtforms.validators import ValidationError
import imghdr

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db' 
app.config['SECRET_KEY'] = 'abababab'
db = SQLAlchemy(app)


### Database

class Manager(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    manager_name = db.Column(db.String(25))
    password = db.Column(db.String(20)) 

class Venue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    venue_name = db.Column(db.String(50))
    capacity = db.Column(db.Integer) 
    From = db.Column(db.Time)
    to = db.Column(db.Time)
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
    _from = db.Column(db.Time)
    _to = db.Column(db.Time)
    theme = db.Column(db.String(50))
    cuisine = db.Column(db.String(20))
    food_items = db.Column(db.String(50))
    food_type = db.Column(db.String(10))
    band_name = db.Column(db.String(25))
    status = db.Column(db.String(20), default='Pending')
    manager_id = db.Column(db.Integer, db.ForeignKey('manager.id'))

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

admin = Admin(app)
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
