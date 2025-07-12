const express = require('express');
const axios = require('axios');
const fs = require('fs-extra');
const path = require('path');
const cors = require('cors');

// Configuration
const GRAPHQL_ENDPOINT = "https://emma.mav.hu//otp2-backend/otp/routers/default/index/graphql";
const DATA_FILE = "train_data.json";
const UPDATE_INTERVAL = 45000; // milliseconds
const MAX_CONCURRENT_REQUESTS = 10;
const PORT = 8001;

const HEADERS = {
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
};

// Express app setup
const app = express();
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'static')));

/**
 * Get current service day in YYYY-MM-DD format
 */
function getServiceDay() {
    const now = new Date();
    return now.toISOString().split('T')[0];
}

/**
 * Fetch current vehicle positions from EMMA API
 */
async function fetchVehiclePositions() {
    const query = `
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
    }`;

    const response = await axios.post(GRAPHQL_ENDPOINT, { query }, { headers: HEADERS });
    return response.data.data.vehiclePositions;
}

/**
 * Fetch detailed trip information for a specific train
 */
async function fetchTripDetails(gtfsId, serviceDay) {
    const query = `
    {
        trip(id: "${gtfsId}", serviceDay: "${serviceDay}") {
          gtfsId
          tripHeadsign
          trainCategoryName
          trainName
          route { 
            longName(language: "hu")
            shortName
          }
          stoptimes {
            stop {
              name
              lat
              lon
              platformCode
            }
            realtimeArrival
            realtimeDeparture
            arrivalDelay
            departureDelay
            scheduledArrival
            scheduledDeparture
          }
        }
    }`;

    try {
        const response = await axios.post(GRAPHQL_ENDPOINT, { query }, { 
            headers: HEADERS, 
            timeout: 10000 
        });
        return response.data?.data?.trip || {};
    } catch (error) {
        return {};
    }
}

/**
 * Process a single vehicle with trip details
 */
async function processVehicle(vehicle, serviceDay) {
    const trip = vehicle.trip;
    const gtfsId = trip?.gtfsId;
    
    if (!gtfsId) {
        return null;
    }
    
    const tripDetails = await fetchTripDetails(gtfsId, serviceDay);

    const tripShortName = trip?.tripShortName;
    const tripHeadsign = trip?.tripHeadsign;
    const vehicleId = vehicle?.vehicleId;
    const lat = vehicle?.lat;
    const lon = vehicle?.lon;
    const label = vehicle?.label;
    const speed = vehicle?.speed;
    const heading = vehicle?.heading;
    
    // Get mode from trip route
    const tripRoute = trip?.route;
    const mode = tripRoute?.mode;
    
    const trainCat = tripDetails?.trainCategoryName;
    const trainName = tripDetails?.trainName;
    const route = tripDetails?.route || {};
    const routeLongName = route?.longName;
    const routeShortName = route?.shortName;
    const stopTimes = tripDetails?.stoptimes || [];

    // Optimize stop data processing
    const stopsCompressed = stopTimes.map(stop => {
        const st = stop?.stop || {};
        return {
            name: st?.name,
            ra: stop?.realtimeArrival,
            rd: stop?.realtimeDeparture,
            sa: stop?.scheduledArrival,
            sd: stop?.scheduledDeparture,
            a: stop?.arrivalDelay,
            d: stop?.departureDelay,
            v: st?.platformCode
        };
    });

    // Determine display name
    let name = tripShortName;
    if (routeLongName && routeLongName.length < 6) {
        name = `[${routeLongName}] ${tripShortName}`;
    }

    return {
        id: gtfsId,
        name: name,
        headsgn: tripHeadsign,
        lat: lat,
        lon: lon,
        sp: speed,
        hd: heading,
        mode: mode,
        stops: stopsCompressed
    };
}

/**
 * Update train data from EMMA API with concurrent processing
 */
