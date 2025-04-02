#required imports
from flask import Flask, render_template, redirect, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import requests
import re

# app setup
app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
db = SQLAlchemy(app)

class Client(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    seat_number = db.Column(db.Integer, nullable=False, unique=True)
    from_location = db.Column(db.String(100), nullable=False)
    to_location = db.Column(db.String(100), nullable=False)
    added = db.Column(db.DateTime, default=datetime.utcnow)

class Route(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    route_string = db.Column(db.String(100), nullable=False)
    route_parts = db.Column(db.PickleType, nullable=False) 
    added = db.Column(db.DateTime, default=datetime.utcnow)


#updating client database for each city
def update_client_database(desired_city):
    route = Route.query.first()
    clients_info = []
    clients_to_delete = []

    if route:
        route_parts = route.route_parts
        desired_city_index = route_parts.index(desired_city)

        clients = Client.query.all()
        for client in clients:
            client_to_index = route_parts.index(client.to_location)
            
            # Delete client if their 'to_location' is before the selected city
            if client_to_index < desired_city_index:
                clients_to_delete.append(client)
            else:
                clients_info.append(client)

        for client in clients_to_delete:
            db.session.delete(client)
        db.session.commit()

    return clients_info
            


#the homepage
@app.route("/",methods=["POST","GET"])
def index():

    #current_request = request.form[]
    return render_template("index.html")

#entering clients
@app.route("/enter", methods=["POST", "GET"])
def enter():
    
    #entering new clients
    if request.method == "POST":
        
        seat_number = request.form['seat_number']
        from_location = request.form['from_location']
        to_location = request.form['to_location']

        route_string = request.form['route']
        route_parts = route_string.split("-")

        if (from_location and to_location) in route_parts:

            new_client = Client(seat_number=seat_number, from_location=from_location, to_location=to_location)

        else:
            return "Check The Route"

        try:
            db.session.add(new_client)
            db.session.commit()
            return redirect("/")
    
        except Exception as ex:
            print(f"ERROR:{ex}")
            return f"ERROR:{ex}"
    
    #viewing existing clients
    else:
        clients = Client.query.order_by(Client.added).all()
        return render_template("enter.html", clients = clients)


#deleting clients
@app.route("/delete/<int:id>")
def delete(id:int):
    deleting_client = Client.query.get_or_404(id)
    try:
        db.session.delete(deleting_client)
        db.session.commit()
        return redirect("/")
    except Exception as ex:
        return f"ERROR:{ex}"


#entering a bus route
@app.route("/enter_route", methods=["POST","GET"])
def enter_route():

    if request.method == "POST":
        route_string = request.form['route']
        #we will need this part when creating the label
        route_parts = route_string.split("-")

        # Create a new Route object
        new_route = Route(route_string=route_string, route_parts=route_parts)

        try:
            db.session.add(new_route)
            db.session.commit()
            return redirect('/enter_route')
        except Exception as ex:
            print(f"ERROR: {ex}")
            return f"ERROR: {ex}"

    # Retrieve all routes from the database
    routes = Route.query.order_by(Route.added).all()
    return render_template("enter_route.html", routes=routes)


@app.route("/edit_route/<int:id>", methods=["POST","GET"])
def edit_route(id):
    route = Route.query.get_or_404(id)
    if request.method =="POST":
        route.route_string = request.form['route']
        route.route_parts = route.route_string.split("-")
        try:
            db.session.commit()
            return redirect('/enter_route')
        except Exception as ex:
            print(f"ERROR: {ex}")
            return f"ERROR: {ex}"

    return render_template("edit_route.html", route=route)



#creating a script that is diferent in every city
@app.route("/label", methods=["POST","GET"])
def label():
    route = Route.query.first()

    if route:
        route_parts = route.route_parts

        if request.method == "POST":
            selected_city = request.form['city']
            clients_info = update_client_database(selected_city)

            return render_template("label.html", clients_info=clients_info, selected_city=selected_city, route_parts=route_parts)


        return render_template("label.html", route_parts=route_parts)

    return "Route Not Found"


#runner and debugger
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(port=5001,debug = True)
