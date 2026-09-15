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

        # Check if API request was successful
        response.raise_for_status()

        data = response.json()

        current = data.get("current", {})
        daily = data.get("daily", {})

        temperature = current.get("temperature_2m")
        wind_speed = current.get("wind_speed_10m")
        precipitation = current.get("precipitation")

        rain_probability_list = daily.get(
            "precipitation_probability_max", []
        )

        rain_probability = (
            rain_probability_list[0]
            if rain_probability_list
            else 0
        )

        # Risk calculation
        if wind_speed is None:
            risk = "Unavailable"
        elif wind_speed >= 40 or rain_probability >= 80:
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

    except Exception as e:

        print("WEATHER ERROR:", destination, e)

        return {
            "temperature": "N/A",
            "wind_speed": "N/A",
            "precipitation": "N/A",
            "rain_probability": "N/A",
            "risk": "Unavailable"
        }
    
# ================= ROUTE ANALYSIS =================

# Destination port coordinates

port_coordinates = {
    "Paradip": (20.27, 86.68),
    "Vizag": (17.69, 83.22),
    "Gangavaram": (17.63, 83.27),
    "Gopalpur": (19.27, 84.88),
    "Dhamra": (20.78, 86.95),
    "Sagar-Sandheads": (21.65, 88.00),
    "Haldia": (22.03, 88.06)
}


# Export port coordinates
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


# -------------------------------------------------
# Country mapping
# -------------------------------------------------

export_port_country = {

    "Newcastle": "Australia",
    "Port Hedland": "Australia",
    "Gladstone": "Australia",
    "Weipa": "Australia",

    "Taboneo": "Indonesia",
    "Surabaya": "Indonesia",
    "Balikpapan": "Indonesia",

    "Maputo": "Mozambique",

    "New Orleans": "USA",
    "Mobile": "USA",

    "Vostochny": "Russia",

    "Tubarao": "Brazil"
}


# -------------------------------------------------
# Offshore route corridors
# -------------------------------------------------
#
# These are visual maritime corridors.
# They are NOT navigation-grade routes.
#
# Destination-specific Indian Ocean approaches
# are used so that all Indian ports don't share
# exactly the same final route.
# -------------------------------------------------

base_corridors = {

    # Australia
    "Australia": [
        (-25.0, 150.0),
        (-22.0, 140.0),
        (-18.0, 130.0),
        (-13.0, 120.0),
        (-8.0, 112.0),
        (-3.0, 105.0),
        (3.0, 100.0),
        (8.0, 95.0),
        (12.0, 92.0)
    ],

    # Indonesia
    "Indonesia": [
        (-5.0, 110.0),
        (0.0, 105.0),
        (5.0, 100.0),
        (8.0, 96.0),
        (11.0, 93.0),
        (13.0, 91.0)
    ],

    # Mozambique
    "Mozambique": [
        (-25.0, 40.0),
        (-27.0, 48.0),
        (-24.0, 55.0),
        (-19.0, 62.0),
        (-13.0, 69.0),
        (-7.0, 76.0),
        (-1.0, 82.0),
        (6.0, 87.0),
        (12.0, 91.0)
    ],

    # USA Gulf -> Atlantic -> Cape of Good Hope
    "USA": [
        (25.0, -80.0),
        (15.0, -65.0),
        (5.0, -50.0),
        (-8.0, -30.0),
        (-20.0, -15.0),
        (-32.0, 5.0),
        (-35.0, 20.0),
        (-30.0, 35.0),
        (-20.0, 50.0),
        (-10.0, 65.0),
        (0.0, 78.0),
        (7.0, 85.0),
        (12.0, 91.0)
    ],

    # Russia Pacific
    "Russia": [
        (40.0, 140.0),
        (32.0, 135.0),
        (24.0, 130.0),
        (16.0, 125.0),
        (8.0, 120.0),
        (2.0, 112.0),
        (5.0, 103.0),
        (9.0, 97.0),
        (12.0, 92.0)
    ],

    # Brazil -> Cape -> Indian Ocean
    "Brazil": [
        (-10.0, -35.0),
        (-20.0, -20.0),
        (-30.0, -5.0),
        (-35.0, 15.0),
        (-30.0, 35.0),
        (-20.0, 50.0),
        (-10.0, 65.0),
        (-2.0, 77.0),
        (5.0, 84.0),
        (12.0, 91.0)
    ]
}


# -------------------------------------------------
# Destination-specific Indian coastline approaches
# -------------------------------------------------

destination_approaches = {

    "Vizag": [
        (12.0, 91.0),
        (14.0, 88.5),
        (16.0, 86.0),
        (17.0, 84.5),
        (17.69, 83.22)
    ],

    "Gangavaram": [
        (12.0, 91.0),
        (14.0, 88.5),
        (16.0, 86.0),
        (17.0, 84.5),
        (17.63, 83.27)
    ],

    "Gopalpur": [
        (12.0, 91.0),
        (14.0, 89.0),
        (16.5, 87.5),
        (18.0, 86.0),
        (19.27, 84.88)
    ],

    "Paradip": [
        (12.0, 91.0),
        (14.0, 90.0),
        (17.0, 88.5),
        (19.0, 87.5),
        (20.27, 86.68)
    ],

    "Dhamra": [
        (12.0, 91.0),
        (14.5, 90.5),
        (17.5, 89.5),
        (19.5, 88.5),
        (20.78, 86.95)
    ],

    "Sagar-Sandheads": [
        (12.0, 91.0),
        (15.0, 91.0),
        (18.0, 90.5),
        (20.0, 89.5),
        (21.65, 88.00)
    ],

    "Haldia": [
        (12.0, 91.0),
        (15.0, 91.0),
        (18.0, 90.5),
        (20.0, 89.5),
        (21.5, 88.5),
        (22.03, 88.06)
    ]
}


