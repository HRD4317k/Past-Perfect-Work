from flask import Flask, render_template, redirect, url_for, flash,request,session,jsonify
from flask_login import UserMixin,LoginManager,login_user,login_required,logout_user,current_user
from datetime import datetime
import requests
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_,func,desc
from sqlalchemy.dialects.postgresql import JSON
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField,PasswordField,FileField,IntegerField,SelectField,URLField,RadioField,TextAreaField,MultipleFileField
from wtforms.validators import Length,InputRequired,ValidationError,NumberRange,URL,Optional,Email
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
import os
import email_notifications as en
import numpy as np
from PIL import Image
from functools import wraps 
from pillow_heif import register_heif_opener
from pt_mapping import UI_TO_MODEL_PRODUCT_TYPE,condition_descriptions,img_json
from datetime import timedelta
import boto3
import psycopg2
from urllib.parse import urlparse
import requests
import email_notifications as en
import email_validator
import numpy as np
import uuid
from phonepe.sdk.pg.payments.v2.standard_checkout_client import StandardCheckoutClient
from phonepe.sdk.pg.env import Env
from phonepe.sdk.pg.payments.v2.models.request.standard_checkout_pay_request import StandardCheckoutPayRequest
from io import BytesIO
import json
from json_creator import generate_survey_json


with open("delivery_person.json", "r") as f:
    dp = json.load(f)



client_id = "SU2503181725093842083774"
client_secret = "761b5ae5-0be8-4372-9981-8bbc1083ad9a"
client_version = 1  # Insert your client version here
env = Env.PRODUCTION  # Change to Env.PRODUCTION when you go live
 
standard_phonepe_client = StandardCheckoutClient.get_instance(client_id=client_id, client_secret=client_secret,
client_version=client_version,
env=env)







app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///past_perfect.db')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['AWS_ACCESS_KEY_ID'] = os.environ.get('AWS_ACCESS_KEY_ID')
app.config['AWS_SECRET_ACCESS_KEY'] = os.environ.get('AWS_SECRET_ACCESS_KEY')
app.config['AWS_S3_BUCKET_NAME'] = os.environ.get('AWS_S3_BUCKET_NAME', 'past-perfect')
app.config['AWS_S3_REGION_NAME'] = os.environ.get('AWS_S3_REGION_NAME', 'ap-south-1')
app.config['SESSION_PERMANENT'] = True



s3_client = boto3.client(
    's3',
    aws_access_key_id=app.config['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=app.config['AWS_SECRET_ACCESS_KEY'],
    region_name=app.config['AWS_S3_REGION_NAME']
)

def upload_to_s3(file_stream, bucket_name, key, content_type='image/webp'):
    
    try:
        s3_client.upload_fileobj(
            file_stream,
            bucket_name,
            key,
            ExtraArgs={'ContentType': content_type, 'ACL': 'public-read'}
        )
        s3_url = f"https://{bucket_name}.s3.amazonaws.com/{key}"
        return s3_url
    except Exception as e:
        print("S3 upload error:", e)
        return None


login_manager= LoginManager()
login_manager.init_app(app)
login_manager.login_view ='login'



register_heif_opener()
bcrypt = Bcrypt(app)
db =SQLAlchemy(app)



class Visitor(db.Model):
    __tablename__ = 'visitors'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, unique=True)  # Store unique date
    visit_count = db.Column(db.Integer, nullable=False, default=0)  # Count of visitors for the day
    
    

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    mobile_no = db.Column(db.String(10), nullable=False)
    college = db.Column(db.String(60), nullable=False,default='kgp')
    address = db.Column(db.String(400), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.today().date())


class SurveyResponse(db.Model):
    __tablename__ = 'survey'
    id = db.Column(db.Integer, primary_key=True)
    response = db.Column(JSON, nullable=False)  # Use JSON type for PostgreSQL
    ref = db.Column(db.String, nullable=True) 
    college = db.Column(db.String, nullable=False)




class Item(db.Model):
    __tablename__ = 'items'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # Item name
    category = db.Column(db.Text,nullable=False)
    sub_cat = db.Column(db.Text,nullable=False)  # Subcategory of the item
    price = db.Column(db.Integer, nullable=False)  # Item price
    og_price = db.Column(db.Integer, default = 0)  # Item price
    age = db.Column(db.Integer,nullable=False)
    condition = db.Column(db.Text,nullable=False)
    description = db.Column(db.Text, nullable=False)  # Item description
    pic_file_path = db.Column(db.Text, nullable=False)  # Path to picture file
    vid = db.Column(db.Text, nullable=True)  # Path to video file
    assured = db.Column(db.Text,nullable =False)
    college = db.Column(db.String(60), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.today().date())
    coupon_applied = db.Column(db.String(20), nullable=True, default=None)
    is_reported = db.Column(db.Boolean, default=False) 
    
    # Foreign key to link to the User table
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', backref='items', lazy=True)

class Demand(db.Model):
    __tablename__ = 'demand'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # Item name
    category = db.Column(db.Text,nullable=False)
    sub_cat = db.Column(db.Text,nullable=False)
    avg_price = db.Column(db.Integer,nullable = False)
    email = db.Column(db.Text,nullable = False)
    college = db.Column(db.Text,nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Foreign key to link to the User table
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', backref='demands', lazy=True)



class Misc_Approval(db.Model):
    __tablename__ = 'misc_approval'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # Item name
    category = db.Column(db.Text,nullable=False)
    og_price = db.Column(db.Integer,nullable=False,default=0)
    price = db.Column(db.Integer, nullable=False)  # Item price
    age = db.Column(db.Integer,nullable=False)
    condition = db.Column(db.Text,nullable=False)
    description = db.Column(db.Text, nullable=False)  # Item description
    pic_file_path = db.Column(db.Text, nullable=False)  # Path to picture file
    assured = db.Column(db.Text,nullable =False)
    college = db.Column(db.String(60), nullable=False)
    status = db.Column(db.String(20), default="Pending")
    created_at = db.Column(db.DateTime, default=datetime.today().date())
    reason = db.Column(db.Text, nullable=True,default= "Awaited")  # Reason for rejection if any
    # Foreign key to link to the User table
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', backref='misc_approvals')

class assure_pending(db.Model):
    __tablename__ = 'assured_pending'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # Item name
    category = db.Column(db.Text,nullable=False)
    sub_cat = db.Column(db.Text,nullable=False)  # Subcategory of the item
    price = db.Column(db.Integer, nullable=False)  # Item price
    og_price = db.Column(db.Integer, default = 0)  # Item price
    age = db.Column(db.Integer,nullable=False)
    condition = db.Column(db.Text,nullable=False)
    description = db.Column(db.Text, nullable=False)  # Item description
    pic_file_path = db.Column(db.Text, nullable=False)  # Path to picture file
    assured = db.Column(db.Text,nullable =False)
    college = db.Column(db.String(60), nullable=False)
    mobile = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(120), nullable=False) 
    coupon_applied = db.Column(db.String(20), nullable=True, default=None)

    
    # Foreign key to link to the User table
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', backref='assured_pendings', lazy=True)

class Sold(db.Model):
    __tablename__ = 'items_sold'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # Item name
    category = db.Column(db.Text,nullable=False)
    sub_cat = db.Column(db.Text,nullable=False)  # Subcategory of the item
    vid= db.Column(db.Text, nullable=True)  # Path to video file
    price = db.Column(db.Integer, nullable=False)  # Item price
    og_price = db.Column(db.Integer, default = 0)  # Item price
    age = db.Column(db.Integer,nullable=False)
    condition = db.Column(db.Text,nullable=False)
    description = db.Column(db.Text, nullable=False)  # Item description
    pic_file_path = db.Column(db.Text, nullable=False)  # Path to picture file
    assured = db.Column(db.Text,nullable =False)
    college = db.Column(db.String(60), nullable=False)
    status = db.Column(db.String(20), default="Pending")  # Status (e.g., Pending, Completed, Canceled)
    created_at = db.Column(db.DateTime, default=datetime.today().date())  # Timestamp of sale
    buyer_id = db.Column(db.Integer, nullable=False)  # ID of the buyer
    coupon_applied = db.Column(db.String(20), nullable=True, default=None)
    
    # Foreign key to link to the User table
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

class Purchase(db.Model):
    __tablename__ = 'purchases'
    
    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, nullable=False)  # ID of the buyer
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  
    og_price = db.Column(db.Integer, nullable=False)  # Original price of the item
    purchase_price = db.Column(db.Integer, nullable=False)  # Price at which the item was bought
    purchase_date = db.Column(db.DateTime, default=datetime.today().date())  # Timestamp of purchase
    status = db.Column(db.String(20), default="Pending")  # Status (e.g., Pending, Completed, Canceled)
    pic_file_path = db.Column(db.Text, nullable=False)
    name = db.Column(db.Text, nullable=False)
    category = db.Column(db.Text, nullable=False)
    sub_cat = db.Column(db.Text,nullable=False)  # Subcategory of the item
    vid= db.Column(db.Text, nullable=True)  # Path to video file
    description = db.Column(db.Text, nullable=False)
    assured = db.Column(db.Text,nullable =False)
    age = db.Column(db.Integer,nullable=False)
    condition = db.Column(db.Text,nullable=False)
    college = db.Column(db.String(60), nullable=False)
    delivery_fee = db.Column(db.Float, nullable=False, default=0.0)
    platform_fee = db.Column(db.Float, nullable=False, default=0.0)
    discount_applied = db.Column(db.Boolean, nullable=False, default=False)
    discount_amount = db.Column(db.Float, nullable=False, default=0.0)
    payment_method = db.Column(db.String(20), nullable=False, default='upi')
    otp = db.Column(db.String(6), nullable=True)

class SupportQuery(db.Model):
    __tablename__ = 'support_queries'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    query_text = db.Column(db.Text, nullable=False)
    query_email = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.today().date())

    user = db.relationship('User', backref='support_queries')


