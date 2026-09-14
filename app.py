from flask import Flask, render_template, request
import csv
import requests

app = Flask(__name__)


# -----------------------------
# Function to read CSV files
# -----------------------------
def read_csv(filename):
    with open(filename, "r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


# -----------------------------
# Destination port coordinates
# -----------------------------
port_coordinates = {
    "Paradip": (20.27, 86.68),
    "Vizag": (17.69, 83.22),
    "Gangavaram": (17.63, 83.27),
    "Gopalpur": (19.27, 84.88),
    "Dhamra": (20.78, 86.95),
    "Sagar-Sandheads": (21.65, 88.00),
    "Haldia": (22.03, 88.06)
}


# -----------------------------
# Get weather information
# -----------------------------
def get_weather(destination):

    latitude, longitude = port_coordinates[destination]

    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={latitude}"
        f"&longitude={longitude}"
        "&current=temperature_2m,wind_speed_10m,precipitation"
        "&daily=precipitation_probability_max"
        "&forecast_days=1"
        "&timezone=auto"
    )

    try:

        response = requests.get(url, timeout=10)
        data = response.json()

        temperature = data["current"]["temperature_2m"]
        wind_speed = data["current"]["wind_speed_10m"]
        precipitation = data["current"]["precipitation"]
        rain_probability = data["daily"]["precipitation_probability_max"][0]

        # -----------------------------
        # Calculate weather risk
        # -----------------------------

        if wind_speed >= 40 or rain_probability >= 80:
            risk = "HIGH"

        elif wind_speed >= 25 or rain_probability >= 50:
            risk = "MODERATE"

        else:
            risk = "LOW"

        return {
            "temperature": temperature,
            "wind_speed": wind_speed,
            "precipitation": precipitation,
            "rain_probability": rain_probability,
            "risk": risk
        }

    except Exception:

        return {
            "temperature": "N/A",
            "wind_speed": "N/A",
            "precipitation": "N/A",
            "rain_probability": "N/A",
            "risk": "Unavailable"
        }
    
# ================= ROUTE ANALYSIS =================

port_coordinates = {
    "Paradip": (20.27, 86.68),
    "Vizag": (17.69, 83.22),
    "Gangavaram": (17.63, 83.27),
    "Gopalpur": (19.27, 84.88),
    "Dhamra": (20.78, 86.95),
    "Sagar-Sandheads": (21.65, 88.00),
    "Haldia": (22.03, 88.06)
}

export_port_coordinates = {

    "Newcastle": (-32.93, 151.78),

    "Taboneo": (-3.80, 114.55),

    "Maputo": (-25.97, 32.58),

    "New Orleans": (29.95, -90.07),

    "Vostochny": (42.76, 133.08),

    "Port Hedland": (-20.31, 118.58),

    "Tubarao": (-20.28, -40.24),

    "Gladstone": (-23.84, 151.25),

    "Surabaya": (-7.25, 112.75),

    "Mobile": (30.69, -88.04),

    "Weipa": (-12.63, 141.88),

    "Balikpapan": (-1.27, 116.83)
}

def calculate_distance(lat1, lon1, lat2, lon2):

    from math import radians, sin, cos, sqrt, atan2

    R = 3440.065   # Earth radius in nautical miles

    lat1 = radians(lat1)
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        sin(dlat / 2) ** 2
        + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    )

    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c


def get_route(export_port, destination):

    if export_port not in export_port_coordinates:
        return None

    if destination not in port_coordinates:
        return None

    start_lat, start_lon = export_port_coordinates[export_port]
    end_lat, end_lon = port_coordinates[destination]

    distance = calculate_distance(
        start_lat,
        start_lon,
        end_lat,
        end_lon
    )

    # Prototype vessel speed
    average_speed = 13

    transit_hours = distance / average_speed
    transit_days = transit_hours / 24

    return {
    "export_port": export_port,
    "destination": destination,

    "export_lat": start_lat,
    "export_lon": start_lon,

    "destination_lat": end_lat,
    "destination_lon": end_lon,

    "distance": round(distance),
    "transit_days": round(transit_days, 1),
    "speed": average_speed
}

# -----------------------------
# Home page
# -----------------------------
@app.route("/")
def home():
    return render_template("index.html")


