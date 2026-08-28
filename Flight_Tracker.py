import json
import math
import os
import time
import urllib.request
from datetime import datetime

# ============================================================
# REAL-TIME FLIGHT TRACKER
# Powered by OpenSky Network API
# ============================================================

API_URL = "https://opensky-network.org/api/states/all"

REFRESH_SECONDS = 8
DISPLAY_COUNT = 50
REQUEST_TIMEOUT = 20


# ============================================================
# BASIC FUNCTIONS
# ============================================================

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def pause():
    input("\nPress ENTER to continue...")


def get_flights():
    """Retrieve current aircraft state data from OpenSky."""

    request = urllib.request.Request(
        API_URL,
        headers={
            "User-Agent": "Real-Time-Flight-Tracker/1.0"
        }
    )

    with urllib.request.urlopen(
        request,
        timeout=REQUEST_TIMEOUT
    ) as response:

        data = json.loads(
            response.read().decode("utf-8")
        )

    return data.get("states") or []


# ============================================================
# DATA CONVERSION / EXTRACTION
# ============================================================

def to_number(value):
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def get_callsign(flight):
    if len(flight) > 1 and flight[1]:
        return flight[1].strip()

    return "UNKNOWN"


def get_country(flight):
    if len(flight) > 2 and flight[2]:
        return flight[2]

    return "UNKNOWN"


def get_altitude_feet(flight):
    """
    OpenSky altitude is provided in meters.
    Convert meters to feet.
    """

    if len(flight) <= 7:
        return None

    altitude_meters = to_number(flight[7])

    if altitude_meters is None:
        return None

    return altitude_meters * 3.28084


def get_speed_mph(flight):
    """
    OpenSky velocity is provided in meters/second.
    Convert m/s to MPH.
    """

    if len(flight) <= 9:
        return None

    velocity = to_number(flight[9])

    if velocity is None:
        return None

    return velocity * 2.23694


def get_heading(flight):

    if len(flight) <= 10:
        return None

    return to_number(flight[10])


def get_vertical_rate(flight):
    """
    OpenSky vertical rate is meters/second.
    Convert to feet/minute.
    """

    if len(flight) <= 11:
        return None

    rate = to_number(flight[11])

    if rate is None:
        return None

    return rate * 196.8504


def get_latitude(flight):

    if len(flight) <= 6:
        return None

    return to_number(flight[6])


def get_longitude(flight):

    if len(flight) <= 5:
        return None

    return to_number(flight[5])


