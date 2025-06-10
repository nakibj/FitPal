from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import json
import os
from datetime import datetime
import requests
from main import *  # Import our existing classes
from login.auth_manager import AuthManager

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-this-to-random-string'  # Change this to a random string


# Initialize auth manager
auth_manager = AuthManager()

# Initialize the virtual closet app
virtual_closet = None
WEATHER_API_KEY = "0eb22a3078da1eeed62200aec5ee2181"  # You'll need to get this from OpenWeatherMap

# Store user data in memory (in production, use a database)
user_profiles = {}  # Structure: {user_email: {measurements, preferred_styles, avatar_data}}


class FlaskWeatherService:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "http://api.openweathermap.org/data/2.5"
    
    def get_current_weather(self, lat, lon):
        """Get weather by coordinates"""
        if not self.api_key or self.api_key == "0eb22a3078da1eeed62200aec5ee2181":
            # Return mock data if no API key
            return WeatherData(22.0, WeatherCondition.SUNNY, 45, 5.2, 24.0)
        
        try:
            url = f"{self.base_url}/weather"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'metric'
            }
            response = requests.get(url, params=params)
            data = response.json()
            
            # Map weather conditions
            weather_mapping = {
                'clear': WeatherCondition.SUNNY,
                'clouds': WeatherCondition.CLOUDY,
                'rain': WeatherCondition.RAINY,
                'snow': WeatherCondition.SNOWY
            }
            
            main_weather = data['weather'][0]['main'].lower()
            condition = weather_mapping.get(main_weather, WeatherCondition.SUNNY)
            
            return WeatherData(
                temperature=data['main']['temp'],
                condition=condition,
                humidity=data['main']['humidity'],
                wind_speed=data['wind']['speed'],
                feels_like=data['main']['feels_like']
            )
        except:
            # Return mock data if API call fails
            return WeatherData(22.0, WeatherCondition.SUNNY, 45, 5.2, 24.0)

# Login required decorator
def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def get_user_virtual_closet():
    """Get or create virtual closet for current user"""
    global virtual_closet
    user_email = session.get('user_email')
    
    if not virtual_closet and user_email in user_profiles:
        # Recreate virtual closet from stored profile
        profile_data = user_profiles[user_email]
        weather_service = FlaskWeatherService(WEATHER_API_KEY)
        virtual_closet = VirtualClosetApp("dummy")
        virtual_closet.weather_service = weather_service
        
        # Restore user profile
        measurements = profile_data['measurements']
        preferred_styles = profile_data['preferred_styles']
        virtual_closet.setup_user_profile(measurements, preferred_styles)
        
        # Restore wardrobe items if any
        if 'wardrobe_items' in profile_data:
            virtual_closet.wardrobe = profile_data['wardrobe_items']
    
    return virtual_closet

@app.route('/')
def home():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        user = auth_manager.login(email, password)
        
        if isinstance(user, dict):  # successful login
            session['user'] = user
            session['user_email'] = email
            return jsonify({'success': True, 'message': 'Login successful!'})
        else:
            return jsonify({'success': False, 'message': 'Invalid email or password'})
    
    return render_template('login.html')

@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    user = auth_manager.signup(email, password)
    
    if isinstance(user, dict):  # successful signup
        return jsonify({'success': True, 'message': 'Account created successfully! You can now log in.'})
    else:
        return jsonify({'success': False, 'message': str(user)})

@app.route('/logout')
def logout():
    global virtual_closet
    virtual_closet = None  # Clear the virtual closet
    session.clear()
    flash('You have been logged out successfully.')
    return redirect(url_for('login'))