# -----------------------------
# Analyze shipment
# -----------------------------
@app.route("/analyze", methods=["POST"])
def analyze():

    material = request.form["material"]
    quantity = float(request.form["quantity"])
    origin = request.form["origin"]
    destination = request.form["destination"]

    # Read datasets
    sourcing_data = read_csv("data/sourcing.csv")
    vessel_data = read_csv("data/vessels.csv")
    port_data = read_csv("data/ports.csv")

    # -----------------------------
    # Find destination port
    # -----------------------------

    selected_port = None

    for port in port_data:

        if port["Port"] == destination:
            selected_port = port
            break

    if selected_port is None:
        return "Destination port not found."

    # Convert port restrictions
    max_loa = float(selected_port["Max_LOA"])
    max_beam = float(selected_port["Max_Beam"])
    max_draft = float(selected_port["Max_Draft"])

    # -----------------------------
    # Weather analysis
    # -----------------------------

    weather = get_weather(destination)

    # -----------------------------
    # Source country ranking
    # -----------------------------

    source_results = []

    for source in sourcing_data:

        if source["Commodity"].lower() != material.lower():
            continue

        if origin != "All" and source["Country"] != origin:
            continue

        material_price = float(source["Material_Price"])
        freight = float(source["Freight"])

        total_per_tonne = material_price + freight
        total_cost = total_per_tonne * quantity

        source_results.append({
            "country": source["Country"],
            "export_port": source["Export_Port"],
            "material_price": material_price,
            "freight": freight,
            "total_per_tonne": total_per_tonne,
            "total_cost": total_cost,
            "transit_days": source["Transit_Days"],
            "risk": source["Risk"]
        })

    source_results.sort(
        key=lambda x: x["total_per_tonne"]
    )

    # -----------------------------
    # Vessel filtering
    # -----------------------------

    eligible_vessels = []
    rejected_vessels = []

    for vessel in vessel_data:

        capacity = float(vessel["Capacity"])
        loa = float(vessel["LOA"])
        beam = float(vessel["Beam"])
        draft = float(vessel["Draft"])

        capacity_ok = capacity >= quantity
        loa_ok = loa <= max_loa
        beam_ok = beam <= max_beam
        draft_ok = draft <= max_draft

        if capacity_ok and loa_ok and beam_ok and draft_ok:

            eligible_vessels.append({
                "type": vessel["Vessel_Type"],
                "capacity": capacity,
                "loa": loa,
                "beam": beam,
                "draft": draft
            })

        else:

            reasons = []

            if not capacity_ok:
                reasons.append("Insufficient capacity")

            if not loa_ok:
                reasons.append("LOA exceeds port limit")

            if not beam_ok:
                reasons.append("Beam exceeds port limit")

            if not draft_ok:
                reasons.append("Draft exceeds port limit")

            rejected_vessels.append({
                "type": vessel["Vessel_Type"],
                "reason": ", ".join(reasons)
            })

    # -----------------------------
    # Best source
    # -----------------------------

    best_source = (
        source_results[0]
        if source_results
        else None
    )
    route = None

    if best_source:
        route = get_route(
        best_source["export_port"],
        destination
    )

    # -----------------------------
    # Final recommendation
    # -----------------------------

    if best_source and eligible_vessels:

        recommended_vessel = eligible_vessels[0]

        recommendation = (
            f"Source from {best_source['country']} through "
            f"{best_source['export_port']} and consider a "
            f"{recommended_vessel['type']} vessel. "
            f"Destination weather risk is {weather['risk']}."
        )

    elif best_source:

        recommendation = (
            "A suitable vessel could not be found for the "
            "entered cargo quantity and destination port."
        )

    else:

        recommendation = "No suitable sourcing data found."

    # -----------------------------
    # Send results to HTML
    # -----------------------------

    return render_template(
    "index.html",
    material=material,
    quantity=quantity,
    origin=origin,
    destination=destination,
    port=selected_port,
    source_results=source_results,
    best_source=best_source,
    eligible_vessels=eligible_vessels,
    rejected_vessels=rejected_vessels,
    recommendation=recommendation,
    route=route,
    weather=weather
)

if __name__ == "__main__":
    app.run(debug=True)