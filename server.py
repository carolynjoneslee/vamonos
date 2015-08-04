from flask import Flask, redirect, render_template, flash, session, request
from model import User, Trip, Permission, Friendship, db, connect_to_db
from datetime import datetime


app = Flask(__name__)
app.secret_key = "most_secret_key_EVER!!!!!!!"

#############################################################
# Routes

@app.route("/")
def home():
	"""Displays homepage"""
	
	return render_template('home.html')



@app.route("/login", methods=['GET'])
def login_page():
	"""Displays login page"""

	return render_template("login.html")



@app.route("/login", methods=['POST'])
def login():
	"""Logs in the user, or denies access"""

	email = request.form.get("email")
	password = request.form.get("password")
	
	user = User.authenticate(email, password)

	if user:
		session["user_id"] = user.user_id
		return redirect("/trips")

	else:
		flash("Your information could not be found in the system. Try again or sign up!")
		return redirect("/login")



@app.route("/signup", methods=['GET'])
def signup_page():
	"""Displays signup page"""

	return render_template("signup.html")



@app.route("/signup", methods=['POST'])
def signup():
	"""Adds new user to the DB."""

	email = request.form.get("email")
	found_user = User.query.filter_by(email=email).all()

	if found_user:
		msg = "We found your email in our database. Try logging in instead!"

	else:
		# Get user info from form
		fname = request.form.get("fname")
		lname = request.form.get("lname")
		password = request.form.get("password")

		# Add user to DB
		user = User(fname=fname,
				   lname=lname,
				   email=email,
				   password=password,
				   )
		db.session.add(user)
		db.session.commit()

		msg = "Welcome, %s! You're now signed up. Log in to get started!" % (fname)
	
	flash(msg)
	return redirect("/login")



@app.route("/logout")
def logout():
	"""Logs the user out, clearing the session"""

	session.clear()
	flash("You have been successfully logged out.")
	return redirect("/")



@app.route("/user<int:user_id>/profile")
def profile(user_id):
	"""Displays a user's profile"""

	user = User.query.get(user_id)
	friends = [(friendship.friend_id, friendship.friend.fname, friendship.friend.img_url) for friendship in user.friendships]
	print friends
	return render_template("profile.html", user=user, friends=friends)



@app.route("/add_friend", methods=["POST"])
def add_friend():
	"""Adds a new friendship to the DB"""

	email = request.form.get("email")
	friend = User.get_by_email(email)

	if friend:
		# Add friendship to the DB
		friendship = Friendship(admin_id=session['user_id'],
								friend_id=friend.user_id
								)
		db.session.add(friendship)
		db.session.commit()
		msg = "You have successfully added %s to your friends!" % (friend.fname)

	else:
		msg = "We couldn't find anyone with that email in our system."

	flash(msg)

	url = "/user%d/profile" % (session['user_id'])
	return redirect(url)



@app.route("/trips")
def trips():
	"""Displays all of a user's trips"""

	user_id = session["user_id"]
	permissions = Permission.query.filter_by(user_id=user_id).all()
	trip_tuples = [(perm.trip.title, perm.trip.trip_id) for perm in permissions]

	return render_template("trips.html", user_id=user_id, trip_tuples=trip_tuples)



@app.route("/user<int:viewer_id>/trip<int:trip_id>", methods=["GET"])
def my_trip(viewer_id, trip_id):
	"""Displays trip planning page"""

	admin_id = Trip.query.get(trip_id).admin_id
	permissions = Permission.query.filter(Permission.trip_id == trip_id, Permission.user_id != admin_id).all()
	friendships = Friendship.query.filter_by(admin_id = viewer_id).all()
	friends = [(friendship.friend.fname, friendship.friend_id) for friendship in friendships]

	return render_template("trip_planner.html", admin_id=admin_id, trip_id=trip_id, permissions=permissions, friends=friends)



@app.route("/add_permission", methods=["POST"])
def add_permission():
	"""Adds a new permission to the DB"""

	# Get info from form
	trip_id = request.form.get("trip_id")
	friend_id = request.form.get("friend_id")
	can_edit = request.form.get("can_edit")

	# Add permission to DB
	perm = Permission(trip_id=trip_id,
					  user_id=friend_id,
					  can_view=True,
					  can_edit=can_edit
					  )
	db.session.add(perm)
	db.session.commit()

	# Confirm submission
	friend = User.query.get(friend_id)
	if can_edit:
		ability = "view & edit"
	else:
		ability = "view"

	msg = "%s is now allowed to %s this trip!" % (friend.fname, ability)
	flash(msg)

	return redirect("/")


@app.route("/rm_permission", methods=["POST"])
def rm_permission():
	"""Deletes a permission from the DB"""

	return redirect("/")



@app.route("/create_trip")
def new_trip():
	"""Displays a form for creating a new trip"""

	user_id = session["user_id"]
	return render_template("create_trip.html", user_id=user_id)



@app.route("/create_trip", methods=["POST"])
def create_trip():
	"""Adds a trip to the database"""

	# Get trip details from form
	title = request.form.get("title")
	city = request.form.get("city")

	start_raw = request.form.get("start")
	start = datetime.strptime(start_raw, "%Y-%m-%d")

	end_raw = request.form.get("end")
	end = datetime.strptime(end_raw, "%Y-%m-%d")

	# Add trip to DB
	trip = Trip(admin_id=session["user_id"],
				title=title,
				start=start,
				end=end,
				city=city
				)
	db.session.add(trip)
	db.session.commit() # Commit here so that you can retrieve the trip_id!

	# Add admin permission to DB
	perm = Permission(trip_id=trip.trip_id,
					  user_id=session["user_id"],
					  can_view=True,
					  can_edit=True
					  )
	db.session.add(perm)
	db.session.commit()

	flash("Your trip has been created!")

	return render_template("trip_planner.html", trip_id=trip.trip_id)


#############################################################

if __name__ == "__main__":
	connect_to_db(app)
	app.run(debug=True)