import json
import random
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Optional
import requests

class Gender(Enum):
    MALE = "male"
    FEMALE = "female"
    NON_BINARY = "non_binary"

class Fitting(Enum):
    TIGHT = "tight"
    REGULAR = "regular"
    OVERSIZED = "oversized"
    LONG = "long"

class Style(Enum):
    STREETWEAR = "streetwear"
    OLD_MONEY = "old_money"
    ALT = "alt"
    CASUAL = "casual"

class ClothingType(Enum):
    TOP = "top"
    BOTTOM = "bottom"
    OUTERWEAR = "outerwear"
    SHOES = "shoes"
    ACCESSORY = "accessory"

class WeatherCondition(Enum):
    SUNNY = "sunny"
    CLOUDY = "cloudy"
    RAINY = "rainy"
    SNOWY = "snowy"

@dataclass
class BodyMeasurements:
    height: float  # in cm
    chest_bust: float  # in cm
    waist: float  # in cm
    hips: float  # in cm
    shoulder_width: float  # in cm
    gender: Gender

@dataclass
class ClothingItem:
    id: str
    name: str
    type: ClothingType
    fitting: Fitting
    style: Style
    color: str
    warmth_level: int  # 1-5, 5 being warmest
    weather_resistance: List[WeatherCondition]
    image_path: str
    tags: List[str]

@dataclass
class WeatherData:
    temperature: float  # in Celsius
    condition: WeatherCondition
    humidity: int
    wind_speed: float
    feels_like: float
    description: str = ""

@dataclass
class Avatar:
    measurements: BodyMeasurements
    preferred_styles: List[Style]
    
    def generate_2d_representation(self) -> Dict:
        """Generate a simple 2D avatar based on measurements"""
        # Basic proportional calculations for 2D representation
        scale_factor = self.measurements.height / 170  # normalize to average height
        
        return {
            "head_size": 20 * scale_factor,
            "shoulder_width": self.measurements.shoulder_width * scale_factor * 0.3,
            "chest_width": self.measurements.chest_bust * scale_factor * 0.25,
            "waist_width": self.measurements.waist * scale_factor * 0.25,
            "hip_width": self.measurements.hips * scale_factor * 0.25,
            "height": self.measurements.height * scale_factor * 0.5,
            "gender": self.measurements.gender.value
        }

class WeatherService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "http://api.openweathermap.org/data/2.5"
    
    def get_current_weather(self, location: str) -> WeatherData:
        """Fetch current weather data (placeholder implementation)"""
        # In a real app, you'd make an API call here
        # For demo purposes, returning mock data
        mock_conditions = [
            WeatherData(22.0, WeatherCondition.SUNNY, 45, 5.2, 24.0, "clear sky"),
            WeatherData(15.0, WeatherCondition.RAINY, 80, 12.1, 12.0, "light rain"),
            WeatherData(8.0, WeatherCondition.CLOUDY, 65, 8.5, 6.0, "overcast clouds"),
            WeatherData(28.0, WeatherCondition.SUNNY, 35, 3.1, 30.0, "clear sky")
        ]
        return random.choice(mock_conditions)

