# app.py

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, send_file, Response
import json
import os
from datetime import datetime
import requests
import threading
import time
import uuid
from main import *
from login.auth_manager import AuthManager
from login.firebase_service import save_user_profile, get_user_profile
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-this-to-random-string'

# Initialize auth manager
auth_manager = AuthManager()

# Weather API key
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY")
if not WEATHER_API_KEY:
    raise RuntimeError("❌ WEATHER_API_KEY not found. Set it in your .env file or environment.")

class FlaskWeatherService:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "http://api.openweathermap.org/data/2.5"
        self.geo_url = "http://api.openweathermap.org/geo/1.0"

    def get_current_weather(self, lat, lon):
        try:
            url = f"{self.base_url}/weather?lat={lat}&lon={lon}&appid={self.api_key}&units=metric"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            temperature = data['main']['temp']
            feels_like = data['main']['feels_like']
            humidity = data['main']['humidity']
            wind_speed = data['wind']['speed']
            weather_description = data['weather'][0]['description']
            weather_id = data['weather'][0]['id']

            if 200 <= weather_id < 600:
                condition = WeatherCondition.RAINY
            elif 600 <= weather_id < 700:
                condition = WeatherCondition.SNOWY
            elif 700 <= weather_id < 800:
                condition = WeatherCondition.CLOUDY
            elif weather_id == 800:
                condition = WeatherCondition.SUNNY
            elif 801 <= weather_id < 900:
                condition = WeatherCondition.CLOUDY
            else:
                condition = WeatherCondition.CLOUDY

            return WeatherData(
                temperature=temperature,
                condition=condition,
                feels_like=feels_like,
                humidity=humidity,
                wind_speed=wind_speed,
                description=weather_description
            )
        except requests.exceptions.RequestException as e:
            print(f"Error fetching weather data: {e}")
            raise

    def get_location_name(self, lat, lon):
        if not self.api_key:
            raise RuntimeError("❌ Missing OpenWeatherMap API key for reverse geocoding.")

        try:
            url = f"{self.geo_url}/reverse?lat={lat}&lon={lon}&limit=1&appid={self.api_key}"
            print(f"🌍 Reverse geocoding URL: {url}")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            print(f"🌍 Reverse geocoding response: {data}")

            if data and len(data) > 0:
                location_info = data[0]
                city = location_info.get('name')
                state = location_info.get('state')
                country = location_info.get('country')
                print(f"✅ Reverse geocoding successful: {city}, {state}, {country}")
                return city, state, country
            else:
                print(f"❌ No location data found for lat: {lat}, lon: {lon}")
                return None, None, None
        except requests.exceptions.RequestException as e:
            print(f"❌ Error during reverse geocoding: {e}")
            return None, None, None

# Initialize your FlaskWeatherService with the secure API key
weather_service = FlaskWeatherService(WEATHER_API_KEY)

# ... rest of your Flask routes and logic remain unchanged ...


def login_required(f):
    def wrap(*args, **kwargs):
        if 'user' not in session:
            flash("You need to log in first.", "danger")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap

def get_user_virtual_closet():
    user_info = session.get('user', {})
    user_id = user_info.get('localId')
    id_token = user_info.get('idToken')

    if user_id and id_token:
        profile_data = get_user_profile(user_id, id_token)
        if profile_data:
            try:
                # Simple avatar approach - just get the selected avatar type
                selected_avatar = profile_data.get('selected_avatar', 'fit_man')
                preferred_styles = [Style(s) for s in profile_data.get('preferred_styles', [])]

                wardrobe_items_data = profile_data.get('wardrobe', [])
                wardrobe = []
                for item_data in wardrobe_items_data:
                    try:
                        wardrobe.append(ClothingItem(
                            id=item_data['id'],
                            name=item_data['name'],
                            type=ClothingType(item_data['type']),
                            fitting=Fitting(item_data['fitting']),
                            style=Style(item_data['style']),
                            color=item_data['color'],
                            warmth_level=item_data['warmth_level'],
                            weather_resistance=[WeatherCondition(wr) for wr in item_data['weather_resistance']],
                            image_path=item_data.get('image_path', ''),
                            tags=item_data.get('tags', [])
                        ))
                    except (KeyError, ValueError) as e:
                        print(f"Skipping malformed wardrobe item: {e}")

                latitude = profile_data.get('latitude')
                longitude = profile_data.get('longitude')

                user_closet = VirtualClosetApp(
                    weather_service=weather_service,
                    recommendation_engine=OutfitRecommendationEngine(),
                    wardrobe=wardrobe
                )
                user_closet.latitude = latitude
                user_closet.longitude = longitude
                user_closet.selected_avatar = selected_avatar
                return user_closet
            except Exception as e:
                print(f"Error reconstructing user_closet from profile data: {e}")
                return None
    return None

