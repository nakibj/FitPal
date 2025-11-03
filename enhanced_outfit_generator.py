# Enhanced AI Outfit Generator - Manual Items with Smart Styling

import json
import uuid
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import openai
from main import ClothingItem, ClothingType, Fitting, Style, WeatherCondition

# Expanded Style Enum with many more options
class ExpandedStyle(Enum):
    # Casual Styles
    CASUAL = "casual"
    ATHLEISURE = "athleisure"
    BOHO = "boho"
    MINIMALIST = "minimalist"
    
    # Fashion Forward
    STREETWEAR = "streetwear"
    Y2K = "y2k"
    GRUNGE = "grunge"
    ALT = "alt"
    GOTH = "goth"
    PUNK = "punk"
    EMO = "emo"
    
    # Classic/Professional
    OLD_MONEY = "old_money"
    PREPPY = "preppy"
    BUSINESS_CASUAL = "business_casual"
    BUSINESS_FORMAL = "business_formal"
    SMART_CASUAL = "smart_casual"
    CLASSIC = "classic"
    
    # Special Occasion
    FORMAL = "formal"
    COCKTAIL = "cocktail"
    BLACK_TIE = "black_tie"
    DATE_NIGHT = "date_night"
    PARTY = "party"
    
    # Seasonal/Theme
    VACATION = "vacation"
    BEACH = "beach"
    SPORTY = "sporty"
    OUTDOOR = "outdoor"
    COZY = "cozy"
    
    # Trendy/Modern
    AESTHETIC = "aesthetic"
    DARK_ACADEMIA = "dark_academia"
    LIGHT_ACADEMIA = "light_academia"
    COTTAGECORE = "cottagecore"
    VINTAGE = "vintage"
    RETRO = "retro"
    
    # Edgy/Bold
    AVANT_GARDE = "avant_garde"
    EXPERIMENTAL = "experimental"
    ARTSY = "artsy"
    ECLECTIC = "eclectic"

