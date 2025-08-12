import math
import aiohttp
from typing import Dict, Optional
from shared.config import get_settings

settings = get_settings()

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the distance between two points on Earth using the Haversine formula.
    
    Args:
        lat1, lon1: Latitude and longitude of first point in decimal degrees
        lat2, lon2: Latitude and longitude of second point in decimal degrees
        
    Returns:
        Distance in meters
    """
    # Convert latitude and longitude from degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = (math.sin(dlat / 2) ** 2 + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2)
    
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of Earth in meters
    earth_radius = 6371000
    
    # Calculate the distance
    distance = earth_radius * c
    
    return distance

def is_point_in_circle(point_lat: float, point_lon: float, 
                      center_lat: float, center_lon: float, 
                      radius_meters: float) -> bool:
    """Check if a point is within a circular geofence.
    
    Args:
        point_lat, point_lon: Coordinates of the point to check
        center_lat, center_lon: Coordinates of the circle center
        radius_meters: Radius of the circle in meters
        
    Returns:
        True if point is inside the circle, False otherwise
    """
    distance = calculate_distance(point_lat, point_lon, center_lat, center_lon)
    return distance <= radius_meters

def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the bearing (direction) from point 1 to point 2.
    
    Args:
        lat1, lon1: Latitude and longitude of first point in decimal degrees
        lat2, lon2: Latitude and longitude of second point in decimal degrees
        
    Returns:
        Bearing in degrees (0-360)
    """
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlon_rad = math.radians(lon2 - lon1)
    
    y = math.sin(dlon_rad) * math.cos(lat2_rad)
    x = (math.cos(lat1_rad) * math.sin(lat2_rad) - 
         math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon_rad))
    
    bearing_rad = math.atan2(y, x)
    bearing_deg = math.degrees(bearing_rad)
    
    # Normalize to 0-360 degrees
    bearing_deg = (bearing_deg + 360) % 360
    
    return bearing_deg

