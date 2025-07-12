import requests
import json
import time
import threading
import os
import sys
from datetime import datetime
from flask import Flask, send_from_directory, jsonify, request

# Configuration
GRAPHQL_ENDPOINT = "https://emma.mav.hu//otp2-backend/otp/routers/default/index/graphql"
DATA_FILE = "live_data.json"
UPDATE_INTERVAL = 45  # seconds - reduced for faster updates
MAX_CONCURRENT_REQUESTS = 20  # Limit concurrent API calls

HEADERS = {
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.6",
    "Connection": "keep-alive",
    "Content-Type": "application/json",
    "Origin": "https://emma.mav.hu",
    "Referer": "https://emma.mav.hu/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Sec-GPC": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Brave";v="138"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"'
}

# Flask app setup
app = Flask(__name__, static_folder='static', static_url_path='')

def get_service_day():
    """Get current service day in YYYY-MM-DD format."""
    now = datetime.now()
    return now.strftime("%Y-%m-%d")

def fetch_vehicle_positions(session):
    """Fetch current vehicle positions from EMMA API."""
    query = '''
    {
        vehiclePositions(
          swLat: 45.5,
          swLon: 16.1,
          neLat: 48.7,
          neLon: 22.8,
          modes: [RAIL, RAIL_REPLACEMENT_BUS, COACH ,SUBURBAN_RAILWAY, TRAMTRAIN]
        ) {
          trip {
            gtfsId
            tripShortName
            tripHeadsign
            route {
              mode
            }
          }
          vehicleId
          lat
          lon
          label
          speed
          heading
        }
    }'''

    response = session.post(GRAPHQL_ENDPOINT, headers=HEADERS, json={"query": query})
    response.raise_for_status()
    return response.json()["data"]["vehiclePositions"]

def fetch_trip_details(session, gtfs_id, service_day):
    """Fetch detailed trip information for a specific train."""
    query = f'''
    {{
        trip(id: "{gtfs_id}", serviceDay: "{service_day}") {{
          gtfsId
          tripHeadsign
          trainCategoryName
          trainName
          route {{ 
            longName(language: "hu")
            shortName
          }}
          stoptimes {{
            stop {{
              name
              lat
              lon
              platformCode
            }}
            realtimeArrival
            realtimeDeparture
            arrivalDelay
            departureDelay
            scheduledArrival
            scheduledDeparture
          }}
        }}
    }}'''

    try:
        response = session.post(GRAPHQL_ENDPOINT, headers=HEADERS, json={"query": query}, timeout=10)
        response.raise_for_status()
        return response.json().get("data", {}).get("trip", {})
    except Exception as e:
        return {}

