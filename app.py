from flask import Flask, request, jsonify, session, render_template, redirect, url_for
from flask_session import Session
from supabase import create_client, Client
from flask_bcrypt import Bcrypt
import os
from datetime import datetime

load_dotenv() 

app = Flask(__name__)

# Flask Session Configuration
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"  
Session(app)

# Supabase Configuration
SUPABASE_URL = "https://pwohpwzbttvewrouiqdz.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InB3b2hwd3pidHR2ZXdyb3VpcWR6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDE0MTIyMTEsImV4cCI6MjA1Njk4ODIxMX0.gfnzbrNkPhA4RH7zSxE7_0AbO7HWOvzpH6KApusuyyQ"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

import datetime

DEFAULT_VACCINATIONS = [
    ("Anthrax", 6, "Annually"),
    ("Haemorrhagic Septicemia (H.S.)", 6, "Annually"),
    ("Enterotoxaemia", 4, "Before Monsoon"),
    ("Black Quarter (B.Q)", 6, "Annually"),
    ("P.P.R.", 3, "Every 3 years"),
    ("Foot & Mouth Disease (F.M.D.)", 4, "Twice a year"),
    ("Goat Pox", 3, "Annually"),
    ("C.C.P.P", 3, "Annually"),
]

def initialize_vaccination_records(livestock_id):
    records = []
    current_date = datetime.datetime.now()  # Use current date instead of birth_date

    for vaccine, age_months, frequency in DEFAULT_VACCINATIONS:
        due_date = current_date + datetime.timedelta(days=age_months * 30)  # Approximate months
        records.append({
            "livestock_id": livestock_id,
            "vaccine_name": vaccine,
            "due_date": due_date.strftime("%Y-%m-%d"),
            "status": "Pending"
        })

    supabase.table("vaccinations").insert(records).execute()

bcrypt = Bcrypt(app)  # For password hashing

@app.route("/")
def home():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return render_template("index.html")

