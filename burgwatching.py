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
# Configure base directory of app

basedir = os.path.abspath(os.path.dirname(__file__))


## App setup code
app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'hardtoguessstringfromsi364thisisnotsupersecurebutitsok'
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://jackstephenson@localhost/burgwatching"
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
## All app.config values

## API setup code
apikey = 'nQZlfNE4qJdhGstTNGoLy5AZsZWNcefZ'

db = SQLAlchemy(app) # For database use



######################################
######## HELPER FXNS (If any) ########
######################################

def get_coords(locationstring):
	#Google API to get latitude and longitude from an address
	params = {}
	params['location'] = locationstring
	params['key'] = apikey
	url = 'http://open.mapquestapi.com/geocoding/v1/address'
	r = requests.get(url, params)
	response = r.json()
	rdict = {'lat':response['results'][0]['locations'][0]['latLng']['lat'], 
			 'lng':response['results'][0]['locations'][0]['latLng']['lng']}
	return rdict

def validate_username(form, field):
	if len(str(field.data).split(" ")) > 1:
		raise ValidationError('username must be one word')

##################
##### MODELS #####
##################


## Many
class Sighting(db.Model):
	__tablename__ = 'sighting'
	id = db.Column(db.Integer, primary_key=True)
	location = db.Column(db.String(280))
	lat = db.Column(db.Numeric)
	lng = db.Column(db.Numeric)
	activity = db.Column(db.String(280))
	time = db.Column(db.DateTime, nullable=False,
		default=datetime.utcnow)
	user_id = db.Column(db.Integer, db.ForeignKey("user.id")) 
	def __repr__(self):
		return "{} @ {} (ID: {})".format(self.activity, self.location, self.id)
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
		location = form.location.data
		activity = form.activity.data

		user = db.session.query(User).filter_by(username=username).first()
		if not user:
			user = User(username=username)
			db.session.add(user)
			db.session.commit()

		if db.session.query(Sighting).filter_by(activity=activity, location=location).first():
			flash("Someone has already saved this sighting!")
			return redirect(url_for('infoform'))

		lat = get_coords(location)['lat']
		lng = get_coords(location)['lng']
		sight = Sighting(
						location=location, 
						lat=lat, 
						lng=lng, 
						activity=activity,  
						time=datetime.now(),
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
	sightings = [(sighting.activity, sighting.location, sighting.lat, sighting.lng, 
		str(sighting.time)[:19], str(User.query.filter_by(id=sighting.user_id).first())) 
	for sighting in Sighting.query.all()]
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
				sightings = [(sighting.activity, sighting.location, sighting.lat, sighting.lng, 
				str(sighting.time)[:19], username) 
				for sighting in Sighting.query.filter_by(user_id=user_id).all()]
				print("TESTING")
				return render_template('search.html', form=searchform, sightings=sightings)

			except:

				flash("No sightings with that username")
				print("ERROR")
				return redirect(url_for("search"))
	return render_template('search.html', form=searchform)


# @app.route('/search_results', methods=['POST'])
# def search_results():
# 	searchform = SearchForm(request.form)
# 	username = str(searchform.search.data)
# 	try:
# 		user = User.query.filter_by(username=username).first()
# 		user_id = user.id
# 		sightings = [(sighting.activity, sighting.location, sighting.lat, sighting.lng, 
# 		str(sighting.time)[:19], username) 
# 		for sighting in Sighting.query.filter_by(user_id=user_id).all()]

# 		return render_template('search_results.html', username=username, sightings=sightings)

# 	except:

# 		flash("No sightings with that username")
# 		print("ERROR")
# 		return redirect(url_for("search"))
	# print("USERID")
	# print(user_id)
	


'''
TO ADD:
1. get submissions by user (search user) - counts for GET request (use form.validate())
	- how to get search bar on same page as feed
2. map page with all locations (optional)
'''


#@app.route('/map')
# ^ takes user to google map plugin with all locations marked (lat and lon)







## Code to run the application...
if __name__ == '__main__':
	db.create_all() # Will create any defined models when you run the application
	app.run(use_reloader=True,debug=True) # The usual
# Put the code to do so here!
# NOTE: Make sure you include the code you need to initialize the database structure when you run the application!