def update_train_data():
    """Update train data from EMMA API with optimized concurrent processing."""
    try:
        service_day = get_service_day()
        
        with requests.Session() as session:
            # Configure session for better performance
            session.headers.update(HEADERS)
            
            vehicles = fetch_vehicle_positions(session)
            
            all_data = {
                "lastUpdated": int(time.time()),
                "vehicles": []
            }

            # Process vehicles in batches for better performance
            from concurrent.futures import ThreadPoolExecutor, as_completed
            
            def process_vehicle(vehicle):
                trip = vehicle.get("trip")
                gtfs_id = trip.get("gtfsId") if trip else None
                
                if not gtfs_id:
                    return None
                    
                trip_details = fetch_trip_details(session, gtfs_id, service_day)

                trip_short_name = trip.get("tripShortName")
                trip_headsign = trip.get("tripHeadsign")
                vehicle_id = vehicle.get("vehicleId")
                lat = vehicle.get("lat")
                lon = vehicle.get("lon")
                label = vehicle.get("label")
                speed = vehicle.get("speed")
                heading = vehicle.get("heading")
                
                # Get mode from trip route
                trip_route = trip.get("route", {})
                mode = trip_route.get("mode") if trip_route else None
                
                train_cat = trip_details.get("trainCategoryName")
                train_name = trip_details.get("trainName")
                route = trip_details.get("route", {})
                route_long_name = route.get("longName") if route else None
                route_short_name = route.get("shortName") if route else None
                stop_times = trip_details.get("stoptimes", [])

                # Optimize stop data processing
                stops_compressed = []
                for stop in stop_times:
                    st = stop.get("stop", {})
                    stops_compressed.append({
                        "name": st.get("name"),
                        "ra": stop.get("realtimeArrival"),
                        "rd": stop.get("realtimeDeparture"),
                        "sa": stop.get("scheduledArrival"),
                        "sd": stop.get("scheduledDeparture"),
                        "a": stop.get("arrivalDelay"),
                        "d": stop.get("departureDelay"),
                        "v": st.get("platformCode")
                    })

                # Determine display name
                name = trip_short_name
                if route_long_name and len(route_long_name) < 6:
                    name = f"[{route_long_name}] {trip_short_name}"

                return {
                    "id": gtfs_id,
                    "name": name,
                    "headsgn": trip_headsign,
                    "lat": lat,
                    "lon": lon,
                    "sp": speed,
                    "hd": heading,
                    "mode": mode,
                    "stops": stops_compressed
                }
            
            # Process vehicles concurrently with limited threads
            with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_REQUESTS) as executor:
                future_to_vehicle = {executor.submit(process_vehicle, vehicle): vehicle for vehicle in vehicles}
                
                for future in as_completed(future_to_vehicle):
                    try:
                        result = future.result(timeout=15)
                        if result:
                            all_data["vehicles"].append(result)
                    except Exception as e:
                        vehicle = future_to_vehicle[future]
                        trip = vehicle.get("trip", {})
                        gtfs_id = trip.get("gtfsId", "unknown")
            
            # Save data to file
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(all_data, f, separators=(",", ":"), ensure_ascii=False)
            
    except Exception as e:
        pass

def data_updater_thread():
    """Background thread that periodically updates train data."""
    while True:
        update_train_data()
        time.sleep(UPDATE_INTERVAL)

# Flask routes
@app.route('/')
def serve_index():
    """Serve the main HTML page."""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/trip')
def serve_trip():
    """Serve the trip planning page."""
    return send_from_directory(app.static_folder, 'trip.html')

@app.route('/live_data.json')
def serve_train_data():
    """Serve the train data JSON file."""
    try:
        if os.path.exists(DATA_FILE):
            return send_from_directory('.', DATA_FILE)
        else:
            return jsonify({"error": "Data not available yet", "vehicles": [], "lastUpdated": 0})
    except Exception as e:
        return jsonify({"error": str(e), "vehicles": [], "lastUpdated": 0})