# -------------------------------------------------
# Distance calculation
# -------------------------------------------------

def calculate_distance(lat1, lon1, lat2, lon2):

    from math import radians, sin, cos, sqrt, atan2

    R = 3440.065

    lat1 = radians(lat1)
    lon1 = radians(lon1)

    lat2 = radians(lat2)
    lon2 = radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        sin(dlat / 2) ** 2
        + cos(lat1)
        * cos(lat2)
        * sin(dlon / 2) ** 2
    )

    c = 2 * atan2(
        sqrt(a),
        sqrt(1 - a)
    )

    return R * c


# -------------------------------------------------
# Generate maritime route
# -------------------------------------------------

def get_route(export_port, destination):

    if export_port not in export_port_coordinates:
        return None

    if destination not in port_coordinates:
        return None

    start = export_port_coordinates[export_port]

    country = export_port_country.get(
        export_port,
        "Australia"
    )

    base_route = base_corridors.get(
        country,
        []
    )

    final_approach = destination_approaches.get(
        destination,
        []
    )

    # Build complete route
    route_points = [start]

    route_points.extend(base_route)

    # Remove duplicate point if corridor
    # and approach start at same location
    for point in final_approach:

        if not route_points:
            route_points.append(point)
            continue

        previous = route_points[-1]

        distance = calculate_distance(
            previous[0],
            previous[1],
            point[0],
            point[1]
        )

        if distance > 10:
            route_points.append(point)

    # Always make sure the exact destination
    # is the final point
    destination_point = port_coordinates[destination]

    previous = route_points[-1]

    if calculate_distance(
        previous[0],
        previous[1],
        destination_point[0],
        destination_point[1]
    ) > 1:

        route_points.append(destination_point)

    # -------------------------------------------------
    # Calculate total distance
    # -------------------------------------------------

    total_distance = 0

    for i in range(len(route_points) - 1):

        lat1, lon1 = route_points[i]
        lat2, lon2 = route_points[i + 1]

        total_distance += calculate_distance(
            lat1,
            lon1,
            lat2,
            lon2
        )

    # Prototype bulk carrier speed
    average_speed = 13

    transit_hours = total_distance / average_speed
    transit_days = transit_hours / 24

    return {

        "export_port": export_port,

        "destination": destination,

        "export_lat": start[0],
        "export_lon": start[1],

        "destination_lat": destination_point[0],
        "destination_lon": destination_point[1],

        "distance": round(total_distance),

        "transit_days": round(
            transit_days,
            1
        ),

        "speed": average_speed,

        "route_points": [
            {
                "lat": point[0],
                "lon": point[1]
            }
            for point in route_points
        ]
    }

# ================= FREIGHT PRICE TREND =================

def get_freight_trend(export_port, material):

    # Demo monthly freight prices ($/tonne)
    # Replace these values with actual historical data later

    freight_data = {

        "Newcastle": {
            "Coal": [34, 36, 35, 38, 40, 37, 35, 33, 36, 39, 41, 38]
        },

        "Taboneo": {
            "Coal": [18, 19, 20, 18, 17, 19, 21, 20, 18, 17, 19, 20]
        },

        "Maputo": {
            "Coal": [32, 34, 33, 35, 37, 36, 34, 32, 35, 38, 36, 34]
        },

        "New Orleans": {
            "Coal": [40, 42, 44, 41, 39, 43, 45, 44, 42, 40, 43, 46]
        },

        "Vostochny": {
            "Coal": [38, 40, 42, 39, 37, 41, 43, 42, 40, 38, 41, 44]
        },

        "Port Hedland": {
            "Iron Ore": [22, 24, 23, 25, 27, 26, 24, 23, 25, 28, 26, 24]
        },

        "Tubarao": {
            "Iron Ore": [30, 32, 34, 31, 29, 33, 35, 34, 32, 30, 33, 36]
        },

        "Gladstone": {
            "Limestone": [18, 19, 21, 20, 18, 17, 19, 21, 20, 18, 19, 22]
        },

        "Surabaya": {
            "Limestone": [20, 21, 19, 18, 20, 22, 21, 19, 18, 20, 22, 23]
        },

        "Mobile": {
            "Limestone": [30, 32, 31, 34, 36, 35, 33, 31, 34, 37, 35, 33]
        },

        "Weipa": {
            "Bauxite": [20, 21, 23, 22, 20, 19, 21, 23, 22, 20, 21, 24]
        },

        "Balikpapan": {
            "Bauxite": [18, 19, 20, 18, 17, 19, 21, 20, 18, 17, 19, 20]
        }
    }

    months = [
        "Jan", "Feb", "Mar", "Apr",
        "May", "Jun", "Jul", "Aug",
        "Sep", "Oct", "Nov", "Dec"
    ]

    prices = freight_data.get(export_port, {}).get(material)

    if not prices:
        return None

    return [
        {
            "month": months[i],
            "price": prices[i]
        }
        for i in range(12)
    ]

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

    cost_priority = float(
    request.form.get("cost_priority", 25)
)

    transit_priority = float(
    request.form.get("transit_priority", 25)
)

    trade_priority = float(
    request.form.get("trade_priority", 25)
)

    weather_priority = float(
    request.form.get("weather_priority", 25)
)

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

    best_source = source_results[0] if source_results else None
    route = None
    freight_trend = None

    if best_source:
        freight_trend = get_freight_trend(
        best_source["export_port"],
        material
    )

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
    weather=weather,
    freight_trend=freight_trend,

    cost_priority=cost_priority,
    transit_priority=transit_priority,
    trade_priority=trade_priority,
    weather_priority=weather_priority
)

if __name__ == "__main__":
    app.run(debug=True)