class EnhancedAIOutfitGenerator:
    """Enhanced outfit generator using manual wardrobe items with AI styling"""
    
    def __init__(self, openai_api_key: str):
        self.client = openai.OpenAI(api_key=openai_api_key)
        
        # Style descriptions for better AI understanding
        self.style_descriptions = {
            "casual": "Comfortable, everyday wear. Relaxed and effortless.",
            "athleisure": "Athletic-inspired casual wear. Sporty yet stylish.",
            "boho": "Bohemian, free-spirited with flowing fabrics and earthy tones.",
            "minimalist": "Clean lines, neutral colors, simple and sophisticated.",
            
            "streetwear": "Urban, trendy, often featuring sneakers and statement pieces.",
            "y2k": "Early 2000s inspired with metallic fabrics and bold colors.",
            "grunge": "Alternative, edgy with distressed items and dark colors.",
            "alt": "Alternative fashion, non-mainstream and creative.",
            "goth": "Dark, dramatic with black clothing and bold accessories.",
            "punk": "Rebellious with leather, studs, and unconventional pieces.",
            "emo": "Emotional expression through dark colors and fitted clothing.",
            
            "old_money": "Understated luxury, classic pieces, refined elegance.",
            "preppy": "Polished, collegiate-inspired with clean cuts.",
            "business_casual": "Professional yet approachable for office settings.",
            "business_formal": "Formal professional attire for important meetings.",
            "smart_casual": "Polished casual that's appropriate for nice occasions.",
            "classic": "Timeless, well-tailored pieces that never go out of style.",
            
            "formal": "Elegant evening wear for special occasions.",
            "cocktail": "Semi-formal party attire, stylish and sophisticated.",
            "black_tie": "Ultra-formal evening wear for gala events.",
            "date_night": "Romantic and attractive for special evenings.",
            "party": "Fun, festive outfits for celebrations.",
            
            "vacation": "Comfortable travel wear for exploring new places.",
            "beach": "Light, breezy clothing perfect for seaside activities.",
            "sporty": "Athletic wear for active pursuits and workouts.",
            "outdoor": "Practical clothing for hiking and outdoor adventures.",
            "cozy": "Warm, comfortable clothing for relaxing at home.",
            
            "aesthetic": "Visually pleasing, Instagram-worthy outfits.",
            "dark_academia": "Scholarly, vintage-inspired with rich colors.",
            "light_academia": "Academic-inspired with lighter, softer tones.",
            "cottagecore": "Rural, romantic with natural fabrics and florals.",
            "vintage": "Authentic pieces from past decades.",
            "retro": "Modern interpretations of past fashion trends.",
            
            "avant_garde": "Experimental, artistic, pushing fashion boundaries.",
            "experimental": "Unconventional combinations and unique styling.",
            "artsy": "Creative, expressive clothing choices.",
            "eclectic": "Mix of different styles and eras in one outfit."
        }
    
    def generate_outfit_from_wardrobe(self, wardrobe: List[ClothingItem], weather_data: Dict, 
                                    target_style: str, user_preferences: Dict = None) -> Dict:
        """Generate outfit using manual wardrobe items with AI styling intelligence"""
        
        if not wardrobe:
            return {"error": "No items in wardrobe"}
        
        # Filter items suitable for weather
        weather_suitable_items = self._filter_by_weather(wardrobe, weather_data)
        
        if not weather_suitable_items:
            weather_suitable_items = wardrobe  # Fallback to all items
        
        # Create detailed wardrobe context
        wardrobe_context = self._create_wardrobe_context(weather_suitable_items)
        weather_context = self._create_weather_context(weather_data)
        style_context = self._create_style_context(target_style)
        
        prompt = f"""
You are an expert fashion stylist. Create a cohesive outfit from the user's wardrobe.

TARGET STYLE: {target_style.upper()}
{style_context}

CURRENT WEATHER:
{weather_context}

USER'S WARDROBE ITEMS:
{wardrobe_context}

STYLING RULES:
1. Choose items that work well together for the {target_style} aesthetic
2. Consider color coordination and style harmony
3. Ensure weather appropriateness 
4. Create a complete outfit with top, bottom, shoes (add outerwear/accessories if suitable)
5. Only use item IDs from the provided wardrobe list
6. Prioritize items that match or complement the target style

Respond with JSON:
{{
    "outfit": {{
        "top": "item_id or null",
        "bottom": "item_id or null",
        "outerwear": "item_id or null", 
        "shoes": "item_id or null",
        "accessory": "item_id or null"
    }},
    "reasoning": "Detailed explanation of why these items work together for {target_style}",
    "style_match_score": 1-10,
    "weather_appropriateness": 1-10,
    "color_harmony": "description of color coordination",
    "styling_tips": ["specific tips for wearing this outfit"],
    "alternative_pieces": ["item_ids that could be swapped for variety"]
}}

Focus on creating an authentic {target_style} look using the available pieces.
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a professional fashion stylist specializing in {target_style} aesthetics. Create cohesive, weather-appropriate outfits."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.3  # Some creativity but consistent
            )
            
            ai_response = response.choices[0].message.content
            return self._parse_outfit_response(ai_response, weather_suitable_items, target_style)
            
        except Exception as e:
            print(f"❌ Error generating AI outfit: {e}")
            return self._fallback_outfit_generation(weather_suitable_items, weather_data, target_style)
    
    def _filter_by_weather(self, items: List[ClothingItem], weather_data: Dict) -> List[ClothingItem]:
        """Filter items appropriate for current weather"""
        temperature = weather_data.get('temperature', 20)
        condition = weather_data.get('condition', 'sunny').lower()
        
        suitable_items = []
        
        # Weather condition mapping
        weather_condition_map = {
            'rainy': WeatherCondition.RAINY,
            'rain': WeatherCondition.RAINY,
            'snowy': WeatherCondition.SNOWY,
            'snow': WeatherCondition.SNOWY,
            'sunny': WeatherCondition.SUNNY,
            'clear': WeatherCondition.SUNNY,
            'cloudy': WeatherCondition.CLOUDY
        }
        
        required_condition = weather_condition_map.get(condition, WeatherCondition.SUNNY)
        
        for item in items:
            # Temperature appropriateness
            temp_suitable = False
            if temperature < 5:  # Very cold
                temp_suitable = item.warmth_level >= 4
            elif temperature < 15:  # Cold
                temp_suitable = item.warmth_level >= 2
            elif temperature < 25:  # Moderate
                temp_suitable = True  # Most items work
            else:  # Hot
                temp_suitable = item.warmth_level <= 3
            
            # Weather condition check
            weather_suitable = required_condition in item.weather_resistance
            
            if temp_suitable and weather_suitable:
                suitable_items.append(item)
        
        return suitable_items if suitable_items else items
    
    def _create_wardrobe_context(self, items: List[ClothingItem]) -> str:
        """Create detailed context of available wardrobe items"""
        context_lines = []
        
        # Group by type for better organization
        by_type = {}
        for item in items:
            if item.type not in by_type:
                by_type[item.type] = []
            by_type[item.type].append(item)
        
        for clothing_type, type_items in by_type.items():
            context_lines.append(f"\n{clothing_type.value.upper()}S:")
            for item in type_items:
                # Include all relevant details
                tags_str = ", ".join(item.tags) if item.tags else "no tags"
                weather_str = ", ".join([w.value for w in item.weather_resistance])
                
                context_lines.append(
                    f"  ID: {item.id} | {item.name} | Color: {item.color} | "
                    f"Style: {item.style.value} | Fit: {item.fitting.value} | "
                    f"Warmth: {item.warmth_level}/5 | Weather: {weather_str} | "
                    f"Tags: {tags_str}"
                )
        
        return "\n".join(context_lines)
    
    def _create_weather_context(self, weather_data: Dict) -> str:
        """Create weather description for styling context"""
        return f"""
