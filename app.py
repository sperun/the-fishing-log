import streamlit as st
import json
import os
from datetime import date
import pandas as pd
import matplotlib.pyplot as plt

# --- Config ---
DATA_FILE = "fishing_log.json"
DEFAULT_ANGERS = ["Dad", "Alek"]
DEFAULT_SPECIES = [
    "Bluegill", "Green Sunfish", "Black Crappie", "White Crappie",
    "Largemouth Bass", "Smallmouth Bass", "Bluefish",
    "Summer Flounder", "Winter Flounder",
    "Trout - Rainbow", "Trout - Brown", "Trout - Brook"
]
DEFAULT_WEATHER = ["Sunny", "Cloudy", "Rainy", "Windy", "Cold", "Hot"]

# --- Load/Initialize Data ---
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
else:
    data = {
        "trips": [],
        "locations": [],
        "anglers": DEFAULT_ANGERS,
        "species": DEFAULT_SPECIES
    }

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- Streamlit UI ---
st.set_page_config(page_title="Alek and Dad's Fishing Log", layout="wide")
st.title("🎣 Alek and Dad's Fishing Log")

# Tabs
tab1, tab2, tab3 = st.tabs(["Log a Trip", "Stats", "View/Edit Trips"])

# === TAB 1: LOG A TRIP ===
with tab1:
    st.header("📝 New Trip Entry")
    if "edit_trip_index" in st.session_state:
        edit_mode = True
        trip_index = st.session_state.pop("edit_trip_index")
        trip = data["trips"][trip_index]
        trip_date = date.fromisoformat(trip["date"])
        location = trip["location"]
        weather = trip["weather"]
        selected_anglers = trip["anglers"]
        blanked = trip["blanked"]
        catches = trip.get("catches", {})
    else:
        edit_mode = False
        trip_date = date.today()
        location = ""
        weather = DEFAULT_WEATHER[0]
        selected_anglers = []
        blanked = False
        catches = {}

    trip_date = st.date_input("Date of Trip", trip_date)
    location = st.selectbox("Location", options=data["locations"] + ["Add new..."], index=data["locations"].index(location) if location in data["locations"] else len(data["locations"]))
    if location == "Add new...":
        new_location = st.text_input("Enter new location")
        if new_location:
            location = new_location
            if location not in data["locations"]:
                data["locations"].append(location)

    weather = st.selectbox("Weather", options=DEFAULT_WEATHER, index=DEFAULT_WEATHER.index(weather) if weather in DEFAULT_WEATHER else 0)

    st.subheader("Anglers on Trip")
    col1, col2 = st.columns([3, 1])
    with col1:
        selected_anglers = st.multiselect("Choose anglers", data["anglers"], default=selected_anglers)
    with col2:
        new_angler = st.text_input("➕ Add new angler")
        if new_angler and new_angler not in data["anglers"]:
            data["anglers"].append(new_angler)
            selected_anglers.append(new_angler)

    blanked = st.checkbox("Check if no fish were caught", value=blanked)
    angler_catches = {}

    if not blanked:
        st.subheader("Fish Caught (Per Angler)")

        for angler in selected_anglers:
            st.markdown(f"**{angler}'s Catch**")
            if f"catch_rows_{angler}" not in st.session_state:
                if catches.get(angler):
                    st.session_state[f"catch_rows_{angler}"] = [{"id": i} for i in range(len(catches[angler]))]
                else:
                    st.session_state[f"catch_rows_{angler}"] = [{"id": 0}]

            catch_rows = st.session_state[f"catch_rows_{angler}"]
            updated_rows = []

            for i, row in enumerate(catch_rows):
                cols = st.columns([3, 1, 1])
                species_default = catches.get(angler, [{}])[i].get("species") if i < len(catches.get(angler, [])) else ""
                count_default = catches.get(angler, [{}])[i].get("count", 0) if i < len(catches.get(angler, [])) else 0
                with cols[0]:
                    species = st.selectbox(
                        f"Species #{i+1} ({angler})",
                        options=data["species"] + ["Add new..."],
                        key=f"species_{angler}_{i}",
                        index=(data["species"].index(species_default) if species_default in data["species"] else len(data["species"])) if species_default else 0
                    )
                    if species == "Add new...":
                        new_species = st.text_input(f"Enter new species ({angler})", key=f"new_species_{angler}_{i}")
                        if new_species:
                            species = new_species
                            if species not in data["species"]:
                                data["species"].append(species)
                with cols[1]:
                    count = st.number_input(f"Count ({angler} - #{i+1})", min_value=0, step=1, key=f"count_{angler}_{i}", value=count_default)
                with cols[2]:
                    if i > 0:
                        if st.button("🗑️ Remove", key=f"remove_{angler}_{i}"):
                            continue
                updated_rows.append({"id": i, "species": species, "count": count})

            st.session_state[f"catch_rows_{angler}"] = updated_rows

            if st.button(f"➕ Add species for {angler}", key=f"add_species_{angler}"):
                next_id = max([r["id"] for r in catch_rows] + [0]) + 1
                catch_rows.append({"id": next_id})
                st.session_state[f"catch_rows_{angler}"] = catch_rows

            # Collect catches
            angler_catches[angler] = []
            for row in st.session_state[f"catch_rows_{angler}"]:
                species = st.session_state.get(f"species_{angler}_{row['id']}")
                count = st.session_state.get(f"count_{angler}_{row['id']}", 0)
                if species and count > 0:
                    angler_catches[angler].append({"species": species, "count": count})

    if st.button("✅ Save Trip Log"):
        trip_entry = {
            "date": trip_date.isoformat(),
            "location": location,
            "weather": weather,
            "anglers": selected_anglers,
            "blanked": blanked,
            "catches": angler_catches if not blanked else {}
        }
        if edit_mode:
            data["trips"][trip_index] = trip_entry
            st.success("Trip updated!")
        else:
            data["trips"].append(trip_entry)
            st.success("Trip logged!")
        save_data()
        for key in list(st.session_state.keys()):
            if key.startswith("catch_rows_") or key.startswith("species_") or key.startswith("count_") or key.startswith("new_species_"):
                del st.session_state[key]
        st.experimental_rerun()