@app.route('/setup', methods=['GET', 'POST'])
@login_required
def setup_profile():
    if request.method == 'POST':
        # Get form data
        data = request.json
        user_email = session.get('user_email')
        
        # Create measurements
        measurements = BodyMeasurements(
            height=float(data['height']),
            chest_bust=float(data['chest_bust']),
            waist=float(data['waist']),
            hips=float(data['hips']),
            shoulder_width=float(data['shoulder_width']),
            gender=Gender(data['gender'])
        )
        
        # Create preferred styles
        preferred_styles = [Style(style) for style in data['preferred_styles']]
        
        # Initialize virtual closet
        global virtual_closet
        weather_service = FlaskWeatherService(WEATHER_API_KEY)
        virtual_closet = VirtualClosetApp("dummy")  # We'll replace the weather service
        virtual_closet.weather_service = weather_service
        
        # Setup user profile
        avatar_data = virtual_closet.setup_user_profile(measurements, preferred_styles)
        
        # Store profile data
        user_profiles[user_email] = {
            'measurements': measurements,
            'preferred_styles': preferred_styles,
            'avatar_data': avatar_data,
            'wardrobe_items': []
        }
        
        # Store in session
        session['profile_setup'] = True
        session['avatar_data'] = avatar_data
        
        return jsonify({'success': True, 'avatar': avatar_data})
    
    return render_template('setup.html')

@app.route('/profile')
@login_required
def profile():
    """Render the profile page"""
    if not session.get('profile_setup'):
        return redirect(url_for('setup_profile'))
    return render_template('profile.html')

@app.route('/api/profile')
@login_required
def get_profile():
    """API endpoint to get user profile data"""
    user_email = session.get('user_email')
    
    if user_email not in user_profiles:
        return jsonify({'error': 'Profile not found'}), 404
    
    profile_data = user_profiles[user_email]
    measurements = profile_data['measurements']
    preferred_styles = profile_data['preferred_styles']
    
    # Convert to JSON-serializable format
    profile_json = {
        'height': measurements.height,
        'gender': measurements.gender.value,
        'chest_bust': measurements.chest_bust,
        'waist': measurements.waist,
        'hips': measurements.hips,
        'shoulder_width': measurements.shoulder_width,
        'preferred_styles': [style.value for style in preferred_styles]
    }
    
    return jsonify(profile_json)

@app.route('/wardrobe')
@login_required
def wardrobe():
    if not session.get('profile_setup'):
        return redirect(url_for('setup_profile'))
    return render_template('wardrobe.html')

@app.route('/add_clothing', methods=['POST'])
@login_required
def add_clothing():
    data = request.json
    user_email = session.get('user_email')
    
    # Get or create virtual closet
    virtual_closet = get_user_virtual_closet()
    if not virtual_closet:
        return jsonify({'error': 'Profile not set up'}), 400
    
    # Create clothing item
    item = ClothingItem(
        id=str(len(virtual_closet.wardrobe) + 1),
        name=data['name'],
        type=ClothingType(data['type']),
        fitting=Fitting(data['fitting']),
        style=Style(data['style']),
        color=data['color'],
        warmth_level=int(data['warmth_level']),
        weather_resistance=[WeatherCondition(w) for w in data['weather_resistance']],
        image_path=data.get('image_path', ''),
        tags=data.get('tags', [])
    )
    
    virtual_closet.add_clothing_item(item)
    
    # Update stored wardrobe
    if user_email in user_profiles:
        user_profiles[user_email]['wardrobe_items'] = virtual_closet.wardrobe
    
    return jsonify({'success': True, 'message': f'Added {item.name} to wardrobe!'})

@app.route('/get_outfit', methods=['POST'])
@login_required
def get_outfit():
    data = request.json
    lat = data.get('lat')
    lon = data.get('lon')
    
    virtual_closet = get_user_virtual_closet()
    if not virtual_closet:
        return jsonify({'error': 'Profile not set up'})
    
    if not virtual_closet.wardrobe:
        return jsonify({'error': 'No clothes in wardrobe'})
    
    # Get weather data
    weather = virtual_closet.weather_service.get_current_weather(lat, lon)
    
    # Get outfit recommendation
    recommendation = virtual_closet.recommendation_engine.recommend_outfit(
        virtual_closet.user_avatar, weather, virtual_closet.wardrobe
    )
    
    # Format response
    outfit_data = {}
    for category, item in recommendation['outfit'].items():
        outfit_data[category] = {
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
        'recommendations': recommendation['weather_recommendations']
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
            'warmth_level': item.warmth_level
        })
    
    return jsonify(items)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)