@app.route('/api/stations', methods=['GET'])
def search_stations():
    """Proxy station search requests to MAV API to avoid CORS issues."""
    try:
        query = request.args.get('q', '')
        limit = request.args.get('limit', '5')
        
        if not query or len(query) < 2:
            return jsonify({"error": "Query must be at least 2 characters long"}), 400
        
        # Make request to MAV API
        mav_url = f"https://emma.mav.hu/otp2-backend/otp/routers/default/geocode/stations?q={query}&limit={limit}"
        
        headers = {
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.8',
            'Connection': 'keep-alive',
            'Referer': 'https://emma.mav.hu/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-GPC': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Brave";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        }
        
        response = requests.get(mav_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({"error": f"MAV API returned status {response.status_code}"}), response.status_code
            
    except requests.exceptions.Timeout:
        return jsonify({"error": "Request timeout"}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Network error: {str(e)}"}), 503
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/api/plan', methods=['POST'])
def plan_trip():
    """Handle trip planning requests."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        from_coords = data.get('from')
        to_coords = data.get('to')
        num_itineraries = data.get('numItineraries', 3)
        date_time = data.get('dateTime')
        arrive_by = data.get('arriveBy', False)
        
        if not from_coords or not to_coords:
            return jsonify({"error": "From and to coordinates are required"}), 400
        
        if not isinstance(from_coords, dict) or not isinstance(to_coords, dict):
            return jsonify({"error": "Invalid coordinate format"}), 400
            
        if 'lat' not in from_coords or 'lon' not in from_coords or 'lat' not in to_coords or 'lon' not in to_coords:
            return jsonify({"error": "Missing lat/lon in coordinates"}), 400
        
        # Build query parameters
        query_params = [
            f'from: {{lat: {from_coords["lat"]}, lon: {from_coords["lon"]}}}',
            f'to: {{lat: {to_coords["lat"]}, lon: {to_coords["lon"]}}}',
            'numItineraries: 5',
            'transportModes: [{mode: RAIL}, {mode: COACH}, {mode: BUS}, {mode: TRAM}, {mode: SUBWAY}]',
            'walkReluctance: 2.0',
            'walkBoardCost: 600',
            'minTransferTime: 120',
            'maxWalkDistance: 2000'
        ]
        
        # Add date and time parameters if provided
        if date_time:
            # Parse local datetime format (YYYY-MM-DDTHH:MM) and split into date and time
            from datetime import datetime
            try:
                # Handle both ISO format with timezone and local format
                if 'T' in date_time:
                    if date_time.endswith('Z') or '+' in date_time or date_time.count(':') > 2:
                        # ISO format with timezone - convert from UTC
                        dt = datetime.fromisoformat(date_time.replace('Z', '+00:00'))
                    else:
                        # Local format (YYYY-MM-DDTHH:MM) - use as is
                        dt = datetime.fromisoformat(date_time)
                    date_str = dt.strftime('%Y-%m-%d')
                    time_str = dt.strftime('%H:%M')
                    query_params.append(f'date: "{date_str}"')
                    query_params.append(f'time: "{time_str}"')
                    query_params.append(f'arriveBy: {"true" if arrive_by else "false"}')
            except ValueError as e:
                pass
        
        # Construct GraphQL query for trip planning
        query = f'''
        {{
            plan(
                {chr(10).join(["                " + param for param in query_params])}
            ) {{
                itineraries {{
                    duration
                    walkTime
                    waitingTime
                    legs {{
                        mode
                        startTime
                        endTime
                        duration
                        distance
                        from {{
                            name
                            lat
                            lon
                        }}
                        to {{
                            name
                            lat
                            lon
                        }}
                        intermediateStops {{
                            name
                            lat
                            lon
                        }}
                        realTime
                        legGeometry {{
                            points
                        }}
                        route {{
                            shortName
                            longName
                            mode
                        }}
                        trip {{
                            tripShortName
                            tripHeadsign
                        }}
                    }}
                }}
            }}
        }}'''
        
        # Send request to EMMA API
        response = requests.post(
            GRAPHQL_ENDPOINT,
            headers=HEADERS,
            json={"query": query},
            timeout=30
        )
        
        if response.status_code != 200:
            return jsonify({"error": f"API request failed with status {response.status_code}"}), 500
        
        result = response.json()
        
        if "errors" in result:
            return jsonify({"error": "GraphQL errors", "details": result["errors"]}), 500
        
        plan_data = result.get("data", {}).get("plan", {})
        itineraries = plan_data.get("itineraries", [])
        
        return jsonify({
            "success": True,
            "plan": {
                "itineraries": itineraries
            }
        })
        
    except requests.exceptions.Timeout:
        return jsonify({"error": "Request timeout - please try again"}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Network error: {str(e)}"}), 503
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

def main():
    """Main function to start the application."""
    # Check if static folder exists
    if not os.path.exists('static'):
        sys.exit(1)
    
    if not os.path.exists('static/index.html'):
        sys.exit(1)
    
    # Start data updater thread
    updater_thread = threading.Thread(target=data_updater_thread, daemon=True)
    updater_thread.start()
    
    # Initial data fetch
    update_train_data()
    
    # Start Flask server
    try:
        app.run(host='0.0.0.0', port=8000, debug=False)
    except KeyboardInterrupt:
        sys.exit(0)

if __name__ == "__main__":
    main()