# === TAB 2: STATS ===
with tab2:
    st.header("📊 Fishing Stats")

    angler_totals = {}
    species_totals = {}

    for trip in data["trips"]:
        if trip["blanked"]:
            continue
        for angler, catches in trip["catches"].items():
            for entry in catches:
                species = entry["species"]
                count = entry["count"]
                angler_totals.setdefault(angler, {}).setdefault(species, 0)
                angler_totals[angler][species] += count
                species_totals.setdefault(species, 0)
                species_totals[species] += count

    st.subheader("🎣 Total Catches by Angler")
    for angler, catch in angler_totals.items():
        st.markdown(f"**{angler}**")
        for species, count in catch.items():
            st.write(f"• {species}: {count}")

    st.subheader("📊 Bar Chart: Total Fish per Angler")
    chart1_data = {"Angler": [], "Total Fish": []}
    for angler, catches in angler_totals.items():
        chart1_data["Angler"].append(angler)
        chart1_data["Total Fish"].append(sum(catches.values()))
    if chart1_data["Angler"]:
        st.bar_chart(chart1_data)

    st.subheader("🐟 Total Catches by Species")
    for species, count in species_totals.items():
        st.write(f"• {species}: {count}")

    st.subheader("🥧 Pie Chart: Total Catches by Species")
    if species_totals:
        df_species = pd.DataFrame.from_dict(species_totals, orient='index', columns=['Count'])
        df_species = df_species[df_species['Count'] > 0]
        fig, ax = plt.subplots()
        ax.pie(df_species['Count'], labels=df_species.index, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')
        st.pyplot(fig)

# === TAB 3: VIEW / EDIT TRIPS ===
with tab3:
    st.header("🧾 View Past Trips")

    col1, col2, col3 = st.columns(3)
    with col1:
        filter_location = st.selectbox("Filter by location", ["All"] + data["locations"])
    with col2:
        filter_weather = st.selectbox("Filter by weather", ["All"] + DEFAULT_WEATHER)
    with col3:
        filter_angler = st.selectbox("Filter by angler", ["All"] + data["anglers"])

    for idx, trip in enumerate(reversed(data["trips"])):
        actual_index = len(data["trips"]) - 1 - idx
        match = True
        if filter_location != "All" and trip["location"] != filter_location:
            match = False
        if filter_weather != "All" and trip["weather"] != filter_weather:
            match = False
        if filter_angler != "All" and filter_angler not in trip["anglers"]:
            match = False
        if not match:
            continue

        st.markdown(f"### 📅 {trip['date']} at {trip['location']} ({trip['weather']})")
        st.write(f"Anglers: {', '.join(trip['anglers'])}")
        if trip["blanked"]:
            st.info("No fish were caught on this trip.")
        else:
            for angler, catches in trip["catches"].items():
                st.markdown(f"**{angler}**")
                for entry in catches:
                    st.write(f"• {entry['species']}: {entry['count']}")

        if st.button("✏️ Edit Trip", key=f"edit_trip_{actual_index}"):
            st.session_state["edit_trip_index"] = actual_index
            st.experimental_rerun()

        st.markdown("---")