@app.route('/')
def home():
    if 'user' not in session:
        return redirect(url_for('login'))

    user_info = session.get('user', {})
    user_id = user_info.get('localId')
    id_token = user_info.get('idToken')

    has_profile_setup = False
    if user_id and id_token:
        profile_data = get_user_profile(user_id, id_token)
        has_profile_setup = bool(profile_data and profile_data.get('selected_avatar'))

    return render_template('index.html', has_profile_setup=has_profile_setup)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.json.get('email')
        password = request.json.get('password')
        user = auth_manager.login(email, password)
        if isinstance(user, dict):
            session['user'] = user
            return jsonify({'success': True, 'message': 'Login successful'})
        else:
            return jsonify({'success': False, 'message': user})
    return render_template('login.html')

@app.route('/signup', methods=['POST'])
def signup():
    email = request.json.get('email')
    password = request.json.get('password')
    user = auth_manager.signup(email, password)
    if isinstance(user, dict):
        session['user'] = user
        user_id = user['localId']
        id_token = user['idToken']
        save_user_profile(user_id, {}, id_token)
        return jsonify({'success': True, 'message': 'Signup successful'})
    else:
        return jsonify({'success': False, 'message': user})

@app.route('/logout')
@login_required
def logout():
    session.pop('user', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

@app.route('/setup', methods=['GET', 'POST'])
@login_required
def setup_profile():
    if request.method == 'POST':
        user_info = session['user']
        user_id = user_info['localId']
        id_token = user_info['idToken']
        data = request.get_json()

        print(f"📥 Setup received data: {data}")  # Debug log

        try:
            selected_avatar = data['selected_avatar']
            preferred_styles = [Style(s) for s in data['preferred_styles']]

            latitude_str = data.get('latitude')
            longitude_str = data.get('longitude')
            
            print(f"📍 Raw location data: lat='{latitude_str}', lon='{longitude_str}'")  # Debug log
            print(f"📍 Location data types: lat={type(latitude_str)}, lon={type(longitude_str)}")

            # Handle location data and convert to city/state/country
            latitude = None
            longitude = None
            city = None
            state = None
            country = None
            
            if latitude_str and longitude_str and latitude_str != '' and longitude_str != '':
                try:
                    latitude = float(latitude_str)
                    longitude = float(longitude_str)
                    print(f"✅ Location parsed successfully: {latitude}, {longitude}")
                    
                    # Do reverse geocoding to get city, state, country
                    print(f"🌍 Converting coordinates to location names...")
                    city, state, country = weather_service.get_location_name(latitude, longitude)
                    print(f"🏙️ Reverse geocoding result: city='{city}', state='{state}', country='{country}'")
                    
                    # Validate the results
                    if city and state and country:
                        print(f"✅ Complete location data obtained: {city}, {state}, {country}")
                    else:
                        print(f"⚠️ Incomplete location data: city={city}, state={state}, country={country}")
                    
                except (ValueError, TypeError) as e:
                    print(f"❌ Error parsing location coordinates: {e}")
                    latitude = None
                    longitude = None
            else:
                print("⚠️ No location data provided or empty strings")

            # Get existing profile data to merge
            current_profile = get_user_profile(user_id, id_token) or {}
            
            # Update the user's profile with location data
            profile_data_to_save = {
                **current_profile,
                'selected_avatar': selected_avatar,
                'preferred_styles': [s.value for s in preferred_styles],
                'latitude': latitude,
                'longitude': longitude,
                'city': city,
                'state': state,
                'country': country,
                'setup_timestamp': datetime.utcnow().isoformat()
            }
            
            print(f"💾 Saving profile data:")
            print(f"   - Avatar: {selected_avatar}")
            print(f"   - Styles: {[s.value for s in preferred_styles]}")
            print(f"   - Coordinates: {latitude}, {longitude}")
            print(f"   - Location: {city}, {state}, {country}")
            
            success = save_user_profile(user_id, profile_data_to_save, id_token)
            
            if success:
                print("✅ Profile saved successfully to database")
                
                # Verify the save by reading back
                saved_profile = get_user_profile(user_id, id_token)
                if saved_profile:
                    print(f"✅ Profile verification successful. Saved data: {saved_profile}")
                else:
                    print("⚠️ Could not verify saved profile")
                
                flash("Profile setup complete!", "success")
                return jsonify({'success': True, 'message': 'Profile setup complete.'})
            else:
                print("❌ Failed to save profile to database")
                return jsonify({'success': False, 'message': 'Failed to save profile to database'})
                
        except Exception as e:
            print(f"❌ Error in setup: {e}")
            import traceback
            print(f"❌ Full traceback: {traceback.format_exc()}")
            flash(f"Error setting up profile: {e}", "danger")
            return jsonify({'success': False, 'message': str(e)})

    return render_template('setup.html')

@app.route('/profile')
@login_required
def view_profile():
    return render_template('profile.html')

# NEW ENDPOINT: Update location for existing users
@app.route('/api/update-location', methods=['POST'])
@login_required
def update_location():
    """Update location data for users who have coordinates but no city names"""
    user_info = session.get('user', {})
    user_id = user_info.get('localId')
    id_token = user_info.get('idToken')

    if not user_id or not id_token:
        return jsonify({'error': 'User not authenticated'}), 401

    # Get current profile
    profile_data = get_user_profile(user_id, id_token)
    if not profile_data:
        return jsonify({'error': 'Profile not found'}), 404

    latitude = profile_data.get('latitude')
    longitude = profile_data.get('longitude')

    if not latitude or not longitude:
        return jsonify({'error': 'No coordinates in profile'}), 400

    # Check if we already have city data
    if profile_data.get('city') and profile_data.get('state') and profile_data.get('country'):
        return jsonify({
            'message': 'Location already updated',
            'city': profile_data.get('city'),
            'state': profile_data.get('state'),
            'country': profile_data.get('country')
        })

    # Do reverse geocoding
    try:
        city, state, country = weather_service.get_location_name(latitude, longitude)
        
        if city and country:  # At minimum we need city and country
            # Update profile with location names
            profile_data.update({
                'city': city,
                'state': state,  # May be None for non-US locations
                'country': country,
                'location_updated_timestamp': datetime.utcnow().isoformat()
            })
            
            success = save_user_profile(user_id, profile_data, id_token)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Location updated successfully',
                    'city': city,
                    'state': state,
                    'country': country
                })
            else:
                return jsonify({'error': 'Failed to save updated location'}), 500
        else:
            return jsonify({'error': 'Could not determine location names'}), 400
            
    except Exception as e:
        print(f"Error updating location: {e}")
        return jsonify({'error': 'Failed to update location'}), 500