async function updateTrainData() {
    try {
        const serviceDay = getServiceDay();
        const vehicles = await fetchVehiclePositions();
        
        const allData = {
            lastUpdated: Math.floor(Date.now() / 1000),
            vehicles: []
        };

        // Process vehicles in batches for better performance
        const batchSize = MAX_CONCURRENT_REQUESTS;
        const results = [];
        
        for (let i = 0; i < vehicles.length; i += batchSize) {
            const batch = vehicles.slice(i, i + batchSize);
            const batchPromises = batch.map(vehicle => processVehicle(vehicle, serviceDay));
            
            try {
                const batchResults = await Promise.allSettled(batchPromises);
                const successfulResults = batchResults
                    .filter(result => result.status === 'fulfilled' && result.value !== null)
                    .map(result => result.value);
                results.push(...successfulResults);
            } catch (error) {
                console.error('Batch processing error:', error);
            }
        }
        
        allData.vehicles = results;
        
        // Save data to file
        await fs.writeJson(DATA_FILE, allData, { spaces: 0 });
        
        console.log(`Updated train data: ${results.length} vehicles`);
        
    } catch (error) {
        console.error('Error updating train data:', error);
    }
}

/**
 * Background interval that periodically updates train data
 */
function startDataUpdater() {
    // Initial update
    updateTrainData();
    
    // Set up periodic updates
    setInterval(updateTrainData, UPDATE_INTERVAL);
}

// Routes
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'static', 'index.html'));
});

app.get('/trip', (req, res) => {
    res.sendFile(path.join(__dirname, 'static', 'trip.html'));
});

app.get('/train_data.json', async (req, res) => {
    try {
        if (await fs.pathExists(DATA_FILE)) {
            const data = await fs.readJson(DATA_FILE);
            res.json(data);
        } else {
            res.json({ error: "Data not available yet", vehicles: [], lastUpdated: 0 });
        }
    } catch (error) {
        res.json({ error: error.message, vehicles: [], lastUpdated: 0 });
    }
});

app.get('/api/stations', async (req, res) => {
    try {
        const query = req.query.q || '';
        const limit = req.query.limit || '5';
        
        if (!query || query.length < 2) {
            return res.status(400).json({ error: "Query must be at least 2 characters long" });
        }
        
        const mavUrl = `https://emma.mav.hu/otp2-backend/otp/routers/default/geocode/stations?q=${query}&limit=${limit}`;
        
        const headers = {
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
        };
        
        const response = await axios.get(mavUrl, { headers, timeout: 10000 });
        
        if (response.status === 200) {
            res.json(response.data);
        } else {
            res.status(response.status).json({ error: `MAV API returned status ${response.status}` });
        }
        
    } catch (error) {
        if (error.code === 'ECONNABORTED') {
            res.status(504).json({ error: "Request timeout" });
        } else if (error.response) {
            res.status(error.response.status).json({ error: `Network error: ${error.message}` });
        } else {
            res.status(503).json({ error: `Network error: ${error.message}` });
        }
    }
});

