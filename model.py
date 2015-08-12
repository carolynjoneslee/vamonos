from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm.exc import NoResultFound
from datetime import datetime, timedelta
from reportlab.pdfgen import canvas

db = SQLAlchemy()

########################################################################
# Model definitions

class User(db.Model):
	""" A class for users in the sqlite3 database"""

	__tablename__ = "Users"

	user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	fname = db.Column(db.String(30), nullable=False)
	lname = db.Column(db.String(30), nullable=False)
	email = db.Column(db.String(100), nullable=False, unique=True)
	password = db.Column(db.String(30), nullable=False)
	img_url = db.Column(db.String(300))
	
	def __repr__(self):
		return "< User ID: %d, NAME: %s >" %(self.user_id, self.fname)

	@classmethod
	def authenticate(cls, email, password):
		"""Looks up user by email and password."""

		try:
			return cls.query.filter_by(email=email, password=password).one()

		except NoResultFound:
			return None

	@classmethod
	def get_by_email(cls, email):
		"""Looks up user by email"""

		try:
			found_user = cls.query.filter_by(email=email).one()
			return found_user

		except NoResultFound:
			return None

class Trip(db.Model):

	__tablename__ = "Trips"

	trip_id = db.Column(db.Integer,
						primary_key=True,
						autoincrement=True
						)
	admin_id = db.Column(db.Integer,
						 db.ForeignKey('Users.user_id'),
						 nullable=False
						 )
	title = db.Column(db.String(100))
	start = db.Column(db.DateTime, nullable=False)
	end = db.Column(db.DateTime, nullable=False)

	# Location details
	place_name = db.Column(db.String(100))
	latitude = db.Column(db.Float, nullable=False)
	longitude = db.Column(db.Float, nullable=False)
	address = db.Column(db.String(200))
	city = db.Column(db.String(60))
	country_code = db.Column(db.String(5))


	def __repr__(self):
		return "< Trip ID: %d ADMIN: %s TITLE: %s >" % (self.trip_id, self.admin_id, self.title)


	def create_days(self):
		"""Creates the appropriate number of days for this trip"""

		trip_start = self.start
		trip_end = self.end

		day_start = trip_start
		day_end = day_start + timedelta(hours=23, minutes=59)
		day_num = 1

		while day_end <= trip_end:
			day = Day(trip_id = self.trip_id,
					  day_num = day_num,
					  start=day_start,
					  end=day_end
					  )
			db.session.add(day)

			day_num += 1
			day_start += timedelta(days=1)
			day_end += timedelta(days=1)

		db.session.commit()


	def generateItinerary(self, filename):
		"""Writes the itinerary on a canvas"""

		# Create canvas
		my_canvas = canvas.Canvas(filename, bottomup=0)

		# Write to canvas
		my_canvas.drawString(100, 100, "This is my itinerary!")

		# Save canvas to PDF file
		my_canvas.showPage
		my_canvas.save()



class Permission(db.Model):

	__tablename__ = "Permissions"

	perm_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	trip_id = db.Column(db.Integer,
						db.ForeignKey('Trips.trip_id'),
						nullable=False
						)
	user_id = db.Column(db.Integer,
						db.ForeignKey('Users.user_id'),
						nullable=False
						)
	can_view = db.Column(db.Boolean, nullable=False)
	can_edit = db.Column(db.Boolean, nullable=False)

	user = db.relationship(
				'User',
				backref=db.backref('permissions', order_by=trip_id)
				)

	trip = db.relationship(
				'Trip',
				backref=db.backref('permissions', order_by=trip_id)
				)

	def __repr__(self):
		return "< Permission ID: %s TRIP: %s USER: %s Edit: %r >" % (self.perm_id, self.trip_id, self.user_id, self.can_edit)


class Day(db.Model):

	__tablename__ = "Days"

	day_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	trip_id = db.Column(db.Integer,
						db.ForeignKey('Trips.trip_id'),
						nullable=False
						)
	day_num = db.Column(db.Integer, autoincrement=False, nullable=False)
	start = db.Column(db.DateTime, nullable=False)
	end = db.Column(db.DateTime, nullable=False)
	
	trip = db.relationship(
				'Trip',
				backref=db.backref('days', order_by=day_num)
				)

	# def __repr__(self):
	# 	return "< Day ID: %d TRIP: %d DAY_NUM: %d >" % (self.day_id, self.trip_id, self.day_num)


class Event(db.Model):

	__tablename__ = "Events"

	event_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	day_id = db.Column(db.Integer,
						db.ForeignKey('Days.day_id'),
						nullable=False
						)
	user_id = db.Column(db.Integer,
						db.ForeignKey('Users.user_id'),
						nullable=False
						)
	title = db.Column(db.String(100))
	description = db.Column(db.Text, default="No description available.", nullable=False)
	start = db.Column(db.DateTime, nullable=False)
	end = db.Column(db.DateTime, nullable=False)
	url = db.Column(db.String(300))

	# Location details
	place_name = db.Column(db.String(100))
	latitude = db.Column(db.Float)
	longitude = db.Column(db.Float)
	address = db.Column(db.String(200))
	city = db.Column(db.String(60), nullable=False)
	country_code = db.Column(db.String(10))

	user = db.relationship(
				'User',
				backref=db.backref('events', order_by=start) # user.events returns all of the events added by a given user
				)
	day = db.relationship(
				'Day',
				backref=db.backref('events', order_by=start)
				)

	def __repr__(self):
		return "<Event ID: %d TITLE: %s>" % (self.event_id, self.title)



class Friendship(db.Model):

	__tablename__ = "Friendships"

	friendship_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	admin_id = db.Column(db.Integer,
						db.ForeignKey('Users.user_id'),
						nullable=False
						)
	friend_id = db.Column(db.Integer,
						db.ForeignKey('Users.user_id'),
						nullable=False
						)

	admin = db.relationship('User',
							   primaryjoin="User.user_id == Friendship.admin_id",
							   backref=db.backref("friendships")
							   )

	friend = db.relationship('User', primaryjoin="User.user_id == Friendship.friend_id")

	def __repr__(self):
		return "< Friendship ID: %d AdminID: %d FriendID: %d >" % (self.friendship_id, self.admin_id, self.friend_id)

########################################################################
# Helper functions
def find_next_day(date):
	"""Given a datetime object, returns the following day as a datetime object
	
	>>> date = datetime(2015, 12, 23) 
	>>> find_next_day(date)
	datetime.datetime(2015, 12, 24, 0, 0)
	"""

	day = timedelta(days=1)
	date += day
	return date


def connect_to_db(app):
    """Connect the database to our Flask app."""

    # Configure to use our SQLite database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///travelapp.db'
    # app.config['SQLALCHEMY_ECHO'] = True
    db.app = app
    db.init_app(app)


if __name__ == "__main__":

    from server import app
    connect_to_db(app)
    print "Connected to DB."

    # db.create_all()
    # print "DB tables built."