async def get_location_info(latitude: float, longitude: float) -> Optional[Dict]:
    """Get location information using reverse geocoding.
    
    Args:
        latitude: Latitude in decimal degrees
        longitude: Longitude in decimal degrees
        
    Returns:
        Dictionary with location information or None if failed
    """
    try:
        # Use OpenStreetMap Nominatim for reverse geocoding (free service)
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            "lat": latitude,
            "lon": longitude,
            "format": "json",
            "addressdetails": 1,
            "zoom": 18
        }
        
        headers = {
            "User-Agent": "PanicAlertSystem/1.0 (emergency-app)"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers, timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Extract useful information
                    address_components = data.get("address", {})
                    
                    location_info = {
                        "address": data.get("display_name", ""),
                        "house_number": address_components.get("house_number", ""),
                        "road": address_components.get("road", ""),
                        "neighbourhood": address_components.get("neighbourhood", ""),
                        "suburb": address_components.get("suburb", ""),
                        "city": address_components.get("city", ""),
                        "county": address_components.get("county", ""),
                        "state": address_components.get("state", ""),
                        "country": address_components.get("country", ""),
                        "postcode": address_components.get("postcode", ""),
                        "place_id": data.get("place_id"),
                        "osm_type": data.get("osm_type"),
                        "osm_id": data.get("osm_id"),
                        "lat": data.get("lat"),
                        "lon": data.get("lon"),
                        "importance": data.get("importance"),
                        "place_rank": data.get("place_rank")
                    }
                    
                    return location_info
                    
    except Exception as e:
        # Log the error but don't raise it - location info is not critical
        print(f"Failed to get location info for {latitude}, {longitude}: {str(e)}")
        
    return None

async def get_nearby_places(latitude: float, longitude: float, 
                           radius_meters: int = 1000, 
                           place_type: str = "emergency") -> Optional[List[Dict]]:
    """Get nearby places of interest (hospitals, police stations, etc.).
    
    Args:
        latitude: Latitude in decimal degrees
        longitude: Longitude in decimal degrees
        radius_meters: Search radius in meters
        place_type: Type of places to search for
        
    Returns:
        List of nearby places or None if failed
    """
    try:
        # Use Overpass API to find nearby emergency services
        overpass_url = "https://overpass-api.de/api/interpreter"
        
        # Define queries for different place types
        queries = {
            "emergency": f"""
                [out:json][timeout:10];
                (
                  node["amenity"~"^(hospital|clinic|doctors|pharmacy|police|fire_station)$"](around:{radius_meters},{latitude},{longitude});
                  way["amenity"~"^(hospital|clinic|doctors|pharmacy|police|fire_station)$"](around:{radius_meters},{latitude},{longitude});
                );
                out center meta;
            """,
            "medical": f"""
                [out:json][timeout:10];
                (
                  node["amenity"~"^(hospital|clinic|doctors|pharmacy)$"](around:{radius_meters},{latitude},{longitude});
                  way["amenity"~"^(hospital|clinic|doctors|pharmacy)$"](around:{radius_meters},{latitude},{longitude});
                );
                out center meta;
            """,
            "safety": f"""
                [out:json][timeout:10];
                (
                  node["amenity"~"^(police|fire_station)$"](around:{radius_meters},{latitude},{longitude});
                  way["amenity"~"^(police|fire_station)$"](around:{radius_meters},{latitude},{longitude});
                );
                out center meta;
            """
        }
        
        query = queries.get(place_type, queries["emergency"])
        
        async with aiohttp.ClientSession() as session:
            async with session.post(overpass_url, data=query, timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    places = []
                    for element in data.get("elements", []):
                        tags = element.get("tags", {})
                        
                        # Get coordinates
                        if element.get("type") == "node":
                            place_lat = element.get("lat")
                            place_lon = element.get("lon")
                        elif element.get("type") == "way" and element.get("center"):
                            place_lat = element["center"].get("lat")
                            place_lon = element["center"].get("lon")
                        else:
                            continue
                        
                        if place_lat and place_lon:
                            distance = calculate_distance(latitude, longitude, place_lat, place_lon)
                            
                            place_info = {
                                "name": tags.get("name", "Unknown"),
                                "amenity": tags.get("amenity", ""),
                                "address": tags.get("addr:full", ""),
                                "phone": tags.get("phone", ""),
                                "website": tags.get("website", ""),
                                "opening_hours": tags.get("opening_hours", ""),
                                "emergency": tags.get("emergency", ""),
                                "latitude": place_lat,
                                "longitude": place_lon,
                                "distance_meters": round(distance, 2),
                                "osm_id": element.get("id"),
                                "osm_type": element.get("type")
                            }
                            
                            places.append(place_info)
                    
                    # Sort by distance
                    places.sort(key=lambda x: x["distance_meters"])
                    
                    return places[:20]  # Return top 20 closest places
                    
    except Exception as e:
        print(f"Failed to get nearby places for {latitude}, {longitude}: {str(e)}")
        
    return None

def validate_coordinates(latitude: float, longitude: float) -> bool:
    """Validate latitude and longitude coordinates.
    
    Args:
        latitude: Latitude in decimal degrees
        longitude: Longitude in decimal degrees
        
    Returns:
        True if coordinates are valid, False otherwise
    """
    return (-90 <= latitude <= 90) and (-180 <= longitude <= 180)

def format_coordinates(latitude: float, longitude: float, precision: int = 6) -> str:
    """Format coordinates as a string.
    
    Args:
        latitude: Latitude in decimal degrees
        longitude: Longitude in decimal degrees
        precision: Number of decimal places
        
    Returns:
        Formatted coordinate string
    """
    return f"{latitude:.{precision}f}, {longitude:.{precision}f}"

def get_coordinate_precision_meters(latitude: float) -> Dict[str, float]:
    """Get the precision in meters for different decimal places at a given latitude.
    
    Args:
        latitude: Latitude in decimal degrees
        
    Returns:
        Dictionary with precision information
    """
    # At the equator, 1 degree = ~111,320 meters
    # Longitude precision varies with latitude
    lat_precision_per_degree = 111320  # meters per degree latitude (constant)
    lon_precision_per_degree = 111320 * math.cos(math.radians(latitude))  # varies with latitude
    
    precisions = {}
    for decimal_places in range(1, 9):
        lat_precision = lat_precision_per_degree / (10 ** decimal_places)
        lon_precision = lon_precision_per_degree / (10 ** decimal_places)
        
        precisions[f"{decimal_places}_decimal_places"] = {
            "latitude_precision_meters": round(lat_precision, 2),
            "longitude_precision_meters": round(lon_precision, 2),
            "approximate_precision_meters": round(max(lat_precision, lon_precision), 2)
        }
    
    return precisions

# Import required modules
from typing import List