@app.route('/api/profile')
@login_required
def api_profile():
    user_info = session.get('user', {})
    user_id = user_info.get('localId')
    id_token = user_info.get('idToken')

    print(f"📡 Profile API called for user: {user_id}")  # Debug log

    if user_id and id_token:
        profile_data = get_user_profile(user_id, id_token)
        print(f"📊 Raw profile data from database: {profile_data}")  # Debug log
        
        if profile_data:
            response_data = {
                'user_id': user_id,
                'selected_avatar': profile_data.get('selected_avatar'),
                'preferred_styles': profile_data.get('preferred_styles'),
                'city': profile_data.get('city'),
                'state': profile_data.get('state'),
                'country': profile_data.get('country'),
                'latitude': profile_data.get('latitude'),
                'longitude': profile_data.get('longitude'),
                'setup_timestamp': profile_data.get('setup_timestamp')
            }

            print(f"✅ Sending profile response:")
            print(f"   - Avatar: {response_data['selected_avatar']}")
            print(f"   - Styles: {response_data['preferred_styles']}")
            print(f"   - Location: {response_data['city']}, {response_data['state']}, {response_data['country']}")
            print(f"   - Coordinates: {response_data['latitude']}, {response_data['longitude']}")
            
            return jsonify(response_data)
    
    print("❌ No profile data found")
    return jsonify({'error': 'Profile not found'}), 404