# ============================================================
# DISTANCE CALCULATION
# ============================================================

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate approximate distance between two coordinates
    using the Haversine formula.
    """

    if None in (lat1, lon1, lat2, lon2):
        return None

    earth_radius = 3958.7613  # miles

    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)

    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_lat / 2) ** 2
        +
        math.cos(lat1)
        *
        math.cos(lat2)
        *
        math.sin(delta_lon / 2) ** 2
    )

    distance = (
        2
        *
        earth_radius
        *
        math.asin(math.sqrt(a))
    )

    return distance


# ============================================================
# DISPLAY TABLE
# ============================================================

def display_table(flights, title="LIVE FLIGHTS"):

    print("=" * 112)
    print(f"✈ {title}")
    print("=" * 112)

    print(
        f"{'FLIGHT':<12}"
        f"{'COUNTRY':<22}"
        f"{'ALTITUDE':>14}"
        f"{'SPEED':>12}"
        f"{'HEADING':>11}"
        f"{'ICAO24':>10}"
    )

    print("-" * 112)

    for flight in flights[:DISPLAY_COUNT]:

        callsign = get_callsign(flight)
        country = get_country(flight)

        altitude = get_altitude_feet(flight)
        speed = get_speed_mph(flight)
        heading = get_heading(flight)

        icao24 = (
            flight[0]
            if len(flight) > 0 and flight[0]
            else "UNKNOWN"
        )

        if altitude is not None:
            altitude_text = f"{altitude:,.0f} ft"
        else:
            altitude_text = "GROUND"

        if speed is not None:
            speed_text = f"{speed:,.0f} mph"
        else:
            speed_text = "N/A"

        if heading is not None:
            heading_text = f"{heading:,.0f}°"
        else:
            heading_text = "N/A"

        print(
            f"{callsign[:11]:<12}"
            f"{country[:21]:<22}"
            f"{altitude_text:>14}"
            f"{speed_text:>12}"
            f"{heading_text:>11}"
            f"{icao24:>10}"
        )

    print("-" * 112)

    print(
        f"Showing "
        f"{min(len(flights), DISPLAY_COUNT)} "
        f"of {len(flights):,} aircraft."
    )


# ============================================================
# OPTION 1
# SHOW FLIGHTS NEAR A LOCATION
# ============================================================

def flights_near_location():

    clear_screen()

    print("=" * 60)
    print("✈ FLIGHTS NEAR A LOCATION")
    print("=" * 60)
    print()

    try:

        latitude = float(
            input("Enter latitude: ")
        )

        longitude = float(
            input("Enter longitude: ")
        )

        radius = float(
            input("Search radius in miles: ")
        )

        if radius <= 0:
            print("\n❌ Radius must be greater than zero.")
            pause()
            return

        print("\n📡 Getting live aircraft data...")

        flights = get_flights()

        nearby = []

        for flight in flights:

            distance = calculate_distance(
                latitude,
                longitude,
                get_latitude(flight),
                get_longitude(flight)
            )

            if distance is not None and distance <= radius:

                nearby.append(
                    (distance, flight)
                )

        nearby.sort(
            key=lambda item: item[0]
        )

        clear_screen()

        print("=" * 100)
        print(
            f"✈ AIRCRAFT WITHIN "
            f"{radius:g} MILES"
        )
        print("=" * 100)

        if not nearby:

            print(
                "\nNo aircraft were found "
                "within that radius."
            )

            pause()
            return

        print(
            f"{'FLIGHT':<12}"
            f"{'COUNTRY':<22}"
            f"{'DISTANCE':>12}"
            f"{'ALTITUDE':>16}"
            f"{'SPEED':>14}"
        )

        print("-" * 100)

        for distance, flight in nearby[:DISPLAY_COUNT]:

            altitude = get_altitude_feet(flight)
            speed = get_speed_mph(flight)

            altitude_text = (
                f"{altitude:,.0f} ft"
                if altitude is not None
                else "GROUND"
            )

            speed_text = (
                f"{speed:,.0f} mph"
                if speed is not None
                else "N/A"
            )

            print(
                f"{get_callsign(flight)[:11]:<12}"
                f"{get_country(flight)[:21]:<22}"
                f"{distance:>9.1f} mi"
                f"{altitude_text:>16}"
                f"{speed_text:>14}"
            )

        print("-" * 100)

        print(
            f"Found {len(nearby):,} aircraft."
        )

        print(
            f"Showing up to {DISPLAY_COUNT}."
        )

        pause()

    except ValueError:

        print(
            "\n❌ Please enter valid numbers."
        )

        pause()

    except Exception as error:

        print(
            f"\n❌ Error: {error}"
        )

        pause()


# ============================================================
# OPTION 2
# SEARCH BY CALLSIGN
# ============================================================

def search_by_callsign():

    clear_screen()

    print("=" * 60)
    print("✈ SEARCH FLIGHT BY CALLSIGN")
    print("=" * 60)
    print()

    query = input(
        "Enter callsign: "
    ).strip().upper()

    if not query:
        return

    try:

        print("\n📡 Searching live data...")

        flights = get_flights()

        matches = []

        for flight in flights:

            if query in get_callsign(
                flight
            ).upper():

                matches.append(flight)

        clear_screen()

        if not matches:

            print(
                f"No active aircraft found "
                f"matching '{query}'."
            )

            pause()
            return

        display_table(
            matches,
            f"CALLSIGN SEARCH: {query}"
        )

        pause()

    except Exception as error:

        print(
            f"\n❌ Error: {error}"
        )

        pause()


# ============================================================
# OPTION 3
# TRACK SPECIFIC AIRCRAFT
# ============================================================

def track_aircraft():

    clear_screen()

    print("=" * 60)
    print("✈ TRACK A SPECIFIC AIRCRAFT")
    print("=" * 60)
    print()

    query = input(
        "Enter callsign or ICAO24: "
    ).strip().upper()

    if not query:
        return

    print(
        "\nTracking aircraft..."
    )

    while True:

        try:

            flights = get_flights()

            matches = []

            for flight in flights:

                flight_callsign = (
                    get_callsign(flight)
                    .upper()
                )

                icao24 = (
                    flight[0].upper()
                    if len(flight) > 0
                    and flight[0]
                    else ""
                )

                if (
                    query == flight_callsign
                    or query == icao24
                ):

                    matches.append(flight)

            clear_screen()

            if not matches:

                print("=" * 70)
                print("✈ AIRCRAFT TRACKING")
                print("=" * 70)

                print(
                    f"\n❌ Aircraft '{query}' "
                    "is not currently transmitting."
                )

            else:

                flight = matches[0]

                altitude = (
                    get_altitude_feet(flight)
                )

                speed = (
                    get_speed_mph(flight)
                )

                heading = (
                    get_heading(flight)
                )

                vertical_rate = (
                    get_vertical_rate(flight)
                )

                latitude = (
                    get_latitude(flight)
                )

                longitude = (
                    get_longitude(flight)
                )

                print("=" * 70)
                print("✈ AIRCRAFT TRACKING")
                print("=" * 70)

                print(
                    f"Callsign:       "
                    f"{get_callsign(flight)}"
                )

                print(
                    f"ICAO24:         "
                    f"{flight[0]}"
                )

                print(
                    f"Country:        "
                    f"{get_country(flight)}"
                )

                if altitude is not None:

                    print(
                        f"Altitude:       "
                        f"{altitude:,.0f} ft"
                    )

                else:

                    print(
                        "Altitude:       GROUND"
                    )

                if speed is not None:

                    print(
                        f"Speed:          "
                        f"{speed:,.0f} mph"
                    )

                else:

                    print(
                        "Speed:          N/A"
                    )

                if heading is not None:

                    print(
                        f"Heading:        "
                        f"{heading:,.0f}°"
                    )

                else:

                    print(
                        "Heading:        N/A"
                    )

                if vertical_rate is not None:

                    print(
                        f"Vertical Rate:  "
                        f"{vertical_rate:+,.0f} ft/min"
                    )

                else:

                    print(
                        "Vertical Rate:  N/A"
                    )

                if latitude is not None:

                    print(
                        f"Latitude:       "
                        f"{latitude:.5f}"
                    )

                else:

                    print(
                        "Latitude:       N/A"
                    )

                if longitude is not None:

                    print(
                        f"Longitude:      "
                        f"{longitude:.5f}"
                    )

                else:

                    print(
                        "Longitude:      N/A"
                    )

                print("=" * 70)

            print(
                f"\nLast update: "
                f"{datetime.now():%Y-%m-%d %H:%M:%S}"
            )

            print(
                f"Refreshing every "
                f"{REFRESH_SECONDS} seconds."
            )

            print(
                "\nPress CTRL+C to return "
                "to the main menu."
            )

            time.sleep(
                REFRESH_SECONDS
            )

        except KeyboardInterrupt:

            return

        except Exception as error:

            clear_screen()

            print(
                "❌ TRACKING ERROR"
            )

            print(
                f"\n{error}"
            )

            print(
                f"\nRetrying in "
                f"{REFRESH_SECONDS} seconds..."
            )

            time.sleep(
                REFRESH_SECONDS
            )


# ============================================================
# OPTION 4
# FLIGHTS BY COUNTRY
# ============================================================

def flights_by_country():

    clear_screen()

    print("=" * 60)
    print("✈ FLIGHTS BY COUNTRY")
    print("=" * 60)
    print()

    query = input(
        "Enter country name: "
    ).strip().lower()

    if not query:
        return

    try:

        print(
            "\n📡 Getting live data..."
        )

        flights = get_flights()

        matches = []

        for flight in flights:

            if query in get_country(
                flight
            ).lower():

                matches.append(flight)

        clear_screen()

        if not matches:

            print(
                f"No active aircraft found "
                f"for '{query}'."
            )

            pause()
            return

        display_table(
            matches,
            f"FLIGHTS: {query.upper()}"
        )

        pause()

    except Exception as error:

        print(
            f"\n❌ Error: {error}"
        )

        pause()


# ============================================================
# OPTION 5 / 6
# HIGHEST OR FASTEST AIRCRAFT
# ============================================================

def ranked_aircraft(mode):

    clear_screen()

    try:

        print(
            "📡 Getting live aircraft data..."
        )

        flights = get_flights()

        if mode == "highest":

            usable = [
                flight
                for flight in flights
                if get_altitude_feet(
                    flight
                ) is not None
            ]

            results = sorted(
                usable,
                key=get_altitude_feet,
                reverse=True
            )

            title = "HIGHEST AIRCRAFT"

        else:

            usable = [
                flight
                for flight in flights
                if get_speed_mph(
                    flight
                ) is not None
            ]

            results = sorted(
                usable,
                key=get_speed_mph,
                reverse=True
            )

            title = "FASTEST AIRCRAFT"

        clear_screen()

        display_table(
            results,
            title
        )

        pause()

    except Exception as error:

        print(
            f"\n❌ Error: {error}"
        )

        pause()


# ============================================================
# OPTION 7
# AUTOMATIC LIVE REFRESH
# ============================================================

def automatic_refresh():

    while True:

        try:

            flights = get_flights()

            clear_screen()

            print(
                f"Last update: "
                f"{datetime.now():%Y-%m-%d %H:%M:%S}"
            )

            print(
                f"Active aircraft: "
                f"{len(flights):,}"
            )

            print(
                f"Automatically refreshing every "
                f"{REFRESH_SECONDS} seconds..."
            )

            print()

            display_table(
                flights,
                "LIVE FLIGHT DATA"
            )

            print(
                "\nPress CTRL+C to return "
                "to the main menu."
            )

            time.sleep(REFRESH_SECONDS)

        except KeyboardInterrupt:

            return

        except Exception as error:

            clear_screen()

            print(
                "❌ Error retrieving flight data:"
            )

            print(error)

            print(
                f"\nRetrying in "
                f"{REFRESH_SECONDS} seconds..."
            )

            time.sleep(REFRESH_SECONDS)

# ============================================================
# MAIN MENU
# ============================================================

def main_menu():

    while True:

        clear_screen()

        print("=" * 62)
        print(
            " " * 15 +
            "✈ REAL-TIME FLIGHT TRACKER"
        )
        print("=" * 62)

        print(
            "1. Show flights near me"
        )

        print(
            "2. Search flight by callsign"
        )

        print(
            "3. Track a specific aircraft"
        )

        print(
            "4. Show flights by country"
        )

        print(
            "5. Show highest aircraft"
        )

        print(
            "6. Show fastest aircraft"
        )

        print(
            "7. Automatic live flight data"
        )

        print(
            "8. Exit"
        )

        print("=" * 62)

        choice = input(
            "Select an option: "
        ).strip()

        if choice == "1":

            flights_near_location()

        elif choice == "2":

            search_by_callsign()

        elif choice == "3":

            track_aircraft()

        elif choice == "4":

            flights_by_country()

        elif choice == "5":

            ranked_aircraft(
                "highest"
            )

        elif choice == "6":

            ranked_aircraft(
                "fastest"
            )

        elif choice == "7":

            automatic_refresh()

        elif choice == "8":

            clear_screen()

            print(
                "✈ Flight Tracker closed."
            )

            break

        else:

            print(
                "\n❌ Invalid option. "
                "Choose 1-8."
            )

            time.sleep(1.5)


# ============================================================
# PROGRAM START
# ============================================================

if __name__ == "__main__":

    main_menu()