class OutfitRecommendationEngine:
    def __init__(self):
        self.temperature_thresholds = {
            "very_cold": 5,
            "cold": 15,
            "mild": 20,
            "warm": 25,
            "hot": 30
        }
    
    def recommend_outfit(self, avatar: Avatar, weather: WeatherData, 
                        wardrobe: List[ClothingItem]) -> Dict:
        """Generate outfit recommendation based on weather and preferences"""
        
        # Filter clothes by weather appropriateness
        suitable_items = self._filter_by_weather(wardrobe, weather)
        
        # Filter by preferred styles
        style_filtered = self._filter_by_style(suitable_items, avatar.preferred_styles)
        
        # Build outfit
        outfit = self._build_outfit(style_filtered, weather)
        
        # Add weather-specific recommendations
        recommendations = self._add_weather_recommendations(weather)
        
        return {
            "outfit": outfit,
            "weather_recommendations": recommendations,
            "weather_info": {
                "temperature": weather.temperature,
                "condition": weather.condition.value,
                "feels_like": weather.feels_like
            }
        }
    
    def _filter_by_weather(self, items: List[ClothingItem], 
                          weather: WeatherData) -> List[ClothingItem]:
        """Filter clothing items based on weather conditions"""
        suitable_items = []
        
        for item in items:
            # Check temperature appropriateness
            if weather.temperature < self.temperature_thresholds["cold"]:
                if item.warmth_level >= 3:  # Need warm clothes
                    suitable_items.append(item)
            elif weather.temperature > self.temperature_thresholds["warm"]:
                if item.warmth_level <= 2:  # Need cool clothes
                    suitable_items.append(item)
            else:
                suitable_items.append(item)  # Mid-range temperature
            
            # Check weather condition compatibility
            if weather.condition in item.weather_resistance:
                if item not in suitable_items:
                    suitable_items.append(item)
        
        return suitable_items
    
    def _filter_by_style(self, items: List[ClothingItem], 
                        preferred_styles: List[Style]) -> List[ClothingItem]:
        """Filter items by user's preferred styles"""
        return [item for item in items if item.style in preferred_styles]
    
    def _build_outfit(self, items: List[ClothingItem], 
                     weather: WeatherData) -> Dict[str, ClothingItem]:
        """Build a complete outfit from available items"""
        outfit = {}
        
        # Categorize items by type
        items_by_type = {}
        for item in items:
            if item.type not in items_by_type:
                items_by_type[item.type] = []
            items_by_type[item.type].append(item)
        
        # Select one item from each category
        for clothing_type in [ClothingType.TOP, ClothingType.BOTTOM, ClothingType.SHOES]:
            if clothing_type in items_by_type:
                outfit[clothing_type.value] = random.choice(items_by_type[clothing_type])
        
        # Add outerwear if cold or rainy
        if (weather.temperature < self.temperature_thresholds["mild"] or 
            weather.condition == WeatherCondition.RAINY):
            if ClothingType.OUTERWEAR in items_by_type:
                outfit[ClothingType.OUTERWEAR.value] = random.choice(
                    items_by_type[ClothingType.OUTERWEAR]
                )
        
        # Add accessories
        if ClothingType.ACCESSORY in items_by_type:
            outfit[ClothingType.ACCESSORY.value] = random.choice(
                items_by_type[ClothingType.ACCESSORY]
            )
        
        return outfit
    
    def _add_weather_recommendations(self, weather: WeatherData) -> List[str]:
        """Add specific recommendations based on weather"""
        recommendations = []
        
        if weather.condition == WeatherCondition.RAINY:
            recommendations.append("Consider bringing an umbrella")
            recommendations.append("Wear waterproof shoes if available")
        
        if weather.temperature < 10:
            recommendations.append("Layer up for warmth")
            recommendations.append("Don't forget a warm accessory like a scarf")
        
        if weather.temperature > 30:
            recommendations.append("Stay hydrated and seek shade")
            recommendations.append("Light, breathable fabrics recommended")
        
        if weather.wind_speed > 15:
            recommendations.append("Secure loose clothing and accessories")
        
        return recommendations