# Weather API endpoint
@app.route('/api/weather')
@login_required
def api_weather():
    user_info = session.get('user', {})
    user_id = user_info.get('localId')
    id_token = user_info.get('idToken')

    if not user_id or not id_token:
        return jsonify({'error': 'User not authenticated'}), 401

    # Get user's location from profile
    profile_data = get_user_profile(user_id, id_token)
    if not profile_data:
        return jsonify({'error': 'Profile not found'}), 404

    latitude = profile_data.get('latitude')
    longitude = profile_data.get('longitude')

    if not latitude or not longitude:
        return jsonify({'error': 'Location not set in profile'}), 400

    try:
        # Get current weather
        weather = weather_service.get_current_weather(latitude, longitude)
        
        return jsonify({
            'temperature': round(weather.temperature, 1),
            'condition': weather.condition.value,
            'feels_like': round(weather.feels_like, 1),
            'humidity': weather.humidity,
            'wind_speed': round(weather.wind_speed, 1),
            'description': weather.description
        })
    except Exception as e:
        print(f"Error getting weather: {e}")
        return jsonify({'error': 'Could not fetch weather data'}), 500

@app.route('/wardrobe')
@login_required
def wardrobe():
    return render_template('wardrobe.html')

@app.route('/add_clothing', methods=['POST'])
@login_required
def add_clothing():
    user_info = session.get('user', {})
    user_id = user_info.get('localId')
    id_token = user_info.get('idToken')

    if not user_id or not id_token:
        return jsonify({'success': False, 'message': 'User not authenticated'}), 401

    data = request.get_json()

    try:
        item_id = str(uuid.uuid4())

        new_item = ClothingItem(
            id=item_id,
            name=data['name'],
            type=ClothingType(data['type']),
            fitting=Fitting(data['fitting']),
            style=Style(data['style']),
            color=data['color'],
            warmth_level=int(data['warmth_level']),
            weather_resistance=[WeatherCondition(wr) for wr in data['weather_resistance']],
            image_path=data.get('image_path', ''),
            tags=data.get('tags', [])
        )

        profile_data = get_user_profile(user_id, id_token)
        if not profile_data:
            profile_data = {}

        wardrobe_list = profile_data.get('wardrobe', [])

        new_item_dict = {
            'id': new_item.id,
            'name': new_item.name,
            'type': new_item.type.value,
            'fitting': new_item.fitting.value,
            'style': new_item.style.value,
            'color': new_item.color,
            'warmth_level': new_item.warmth_level,
            'weather_resistance': [wr.value for wr in new_item.weather_resistance],
            'image_path': new_item.image_path,
            'tags': new_item.tags
        }
        wardrobe_list.append(new_item_dict)
        profile_data['wardrobe'] = wardrobe_list

        save_user_profile(user_id, profile_data, id_token)

        return jsonify({'success': True, 'message': 'Clothing item added successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/get_outfit', methods=['POST'])
@login_required
def get_outfit():
    virtual_closet = get_user_virtual_closet()
    if not virtual_closet:
        return jsonify({'error': 'User profile or wardrobe not found.'}), 404

    lat = virtual_closet.latitude
    lon = virtual_closet.longitude

    if lat is None or lon is None:
        return jsonify({'error': 'Location not set in profile. Please set up your profile first.'}), 400

    weather = weather_service.get_current_weather(lat, lon)

    # Simple recommendation for now
    outfit_data = {}
    for item in virtual_closet.wardrobe[:4]:  # Just take first few items
        outfit_data[item.type.value] = {
            'name': item.name,
            'color': item.color,
            'fitting': item.fitting.value,
            'style': item.style.value
        }
    
    return jsonify({
        'outfit': outfit_data,
        'weather': {
            'temperature': weather.temperature,
            'condition': weather.condition.value,
            'feels_like': weather.feels_like,
            'humidity': weather.humidity
        },
        'recommendations': ['Stay comfortable!']
    })

@app.route('/wardrobe_items')
@login_required
def get_wardrobe_items():
    virtual_closet = get_user_virtual_closet()
    if not virtual_closet:
        return jsonify([])
    
    items = []
    for item in virtual_closet.wardrobe:
        items.append({
            'id': item.id,
            'name': item.name,
            'type': item.type.value,
            'fitting': item.fitting.value,
            'style': item.style.value,
            'color': item.color,
            'warmth_level': item.warmth_level,
            'weather_resistance': [wr.value for wr in item.weather_resistance],
            'image_path': item.image_path,
            'tags': item.tags
        })
    return jsonify(items)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')