class RegisterForm(FlaskForm):
    username = StringField('Name',validators=[InputRequired(), Length(min=4, max=20)], render_kw={'placeholder': 'Enter Username'})
    password = PasswordField('Password',validators=[InputRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[InputRequired(), Email(), Length(max=120)], render_kw={'placeholder': 'Enter Email'})
    mobile_no = StringField('Mobile Number', validators=[InputRequired(), Length(min=10, max=10)], render_kw={'placeholder': 'Enter Mobile Number'})
    college = SelectField('Select College',
                           choices=[
                                ('kgp', 'IIT Kharagpur'),
                                ('bhu', 'IIT Varanasi'),
                                ('dayalsingh','Dayal Singh College '),
                                ('motilalnehru','Moti Lal Nehru College'),
                                ('hansraj','Hansraj College'),
                                ('deendayalupadhyay',' Deen Dayal Upadhyay College'),
                                ('lucknowuniversity','Lucknow University'),
							   	('gargi','Gargi College'),
							   	('matasundari',' Mata Sundari College'),
							   	('shaheedbhagatsingh','Shaheed Bhagat Singh College')
        ],render_kw={'placeholder':'Choose College'})
    address = TextAreaField('Address', render_kw={'placeholder': 'Enter Delivery Address'})
    submit = SubmitField('Create Account')

    def validate_username(self, username):
        existing_user = User.query.filter_by(username=username.data).first()
        if existing_user:
            raise ValidationError("That username already exists. Please choose another!")

    def validate_email(self, email):
        existing_email = User.query.filter_by(email=email.data).first()
        if existing_email:
            raise ValidationError("That email address is already registered. Please use a different one.")

class LoginForm(FlaskForm):
    email = StringField(validators=[InputRequired(),Length(min=4)],render_kw={'placeholder':'Enter Email'})
    password = PasswordField(validators=[InputRequired(),Length(min=4,max=20)])
    submit = SubmitField('Log in')

class DemandForm(FlaskForm):
    name = StringField(validators=[InputRequired(),Length(min=4)],render_kw={'placeholder':'Enter Item name'})
    category = SelectField(
                           choices=[
                               ("", "Choose a category"),
                                ('Cycles', 'Cycles'),
                                ('Electronics', 'Electronics'),
                                ('Hostel Essentials', 'Hostel Essentials'),
                                ('Mattress', 'Mattresses'),
                                ('Watches', 'Watches'),
                                ('Books', 'Books'),
                                ('Fitness & Sports', 'Fitness & Sports'),                               
                                ('Academic Accessories', 'Academic Accessories'),
                                ('Appliances & Kitchenware', 'Appliances & Kitchenware'),
                                ('Personal Accessories', 'Personal Accessories'),
                                ('Miscellaneous', 'Miscellaneous')
                                
        ],render_kw={'placeholder':'Choose Category'})
    sub_watch = SelectField('Choose a subclass', choices=[
        ('Digital', 'Digital'),
        ('Analog', 'Analog'),
        ('Smartwatches', 'Smartwatches'),
        ('Other', 'Other')
    ], render_kw={'placeholder': 'Choose Subcategory'})

    sub_sports = SelectField('Choose a subclass', choices=[
        ('Gym Gear', 'Gym Gear'),
        ('Balls', 'Balls'),
        ('Yoga Mat', 'Yoga Mat'),
        ('Skipping Rope', 'Skipping Rope'),
        ('Rackets', 'Rackets'),
        ('Other', 'Other')
    ], render_kw={'placeholder': 'Choose Subcategory'})

    sub_hostel = SelectField('Choose a subclass', choices=[
        ('WiFi Router', 'WiFi Router'),
        ('Umbrella', 'Umbrella'),
        ('Mosquito Nets/Rackets', 'Mosquito Nets/Rackets'),
        ('Curtains', 'Curtains'),
        ('Wooden Chair', 'Wooden Chair'),
        ('Office Chair', 'Office Chair'),
        ('Shelves', 'Shelves'),
        ('Decor', 'Decor'),
        ('Buckets/Mugs', 'Buckets/Mugs'),
        ('Other', 'Other')
    ], render_kw={'placeholder': 'Choose Subcategory'})

    sub_elec_app = SelectField('Choose a subclass', choices=[
        ('Table Fan', 'Table Fan'),
        ('Cooler', 'Cooler'),
        ('Utensils/Cutlery', 'Utensils/Cutlery'),
        ('Washing Machine', 'Washing Machine'),
        ('Induction', 'Induction'),
        ('Kettle', 'Kettle'),
        ('Other', 'Other')
    ], render_kw={'placeholder': 'Choose Subcategory'})
    sub_elec_acc = SelectField('Choose a subclass', choices=[
        ('Keyboard/Mouse', 'Keyboard/Mouse'),
        ('Writing Pad', 'Writing Pad'),
        ('Kindle', 'Kindle'),
        ('Monitor', 'Monitor'),
        ('USB/LAN Devices', 'USB/LAN Devices (Hard Disk, pen drive, etc.)'),
        ('Trimmer', 'Trimmer'),
        ('Controller/Consoles', 'Controller/Consoles'),
        ('Extension Cord', 'Extension Cord'),
        ('Wifi Router', 'Wifi Router'),
        ('Earbuds', 'Earbuds'),
        ('Speaker', 'Speaker'),
        ('Mouse', 'Mouse'),
        ('Power Bank', 'Power Bank'),
        ('Other', 'Other')
    ], render_kw={'placeholder': 'Choose Subcategory'})

    sub_acad_acc = SelectField('Choose a subclass', choices=[
        ('ED drafter', 'ED Kit'),
        ('Whiteboard', 'White Board'),
        ('Chart Holder', 'Chart Holder'),
        ('Lab Coat', 'Lab Coat'),
        ('Calculator', 'Calculator'),
        ('Laptop_stand', 'Laptop Stand'),
        ('Study Lamp', 'Study Lamp'),
        ('Writing Pad', 'Writing Pad'),
        ('Other', 'Other')
    ], render_kw={'placeholder': 'Choose Subcategory'})

    sub_personal_acc = SelectField('Choose a subclass', choices=[
        ('Shoes', 'Shoes'),
        ('Musical Instruments', 'Musical Instruments'),
        ('Belts', 'Belts'),
        ('Bags', 'Bags'),
        ('Umbrella', 'Umbrella'),
        ('Other', 'Other')
    ], render_kw={'placeholder': 'Choose Subcategory'})

    sub_books = SelectField('Choose a subclass', choices=[
        ('Novels', 'Novels'),
        ('Course Books', 'Course Book'),
        ('Other', 'Other')
    ], render_kw={'placeholder': 'Choose Subcategory'})
    sub_mat = SelectField('Choose a subclass', choices=[
        ('Cotton', 'Cotton'),
        ('Foam', 'Foam'),
	('Notes','Notes'),
        ('Other', 'Other')
    ], render_kw={'placeholder': 'Choose Subcategory'})
    sub_cycle = SelectField('Choose a subclass', choices=[
        ('Gear', 'Gear'),
        ('Gearless', 'Gearless'),
        ('Other', 'Other')
    ], render_kw={'placeholder': 'Choose Subcategory'})
    avg_price = IntegerField(validators=[InputRequired(), NumberRange(min=1)],render_kw={'placeholder':'Enter preferred price to buy'})



class SellForm(FlaskForm):
    name = StringField(validators=[InputRequired(),Length(min=4)],render_kw={'placeholder':'Enter Item name'})
    category = SelectField(
                           choices=[
                               ("", "Choose a category"),
                                ('Cycles', 'Cycles'),
                                ('Electronics', 'Electronics'),
                                ('Hostel Essentials', 'Hostel Essentials'),
                                ('Mattress', 'Mattresses'),
                                ('Watches', 'Watches'),
                                ('Books', 'Books'),
                                ('Fitness & Sports', 'Fitness & Sports'),                               
                                ('Academic Accessories', 'Academic Accessories'),
                                ('Appliances & Kitchenware', 'Appliances & Kitchenware'),
                                ('Personal Accessories', 'Personal Accessories'),
                                ('Miscellaneous', 'Miscellaneous')
                                
        ],render_kw={'placeholder':'Choose Category'})
    price = IntegerField(validators=[InputRequired(), NumberRange(min=1)],render_kw={'placeholder':'Enter Original Price'})
    misc_price = IntegerField(validators=[Optional(),NumberRange(min=1)],render_kw={'placeholder':'Enter Preffered Selling Price'})

    age = SelectField(
                           choices=[
                               
                                (1, 'Less than 1 year'),
                                (2, '2'),
                                (3, '3'),
                                (4, '4'),
                                (5, '5 and greater'),
        ],render_kw={'placeholder':'Select Age'},coerce=int)
    condition = SelectField(choices=[
        ("", "Select condition"),
        ("0", "New"),
        ("1", "Used"),
        ("2", "Heavily Used"),
    ], validators=[InputRequired()])
    description = TextAreaField(validators=[InputRequired(),Length(min=4,max=20000)],render_kw={'placeholder':'Provide all specifics: features, dimensions, materials, notable characteristics, or any imperfections.'})
    
    pic_file_path = MultipleFileField("Upload Images", validators=[InputRequired()])
    assured = SelectField('Assurance',choices=[
                                ('Assured', 'Assured'),
                                ('Not Assured', 'Not Assured'),
        ])

    # Additional subclass field
    sub_watch = SelectField('Choose a subclass', choices=[
        ('Digital', 'Digital'),
        ('Analog', 'Analog'),
        ('Smartwatches', 'Smartwatches'),
        ('Other', 'Other')
    ], render_kw={'placeholder': 'Choose Subcategory'})

    sub_sports = SelectField('Choose a subclass', choices=[
        ('Gym Gear', 'Gym Gear'),
        ('Balls', 'Balls'),
        ('Yoga Mat', 'Yoga Mat'),
        ('Skipping Rope', 'Skipping Rope'),
        ('Rackets', 'Rackets'),
        ('Other', 'Other')
    ], render_kw={'placeholder': 'Choose Subcategory'})

    sub_hostel = SelectField('Choose a subclass', choices=[
        ('WiFi Router', 'WiFi Router'),
        ('Umbrella', 'Umbrella'),
        ('Mosquito Nets/Rackets', 'Mosquito Nets/Rackets'),
        ('Curtains', 'Curtains'),
        ('Wooden Chair', 'Wooden Chair'),
        ('Office Chair', 'Office Chair'),
        ('Shelves', 'Shelves'),
        ('Decor', 'Decor'),
        ('Buckets/Mugs', 'Buckets/Mugs'),
        ('Other', 'Other')
    ], render_kw={'placeholder': 'Choose Subcategory'})

    sub_elec_app = SelectField('Choose a subclass', choices=[
        ('Table Fan', 'Table Fan'),
        ('Cooler', 'Cooler'),
        ('Utensils/Cutlery', 'Utensils/Cutlery'),
        ('Washing Machine', 'Washing Machine'),
        ('Induction', 'Induction'),
        ('Kettle', 'Kettle'),
        ('Other', 'Other')
    ], render_kw={'placeholder': 'Choose Subcategory'})
    sub_elec_acc = SelectField('Choose a subclass', choices=[
        ('Keyboard/Mouse', 'Keyboard/Mouse'),
        ('Writing Pad', 'Writing Pad'),
        ('Kindle', 'Kindle'),
        ('Monitor', 'Monitor'),
        ('USB/LAN Devices', 'USB/LAN Devices (Hard Disk, pen drive, etc.)'),
        ('Trimmer', 'Trimmer'),
        ('Controller/Consoles', 'Controller/Consoles'),
        ('Extension Cord', 'Extension Cord'),
        ('Wifi Router', 'Wifi Router'),
        ('Earbuds', 'Earbuds'),
        ('Speaker', 'Speaker'),
        ('Mouse', 'Mouse'),
        ('Power Bank', 'Power Bank'),
        ('Other', 'Other')
    ], render_kw={'placeholder': 'Choose Subcategory'})

    sub_acad_acc = SelectField('Choose a subclass', choices=[
        ('ED Drafter', 'ED Kit'),
        ('Whiteboard', 'White Board'),
        ('Chart Holder', 'Chart Holder'),
        ('Lab Coat', 'Lab Coat'),
        ('Calculator', 'Calculator'),
        ('Laptop_stand', 'Laptop Stand'),
        ('Study Lamp', 'Study Lamp'),
        ('Writing Pad', 'Writing Pad'),
        ('Other', 'Other')
    ], render_kw={'placeholder': 'Choose Subcategory'})

    sub_personal_acc = SelectField('Choose a subclass', choices=[
        ('Shoes', 'Shoes'),
        ('Musical Instruments', 'Musical Instruments'),
        ('Belts', 'Belts'),
        ('Bags', 'Bags'),
        ('Umbrella', 'Umbrella'),
        ('Other', 'Other')
    ], render_kw={'placeholder': 'Choose Subcategory'})

    sub_books = SelectField('Choose a subclass', choices=[
        ('Novels', 'Novels'),
        ('Course Books', 'Course Book'),
        ('Other', 'Other')
    ], render_kw={'placeholder': 'Choose Subcategory'})
    sub_mat = SelectField('Choose a subclass', choices=[
        ('Cotton', 'Cotton'),
        ('Foam', 'Foam'),
        ('Other', 'Other')
    ], render_kw={'placeholder': 'Choose Subcategory'})
    sub_cycle = SelectField('Choose a subclass', choices=[
        ('Gear', 'Gear'),
        ('Gearless', 'Gearless'),
        ('Other', 'Other')
    ], render_kw={'placeholder': 'Choose Subcategory'})


    submit = SubmitField("Publish Your Listing")
    def validate_pic_file_path(self, field):
        files = request.files.getlist(field.name)
        if len(files) < 2:
            raise ValidationError("You must upload at least 2 files.")







@app.route('/')
def home():
    top_demands = []
    try:
        today = datetime.utcnow().date()
        visitor_record = Visitor.query.filter_by(date=today).first()
        
        if visitor_record:
            visitor_record.visit_count += 1
        else:
            visitor_record = Visitor(date=today, visit_count=1)
            db.session.add(visitor_record)
        
        db.session.commit()
        query = db.session.query(
                        Demand.sub_cat,
                        func.count(Demand.id).label('total_demands'))
        if current_user.is_authenticated:
            query = query.filter(Demand.college == current_user.college)

        top_demands = query.group_by(Demand.sub_cat)\
                       .order_by(desc('total_demands'))\
                       .limit(4)\
                       .all()
    except Exception as e:
        print(f"Database error in home route: {e}")
        top_demands = []
    
    return render_template('index.html',top_demands=top_demands,img_json = img_json)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter(func.lower(User.email) == form.email.data.lower()).first()
        if user:
            if bcrypt.check_password_hash(user.password,form.password.data):
                login_user(user)
                session.permanent = True
                if user.email == dp[user.college]['email']:
                    return redirect(url_for('delivery_dashboard'))
                if user.email in ADMIN_EMAILS or user.username in CAMPUS_AMBASSADORS:
                    return redirect(url_for('admin_dashboard'))
                return redirect(url_for('dashboard'))
            else:
                form.password.errors.append('Wrong Password!')
        else:
            form.email.errors.append("This email doesn't exist!")
    return render_template('login.html',form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():

        email = form.email.data
        otp_1 = en.send_otp(email)  # Send OTP to the user's email

    
        session['registration_data'] = {
            'username': form.username.data,
            'password': bcrypt.generate_password_hash(form.password.data).decode('utf-8'),
            'email': email,
            'mobile_no': form.mobile_no.data,
            'college': form.college.data,
            'address': form.address.data,
        }
        session['otp_1'] = otp_1  # Store the OTP for validation
        flash("An OTP has been sent to your email. Please verify.", 'info')
        return redirect(url_for('verify_otp'))  # Redirect to OTP verification page

    return render_template('register.html', form=form)


@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if 'registration_data' not in session:
        flash("Session expired. Please register again.", 'danger')
        return redirect(url_for('register'))

    if request.method == 'POST':
        dig_1 = request.form.get('dig1')
        dig_2 = request.form.get('dig2')
        dig_3 = request.form.get('dig3')
        dig_4 = request.form.get('dig4')
        dig_5 = request.form.get('dig5')
        dig_6 = request.form.get('dig6')
        
        entered_otp = dig_1+dig_2+dig_3+dig_4+dig_5+dig_6

        if entered_otp == session.get('otp_1'):  # OTP matched
            user_data = session.pop('registration_data')  # Retrieve stored user data
            
            # Create and save the user
            new_user = User(
                username=user_data['username'],
                password=user_data['password'],
                email=user_data['email'],
                mobile_no=user_data['mobile_no'],
                college=user_data['college'],
                address=user_data['address'],
            )

            db.session.add(new_user)
            db.session.commit()

            session.pop('otp_1', None)  # Remove OTP from session

            flash("Account created successfully! Please log in.", 'success')
            return redirect(url_for('login'))

        else:
            flash("Invalid OTP. Please try again.", "danger")
            
            return redirect(url_for('register'))

    return render_template('verify_otp.html',email = session.get('registration_data', {}).get('email', ''))


@app.route('/browse', methods=['GET', 'POST'])
def browse():
    if current_user.is_authenticated:
        items = Item.query.filter((Item.user_id != current_user.id) & (Item.college == current_user.college)).all()
        min_price = db.session.query(func.min(Item.price)).scalar()
        max_price = db.session.query(func.max(Item.price)).scalar()
    else:
        items = Item.query.all()
        min_price = db.session.query(func.min(Item.price)).scalar()
        max_price = db.session.query(func.max(Item.price)).scalar()
    sorted_items = sorted(items, key=lambda x: 0 if x.assured == 'Assured' else 1)
    
    return render_template('browse.html',items = sorted_items, min_price=min_price, max_price=max_price)



@app.route('/faqs', methods=['GET'])
def faqs():
    faq_content = [
	{
    	"question": "What is Past Perfect?",
    	"one": "Past Perfect is a second-hand C2C e-commerce platform",
    	"two": "We aim to revolutionize the buying and selling of second-hand goods with a hassle-free experience",
    	"three": "We eliminate middlemen, ensuring sellers receive the full amount paid by buyers, with no hidden cuts",
    	"four": "Our delivery service allows direct hostel-to-hostel product delivery for maximum convenience"
	},
	{
    	"question": "How does the pricing work?",
    	"one": "We gathered 3,000+ data points through extensive market research",
    	"two": "Our ML model predicts the most desirable price by factoring in product age, condition, and buyer demand",
    	"three": "It calculates depreciation uniquely for each product type, ensuring fair and accurate pricing",
    	"four": "Sellers can trust the price, as it's based on direct buyer preferences from our research"
	},
	{
    	"question": "What are 'Assured' products?",
    	"one": "Choose the 'Assured' option while listing to boost credibility and visibility",
    	"two": "Our agent will verify the authenticity of your product at no initial cost, furthermore a recorded proof of the assurance will be available in the buy page of that product",
    	"three": "If your product sells after being assured, we take a small assurance fee—otherwise, you pay nothing",
    	"four": "Assured listings get priority placement, increasing buyer trust and sales potential"
	},
	{
    	"question": "How does delivery work for buyers?",
    	"one": "Choose between online payment or Cash on Delivery (COD)",
    	"two": "COD orders require a nominal security deposit to ensure commitment",
    	"three": "The security deposit is adjusted in the final transaction",
    	"four": "If you reject the item upon delivery, the security deposit is retained to cover processing costs"
	},
	{
    	"question": "How does delivery work for sellers?",
    	"one": "You will be notified once your product is purchased",
    	"two": "We collect the item and provide a security fee upfront",
    	"three": "Once the transaction is completed, you receive the remaining balance",
    	"four": "If the order is canceled, we return your product in exchange for the security fee"
	},
]

    return render_template('faqs.html', faqs=faq_content)



@app.route('/search')
def search():
    query = request.args.get('q', '')
    search = f"%{query}%"
    
    base_filter = or_(
    Item.name.ilike(search),
    Item.sub_cat.ilike(search)
    )

# Apply filter based on authentication
    if current_user.is_authenticated:
        results = Item.query.filter(
            base_filter,
            Item.college == current_user.college).all()

        price_bounds = db.session.query(
            func.min(Item.price),
            func.max(Item.price)).filter(
                base_filter,
                Item.college == current_user.college).first()
    else:
        results = Item.query.filter(base_filter).all()
        price_bounds = db.session.query(
            func.min(Item.price),
            func.max(Item.price)
        ).filter(base_filter).first()

    sorted_items = sorted(results, key=lambda x: 0 if x.assured == 'Assured' else 1)
    min_price, max_price = price_bounds if price_bounds else (None, None)

    return render_template(
        'browse.html',
        items=sorted_items,
        query=query,
        min_price=min_price,
        max_price=max_price
    )
@app.route('/delete/<int:item_id>', methods=['GET','POST'])
def delete_item(item_id):
    item_to_delete = Item.query.get_or_404(item_id)  # Get the item by ID, or return 404 if not found
    try:
        files_to_remove = item_to_delete.pic_file_path.split(',')
        for file in files_to_remove:
            parsed_url = urlparse(file)
            key = parsed_url.path.lstrip('/')  # Remove leading '/'
            s3_client.delete_object(Bucket=app.config['AWS_S3_BUCKET_NAME'], Key=key)

        # Delete the object from the database 
        db.session.delete(item_to_delete)
        db.session.commit()
        flash('Item deleted successfully!', 'success')
        return redirect(url_for('dashboard'))  # Redirect back to the dashboard after deletion
    except:
        flash('There was a problem deleting that item', 'danger')
        return redirect(url_for('dashboard'))


@app.route('/buy/<int:item_id>',methods =['GET','POST'])
def buy(item_id):
    item = Item.query.get_or_404(item_id)
    if current_user.is_authenticated:
        cat_item = Item.query.filter(
            Item.category == item.category,
            Item.id != item.id,
            Item.user_id != current_user.id
        ).all()
        items = Item.query.filter(
            Item.category != item.category,
            Item.user_id != current_user.id
        ).all()
    else:
        cat_item = Item.query.filter(
            Item.category == item.category,
            Item.id != item.id
        ).all()
        items = Item.query.filter(Item.category != item.category).all()
    return render_template('buy.html',item=item,items= items,cat_item=cat_item)


@app.route('/dashboard', methods=['GET','POST'])
@login_required
def dashboard():
    user_items = Item.query.filter_by(user_id=current_user.id).all()
    pur_items = Purchase.query.filter_by(buyer_id = current_user.id).all()
    assure_items = assure_pending.query.filter_by(user_id = current_user.id).all()
    sold_items = Sold.query.filter_by(user_id = current_user.id).all()
    misc_items = Misc_Approval.query.filter_by(user_id = current_user.id).all()
    return render_template('dashboard.html', user=current_user,items = user_items,pur_items=pur_items,assure_items=assure_items,sold_items=sold_items,misc_items=misc_items)

@app.route("/contact")
def contact():
    # Renders the HTML template you provided
    return render_template("contact.html")


@app.route('/demand',methods= ['GET','POST'])
@login_required
def demand():
    form = DemandForm()
    if form.validate_on_submit():
        subcategory_mapping = {
            'Cycles': form.sub_cycle,
            'Electronics': form.sub_elec_acc,
            'Hostel Essentials': form.sub_hostel,
            'Mattress': form.sub_mat,
            'Watches': form.sub_watch,
            'Fitness & Sports': form.sub_sports,
            'Personal Accessories': form.sub_personal_acc,            
            'Appliances & Kitchenware': form.sub_elec_app,
            'Academic Accessories': form.sub_acad_acc,
            'Books': form.sub_books
        }
        selected_subcategory = subcategory_mapping.get(form.category.data, None)
        item = Demand(
            name = form.name.data,
            category = form.category.data,
            sub_cat = selected_subcategory.data,
            avg_price = form.avg_price.data,
            college = current_user.college,
            user_id = current_user.id,
            email = current_user.email
        )
        db.session.add(item)
        db.session.commit()
        flash('Demand Posted Successfully!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('demand.html', form=form)

@app.route('/demand-board',methods=['GET','POST'])
def demand_board():
    query = db.session.query(
                    Demand.sub_cat,
                    func.count(Demand.id).label('total_demands'))
    if current_user.is_authenticated:
        query = query.filter(Demand.college == current_user.college)

    if current_user.is_authenticated:
        demands = Demand.query.filter(Demand.college == current_user.college).all()
    else:
        demands = Demand.query.all()
    top_demands = query.group_by(Demand.sub_cat)\
                   .order_by(desc('total_demands'))\
                   .limit(4)\
                   .all()
    
    return render_template('demand_board.html',demands=demands,top_demands = top_demands,img_json = img_json)


@app.route('/survey',methods=['GET','POST'])
def survey():
    generate_survey_json()
    ref = request.args.get("ref")  # e.g., "kr"    
    return render_template('survey.html',ref=ref)


@app.route('/submit-survey', methods=['POST','GET'])
def submit_survey():
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"status": "error", "message": "No JSON data received"}), 400

    # Filter only keys where the value is not bool
    ref_code = data.pop('ref', None)
    college = data.pop('college', None)
    responses= {k: v for k, v in data.items() if isinstance(v, int) and not isinstance(v, bool)}

    try:
        survey_entry = SurveyResponse(response=responses,ref=ref_code,college=college)  # store only filtered

        db.session.add(survey_entry)
        db.session.commit()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500 

@app.route('/sell',methods=['GET', 'POST'])
@login_required
def sell():
    form = SellForm()

    if form.validate_on_submit():
        files = request.files.getlist(form.pic_file_path.name)  # Get multiple files from the form       
        uploaded_file_urls = []


        for file in files:
            if file.filename == '':
                flash('No Pic uploaded!', 'danger')
                return render_template('sell.html', user=current_user, form=form)

            if file.filename != '':
                # Convert to WEBP using Pillow
                original_filename = secure_filename(file.filename)
                img = Image.open(file.stream).convert('RGB')

                # Save to in-memory buffer
                buffer = BytesIO()
                img.save(buffer, format='WEBP', quality=85)
                buffer.seek(0)

                # Generate .webp filename
                webp_filename = os.path.splitext(original_filename)[0] + '.webp'

                # Upload to S3 from memory
                s3_url = upload_to_s3(buffer, app.config['AWS_S3_BUCKET_NAME'], 'item_pics/' + webp_filename, content_type='image/webp')
                if s3_url:
                    uploaded_file_urls.append(s3_url)

        session['uploaded_file_urls'] = uploaded_file_urls

        
        session['item_data'] = {
            'name': form.name.data,
            'category': form.category.data,
            'price': form.price.data,
            'age': form.age.data,
            'condition': form.condition.data,
            'description': form.description.data,
            'assured': form.assured.data,
            'college': current_user.college,
            'user_id': current_user.id,
            'pic_file_path' : ','.join(uploaded_file_urls)
        }
        subcategory_mapping = {
            'Cycles': form.sub_cycle,
            'Electronics': form.sub_elec_acc,
            'Hostel Essentials': form.sub_hostel,
            'Mattress': form.sub_mat,
            'Watches': form.sub_watch,
            'Fitness & Sports': form.sub_sports,
            'Personal Accessories': form.sub_personal_acc,            
            'Appliances & Kitchenware': form.sub_elec_app,
            'Academic Accessories': form.sub_acad_acc,
            'Books': form.sub_books
        }

        selected_category = form.category.data

        if selected_category == 'Miscellaneous':
            session['item_data']['misc_price'] = form.misc_price.data
            return redirect(url_for('misc_request'))




        fastapi_predict_endpoint = "https://past-perfect-fastapi-production.up.railway.app/predict"
        if selected_category in subcategory_mapping:
            subcategory_field = subcategory_mapping[selected_category]
            if subcategory_field.data:  # Ensure it has a valid value
                if subcategory_field.data == 'Other':
                    product_type = form.category.data
                else:

                    product_type = subcategory_field.data
                session['item_data']['sub_cat'] = product_type
                session['item_data']['product_type'] = product_type

        else:
            product_type = form.category.data
            session['item_data']['product_type'] = product_type
            
        original_price = form.price.data
        data = {
            "product_type": UI_TO_MODEL_PRODUCT_TYPE[product_type],
            "original_price": original_price
        }
        response = requests.post(fastapi_predict_endpoint, json=data)
        if response.status_code == 200:
            predicted_depreciation = response.json().get("predicted_depreciation")
            PRODUCT_DATA = {
                "calculator": (4, 0.179866),
                "chart_holder": (2, 0.185281),
                "clock": (2, 0.090915),
                "cooler": (2, 0.327731),
                "course_books": (2, 0.186528),
                "cycle": (2, 0.247447),
                "earbuds": (2, 0.356797),
                "ed_drafter": (2, 0.090915),
                "furniture": (4, 0.159071),
                "kettle": (4, 0.182433),
                "lab_coat": (2, 0.257554),
                "laptop_stand": (2, 0.378597),
                "mattress": (2, 0.356797),
                "mouse": (2, 0.273237),
                "novels": (2, 0.149594),
                "office_chair": (4, 0.167619),
                "power_bank": (4, 0.188699),
                "rack": (2, 0.214175),
                "sd_card": (4, 0.166538),
                "speaker": (4, 0.193313),
                "table_fan": (2, 0.083153),
                "watch": (2, 0.177434),
                "academic_accessories": (2, 0.185281),
                "electrical_accessories": (2, 0.149594),
                "electrical_appliances": (4, 0.193313),
                "books": (2, 0.083153),
            }
            category_impact = {
                "Books": 0.005,                    # Books degrade slowly unless damaged
                "Academic Accessories": 0.010,                    # Minor wear is fine
                "Electronics": 0.025,              # Usage affects electronics moderately
                "Watches": 0.020,                  # Cosmetic wear matters a bit
                "Personal Accessories": 0.030,     # Shoes/bags wear out visibly
                "Cycles": 0.030,                    # Significant wear possible
                "Mattresses": 0.045,               # Hygiene sensitive, loses value fast
                "Fitness & Sports": 0.025,         # Equipment wear matters
                "Hostel Essentials": 0.015,        # Functional items, moderate impact
                "Appliances & Kitchenware": 0.025, # Kitchen appliances lose shine with use
                }



            def age_cond_adjust(product_type, original_price,condition, predicted_price, age,category):
                """
                Calculate the adjusted price using stored product data.
                """
                if product_type not in PRODUCT_DATA:
                    raise ValueError("Invalid product type")
            
                base_year, k = PRODUCT_DATA[product_type]
                impact =   category_impact.get(category, 0.02)            
                adjusted_price_age = predicted_price * np.exp(-k * (age - base_year))
                adjusted_price_condition = adjusted_price_age*np.exp(-condition * impact)

                adjusted_price = min(adjusted_price_condition, original_price)

                return max(adjusted_price, 0)
            session['item_data']['pred_price']= round(age_cond_adjust(UI_TO_MODEL_PRODUCT_TYPE[product_type],original_price,int(form.condition.data),original_price-predicted_depreciation,form.age.data,selected_category),0)
            return redirect(url_for('order_summary'))
        
        return redirect(url_for('order_summary'))
    return render_template('sell.html',form = form,cond_desc = condition_descriptions)


@app.route('/misc-request', methods=['GET', 'POST'])
@login_required
def misc_request():
    item_data = session.get('item_data')

    if not item_data:
        flash('No item found!', 'danger')
        return redirect(url_for('sell'))
    
    new_item = Misc_Approval(
        name=item_data['name'],
        category=item_data['category'],
        og_price=item_data['price'],
        price=item_data['misc_price'],
        age=item_data['age'],
        condition=condition_descriptions[item_data['category']][item_data['condition']],
        description=item_data['description'],
        pic_file_path= ','.join(session.get('uploaded_file_urls', [])),
        assured=item_data['assured'],
        college=item_data['college'],
        user_id=item_data['user_id']
    )
    db.session.add(new_item)
    db.session.commit()
    en.send_misc_listing_approval_request(item_data['misc_price'],item_data['name'])
        
    flash('Miscellaneous Request submitted for approval successfully!', 'success')
    return redirect(url_for('dashboard'))



@app.route('/order-summary', methods=['GET', 'POST'])
@login_required
def order_summary():
    item_data = session.get('item_data')

    if not item_data:
        flash('No item found!', 'danger')
        return redirect(url_for('sell'))

    if item_data['assured'] == 'Assured':
        assured_price = round(min(0.05*item_data['pred_price'], 200),0)  
    else:
        assured_price =0

    

    if request.method == 'POST':
        action = request.form.get('action')
        preferred_price = request.form.get("pref_price")
        coupon_applied = request.form.get("coupon_applied") == "True" 
        if preferred_price == '':
            preferred_price = item_data['pred_price']
        preferred_price = float(preferred_price)
        if action == "pay":
            item_data['pred_price'] = preferred_price
            item_data['coupon_applied'] = "NOLIST" if coupon_applied else None  # Store coupon code or None
            session['item_data'] = item_data
            if not (coupon_applied):
                amount = 10

            
                merchant_order_id = str(uuid.uuid4())
                ui_redirect_url = f"https://www.past-perfect.in/confirm-listing?merchant_id={merchant_order_id}"  # Set this as redirect URL 

                standard_pay_request = StandardCheckoutPayRequest.build_request(
                    merchant_order_id=merchant_order_id,
                    amount= amount*100,  # Amount in paisa,
                    message=f"Payment for {item_data['name']}",
                    expire_after=300,
                    redirect_url=ui_redirect_url
                )

                standard_pay_response = standard_phonepe_client.pay(standard_pay_request)
                checkout_page_url = standard_pay_response.redirect_url  # Redirect user here
                return redirect(checkout_page_url)
            else:
                session['payment_status'] = 'Success'
            return redirect(url_for('confirm_listing'))
    
        elif action == "cancel":
        # Delete uploaded files
            uploaded_file_urls = session.get('uploaded_file_urls')
            if uploaded_file_urls:
            	for file_path in uploaded_file_urls:
                    parsed_url = urlparse(file_path)
                    key = parsed_url.path.lstrip('/')
                    s3_client.delete_object(Bucket=app.config['AWS_S3_BUCKET_NAME'], Key=key)
        # Clear session data
            session.pop('item_data', None)
            session.pop('uploaded_file_paths', None)
            flash("Payment canceled. Item was not listed.", "danger")
            return redirect(url_for('sell'))
        
        

    return render_template('order_summary.html', item=item_data, listing_fee=10, assured_price=assured_price, discount=100) 


@app.route('/confirm-listing')
@login_required
def confirm_listing():
    merchant_order_id = request.args.get('merchant_id')
    response = standard_phonepe_client.get_order_status(merchant_order_id, details=False)

    state = response.state
    if state!= "COMPLETED":
        flash('Payment failed or pending. Try again.', 'danger')
        session.pop('item_data', None)
        session.pop('uploaded_file_paths', None)
        return redirect(url_for('sell'))
    if state == "COMPLETED":
        session['payment_status'] = 'Success'


    if session.get('payment_status') != 'Success':
        flash('Payment required!', 'danger')

        # Delete uploaded files if payment was not made
        uploaded_file_urls = session.get('uploaded_file_urls')
        if uploaded_file_urls:
            for file_path in uploaded_file_urls:
                parsed_url = urlparse(file_path)
                key = parsed_url.path.lstrip('/')
                s3_client.delete_object(Bucket=app.config['AWS_S3_BUCKET_NAME'], Key=key)

        # Clear session data
        session.pop('item_data', None)
        session.pop('payment_status', None)
        session.pop('uploaded_file_paths', None)

        return redirect(url_for('sell'))

    item_data = session.get('item_data')
    if not item_data:
        flash('Item details missing!', 'danger')
        return redirect(url_for('sell'))
    uploaded_file_urls = session.get('uploaded_file_urls')

    # Save item in database
    if item_data['assured'] == 'Assured':
        new_item = assure_pending(
            name=item_data['name'],
            category=item_data['category'],
            price=item_data['pred_price'],
            og_price=item_data['price'],
            age=item_data['age'],
            condition=condition_descriptions[item_data['category']][item_data['condition']],
            description=item_data['description'],
            pic_file_path= ','.join(uploaded_file_urls),
            assured='pending',
            sub_cat = item_data['sub_cat'],
            college = item_data['college'],
            email = current_user.email,
            mobile = current_user.mobile_no,
            user_id=item_data['user_id'],
            coupon_applied=item_data['coupon_applied']  # Save coupon status
        )
    else:
        new_item = Item(
            name=item_data['name'],
            category=item_data['category'],
            price=item_data['pred_price'],
            og_price=item_data['price'],
            age=item_data['age'],
            condition=condition_descriptions[item_data['category']][item_data['condition']],
            description=item_data['description'],
            pic_file_path= ','.join(uploaded_file_urls),
            assured=item_data['assured'],
            college = item_data['college'],
            sub_cat = item_data['sub_cat'],
            user_id=item_data['user_id'],
            coupon_applied=item_data['coupon_applied']  # Save coupon status
        )
    db.session.add(new_item)
    db.session.commit()

    is_assured = item_data['assured'] == 'Assured'
    user_email= User.query.filter_by(id=item_data['user_id']).first().email
    en.send_listing_confirmation(user_email,item_data['pred_price'],is_assured)

    if is_assured:
        flash('Item sent for assurance approval and confirmation mail sent!', 'success')
    else:
        flash('Item successfully listed and confirmation mail sent!', 'success')
    # Clear session data
   
    session.pop('item_data', None)
    session.pop('payment_status', None)
    session.pop('uploaded_file_urls', None)

    return redirect(url_for('dashboard'))

@app.route('/confirm-purchase', methods=['POST','GET'])
@login_required
def confirm_purchase():

    item_id = request.args.get('item_id') or session.get('purchase_data', {}).get('item_id')

    if not item_id:
        flash("Invalid transaction!", "danger")
        return redirect(url_for('home'))

    item = Item.query.get(item_id)
    if (item.college != current_user.college):
        flash("You can only purchase items from your college!", "danger")
        return redirect(url_for('home'))

    if not item:
        flash("Item not found!", "danger")
        return redirect(url_for('home'))

    session['sale_data'] = {
        'name':item.name,
        'category': item.category,
        'sub_cat': item.sub_cat,
        'price': item.price,
        'og_price': item.og_price,
        'vid': item.vid,
        'age': item.age,
        'condition': item.condition,
        'description': item.description,
        'buyer_id': current_user.id,
        'user_id': item.user_id,
        'pic_file_path': item.pic_file_path,
        'assured': item.assured,
        'college': item.college
    }
    
  
    # Calculate total amount (example calculation)
    
    
    if item.category == 'Mattress':
        if item.price <= 1000:
            delivery_fee = 30
        else:
            delivery_fee = 50
    else:
        delivery_fee = 20
    platform_fee = 10
    discount = 100

	  # Store item details in session
    session['purchase_data'] = {
        'item_id': item.id,
        'price': item.price,
        'buyer_id': current_user.id,
        'seller_id': item.user_id,
        'pic_file_path': item.pic_file_path,
        'name':item.name,
        'category': item.category,
        'sub_cat': item.sub_cat,
        'vid': item.vid,
        'age': item.age,
        'condition': item.condition,
        'assured': item.assured,
        'og_price': item.og_price,
        'description': item.description,
        'college': item.college,
		'delivery_fee': delivery_fee,
        'platform_fee': platform_fee,
        'discount': discount
    }
    session['user_id'] = current_user.id



    if request.method == 'POST':
        action = request.form.get('action')
        payment_method = request.form.get('payment_method', 'upi')
        coupon_code = request.form.get('coupon_code', '').strip().upper()
        discount_applied = coupon_code == 'NOPLAT'
        discount_amount = discount if discount_applied else 0
        session['purchase_data']['payment_method'] = payment_method
        session['purchase_data']['discount_applied'] = discount_applied
        session['purchase_data']['discount_amount'] = discount_amount
        if action == "pay":
            
            total = request.form.get('totalAmount')
            # Convert to float or int if needed
            amount = float(total)

            merchant_order_id = str(uuid.uuid4())
            ui_redirect_url = f"https://www.past-perfect.in/finalize-purchase?merchant_id={merchant_order_id}"  # Set this as redirect URL 

            standard_pay_request = StandardCheckoutPayRequest.build_request(
                merchant_order_id=merchant_order_id,
                amount= amount*100,  # Amount in paisa,
                message=f"Payment for {item.name}",
                expire_after=300,
                redirect_url=ui_redirect_url
            )

            standard_pay_response = standard_phonepe_client.pay(standard_pay_request)
            checkout_page_url = standard_pay_response.redirect_url  # Redirect user here
            return redirect(checkout_page_url)

        
        if action == "cancel":
            flash("Payment canceled. Item was not purchased.", "danger")
            session.pop('purchase_data', None)
            session.pop('sale_data', None)
            return redirect(url_for('home'))

    


    return render_template('confirm_purchase.html', 
                           item=item, 
                           delivery_fee=delivery_fee, 
                           platform_fee=platform_fee,
                           discount = discount
                        )


@app.route('/finalize-purchase', methods=['POST','GET'])
def finalize_purchase():
    # session.permanent = True
    # user_id = session.get('user_id')
    # if user_id:
    #     user = User.query.get(user_id)
    #     if user:
    #         login_user(user)  # Restore login
    merchant_order_id = request.args.get('merchant_id')
    response = standard_phonepe_client.get_order_status(merchant_order_id, details=False)

    state = response.state
    
    if state != "COMPLETED":
        flash('Payment failed or pending. Try again.', 'danger')
        session.pop('purchase_data', None)
        session.pop('sale_data', None)
        return redirect(url_for('home'))

    purchase_data = session.get('purchase_data',None)
    sale_data = session.get('sale_data',None)

    if not purchase_data:
        flash('Invalid transaction! If payment done, will be refunded within 1-2 Business Days', 'danger')
        return redirect(url_for('home'))
    

    # Store purchase in database
    new_purchase = Purchase(
        buyer_id=current_user.id,
        sub_cat=purchase_data['sub_cat'],
        vid=purchase_data['vid'],
        og_price=purchase_data['og_price'],
        assured=purchase_data['assured'],
        age=purchase_data['age'],
        condition=purchase_data['condition'],
        purchase_price=purchase_data['price'],
        seller_id=purchase_data['seller_id'],
        pic_file_path=purchase_data['pic_file_path'],
        name=purchase_data['name'],
        category=purchase_data['category'],
        description=purchase_data['description'],
        college=purchase_data['college'],
		delivery_fee=purchase_data['delivery_fee'],
        platform_fee=purchase_data['platform_fee'],
        discount_applied=purchase_data['discount_applied'],
        discount_amount=purchase_data['discount_amount'],
        payment_method=purchase_data['payment_method']
    )

    new_sale = Sold(
        name=sale_data['name'],
        category=sale_data['category'],
        sub_cat=sale_data['sub_cat'],
        vid=sale_data['vid'],
        buyer_id=current_user.id,
        price=sale_data['price'],

        og_price=sale_data['og_price'],
        age=sale_data['age'],
        condition=sale_data['condition'],
        description=sale_data['description'],
        
        pic_file_path=sale_data['pic_file_path'],
        assured=sale_data['assured'],
        college=sale_data['college'],
        user_id=sale_data['user_id'],
		coupon_applied=sale_data.get('coupon_applied', None)  # Save coupon status if exists
    )
    item = Item.query.get(purchase_data['item_id'])

    if item:
        db.session.delete(item)  # Ensure item exists before deleting
    
    db.session.add(new_purchase)
    db.session.add(new_sale)
    db.session.commit()


    # Send confirmation emails
    en.send_product_sold_notification(
        User.query.filter_by(id=purchase_data['seller_id']).first().email,
        purchase_data['name'], purchase_data['price']
    )
    en.send_order_confirmation(
        User.query.filter_by(id=current_user.id).first().email,
        purchase_data['name'], purchase_data['price']
    )
    # Now remove session data after checking
    flash('Purchase successful and confirmation mail sent!', 'success')
    session.pop('purchase_data', None)
    session.pop('sale_data', None)

    
    return redirect(url_for('dashboard'))



@app.route('/logout',methods=['GET','POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


#Delivery Code Starts here
def get_next_sunday():
    today = datetime.today()
    days_ahead = 6 - today.weekday()  # Sunday is 6
    if days_ahead <= 0:
        days_ahead += 7
    next_sunday = today + timedelta(days=days_ahead)
    return next_sunday.date()

@app.route('/delivery-dashboard')
@login_required
def delivery_dashboard():
    colleges = dp[current_user.email]['allowed_colleges']
    orders = Purchase.query.filter_by(status='Out for Delivery', college=colleges).filter(Purchase.otp.isnot(None)).all()
    order_details = []
    for purchase in orders:
        buyer = User.query.get(purchase.buyer_id)
        seller = User.query.get(purchase.seller_id)
        
        delivery_fee = purchase.delivery_fee if purchase.delivery_fee is not None else 0
        assurance_fee = round(min(0.05 * purchase.purchase_price, 200), 0) if purchase.assured == 'Assured' else 0
        platform_fee = 0 if purchase.discount_applied else 10
        
        if purchase.payment_method == 'upi':
            money_paid_by_buyer = 0
            money_to_seller = purchase.purchase_price - assurance_fee
        
        elif purchase.payment_method == 'cod':
            money_paid_by_buyer = purchase.purchase_price
            money_to_seller = purchase.purchase_price - assurance_fee
        
        order_details.append({
            'buyer_phone': buyer.mobile_no if buyer else 'Not provided',
            'buyer_name': buyer.username if buyer else 'Not provided',
            'buyer_email': buyer.email if buyer else 'Not provided',
            'seller_phone': seller.mobile_no if seller else 'Not provided',
            'seller_name': seller.username if seller else 'Not provided',
            'seller_address': seller.address if seller else 'Not provided',
            'buyer_address': buyer.address if buyer else 'Not provided',
            'money_from_buyer': money_paid_by_buyer,
            'money_to_seller': money_to_seller,
            'delivery_fee': delivery_fee,
            'assurance_fee': assurance_fee,
            'platform_fee': platform_fee,
            'item_name': purchase.name,
            'purchase_id': purchase.id,
            'status': purchase.status,
            'college': purchase.college,
            'otp':purchase.otp
        })
    



    return render_template('delivery.html',orders=order_details,del_date=get_next_sunday())



# Mark delivered route
@app.route('/mark-delivered/<int:purchase_id>', methods=['POST'])
@login_required
def mark_delivered(purchase_id, allowed_college=None):
    purchase = Purchase.query.get_or_404(purchase_id)
    sold=Sold.query.filter_by(buyer_id=purchase.buyer_id, user_id=purchase.seller_id, name=purchase.name).first()
    
    
    if purchase.status == 'Delivered':
        flash('Order is already marked as Delivered.', 'warning')
        return redirect(url_for('delivery_dashboard'))
    
    try:
        purchase.status = 'Delivered'
        if sold:
            sold.status = 'Delivered'
        
        db.session.commit()
        buyer = User.query.get(purchase.buyer_id)
        if buyer and buyer.email:
            en.send_delivery_confirmation(buyer.email)
        flash('Order marked as Delivered successfully!', 'success')
    except Exception as e:
        flash(f'Error updating order status: {str(e)}', 'danger')
    
    return redirect(url_for('delivery_dashboard'))





#Admin panel code



# Admin and Campus Ambassador Configurations
ADMIN_EMAILS = ['Abhinavharrygo@gmail.com', 'admin2@example.com', 'superadmin@example.com']  # Add your admin emails here
# Changed from usernames to emails for campus ambassador access
CAMPUS_AMBASSADORS = {
    'ambassador1@example.com': 'kgp',
    'ambassador2@example.com': 'bhu',
	'rkumkum16052006@gmail.com': 'lucknowuniversity',
	'Abhinav.cqiitkgp@gmail.com': 'lucknowuniversity'
    # Add more mappings here
}

COLLEGES = [
    ('kgp', 'IIT Kharagpur'),
    ('bhu', 'IIT Varanasi'),
	('lucknowuniversity', 'Lucknow University')
]


# Decorators
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.email not in ADMIN_EMAILS:
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

def campus_ambassador_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'danger')
            return redirect(url_for('login'))
        
        # Check if the user is a campus ambassador or admin
        if current_user.email not in CAMPUS_AMBASSADORS and current_user.email not in ADMIN_EMAILS:
            flash('Access denied. Campus ambassador or admin privileges required.', 'danger')
            return redirect(url_for('home'))
        
        # If the user is a campus ambassador, store their college for filtering
        if current_user.email in CAMPUS_AMBASSADORS:
            kwargs['allowed_college'] = CAMPUS_AMBASSADORS[current_user.email]
        else:
            kwargs['allowed_college'] = None  # Admins can access all colleges
        
        return f(*args, **kwargs)
    return decorated_function



# Admin Panel Routes


@app.route('/admin/dashboard')
@login_required
@campus_ambassador_required
def admin_dashboard(allowed_college=None):
    query_filter = {} if allowed_college is None else {'college': allowed_college}
    
    # Use IST time zone (UTC+5:30)
    utc_offset = timedelta(hours=5, minutes=30)
    current_date = datetime.utcnow() + utc_offset
    start_of_day = current_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1) - timedelta(seconds=1)
    start_of_month = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end_of_month = (start_of_month + timedelta(days=31)).replace(day=1) - timedelta(seconds=1)
    
    # Total counts
    total_users = User.query.filter_by(**query_filter).count()
    total_active_items = Item.query.filter_by(**query_filter).count()  # Active listings
    total_listings = total_active_items + Sold.query.filter_by(**query_filter).count()  # Active + inactive
    total_misc_approvals = Misc_Approval.query.filter_by(status='Pending', **query_filter).count()
    total_assure_pending = assure_pending.query.filter_by(**query_filter).count()
    total_delivery_pending = Purchase.query.filter_by(status='Pending', **query_filter).count()
    total_sales = Sold.query.filter_by(**query_filter).count()
    
    # Monthly counts
    monthly_users = User.query.filter_by(**query_filter).filter(
        User.created_at >= start_of_month,
        User.created_at <= end_of_month
    ).count()
    
    monthly_sales = Sold.query.filter_by(**query_filter).filter(
        Sold.created_at >= start_of_month,
        Sold.created_at <= end_of_month
    ).count()
    
    monthly_items_active = Item.query.filter_by(**query_filter).filter(
        Item.created_at >= start_of_month,
        Item.created_at <= end_of_month
    ).count()
    monthly_items_sold = Sold.query.filter_by(**query_filter).filter(
        Sold.created_at >= start_of_month,
        Sold.created_at <= end_of_month
    ).count()
    monthly_items = monthly_items_active + monthly_items_sold  # Active + inactive for the month

    # Daily counts
    daily_users_query = User.query.filter_by(**query_filter).filter(
        User.created_at >= start_of_day,
        User.created_at <= end_of_day
    )
    daily_users = daily_users_query.count()
    
    daily_sales_query = Sold.query.filter_by(**query_filter).filter(
        Sold.created_at >= start_of_day,
        Sold.created_at <= end_of_day
    )
    daily_sales = daily_sales_query.count()
    
    daily_items_active = Item.query.filter_by(**query_filter).filter(
        Item.created_at >= start_of_day,
        Item.created_at <= end_of_day
    ).count()
    daily_items_sold = Sold.query.filter_by(**query_filter).filter(
        Sold.created_at >= start_of_day,
        Sold.created_at <= end_of_day
    ).count()
    daily_items = daily_items_active + daily_items_sold  # Active + inactive for the day

    # Revenue and Profit Calculations
    # Total Revenue
    total_purchase_query = Purchase.query.filter_by(**query_filter)
    total_delivery_fee = 0
    total_platform_fee = 0
    total_listing_fee = 0
    total_assurance_fee = 0
    monthly_delivery_fee = 0
    monthly_platform_fee = 0
    monthly_listing_fee = 0
    monthly_assurance_fee = 0
    daily_delivery_fee = 0
    daily_platform_fee = 0
    daily_listing_fee = 0
    daily_assurance_fee = 0
    
    for sale in total_purchase_query:
        total_delivery_fee += sale.delivery_fee
        if not sale.discount_applied:
            total_platform_fee += sale.platform_fee
        else:
            total_platform_fee += 0  # 100% discount applied
        
        if sale.assured == 'Assured':
            total_assurance_fee += round(min(0.05 * sale.purchase_price, 200), 0)
        else:
            total_assurance_fee += 0
        
    total_sold_query = Sold.query.filter_by(**query_filter)
    total_item_query = Item.query.filter_by(**query_filter)
    for item in total_item_query:
        total_listing_fee += 0 if item.coupon_applied == 'NOLIST' else 10
        
    for sale in total_sold_query:
        if sale.coupon_applied == 'NOLIST':
            total_listing_fee += 0
        else:
            total_listing_fee += 10
    
    total_revenue = total_listing_fee + total_platform_fee + total_delivery_fee + total_assurance_fee 

    monthly_sold_query = Sold.query.filter_by(**query_filter).filter(
        Sold.created_at >= start_of_month,
        Sold.created_at <= end_of_month
    )
    monthly_item_query = Item.query.filter_by(**query_filter).filter(
        Item.created_at >= start_of_month,
        Item.created_at <= end_of_month
    )
    for item in monthly_item_query:
        monthly_listing_fee += 0 if item.coupon_applied == 'NOLIST' else 10
    
    for sale in monthly_sold_query:
        if sale.coupon_applied == 'NOLIST':
            monthly_listing_fee += 0
        else:
            monthly_listing_fee += 10

    daily_sold_query = Sold.query.filter_by(**query_filter).filter(
        Sold.created_at >= start_of_day,
        Sold.created_at <= end_of_day
    )
    for sale in daily_sold_query:
        if sale.coupon_applied == 'NOLIST':
            daily_listing_fee += 0
        else:
            daily_listing_fee += 10

    daily_item_query = Item.query.filter_by(**query_filter).filter(
        Item.created_at >= start_of_day,
        Item.created_at <= end_of_day
    )
    for item in daily_item_query:
        daily_listing_fee += 0 if item.coupon_applied == 'NOLIST' else 10
        
    monthly_purchase_query = Purchase.query.filter_by(**query_filter).filter(
        Purchase.purchase_date >= start_of_month,
        Purchase.purchase_date <= end_of_month
    )
    for sale in monthly_purchase_query:
        monthly_delivery_fee += sale.delivery_fee
        if not sale.discount_applied:
            monthly_platform_fee += sale.platform_fee
        else:
            monthly_platform_fee += 0
        
        if sale.assured == 'Assured':
            monthly_assurance_fee += round(min(0.05 * sale.purchase_price, 200), 0)
        else:
            monthly_assurance_fee += 0
            
    monthly_revenue = monthly_listing_fee + monthly_platform_fee + monthly_delivery_fee + monthly_assurance_fee
    
    daily_purchase_query = Purchase.query.filter_by(**query_filter).filter(
        Purchase.purchase_date >= start_of_day,
        Purchase.purchase_date <= end_of_day
    )
   
   
    for sale in daily_purchase_query:
        daily_delivery_fee += sale.delivery_fee
        if not sale.discount_applied:
            daily_platform_fee += sale.platform_fee
        else:
            daily_platform_fee += 0
        
        if sale.assured == 'Assured':
            daily_assurance_fee += round(min(0.05 * sale.purchase_price, 200), 0)
        else:
            daily_assurance_fee += 0
            
    daily_revenue = daily_listing_fee + daily_platform_fee + daily_delivery_fee + daily_assurance_fee

    total_profit = (3*(total_revenue - total_platform_fee-total_delivery_fee)/4)+total_platform_fee
    monthly_profit = (3*(monthly_revenue - monthly_platform_fee-monthly_delivery_fee)/4)+monthly_platform_fee
    daily_profit = (3*(daily_revenue - daily_platform_fee-daily_delivery_fee)/4)+daily_platform_fee

    visitor_stats = None
    if current_user.email in ADMIN_EMAILS:
        last_7_days = [(current_date - timedelta(days=x)).date() for x in range(6, -1, -1)]
        visitor_stats = []
        for date in last_7_days:
            visitor = Visitor.query.filter_by(date=date).first()
            visitor_stats.append({
                'date': date,
                'count': visitor.visit_count if visitor else 0
            })

    return render_template('admin_dashboard.html',
                            total_users=total_users,
                            total_active_items=total_active_items,
                            total_listings=total_listings,
                            total_misc_approvals=total_misc_approvals,
                            total_assure_pending=total_assure_pending,
                            total_delivery_pending=total_delivery_pending,
                            total_sales=total_sales,
                            monthly_users=monthly_users,
                            monthly_sales=monthly_sales,
                            monthly_items=monthly_items,
                            daily_users=daily_users,
                            daily_sales=daily_sales,
                            daily_items=daily_items,
                            total_revenue=total_revenue if Purchase.status != 'Pending' else total_listing_fee,
                            monthly_revenue=monthly_revenue if Purchase.status != 'Pending' else monthly_listing_fee,
                            daily_revenue=daily_revenue if Purchase.status != 'Pending' else daily_listing_fee,
                            total_profit=total_profit if Purchase.status != 'Pending' else 0,
                            monthly_profit=monthly_profit if Purchase.status != 'Pending' else 0,
                            daily_profit=daily_profit if Purchase.status != 'Pending' else 0,
                            daily_items_active=daily_items_active,
                            visitor_stats=visitor_stats if visitor_stats else [],
                            allowed_college=allowed_college)    


# Admin orders placed route with debugging
@app.route('/admin/orders_placed', methods=['GET', 'POST'])
@login_required
@campus_ambassador_required
def admin_orders_placed(allowed_college=None):
    # Handle college filter form submission
    if request.method == 'POST':
        college_filter = request.form.get('college_filter', 'all').strip().lower()
        session['college_filter'] = college_filter
    else:
        college_filter = session.get('college_filter', 'all').strip().lower()
    
    
    
    # Build the query
    query = Purchase.query.join(User, Purchase.seller_id == User.id)
    
    # Apply college filter
    if allowed_college:
        query = query.filter(Purchase.college.ilike(allowed_college.strip().lower()))
    elif college_filter != 'all':
        query = query.filter(Purchase.college.ilike(college_filter.strip().lower()))
    
    # Apply status filter (Pending or Out for Delivery)
    query = query.filter(Purchase.status.in_(['Pending', 'Out for Delivery']))
    
    
    
    # Get orders
    orders = query.all()
    
    order_details = []
    for purchase in orders:
        buyer = User.query.get(purchase.buyer_id)
        seller = User.query.get(purchase.seller_id)
        
        delivery_fee = purchase.delivery_fee if purchase.delivery_fee is not None else 0
        assurance_fee = round(min(0.05 * purchase.purchase_price, 200), 0) if purchase.assured == 'Assured' else 0
        platform_fee = 0 if purchase.discount_applied else 10
        
        if purchase.payment_method == 'upi':
            money_paid_by_buyer = 0
            money_to_seller = purchase.purchase_price - assurance_fee
        
        elif purchase.payment_method == 'cod':
            money_paid_by_buyer = purchase.purchase_price
            money_to_seller = purchase.purchase_price - assurance_fee
        
        order_details.append({
            'buyer_phone': buyer.mobile_no if buyer else 'Not provided',
            'buyer_name': buyer.username if buyer else 'Not provided',
            'buyer_email': buyer.email if buyer else 'Not provided',
            'seller_phone': seller.mobile_no if seller else 'Not provided',
            'seller_name': seller.username if seller else 'Not provided',
            'seller_address': seller.address if seller else 'Not provided',
            'buyer_address': buyer.address if buyer else 'Not provided',
            'money_paid_by_buyer': money_paid_by_buyer,
            'money_to_seller': money_to_seller,
            'delivery_fee': delivery_fee,
            'assurance_fee': assurance_fee,
            'platform_fee': platform_fee,
            'item_name': purchase.name,
            'purchase_id': purchase.id,
            'status': purchase.status,
            'college': purchase.college
        })
    
    
    return render_template('admin_orders_placed.html', 
                            orders=order_details, 
                            colleges=COLLEGES, 
                            admin_emails=ADMIN_EMAILS, 
                            college_filter=college_filter)
    
    
    

# Send delivery OTP route
@app.route('/admin/send-delivery-otp/<int:purchase_id>', methods=['POST'])
@login_required
@campus_ambassador_required
def send_delivery_otp(purchase_id, allowed_college=None):
    purchase = Purchase.query.get_or_404(purchase_id)
    sold = Sold.query.filter_by(buyer_id=purchase.buyer_id, user_id=purchase.seller_id, name=purchase.name).first()
    
    college_filter = session.get('college_filter', 'all')
    if allowed_college and purchase.college != allowed_college:
        flash('Access denied. You can only update orders for your college.', 'danger')
        return redirect(url_for('admin_orders_placed'))
    if allowed_college is None and college_filter != 'all' and purchase.college != college_filter:
        flash('Access denied. Order does not match selected college filter.', 'danger')
        return redirect(url_for('admin_orders_placed'))
    
    if purchase.status != 'Pending':
        flash('OTP can only be sent for Pending orders.', 'warning')
        return redirect(url_for('admin_orders_placed'))
    
    try:
        # Generate 6-digit OTP
        otp = en.generate_otp()
        
        # Store OTP in the purchase record
        purchase.otp = otp
        purchase.status = 'Out for Delivery'
        if sold:
            sold.status = 'Out for Pickup'
        
        db.session.commit()
        
        # Get delivery person email
        delivery_person_email = dp[purchase.college]['email']
        if not delivery_person_email:
            flash('No delivery person assigned for this college.', 'danger')
            return redirect(url_for('admin_orders_placed'))
        
        # Send OTP to buyer
        buyer = User.query.get(purchase.buyer_id)
        seller = User.query.get(purchase.seller_id)
        if seller and seller.email:
            en.send_pickup_otp_notification(seller.email, purchase.name, otp, is_delivery_person=False)

        if buyer and buyer.email:
            en.send_delivery_otp_notification(buyer.email, purchase.name, otp, is_delivery_person=False)
        
        # Send OTP to delivery person
        en.send_delivery_otp_notification(delivery_person_email, purchase.name, otp, is_delivery_person=True)
        
        flash('OTP sent successfully to buyer and delivery person!', 'success')
    except Exception as e:
        flash(f'Error sending OTP: {str(e)}', 'danger')
    
    return redirect(url_for('admin_orders_placed'))

# Delete order route
@app.route('/admin/delete-order/<int:purchase_id>', methods=['POST'])
@login_required
@campus_ambassador_required
def admin_delete_order(purchase_id, allowed_college=None):
    purchase = Purchase.query.get_or_404(purchase_id)
    
    if allowed_college and purchase.college != allowed_college:
        flash('Access denied. You can only delete orders for your college.', 'danger')
        return redirect(url_for('admin_orders_placed'))
    
    try:
        db.session.delete(purchase)
        db.session.commit()
        flash('Order deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting order: {str(e)}', 'danger')
    
    return redirect(url_for('admin_orders_placed'))

@app.route('/admin/delivered_products')
@login_required
@campus_ambassador_required
def admin_delivered_products(allowed_college=None):
    search_query= request.args.get('search_query', '').strip().lower()
    if search_query:
        search_term = f"%{search_query}%"
        query=query.filter
    else:
        search_query = session.get('search_query', '').strip().lower()
    
    college_filter = session.get('college_filter', 'all')
    if allowed_college:
        query_filter = {'college': allowed_college, 'status': 'Delivered'}
    else:
        query_filter = {'college': college_filter, 'status': 'Delivered'} if college_filter != 'all' else {'status': 'Delivered'}
    
    # Query purchases and join with User for buyer and seller details
    orders = Purchase.query.filter_by(**query_filter).all()
    
    order_details = []
    for purchase in orders:
        # Get buyer and seller details
        buyer = User.query.get(purchase.buyer_id)
        seller = User.query.get(purchase.seller_id)
        
        delivery_fee = purchase.delivery_fee if purchase.delivery_fee is not None else 0
        # Calculate fees based on Purchase data
        if purchase.assured == 'Assured':
            assurance_fee = round(min(0.05 * purchase.purchase_price, 200), 0)
        elif purchase.assured == 'Not Assured':
            assurance_fee = 0
        
        if purchase.discount_applied:
            platform_fee = 0
        else:
            platform_fee = 10
        
        if purchase.payment_method == 'upi':
            money_paid_by_buyer = 0
            money_to_seller = purchase.purchase_price - assurance_fee
        
        elif purchase.payment_method == 'cod':
            money_paid_by_buyer = purchase.purchase_price
            money_to_seller = purchase.purchase_price - assurance_fee
            
        order_details.append({
            'buyer_phone': buyer.mobile_no if buyer else 'Not provided',
            'seller_phone': seller.mobile_no if seller else 'not provided',
            'buyer_address': buyer.address if buyer else 'Not provided',
            'seller_address': seller.address if seller else 'Not provided',
            'money_paid_by_buyer': money_paid_by_buyer,
            'money_to_seller': money_to_seller,
            'delivery_fee': delivery_fee,
            'assurance_fee': assurance_fee,
            'platform_fee': platform_fee,
            'item_name': purchase.name,
            'purchase_id': purchase.id,
            'status': purchase.status
        })
    
    return render_template('admin_delivered_products.html', orders=order_details)


@app.route('/admin/listed-items', methods=['GET', 'POST'])
@login_required
@campus_ambassador_required
def admin_listed_items(allowed_college=None):
    search_query = request.form.get('search', '') if request.method == 'POST' else request.args.get('search', '')
    
    query = Item.query.join(User, Item.user_id == User.id)
    if allowed_college:
        query = query.filter(Item.college == allowed_college)
    if search_query:
        search_term = f"%{search_query}%"
        query = query.filter(
            (Item.name.ilike(search_term)) |
            (Item.price.ilike(search_term)) |
            (User.username.ilike(search_term)) |
            (User.email.ilike(search_term)) |
            (User.mobile_no.ilike(search_term)) |
            (Item.college.ilike(search_term))
        )
    
    items = query.order_by(Item.created_at.desc()).all()
    return render_template('admin_listed_items.html', items=items, admin_emails=ADMIN_EMAILS, 
                          campus_ambassadors=CAMPUS_AMBASSADORS, search_query=search_query)


@app.route('/admin/report-item/<int:item_id>', methods=['POST'])
@login_required
@campus_ambassador_required
def admin_report_item(item_id, allowed_college=None):
    item = Item.query.get_or_404(item_id)
    
    if allowed_college and item.college != allowed_college:
        flash('Access denied. You can only report items for your college.', 'danger')
        return redirect(url_for('admin_listed_items'))
    
    try:
        item.is_reported = True
        db.session.commit()
        flash('Item reported successfully!', 'success')
    except Exception as e:
        flash(f'Error reporting item: {str(e)}', 'danger')
    
    return redirect(url_for('admin_listed_items'))

@app.route('/admin/delete-item/<int:item_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_item(item_id):
    item = Item.query.get_or_404(item_id)
    
    try:
        files_to_remove = item.pic_file_path.split(',')
        for file in files_to_remove:
                parsed_url = urlparse(file)
                key = parsed_url.path.lstrip('/')  # Remove leading '/'
                s3_client.delete_object(Bucket=app.config['AWS_S3_BUCKET_NAME'], Key=key)
        db.session.delete(item)
        db.session.commit()
        flash('Item deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting item: {str(e)}', 'danger')
    
    return redirect(url_for('admin_listed_items'))



@app.route('/admin/users', methods=['GET', 'POST'])
@login_required
@campus_ambassador_required
def admin_users(allowed_college=None):
    search_query = request.form.get('search', '') if request.method == 'POST' else request.args.get('search', '')
    
    query = User.query
    if allowed_college:
        query = query.filter(User.college == allowed_college)
    if search_query:
        search_term = f"%{search_query}%"
        query = query.filter(
            (User.username.ilike(search_term)) |
            (User.email.ilike(search_term)) |
            (User.mobile_no.ilike(search_term)) |
            (User.address.ilike(search_term)) |
            (User.college.ilike(search_term))
        )
    
    users = query.order_by(User.id.asc()).all()
    return render_template('admin_users.html', users=users, search_query=search_query, admin_emails=ADMIN_EMAILS)


@app.route('/admin/delete-user/<int:user_id>', methods=['POST'])
@login_required
@campus_ambassador_required
def admin_delete_user(user_id, allowed_college=None):
    user = User.query.get_or_404(user_id)
    if allowed_college and user.college != allowed_college:
        flash('Access denied. You can only delete users from your college.', 'danger')
        return redirect(url_for('admin_users'))
    if user.email in ADMIN_EMAILS or user.email in CAMPUS_AMBASSADORS:
        flash('Cannot delete admin or campus ambassador accounts.', 'danger')
        return redirect(url_for('admin_users'))
    try:
        # # Delete user's profile picture if it exists
        # if user.profile_pic and os.path.exists(user.profile_pic):
        #     os.remove(user.profile_pic)
        # Delete associated items
        items = Item.query.filter_by(user_id=user_id).all()
        for item in items:
            files_to_remove = item.pic_file_path.split(',')
            for file in files_to_remove:
                parsed_url = urlparse(file)
                key = parsed_url.path.lstrip('/')  # Remove leading '/'
                s3_client.delete_object(Bucket=app.config['AWS_S3_BUCKET_NAME'], Key=key)

            # Delete the object from the database 
            db.session.delete(item)
            db.session.commit()
        # Delete associated misc approvals
        misc_approvals = Misc_Approval.query.filter_by(user_id=user_id).all()
        for misc in misc_approvals:
            files_to_remove = misc.pic_file_path.split(',')
            for file in files_to_remove:
                parsed_url = urlparse(file)
                key = parsed_url.path.lstrip('/')  # Remove leading '/'
                s3_client.delete_object(Bucket=app.config['AWS_S3_BUCKET_NAME'], Key=key)
            db.session.delete(misc)
            db.session.commit()
        # Delete associated assured pending items
        assured_pendings = assure_pending.query.filter_by(user_id=user_id).all()
        for assured in assured_pendings:
            files_to_remove = assured.pic_file_path.split(',')
            for file in files_to_remove:
                parsed_url = urlparse(file)
                key = parsed_url.path.lstrip('/')  # Remove leading '/'
                s3_client.delete_object(Bucket=app.config['AWS_S3_BUCKET_NAME'], Key=key)
            db.session.delete(assured)
            db.session.commit()
        # Delete associated sold items
        sold_items = Sold.query.filter_by(user_id=user_id).all()
        for sold in sold_items:
            files_to_remove = sold.pic_file_path.split(',')
            for file in files_to_remove:
                parsed_url = urlparse(file)
                key = parsed_url.path.lstrip('/')  # Remove leading '/'
                s3_client.delete_object(Bucket=app.config['AWS_S3_BUCKET_NAME'], Key=key)
            db.session.delete(sold)
            db.session.commit()
        # Delete associated purchases
        purchases = Purchase.query.filter_by(buyer_id=user_id).all()
        for purchase in purchases:
            files_to_remove = purchase.pic_file_path.split(',')
            for file in files_to_remove:
                parsed_url = urlparse(file)
                key = parsed_url.path.lstrip('/')  # Remove leading '/'
                s3_client.delete_object(Bucket=app.config['AWS_S3_BUCKET_NAME'], Key=key)
            db.session.delete(purchase)
            db.session.commit()
        # Delete associated support queries
        support_queries = SupportQuery.query.filter_by(user_id=user_id).all()
        for query in support_queries:
            db.session.delete(query)
        # Delete the user
        db.session.delete(user)
        db.session.commit()
        flash('User and all associated data deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting user: {str(e)}', 'danger')
    return redirect(url_for('admin_users'))




@app.route('/admin/assured-pending')
@login_required
@campus_ambassador_required
def admin_assured_pending(allowed_college=None):
    query = assure_pending.query.join(User, assure_pending.user_id == User.id)
    if allowed_college:
        query = query.filter(assure_pending.college == allowed_college)
    items = query.all()
    return render_template('admin_assured_pending.html', items=items)

@app.route('/admin/approve-assured/<int:item_id>', methods=['POST'])
@login_required
@campus_ambassador_required
def approve_assured(item_id, allowed_college=None):
    try:
        # Fetch the item from assure_pending table
        item = assure_pending.query.get_or_404(item_id)

        # Restrict to the ambassador's college
        if allowed_college and item.college != allowed_college:
            flash('Access denied. You can only approve items for your college.', 'danger')
            return redirect(url_for('admin_assured_pending'))

        # Get URL from form data
        provided_url = request.form.get('url', '').strip()

        # Validate URL
        if not provided_url:
            flash('Error: URL is required to approve the item.', 'danger')
            return redirect(url_for('admin_assured_pending'))

        # Create new Item
        new_item = Item(
            name=item.name,
            category=item.category,
            sub_cat=item.sub_cat,
            price=item.price,
            og_price=item.og_price,
            age=item.age,
            condition=item.condition,
            description=item.description,
            vid=provided_url,
            pic_file_path=item.pic_file_path,
            assured='Assured',
            college=item.college,
            user_id=item.user_id
        )

        # Add new item and delete the assured_pending item
        db.session.add(new_item)
        db.session.delete(item)
        db.session.commit()

        # Send notification
        try:
            user = User.query.get(item.user_id)
            if user:
                en.send_assurance_approval_notification(user.email, item.name, item.price)
            else:
                flash('Item approved, but failed to send notification: User not found.', 'warning')
        except Exception as e:
            flash(f'Item approved, but failed to send notification: {str(e)}', 'warning')

        flash('Item assurance approved and moved to listed items!', 'success')
        return redirect(url_for('admin_assured_pending'))

    except Exception as e:
        db.session.rollback()
        flash(f'Error approving item: {str(e)}', 'danger')
        return redirect(url_for('admin_assured_pending'))




    return render_template('admin_assured_pending.html', items=items)





@app.route('/admin/misc-approvals')
@login_required
@campus_ambassador_required
def admin_misc_approvals(allowed_college=None):
    query = Misc_Approval.query.filter(Misc_Approval.status == 'Pending')
    if allowed_college:
        query = query.filter(Misc_Approval.college == allowed_college)
    items = query.all()
    return render_template('admin_misc_approvals.html', items=items)




@app.route('/admin/approve-misc/<int:item_id>', methods=['POST'])
@login_required
@campus_ambassador_required
def approve_misc(item_id, allowed_college=None):
    item = Misc_Approval.query.get_or_404(item_id)
    
    # Restrict to the ambassador's college
    if allowed_college and item.college != allowed_college:
        flash('Access denied. You can only approve items for your college.', 'danger')
        return redirect(url_for('admin_misc_approvals'))
    
    # Get subcategory from form
    subcategory = request.form.get('subcategory')
    if not subcategory:
        flash('Please select a category/subcategory before approving.', 'danger')
        return redirect(url_for('admin_misc_approvals'))
    
    # Determine category based on subcategory
    category_mapping = {
        'Gear': 'Cycles', 'Gearless': 'Cycles', 'Other_Cycle': 'Cycles',
        'Keyboard/Mouse': 'Electronics', 'Writing Pad': 'Electronics', 'Kindle': 'Electronics',
        'Monitor': 'Electronics', 'USB/LAN Devices': 'Electronics', 'Trimmer': 'Electronics',
        'Controller/Consoles': 'Electronics', 'Extension Cord': 'Electronics', 'Wifi Router': 'Electronics',
        'Earbuds': 'Electronics', 'Speaker': 'Electronics', 'Mouse': 'Electronics', 'Power Bank': 'Electronics',
        'Other_Electronics': 'Electronics',
        'WiFi Router': 'Hostel Essentials', 'Umbrella': 'Hostel Essentials', 'Mosquito Nets/Rackets': 'Hostel Essentials',
        'Curtains': 'Hostel Essentials', 'Wooden Chair': 'Hostel Essentials', 'Office Chair': 'Hostel Essentials',
        'Shelves': 'Hostel Essentials', 'Decor': 'Hostel Essentials', 'Buckets/Mugs': 'Hostel Essentials',
        'Other_Hostel': 'Hostel Essentials',
        'Cotton': 'Mattress', 'Foam': 'Mattress', 'Other_Mattress': 'Mattress',
        'Digital': 'Watches', 'Analog': 'Watches', 'Smartwatches': 'Watches', 'Other_Watches': 'Watches',
        'Novels': 'Books', 'Course Books': 'Books', 'Other_Books': 'Books',
        'Gym Gear': 'Fitness & Sports', 'Balls': 'Fitness & Sports', 'Yoga Mat': 'Fitness & Sports',
        'Skipping Rope': 'Fitness & Sports', 'Rackets': 'Fitness & Sports', 'Other_Sports': 'Fitness & Sports',
        'ED drafter': 'Academic Accessories', 'Whiteboard': 'Academic Accessories', 'Chart Holder': 'Academic Accessories',
        'Lab Coat': 'Academic Accessories', 'Calculator': 'Academic Accessories', 'Laptop_stand': 'Academic Accessories',
        'Study Lamp': 'Academic Accessories', 'Writing Pad': 'Academic Accessories', 'Other_Academic': 'Academic Accessories',
        'Table Fan': 'Appliances & Kitchenware', 'Cooler': 'Appliances & Kitchenware', 'Utensils/Cutlery': 'Appliances & Kitchenware',
        'Washing Machine': 'Appliances & Kitchenware', 'Induction': 'Appliances & Kitchenware', 'Kettle': 'Appliances & Kitchenware',
        'Other_Appliances': 'Appliances & Kitchenware',
        'Shoes': 'Personal Accessories', 'Musical Instruments': 'Personal Accessories', 'Belts': 'Personal Accessories',
        'Bags': 'Personal Accessories', 'Umbrella': 'Personal Accessories', 'Other_Personal': 'Personal Accessories',
        'Other_Miscellaneous': 'Miscellaneous'
    }
    category = category_mapping.get(subcategory, 'Miscellaneous')
    
    if item.assured == 'Assured':
        # Move to assure_pending table if assured is 'Assured'
        assurance_item = assure_pending(
            name=item.name,
            category=category,
            sub_cat=subcategory,
            price=item.price,
            og_price=item.og_price,
            age=item.age,
            condition=item.condition,
            description=item.description,
            pic_file_path=item.pic_file_path,
            assured='pending',
            college=item.college,
            user_id=item.user_id,
            email=User.query.get(item.user_id).email,
            mobile=User.query.get(item.user_id).mobile_no
        )
        db.session.add(assurance_item)
        flash('Miscellaneous item approved and moved to assurance approval queue!', 'success')
    else:
        # Move to Item table if no assurance approval is required
        new_item = Item(
            name=item.name,
            category=category,
            sub_cat=subcategory,
            price=item.price,
            og_price=item.og_price,
            age=item.age,
            condition=item.condition,
            description=item.description,
            pic_file_path=item.pic_file_path,
            assured=item.assured,
            college=item.college,
            user_id=item.user_id
        )
        db.session.add(new_item)
        flash('Miscellaneous item approved and moved to listed items!', 'success')
    
    # Update item status and delete from Misc_Approval
    item.status = 'Approved'
    db.session.delete(item)
    db.session.commit()
    
    # Send notification to the user
    user = User.query.get(item.user_id)
    en.send_misc_listing_approval(user.email, item.name, item.price)
    
    return redirect(url_for('admin_misc_approvals'))


@app.route('/admin/delete-misc/<int:item_id>', methods=['POST'])
@login_required
@campus_ambassador_required
def delete_misc(item_id, allowed_college=None):
    item = Misc_Approval.query.get_or_404(item_id)
    
    # Restrict to the ambassador's college
    if allowed_college and item.college != allowed_college:
        flash('Access denied. You can only reject items for your college.', 'danger')
        return redirect(url_for('admin_misc_approvals'))
    
    # Get reason from form
    reason = request.form.get('reason')
    if not reason or not reason.strip():
        flash('Please provide a reason for rejection.', 'danger')
        return redirect(url_for('admin_misc_approvals'))
    
    try:
        # Update item with rejection reason and status
        item.reason = reason
        item.status = 'Rejected'
        db.session.commit()
        
        # Send rejection notification with reason
        user = User.query.get(item.user_id)
        en.send_misc_rejection_notification(user.email, item.name, item.price, reason)
        
        flash('Miscellaneous item rejected successfully!', 'success')
    except Exception as e:
        flash(f'Error rejecting item: {str(e)}', 'danger')
    
    return redirect(url_for('admin_misc_approvals'))







if __name__=='__main__':
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            print(f"Warning: Could not create database tables: {e}")
            print("App will run but database features may not work.")
    app.run(debug=False, use_reloader=False, host='127.0.0.1', port=5000)


