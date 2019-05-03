import numpy as np
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import os

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify
from flask import render_template

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite",connect_args={'check_same_thread': False})

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)

# Save reference to the table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)
#################################################
# Flask Routes
#################################################

@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/YYYY-MM-DD *enter start date in format YYYY-MM-DD <br/>"
        f"/api/v1.0/YYYY-MM-DD/YYYY-MM-DD *enter start date and end date in format YYYY-MM-DD/YYYY-MM-DD <br/>"
        f"/api/v1.0/tripsummary/YYYY-MM-DD/YYYY-MM-DD *enter start date and end date in format YYYY-MM-DD/YYYY-MM-DD"
    )


@app.route("/api/v1.0/precipitation")
def precipitation():
    """Return a dictionary of date and precipitation"""
    # Query all stations
    results = session.query(Measurement.date, Measurement.prcp).all()

    keys = []
    values = []
    for date,prcp in results:
        keys.append(date)
        values.append(prcp)

    precipitation = dict(zip(keys, values))
    # Convert list of tuples into normal list
    #all_precipitation = list(np.ravel(results))

    return jsonify(precipitation)


@app.route("/api/v1.0/stations")
def stations():
	"""Return a list of each station"""
	results = session.query(Measurement.station).all()
	stations = [x for x in results]
	stations_unique = list(dict.fromkeys(stations))

	return jsonify(stations_unique)

@app.route("/api/v1.0/tobs")
def tobs():
	prcp_date = [x for x in session.query(Measurement.tobs, Measurement.date)]
	last_12_tobs = []
	last_12_date = []
	for tobs,date in prcp_date:
	    if date >= '2016-08-23':
	        last_12_tobs.append(tobs)
	        last_12_date.append(date)
	        
	last_12 = dict(zip(last_12_date, last_12_tobs))
	
	return jsonify(last_12)

@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def data_dates(start=None, end=None):

	sel = [func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)]
	
	if not end:
		results = session.query(*sel).\
			filter(Measurement.date >= start).all()
		temps = list(np.ravel(results))
		return jsonify(temps)

	results = session.query(*sel).\
		filter(Measurement.date >= start).\
		filter(Measurement.date <= end).all()
	temps = list(np.ravel(results))
	return jsonify(temps)




#create a trip weather summary and figure
@app.route("/api/v1.0/tripsummary/<start>/<end>", methods=['GET','POST'])
def calc_trip(start=None, end=None):
	
	#remove figure if exists
	if os.path.exists("static/trip_summary_fig.png"):
		os.remove("static/trip_summary_fig.png")
	
	trip_temps = (session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
    	filter(Measurement.date >= start).\
    	filter(Measurement.date <= end).all())

	tmin = trip_temps[0][0]
	tavg = trip_temps[0][1]
	tmax = trip_temps[0][2]
	x_axis = np.arange(len([tavg]))
	temp = [tavg]
	error = [tmax-tmin]

	plt.bar(x_axis, temp, yerr=error, color='r', alpha=0.2, align="center")
	plt.title('Trip Avg Temp')
	plt.ylim(0,100)
	plt.ylabel('Temp (F)')
	plt.tick_params(axis='x',labelbottom=False, length=0)
	plt.savefig('static/trip_summary_fig.png')

	return render_template('trip_summary.html')


if __name__ == '__main__':
    app.run(debug=True)

