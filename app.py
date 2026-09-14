from flask import Flask, render_template, request
import csv

app = Flask(__name__)


# -----------------------------
# Function to read CSV files
# -----------------------------
def read_csv(filename):
    with open(filename, "r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


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

    # Read our datasets
    sourcing_data = read_csv("data/sourcing.csv")
    vessel_data = read_csv("data/vessels.csv")
    port_data = read_csv("data/ports.csv")

    # Find destination port
    selected_port = None

    for port in port_data:
        if port["Port"] == destination:
            selected_port = port
            break

    if selected_port is None:
        return "Destination port not found."

    # Convert port restrictions into numbers
    max_loa = float(selected_port["Max_LOA"])
    max_beam = float(selected_port["Max_Beam"])
    max_draft = float(selected_port["Max_Draft"])

    # --------------------------------
    # Calculate source country ranking
    # --------------------------------
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

    # Sort countries by total landed cost
    source_results.sort(key=lambda x: x["total_per_tonne"])

    # --------------------------------
    # Vessel filtering
    # --------------------------------
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

    # --------------------------------
    # Best source
    # --------------------------------
    best_source = source_results[0] if source_results else None

    # --------------------------------
    # Final recommendation
    # --------------------------------
    if best_source and eligible_vessels:

        recommended_vessel = eligible_vessels[0]

        recommendation = (
            f"Source from {best_source['country']} through "
            f"{best_source['export_port']} and consider a "
            f"{recommended_vessel['type']} vessel."
        )

    elif best_source:

        recommendation = (
            "A suitable vessel could not be found for the entered "
            "cargo quantity and destination port."
        )

    else:

        recommendation = "No suitable sourcing data found."

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
        recommendation=recommendation
    )


if __name__ == "__main__":
    app.run(debug=True)