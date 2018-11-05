###############################
####### SETUP (OVERALL) #######
###############################

## Import statements
# Import statements
import os
import json
from flask import Flask, render_template, session, redirect, url_for, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, RadioField, SelectField, ValidationError # Note that you may need to import more here! Check out examples that do what you want to figure out what.
from wtforms.validators import Required, Length # here, too
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import requests
from flask_googlemaps import GoogleMaps
from flask_googlemaps import Map
import calendar

# Configure base directory of app

basedir = os.path.abspath(os.path.dirname(__file__))


## App setup code
app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'hardtoguessstringfromsi364thisisnotsupersecurebutitsok'
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://jackstephenson@localhost/burgwatching"
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['GOOGLEMAPS_KEY'] = "AIzaSyApkzvws_KSuyHI7g2vRP1Oop97deyrCyo"

## All app.config values

GoogleMaps(app)
# Initialize GoogleMaps connection

## API setup code
apikey = 'AIzaSyApkzvws_KSuyHI7g2vRP1Oop97deyrCyo'

db = SQLAlchemy(app) # For database use



######################################
######## HELPER FXNS (If any) ########
######################################

'''
	text = db.Column(db.String(280))
	lat = db.Column(db.Numeric)
	lng = db.Column(db.Numeric)
	name = db.Column(db.String(280))
	formatted_address = db.Column(db.String(280))
	'''

def get_coords(locationstring):
	#Google API to get latitude and longitude from an address
	params = {}
	params['key'] = apikey
	params['input'] = locationstring
	params['inputtype'] = 'textquery'
	params['fields'] = "name,id,formatted_address,geometry"
	url = 'https://maps.googleapis.com/maps/api/place/findplacefromtext/json?parameters'
	r = requests.get(url, params)
	response = r.json()

	location = response['candidates'][0]
	r_dict = {'text':locationstring, 'lat':location['geometry']['location']['lat'], 
	'lng':location['geometry']['location']['lng'], 'name':location['name'], 'formatted_address':
	location['formatted_address']}
	return r_dict


def validate_username(form, field):
	if len(str(field.data).split(" ")) > 1:
		raise ValidationError('username must be one word')

# def infoboxer(sighting):
# 	activity = str(sighting.activity)
# 	day = str(calendar.day_name[sighting.time.weekday()])


# 	returnstring = str(sighting.activity) + " on " + str(sighting.time.day) + " at "
# 	+ str(sighting.time.hour) + str(sighting.time.minute)
# 	return returnstring


##################
##### MODELS #####
##################


## Many
class Sighting(db.Model):
	__tablename__ = 'sighting'
	id = db.Column(db.Integer, primary_key=True)
	activity = db.Column(db.String(280))
	location_text = db.Column(db.String(280))
	time = db.Column(db.DateTime, nullable=False,
		default=datetime.utcnow)
	loc_id = db.Column(db.Integer, db.ForeignKey("location.id"))
	user_id = db.Column(db.Integer, db.ForeignKey("user.id")) 
	def __repr__(self):
		return "{} @ {} (ID: {})".format(self.activity, self.location_text, self.id)
##QUESTION## Should have a __repr__ method that returns strings of a format like:
#### {Tweet text...} (ID: {tweet id})

## One
class User(db.Model):
	__tablename__ = 'user'
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(64), unique=True)
	sightings = db.relationship('Sighting',backref='user')
	def __repr__(self):
		return "{}".format(self.username)

class Location(db.Model):
	__tablename__ = 'location'
	id = db.Column(db.Integer, primary_key=True)
	text = db.Column(db.String(280))
	lat = db.Column(db.Numeric)
	lng = db.Column(db.Numeric)
	name = db.Column(db.String(280), unique=True)
	formatted_address = db.Column(db.String(280))
	sightings = db.relationship('Sighting', backref='location')
	def __repr__(self):
		return "{} @ {} ({},{})".format(self.name, self.formatted_address, self.lat,self.lng)


##Question## why is backref lowercase? What is this actually referencing?

###################
###### FORMS ######
###################

class HomeForm(FlaskForm):
	submit = SubmitField("I want to help!")
##  This form should just be a button that takes you to the info part

class InfoForm(FlaskForm):
	username = StringField("Please enter your username", validators=[Required(), validate_username])
	location = StringField("Where you saw him", validators=[Required()]) 
	activity = StringField("What was he doing?", validators=[Required()])
	submit = SubmitField("Submit")