class VirtualClosetApp:
    def __init__(self, weather_service=None, recommendation_engine=None, wardrobe=None):
        self.weather_service = weather_service or WeatherService("api_key_here")
        self.recommendation_engine = recommendation_engine or OutfitRecommendationEngine()
        self.user_avatar = None
        self.wardrobe = wardrobe or []
        self.user_location = "New York"  # Default location
        self.latitude = None
        self.longitude = None
        self.selected_avatar = None
    
    def setup_user_profile(self, measurements: BodyMeasurements, 
                          preferred_styles: List[Style]):
        """Initialize user avatar and preferences"""
        self.user_avatar = Avatar(measurements, preferred_styles)
        print("User profile created successfully!")
        return self.user_avatar.generate_2d_representation()
    
    def add_clothing_item(self, item: ClothingItem):
        """Add a clothing item to the wardrobe"""
        self.wardrobe.append(item)
        print(f"Added {item.name} to your wardrobe!")
    
    def get_daily_outfit(self) -> Dict:
        """Generate today's outfit recommendation"""
        if not self.user_avatar:
            raise ValueError("User profile not set up. Please create your avatar first.")
        
        if not self.wardrobe:
            raise ValueError("No clothing items in wardrobe. Please add some clothes first.")
        
        # Get current weather
        weather = self.weather_service.get_current_weather(self.user_location)
        
        # Generate outfit recommendation
        recommendation = self.recommendation_engine.recommend_outfit(
            self.user_avatar, weather, self.wardrobe
        )
        
        return recommendation
    
    def save_wardrobe(self, filename: str):
        """Save wardrobe to JSON file"""
        wardrobe_data = []
        for item in self.wardrobe:
            wardrobe_data.append({
                "id": item.id,
                "name": item.name,
                "type": item.type.value,
                "fitting": item.fitting.value,
                "style": item.style.value,
                "color": item.color,
                "warmth_level": item.warmth_level,
                "weather_resistance": [w.value for w in item.weather_resistance],
                "image_path": item.image_path,
                "tags": item.tags
            })
        
        with open(filename, 'w') as f:
            json.dump(wardrobe_data, f, indent=2)
        print(f"Wardrobe saved to {filename}")

# Example usage and testing
def demo_app():
    # Initialize app
    app = VirtualClosetApp("your_weather_api_key_here")
    
    # Create user profile
    measurements = BodyMeasurements(
        height=175,
        chest_bust=90,
        waist=75,
        hips=95,
        shoulder_width=42,
        gender=Gender.FEMALE
    )
    
    avatar_data = app.setup_user_profile(measurements, [Style.CASUAL, Style.STREETWEAR])
    print("Avatar representation:", avatar_data)
    
    # Add some sample clothing items
    sample_clothes = [
        ClothingItem("1", "White T-Shirt", ClothingType.TOP, Fitting.REGULAR, 
                    Style.CASUAL, "white", 1, [WeatherCondition.SUNNY], 
                    "images/white_tshirt.jpg", ["basic", "versatile"]),
        
        ClothingItem("2", "Blue Jeans", ClothingType.BOTTOM, Fitting.REGULAR, 
                    Style.CASUAL, "blue", 2, [WeatherCondition.SUNNY, WeatherCondition.CLOUDY], 
                    "images/blue_jeans.jpg", ["denim", "classic"]),
        
        ClothingItem("3", "Hoodie", ClothingType.OUTERWEAR, Fitting.OVERSIZED, 
                    Style.STREETWEAR, "black", 4, [WeatherCondition.CLOUDY, WeatherCondition.RAINY], 
                    "images/black_hoodie.jpg", ["warm", "comfortable"]),
        
        ClothingItem("4", "Sneakers", ClothingType.SHOES, Fitting.REGULAR, 
                    Style.STREETWEAR, "white", 1, [WeatherCondition.SUNNY, WeatherCondition.CLOUDY], 
                    "images/white_sneakers.jpg", ["comfortable", "athletic"])
    ]
    
    for item in sample_clothes:
        app.add_clothing_item(item)
    
    # Get daily outfit recommendation
    try:
        daily_outfit = app.get_daily_outfit()
        print("\n=== TODAY'S OUTFIT RECOMMENDATION ===")
        print(f"Weather: {daily_outfit['weather_info']['temperature']}°C, {daily_outfit['weather_info']['condition']}")
        print("Recommended outfit:")
        for category, item in daily_outfit['outfit'].items():
            print(f"- {category.title()}: {item.name} ({item.color})")
        
        print("\nWeather recommendations:")
        for rec in daily_outfit['weather_recommendations']:
            print(f"- {rec}")
            
    except ValueError as e:
        print(f"Error: {e}")
    
    # Save wardrobe
    app.save_wardrobe("my_wardrobe.json")

if __name__ == "__main__":
    demo_app()