app.post('/api/plan', async (req, res) => {
    try {
        const data = req.body;
        
        if (!data) {
            return res.status(400).json({ error: "No data provided" });
        }
        
        const fromCoords = data.from;
        const toCoords = data.to;
        const numItineraries = data.numItineraries || 3;
        const dateTime = data.dateTime;
        const arriveBy = data.arriveBy || false;
        
        if (!fromCoords || !toCoords) {
            return res.status(400).json({ error: "From and to coordinates are required" });
        }
        
        if (typeof fromCoords !== 'object' || typeof toCoords !== 'object') {
            return res.status(400).json({ error: "Invalid coordinate format" });
        }
            
        if (!('lat' in fromCoords) || !('lon' in fromCoords) || !('lat' in toCoords) || !('lon' in toCoords)) {
            return res.status(400).json({ error: "Missing lat/lon in coordinates" });
        }
        
        // Build query parameters
        const queryParams = [
            `from: {lat: ${fromCoords.lat}, lon: ${fromCoords.lon}}`,
            `to: {lat: ${toCoords.lat}, lon: ${toCoords.lon}}`,
            'numItineraries: 5',
            'transportModes: [{mode: RAIL}, {mode: COACH}, {mode: BUS}, {mode: TRAM}, {mode: SUBWAY}]',
            'walkReluctance: 2.0',
            'walkBoardCost: 600',
            'minTransferTime: 120',
            'maxWalkDistance: 2000'
        ];
        
        // Add date and time parameters if provided
        if (dateTime) {
            try {
                let dt;
                if (dateTime.includes('T')) {
                    if (dateTime.endsWith('Z') || dateTime.includes('+') || (dateTime.match(/:/g) || []).length > 2) {
                        // ISO format with timezone - convert from UTC
                        dt = new Date(dateTime);
                    } else {
                        // Local format (YYYY-MM-DDTHH:MM) - use as is
                        dt = new Date(dateTime);
                    }
                    const dateStr = dt.toISOString().split('T')[0];
                    const timeStr = dt.toTimeString().split(' ')[0].substring(0, 5);
                    queryParams.push(`date: "${dateStr}"`);
                    queryParams.push(`time: "${timeStr}"`);
                    queryParams.push(`arriveBy: ${arriveBy ? 'true' : 'false'}`);
                }
            } catch (error) {
                // Ignore date parsing errors
            }
        }
        
        // Construct GraphQL query for trip planning
        const query = `
        {
            plan(
                ${queryParams.map(param => '                ' + param).join('\n')}
            ) {
                itineraries {
                    duration
                    walkTime
                    waitingTime
                    legs {
                        mode
                        startTime
                        endTime
                        duration
                        distance
                        from {
                            name
                            lat
                            lon
                        }
                        to {
                            name
                            lat
                            lon
                        }
                        intermediateStops {
                            name
                            lat
                            lon
                        }
                        realTime
                        legGeometry {
                            points
                        }
                        route {
                            shortName
                            longName
                            mode
                        }
                        trip {
                            tripShortName
                            tripHeadsign
                        }
                    }
                }
            }
        }`;
        
        // Send request to EMMA API
        const response = await axios.post(
            GRAPHQL_ENDPOINT,
            { query },
            {
                headers: HEADERS,
                timeout: 30000
            }
        );
        
        if (response.status !== 200) {
            return res.status(500).json({ error: `API request failed with status ${response.status}` });
        }
        
        const result = response.data;
        
        if (result.errors) {
            return res.status(500).json({ error: "GraphQL errors", details: result.errors });
        }
        
        const planData = result?.data?.plan || {};
        const itineraries = planData?.itineraries || [];
        
        res.json({
            success: true,
            plan: {
                itineraries: itineraries
            }
        });
        
    } catch (error) {
        if (error.code === 'ECONNABORTED') {
            res.status(504).json({ error: "Request timeout - please try again" });
        } else if (error.response) {
            res.status(503).json({ error: `Network error: ${error.message}` });
        } else {
            res.status(500).json({ error: `Internal server error: ${error.message}` });
        }
    }
});

// Start server
function main() {
    // Check if static folder exists
    const staticPath = path.join(__dirname, 'static');
    if (!fs.existsSync(staticPath)) {
        console.error('Static folder does not exist');
        process.exit(1);
    }
    
    if (!fs.existsSync(path.join(staticPath, 'index.html'))) {
        console.error('index.html does not exist in static folder');
        process.exit(1);
    }
    
    // Start data updater
    startDataUpdater();
    
    // Start server
    app.listen(PORT, '0.0.0.0', () => {
        console.log(`Server running on http://0.0.0.0:${PORT}`);
    });
}

// Handle graceful shutdown
process.on('SIGINT', () => {
    console.log('\nShutting down gracefully...');
    process.exit(0);
});

if (require.main === module) {
    main();
}

module.exports = app;