class SearchForm(FlaskForm):
	search = StringField("Search sightings by user", validators=[Required()])
	submit = SubmitField("Submit")

#######################
###### VIEW FXNS ######
#######################

## Error handling routes
@app.errorhandler(404)
def page_not_found(e):
	return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
	return render_template('500.html'), 500

@app.route('/', methods=['GET', 'POST'])
def home():
	form = HomeForm()
	# if form.validate_on_submit():
	#     return redirect(url_for('infoform'))
	return render_template('home.html',form=form)

##Question## The only 'form' on the homepage is a button to help. I want there to also be a live feed
##           displaying activity @ location by username @ time submitted
##                      How do i do that...
## Also I don't see how inheriting base.html is gonna make sense here

@app.route('/info', methods=['GET','POST'])
def infoform():
	form = InfoForm()
	if form.validate_on_submit():
		username = form.username.data
		location_text = form.location.data
		activity = form.activity.data

		user = db.session.query(User).filter_by(username=username).first()
		if not user:
			user = User(username=username)
			db.session.add(user)


		location = Location.query.filter_by(text=location_text).first()
		if not location:
			l = get_coords(location_text)

			text=l['text']
			lat=l['lat'] 
			lng=l['lng'] 
			name=l['name']
			formatted_address=l['formatted_address']
			location = Location(text=text, lat=lat, lng=lng, name=name,
				formatted_address=formatted_address)

			db.session.add(location)


		# print("TESTING")
		# print(location)
		if Sighting.query.filter_by(activity=activity, location_text=location_text).first():
			flash("Someone has already saved this sighting!")
			return redirect(url_for('infoform'))

		sight = Sighting(
						activity=activity,
						location_text=location_text,  
						loc_id=location.id,
						user_id=user.id
						)
		db.session.add(sight)
		db.session.commit()
		flash('Thanks for your submission!')

		# location = db.session.query(Location).filter_by(location=location).first()
		# if not location:
		#     ##GET GOOGLE SHIT IN HERE##
		#     location = Location(location=location)

	errors = [v for v in form.errors.values()]

	if len(errors) > 0:
		flash("!!!! ERRORS IN FORM SUBMISSION - " + str(errors))
	return render_template('info.html', form=form)

@app.route('/feed', methods=['GET','POST'])
def feed():
	sightings = [(sighting.activity, str(sighting.time)[:19], sighting.location_text,
	User.query.filter_by(id=sighting.user_id).first()) for sighting in Sighting.query.all()]
	return render_template('feed.html', sightings=sightings)

# @app.route('/search', methods=['GET', 'POST'])
# def search():
# 	form = SearchForm()
# 	return render_template('search.html', form=form)
@app.route('/search', methods=['GET', 'POST'])
def search():
	searchform = SearchForm()
	if searchform.validate():
		if request.method == 'POST':
			username = str(searchform.search.data)

			try:

				user = User.query.filter_by(username=username).first()
				user_id = user.id
				sightings = [(sighting.activity, sighting.location_text,
				str(sighting.time)[:10], username) 
				for sighting in Sighting.query.filter_by(user_id=user_id).all()]
				return render_template('search.html', form=searchform, sightings=sightings)

			except:

				flash("No sightings with that username")
				return redirect(url_for("search"))
	return render_template('search.html', form=searchform)

@app.route("/map")
def mapview():

	sightings = []
	for sighting in Sighting.query.all():
		s = {}
		loc = Location.query.filter_by(id=sighting.loc_id).first()
		
		s['icon'] = 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png'
		s['lat'] = float(loc.lat)
		s['lng'] = float(loc.lng)
		s['infobox'] = "{} on {}".format(str(sighting.activity), str(sighting.time)[:10])
		
		sightings.append(s)

	sightingmap = Map(
		lat=42.271785,
		lng=-83.736472,
		identifier="view-side",
	 	markers=sightings)

	return render_template('map.html', sightingmap=sightingmap)


## Code to run the application...
if __name__ == '__main__':
	db.create_all() # Will create any defined models when you run the application
	app.run(use_reloader=True,debug=True) # The usual
# Put the code to do so here!
# NOTE: Make sure you include the code you need to initialize the database structure when you run the application!