@app.route("/features")
def features():
    return render_template("features.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

        # Insert user into Supabase
        response = supabase.table("users").insert({"name": name, "email": email, "password": hashed_password}).execute()

        if response.data:
            return redirect(url_for("login"))
        return jsonify({"error": "Signup failed!"}), 400

    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        # Fetch user from Supabase
        response = supabase.table("users").select("*").eq("email", email).execute()
        user = response.data[0] if response.data else None

        if user and bcrypt.check_password_hash(user["password"], password):
            session["user"] = user["email"]
            return redirect(url_for("dashboard"))
        return jsonify({"error": "Invalid email or password!"}), 401

    return render_template("login.html")

@app.route("/farms", methods=["GET"])
def get_farms():
    if "user" not in session:
        return redirect(url_for("login"))

    user_email = session["user"]
    response = supabase.table("farms").select("*").eq("user_email", user_email).execute()
    
    return jsonify(response.data)

@app.route("/add_farm", methods=["POST"])
def add_farm():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    user_email = session["user"]

    farm_data = {
        "user_email": user_email,
        "name": data["name"],
        "location": data["location"],
        "size": data["size"]
    }

    supabase.table("farms").insert(farm_data).execute()
    return jsonify({"message": "Farm added successfully"})

@app.route("/delete_farm/<farm_id>", methods=["DELETE"])
def delete_farm(farm_id):
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    supabase.table("farms").delete().eq("id", farm_id).execute()
    return jsonify({"message": "Farm deleted successfully"})

@app.route("/farm/<farm_id>", methods=["GET"])
def view_farm(farm_id):
    if "user" not in session:
        return redirect(url_for("login"))

    response = supabase.table("farms").select("*").eq("id", farm_id).execute()
    farm = response.data[0] if response.data else None

    if not farm:
        return "Farm not found", 404

    return render_template("farm.html", farm=farm)


@app.route("/farm/<farm_id>/crops", methods=["GET"])
def get_crops(farm_id):
    if "user" not in session:
        return redirect(url_for("login"))

    response = supabase.table("crops").select("*").eq("farm_id", farm_id).execute()
    return jsonify(response.data)

@app.route("/farm/<farm_id>/add_crop", methods=["POST"])
def add_crop(farm_id):
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json

    crop_data = {
        "farm_id": farm_id,
        "name": data["name"],
        "type": data["type"],
        "quantity": data["quantity"],
        "planted_date": data["planted_date"]
    }

    supabase.table("crops").insert(crop_data).execute()
    return jsonify({"message": "Crop added successfully"})

@app.route("/farm/<farm_id>/delete_crop/<crop_id>", methods=["DELETE"])
def delete_crop(farm_id, crop_id):
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    supabase.table("crops").delete().eq("id", crop_id).execute()
    return jsonify({"message": "Crop deleted successfully"})

@app.route("/farm/<farm_id>/add_livestock", methods=["POST"])
def add_livestock(farm_id):
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    print("🐄 Add Livestock API Called!")  # Debugging message

    # Insert livestock record
    response = supabase.table("livestock").insert({
        "farm_id": farm_id,
        "name": data["name"],
        "type": data["type"],
        "count": data["count"],
        "age": data["age"],
        "health_status": data["health_status"]
    }).execute()

    if response.data:
        livestock_id = response.data[0]["id"]  # Get inserted livestock ID
        print(f"✅ Livestock added with ID: {livestock_id}")

        # Initialize vaccinations
        initialize_vaccination_records(livestock_id)
        print(f"💉 Vaccination records initialized for livestock ID: {livestock_id}")

    return jsonify(response.data), 201


# Get Livestock for a Farm
@app.route("/farm/<farm_id>/livestock", methods=["GET"])
def get_livestock(farm_id):
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    response = supabase.table("livestock").select("*").eq("farm_id", farm_id).execute()
    return jsonify(response.data), 200

# Delete Livestock
@app.route("/livestock/<livestock_id>/delete", methods=["DELETE"])
def delete_livestock(livestock_id):
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    supabase.table("livestock").delete().eq("id", livestock_id).execute()
    return jsonify({"message": "Livestock deleted"}), 200

# 🔹 Get Equipment for a Farm
@app.route("/farm/<farm_id>/equipment", methods=["GET"])
def get_equipment(farm_id):
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    response = supabase.table("equipment").select("*").eq("farm_id", farm_id).execute()
    return jsonify(response.data), 200

# 🔹 Add Equipment
@app.route("/farm/<farm_id>/add_equipment", methods=["POST"])
def add_equipment(farm_id):
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    response = supabase.table("equipment").insert({
        "farm_id": farm_id,
        "name": data["name"],
        "type": data["type"],
        "condition": data["condition"]
    }).execute()

    return jsonify(response.data), 201

# 🔹 Delete Equipment
@app.route("/equipment/<equip_id>/delete", methods=["DELETE"])
def delete_equipment(equip_id):
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    supabase.table("equipment").delete().eq("id", equip_id).execute()
    return jsonify({"message": "Equipment deleted"}), 200

@app.route("/livestock/<livestock_id>/vaccination_page", methods=["GET"])
def vaccination_page(livestock_id):
    if "user" not in session:
        return redirect(url_for("login"))

    # Fetch vaccinations for this livestock
    response = supabase.table("vaccinations").select("*").eq("livestock_id", livestock_id).execute()
    vaccinations = response.data if response.data else []

    return render_template("vaccination.html", livestock_id=livestock_id, vaccinations=vaccinations)





@app.route("/livestock/<uuid:livestock_id>/vaccinations")
def get_vaccinations(livestock_id):
    data = supabase.table("vaccinations").select("*").eq("livestock_id", str(livestock_id)).execute()
    return render_template("vaccination.html", vaccinations=data.data)

@app.route("/vaccination/<uuid:vaccination_id>/complete", methods=["POST"])
def complete_vaccination(vaccination_id):
    data = request.json
    status = "Completed" if data.get("status") == "Completed" else "Pending"

    # Update status in Supabase
    supabase.table("vaccinations").update({"status": status}).eq("id", str(vaccination_id)).execute()

    return jsonify({"message": "Vaccination status updated successfully!"})



@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html", user=session["user"])

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("home"))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)