Temperature: {weather_data.get('temperature', 20)}°C
Condition: {weather_data.get('condition', 'unknown')}
Feels like: {weather_data.get('feels_like', weather_data.get('temperature', 20))}°C
Humidity: {weather_data.get('humidity', 50)}%
"""
    
    def _create_style_context(self, target_style: str) -> str:
        """Create context for the target style"""
        description = self.style_descriptions.get(target_style, "Contemporary fashion style")
        return f"Style Description: {description}"
    
    def _parse_outfit_response(self, ai_response: str, items: List[ClothingItem], style: str) -> Dict:
        """Parse AI response and validate item IDs"""
        try:
            # Clean and extract JSON
            clean_response = ai_response.strip()
            if clean_response.startswith('```json'):
                clean_response = clean_response[7:]
            if clean_response.endswith('```'):
                clean_response = clean_response[:-3]
            
            json_start = clean_response.find('{')
            json_end = clean_response.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                json_str = clean_response[json_start:json_end]
                parsed = json.loads(json_str)
                
                # Validate item IDs
                valid_ids = {item.id for item in items}
                outfit = parsed.get("outfit", {})
                
                for category, item_id in outfit.items():
                    if item_id and item_id not in valid_ids:
                        print(f"⚠️ Invalid item ID {item_id} for {category}")
                        outfit[category] = None
                
                return {
                    "outfit": outfit,
                    "style": style,
                    "reasoning": parsed.get("reasoning", f"AI-styled {style} outfit"),
                    "style_match_score": max(1, min(10, parsed.get("style_match_score", 7))),
                    "weather_appropriateness": max(1, min(10, parsed.get("weather_appropriateness", 7))),
                    "color_harmony": parsed.get("color_harmony", "Colors work well together"),
                    "styling_tips": parsed.get("styling_tips", []),
                    "alternative_pieces": parsed.get("alternative_pieces", []),
                    "ai_powered": True
                }
                
        except Exception as e:
            print(f"❌ Error parsing outfit response: {e}")
        
        return self._fallback_outfit_generation(items, {}, style)
    
    def _fallback_outfit_generation(self, items: List[ClothingItem], weather_data: Dict, style: str) -> Dict:
        """Create a basic outfit when AI fails"""
        outfit = {}
        
        # Group by type
        by_type = {}
        for item in items:
            if item.type not in by_type:
                by_type[item.type] = []
            by_type[item.type].append(item)
        
        # Simple selection - prefer items that match the target style
        for clothing_type in [ClothingType.TOP, ClothingType.BOTTOM, ClothingType.SHOES]:
            if clothing_type in by_type:
                # Try to find items matching the target style first
                matching_style_items = [item for item in by_type[clothing_type] 
                                      if item.style.value == style]
                
                if matching_style_items:
                    outfit[clothing_type.value] = matching_style_items[0].id
                else:
                    outfit[clothing_type.value] = by_type[clothing_type][0].id
        
        # Add outerwear if cold
        temperature = weather_data.get('temperature', 20)
        if temperature < 18 and ClothingType.OUTERWEAR in by_type:
            outfit[ClothingType.OUTERWEAR.value] = by_type[ClothingType.OUTERWEAR][0].id
        
        return {
            "outfit": outfit,
            "style": style,
            "reasoning": f"Basic {style} outfit created from available items",
            "style_match_score": 5,
            "weather_appropriateness": 6,
            "color_harmony": "Basic color coordination",
            "styling_tips": [f"This is a simple {style} outfit. Add more {style} pieces for better results!"],
            "alternative_pieces": [],
            "ai_powered": False
        }

# Style utility functions
def get_all_available_styles():
    """Get all available style options"""
    return {
        "casual_styles": [
            {"value": "casual", "label": "Casual", "description": "Comfortable everyday wear"},
            {"value": "athleisure", "label": "Athleisure", "description": "Sporty yet stylish"},
            {"value": "boho", "label": "Boho", "description": "Free-spirited bohemian"},
            {"value": "minimalist", "label": "Minimalist", "description": "Clean and simple"},
            {"value": "cozy", "label": "Cozy", "description": "Warm and comfortable"}
        ],
        "trendy_styles": [
            {"value": "streetwear", "label": "Streetwear", "description": "Urban and trendy"},
            {"value": "y2k", "label": "Y2K", "description": "Early 2000s inspired"},
            {"value": "aesthetic", "label": "Aesthetic", "description": "Instagram-worthy"},
            {"value": "grunge", "label": "Grunge", "description": "Alternative and edgy"},
            {"value": "alt", "label": "Alternative", "description": "Non-mainstream creative"}
        ],
        "professional_styles": [
            {"value": "business_casual", "label": "Business Casual", "description": "Professional yet approachable"},
            {"value": "business_formal", "label": "Business Formal", "description": "Formal office attire"},
            {"value": "smart_casual", "label": "Smart Casual", "description": "Polished casual"},
            {"value": "old_money", "label": "Old Money", "description": "Understated luxury"},
            {"value": "preppy", "label": "Preppy", "description": "Collegiate polish"}
        ],
        "special_occasion": [
            {"value": "formal", "label": "Formal", "description": "Elegant evening wear"},
            {"value": "cocktail", "label": "Cocktail", "description": "Semi-formal party"},
            {"value": "date_night", "label": "Date Night", "description": "Romantic evening"},
            {"value": "party", "label": "Party", "description": "Fun celebration wear"}
        ],
        "lifestyle_styles": [
            {"value": "vacation", "label": "Vacation", "description": "Comfortable travel wear"},
            {"value": "beach", "label": "Beach", "description": "Light seaside clothing"},
            {"value": "sporty", "label": "Sporty", "description": "Athletic wear"},
            {"value": "outdoor", "label": "Outdoor", "description": "Adventure ready"}
        ],
        "aesthetic_movements": [
            {"value": "dark_academia", "label": "Dark Academia", "description": "Scholarly vintage vibes"},
            {"value": "light_academia", "label": "Light Academia", "description": "Soft academic aesthetic"},
            {"value": "cottagecore", "label": "Cottagecore", "description": "Rural romantic"},
            {"value": "vintage", "label": "Vintage", "description": "Authentic retro pieces"},
            {"value": "goth", "label": "Goth", "description": "Dark dramatic style"}
        ]
    }

def get_style_recommendations_for_occasion(occasion: str) -> List[str]:
    """Get recommended styles for specific occasions"""
    occasion_styles = {
        "work": ["business_casual", "business_formal", "smart_casual", "classic"],
        "weekend": ["casual", "athleisure", "boho", "minimalist"],
        "date": ["date_night", "smart_casual", "cocktail", "aesthetic"],
        "party": ["party", "cocktail", "y2k", "aesthetic"],
        "travel": ["vacation", "casual", "athleisure", "comfortable"],
        "formal_event": ["formal", "cocktail", "black_tie", "classic"]
    }
    return occasion_styles.get(occasion, ["casual"])