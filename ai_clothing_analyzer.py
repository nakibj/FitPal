# ai_clothing_analyzer.py - IMPROVED VERSION WITH BETTER CLASSIFICATION

import base64
import json
import requests
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import openai
from PIL import Image, ImageOps
import io
import os
from main import ClothingItem, ClothingType, Fitting, Style, WeatherCondition

class AIClothingAnalyzer:
    def __init__(self, openai_api_key: str):
        """Initialize the AI clothing analyzer with OpenAI API key"""
        self.client = openai.OpenAI(api_key=openai_api_key)
        
        # IMPROVED type identification with stronger keywords
        self.type_keywords = {
            "bottom": [
                # Core pants/bottoms keywords
                "jean", "jeans", "pant", "pants", "trouser", "trousers", 
                "short", "shorts", "skirt", "skirts", "legging", "leggings",
                "bottom", "bottoms", "leg", "legs", "denim", "cargo", "chino", "chinos",
                "slack", "slacks", "sweatpants", "jogger", "joggers", "pajama pants",
                "track pants", "yoga pants", "dress pants", "khaki", "khakis",
                "culottes", "palazzo", "capri", "bermuda", "board shorts",
                # Key identifying phrases
                "covers legs", "worn on legs", "lower body", "waist to ankle",
                "hip to ankle", "goes on legs", "put on legs"
            ],
            "top": [
                # Core top keywords
                "shirt", "shirts", "tee", "t-shirt", "t-shirts", "blouse", "blouses",
                "tank", "tank top", "sweater", "sweaters", "pullover", "cardigan",
                "top", "tops", "polo", "jersey", "vest", "tube top", "crop top",
                "hoodie", "sweatshirt", "turtleneck", "halter", "camisole",
                "long sleeve", "short sleeve", "sleeveless",
                # Key identifying phrases
                "covers torso", "worn on torso", "upper body", "chest area",
                "goes on torso", "put on upper body", "covers chest"
            ],
            "outerwear": [
                "jacket", "jackets", "coat", "coats", "blazer", "blazers",
                "windbreaker", "bomber", "leather jacket", "denim jacket",
                "trench coat", "parka", "peacoat", "raincoat", "fleece",
                "zip-up", "pullover hoodie", "poncho", "cape", "outerwear",
                "outer layer", "worn over", "layering piece"
            ],
            "shoes": [
                "shoe", "shoes", "sneaker", "sneakers", "boot", "boots",
                "sandal", "sandals", "heel", "heels", "flat", "flats",
                "loafer", "loafers", "oxford", "oxfords", "athletic shoes",
                "running shoes", "dress shoes", "casual shoes", "footwear",
                "worn on feet", "goes on feet", "foot", "feet"
            ],
            "accessory": [
                "hat", "cap", "belt", "bag", "scarf", "gloves", "sunglasses",
                "watch", "necklace", "bracelet", "earrings", "ring", "tie",
                "bow tie", "purse", "backpack", "accessory", "accessories"
            ]
        }

    def analyze_clothing_image(self, image_data: bytes, user_context: Dict = None) -> Dict:
        """Enhanced clothing analysis with MUCH better classification"""
        try:
            # Preprocess image
            processed_image = self.preprocess_image(image_data)
            base64_image = base64.b64encode(processed_image).decode('utf-8')
            
            # Create VERY specific prompt focusing on pants vs tops
            prompt = self._create_ultra_specific_prompt(user_context)
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a CLOTHING TYPE EXPERT. Your #1 job is to CORRECTLY identify if something is PANTS/BOTTOMS vs SHIRTS/TOPS.

CRITICAL CLASSIFICATION RULES:
1. PANTS/JEANS/SHORTS/SKIRTS = "bottom" (they cover LEGS)
2. SHIRTS/T-SHIRTS/BLOUSES/SWEATERS = "top" (they cover TORSO/CHEST)
3. JACKETS/COATS = "outerwear" (worn OVER other clothes)
4. SHOES/BOOTS/SNEAKERS = "shoes" (worn on FEET)
5. HATS/BAGS/BELTS = "accessory"

LOOK AT THE SHAPE:
- If it has TWO LEG HOLES and covers legs → "bottom"
- If it has ARM HOLES and covers chest/torso → "top"
- If it goes OVER other clothes → "outerwear"

YOU MUST BE 100% ACCURATE ON TYPE CLASSIFICATION."""
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=600,
                temperature=0.0  # Zero temperature for consistency
            )
            
            ai_response = response.choices[0].message.content
            print(f"🤖 Raw AI Response: {ai_response}")
            
            # Parse and apply MULTIPLE validation layers
            result = self._parse_and_ultra_validate(ai_response)
            
            return result
            
        except Exception as e:
            print(f"❌ Error in AI analysis: {e}")
            return self._get_smart_fallback_analysis()

    def _create_ultra_specific_prompt(self, user_context: Dict = None) -> str:
        """Create an ultra-specific prompt that focuses on correct classification"""
        
        prompt = """
STEP 1: DESCRIBE WHAT YOU SEE
Look at this image and describe the clothing item in one clear sentence.

STEP 2: IDENTIFY THE BODY PART IT COVERS
- Does this item cover the LEGS/LOWER BODY? → bottom
- Does this item cover the TORSO/CHEST/UPPER BODY? → top  
- Does this item go OVER other clothes? → outerwear
- Does this item go on FEET? → shoes
- Is this an ACCESSORY? → accessory

STEP 3: CHECK THE SHAPE AND STRUCTURE
- Does it have TWO LEG OPENINGS? → bottom (pants/jeans/shorts)
- Does it have ARM OPENINGS and covers chest? → top (shirts/t-shirts)
- Does it have SLEEVES and worn over other items? → outerwear

STEP 4: DOUBLE-CHECK WITH KEYWORDS
BOTTOMS: pants, jeans, shorts, skirt, leggings, trousers
TOPS: shirt, t-shirt, blouse, tank top, sweater
OUTERWEAR: jacket, coat, blazer, hoodie (if thick/worn over)
SHOES: sneakers, boots, sandals, any footwear
ACCESSORIES: hat, bag, belt, jewelry

STEP 5: PROVIDE JSON RESPONSE

{
    "visual_description": "What I see in the image",
    "body_part_covered": "legs/torso/feet/head/etc",
    "shape_analysis": "leg openings/arm openings/structure",
    "type": "bottom/top/outerwear/shoes/accessory",
    "name": "Specific item name",
    "color": "Primary color",
    "fitting": "tight/regular/oversized/long",
    "style": "casual/streetwear/old_money/alt",
    "warmth_level": 1-5,
    "weather_resistance": ["sunny", "cloudy", "rainy", "snowy"],
    "confidence_reasoning": "Why I chose this type"
}

REMEMBER:
- PANTS/JEANS = "bottom" (covers legs)
- SHIRTS = "top" (covers torso)
- Be 100% accurate on type classification!

RESPOND ONLY WITH THE JSON."""
        
        return prompt

    def _parse_and_ultra_validate(self, ai_response: str) -> Dict:
        """Enhanced parsing with multiple validation layers"""
        try:
            # Clean and extract JSON
            clean_response = ai_response.strip()
            if clean_response.startswith('```json'):
                clean_response = clean_response[7:]
            if clean_response.endswith('```'):
                clean_response = clean_response[:-3]
                
            json_start = clean_response.find('{')
            json_end = clean_response.rfind('}') + 1
            
            if json_start == -1 or json_end == -1:
                raise ValueError("No JSON found in response")
                
            json_str = clean_response[json_start:json_end]
            parsed_data = json.loads(json_str)
            
            print(f"🔍 Parsed data: {parsed_data}")
            
            # Apply MULTIPLE validation layers
            validated_result = self._apply_multiple_validation_layers(parsed_data, ai_response)
            
            return validated_result
            
        except Exception as e:
            print(f"❌ Parse error: {e}")
            return self._get_smart_fallback_analysis()

    def _apply_multiple_validation_layers(self, data: Dict, full_response: str) -> Dict:
        """Apply multiple layers of validation to ensure correct classification"""
        
        # Extract key information
        visual_description = str(data.get("visual_description", "")).lower()
        body_part_covered = str(data.get("body_part_covered", "")).lower()
        shape_analysis = str(data.get("shape_analysis", "")).lower()
        original_type = str(data.get("type", "")).lower().strip()
        item_name = str(data.get("name", "Clothing Item"))
        
        print(f"🔍 Validation Input:")
        print(f"   - Description: {visual_description}")
        print(f"   - Body part: {body_part_covered}")
        print(f"   - Shape: {shape_analysis}")
        print(f"   - Original type: {original_type}")
        print(f"   - Name: {item_name}")
        
        # LAYER 1: Keyword-based validation
        all_text = f"{visual_description} {body_part_covered} {shape_analysis} {item_name} {full_response}".lower()
        
        # Count strong indicators for each type
        type_scores = {}
        for clothing_type, keywords in self.type_keywords.items():
            score = 0
            found_keywords = []
            for keyword in keywords:
                if keyword in all_text:
                    score += 1
                    found_keywords.append(keyword)
            type_scores[clothing_type] = score
            if score > 0:
                print(f"   - {clothing_type}: {score} matches ({found_keywords[:3]})")
        
        # LAYER 2: Body part analysis
        body_part_type = None
        if any(word in body_part_covered for word in ["leg", "lower", "waist", "hip"]):
            body_part_type = "bottom"
        elif any(word in body_part_covered for word in ["torso", "chest", "upper", "arm"]):
            body_part_type = "top"
        elif any(word in body_part_covered for word in ["foot", "feet"]):
            body_part_type = "shoes"
        
        print(f"   - Body part analysis suggests: {body_part_type}")
        
        # LAYER 3: Shape analysis
        shape_type = None
        if any(word in shape_analysis for word in ["leg opening", "two legs", "leg holes"]):
            shape_type = "bottom"
        elif any(word in shape_analysis for word in ["arm opening", "sleeve", "torso"]):
            shape_type = "top"
        
        print(f"   - Shape analysis suggests: {shape_type}")
        
        # LAYER 4: Determine final type
        final_type = original_type
        
        # If keyword analysis has a clear winner, use it
        if type_scores:
            max_score = max(type_scores.values())
            if max_score > 0:
                keyword_winner = max(type_scores, key=type_scores.get)
                if max_score >= 2:  # Strong indication
                    final_type = keyword_winner
                    print(f"🔧 Keyword override: {original_type} → {final_type} (score: {max_score})")
        
        # Body part analysis override
        if body_part_type and body_part_type != final_type:
            final_type = body_part_type
            print(f"🔧 Body part override: {original_type} → {final_type}")
        
        # Shape analysis override (strongest indicator)
        if shape_type and shape_type != final_type:
            final_type = shape_type
            print(f"🔧 Shape override: {original_type} → {final_type}")
        
        # Fallback validation
        valid_types = ["top", "bottom", "outerwear", "shoes", "accessory"]
        if final_type not in valid_types:
            final_type = "top"  # Safe default
            print(f"🔧 Fallback to default: {final_type}")
        
        # Validate other fields
        color = self._validate_color(data.get("color", ""), all_text)
        fitting = self._validate_fitting(data.get("fitting", "regular"))
        style = self._validate_style(data.get("style", "casual"))
        warmth_level = self._validate_warmth_level(data.get("warmth_level", 3))
        weather_resistance = self._validate_weather_resistance(data.get("weather_resistance", ["sunny", "cloudy"]))
        
        result = {
            "name": item_name[:50],
            "type": final_type,
            "color": color,
            "fitting": fitting,
            "style": style,
            "warmth_level": warmth_level,
            "weather_resistance": weather_resistance,
            "material_analysis": str(data.get("confidence_reasoning", ""))[:200],
            "style_reasoning": str(data.get("confidence_reasoning", ""))[:200],
            "ai_confidence": 0.9 if max(type_scores.values()) >= 2 else 0.7
        }
        
        print(f"✅ FINAL RESULT: Type={result['type']}, Color={result['color']}, Name={result['name']}")
        return result

    def _validate_color(self, original_color: str, all_text: str) -> str:
        """Validate and correct color based on text analysis"""
        color_keywords = {
            "black": ["black", "dark", "charcoal"],
            "white": ["white", "cream", "ivory"],
            "blue": ["blue", "navy", "denim"],
            "gray": ["gray", "grey", "silver"],
            "red": ["red", "burgundy", "maroon"],
            "green": ["green", "olive", "forest"],
            "yellow": ["yellow", "gold", "mustard"],
            "brown": ["brown", "tan", "beige", "khaki"],
            "pink": ["pink", "rose", "blush"],
            "purple": ["purple", "violet", "lavender"]
        }
        
        # Look for color keywords in text
        for color, keywords in color_keywords.items():
            for keyword in keywords:
                if keyword in all_text:
                    return color
        
        # Return original if valid
        if original_color and len(original_color.strip()) > 2:
            return original_color.strip()
        
        return "unknown"

    def _validate_fitting(self, fitting: str) -> str:
        """Validate fitting value"""
        valid_fittings = ["tight", "regular", "oversized", "long"]
        return fitting if fitting in valid_fittings else "regular"

    def _validate_style(self, style: str) -> str:
        """Validate style value"""
        valid_styles = ["streetwear", "old_money", "alt", "casual"]
        return style if style in valid_styles else "casual"

    def _validate_warmth_level(self, warmth_level) -> int:
        """Validate warmth level"""
        try:
            level = int(warmth_level)
            return max(1, min(5, level))
        except:
            return 3

    def _validate_weather_resistance(self, weather_resistance) -> List[str]:
        """Validate weather resistance"""
        valid_weather = ["sunny", "cloudy", "rainy", "snowy"]
        if isinstance(weather_resistance, str):
            weather_resistance = [weather_resistance]
        
        valid_list = [w for w in weather_resistance if w in valid_weather]
        return valid_list if valid_list else ["sunny", "cloudy"]

    def preprocess_image(self, image_data: bytes) -> bytes:
        """Enhanced image preprocessing"""
        try:
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Auto-orient
            image = ImageOps.exif_transpose(image)
            
            # Resize for optimal analysis
            max_size = 1024
            if max(image.size) > max_size:
                ratio = max_size / max(image.size)
                new_size = tuple(int(dim * ratio) for dim in image.size)
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            # Enhance contrast slightly
            from PIL import ImageEnhance
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.1)
            
            # Save processed image
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=95)
            return output.getvalue()
            
        except Exception as e:
            print(f"Error preprocessing image: {e}")
            return image_data

    def _get_smart_fallback_analysis(self) -> Dict:
        """Improved fallback analysis"""
        return {
            "name": "Unidentified Item",
            "type": "top",  # Safe default
            "color": "unknown",
            "fitting": "regular",
            "style": "casual",
            "warmth_level": 3,
            "weather_resistance": ["sunny", "cloudy"],
            "material_analysis": "Could not analyze automatically",
            "style_reasoning": "Fallback classification",
            "ai_confidence": 0.3
        }

    def create_clothing_item(self, analysis_result: Dict, item_id: str) -> ClothingItem:
        """Convert analysis result to ClothingItem object"""
        
        return ClothingItem(
            id=item_id,
            name=analysis_result["name"],
            type=ClothingType(analysis_result["type"]),
            fitting=Fitting(analysis_result["fitting"]),
            style=Style(analysis_result["style"]),
            color=analysis_result["color"],
            warmth_level=analysis_result["warmth_level"],
            weather_resistance=[WeatherCondition(w) for w in analysis_result["weather_resistance"]],
            image_path="",
            tags=["ai_analyzed"]
        )

    def batch_analyze_images(self, image_list: List[bytes], user_context: Dict = None) -> List[Dict]:
        """Analyze multiple images with improved accuracy tracking"""
        results = []
        
        for i, image_data in enumerate(image_list):
            print(f"🤖 Analyzing image {i+1} of {len(image_list)}...")
            try:
                analysis = self.analyze_clothing_image(image_data, user_context)
                analysis["batch_index"] = i
                
                # Log results for debugging
                print(f"   📊 Result: {analysis['name']} | Type: {analysis['type']} | Color: {analysis['color']}")
                
                results.append(analysis)
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                fallback = self._get_smart_fallback_analysis()
                fallback["batch_index"] = i
                results.append(fallback)
        
        return results


# Keep the existing AIOutfitGenerator class unchanged
class AIOutfitGenerator:
    """Enhanced outfit generator using AI analysis"""
    
    def __init__(self, openai_api_key: str):
        self.client = openai.OpenAI(api_key=openai_api_key)
    
    def generate_smart_outfit(self, wardrobe: List[ClothingItem], weather_data: Dict, 
                            user_preferences: Dict) -> Dict:
        """Generate outfit using enhanced AI reasoning"""
        
        # Pre-filter wardrobe for efficiency
        suitable_items = self._pre_filter_wardrobe(wardrobe, weather_data)
        
        if len(suitable_items) < 3:
            return self._fallback_outfit_generation(wardrobe, weather_data)
        
        # Create enhanced context for AI
        wardrobe_context = self._create_detailed_wardrobe_context(suitable_items)
        weather_context = self._create_weather_context(weather_data)
        preference_context = self._create_preference_context(user_preferences)
        
        prompt = f"""
You are a professional fashion stylist. Create a weather-appropriate outfit.

WEATHER CONDITIONS:
{weather_context}

USER PREFERENCES:
{preference_context}

SUITABLE WARDROBE ITEMS:
{wardrobe_context}

Create a JSON response:
{{
    "outfit": {{
        "top": "item_id or null",
        "bottom": "item_id or null", 
        "outerwear": "item_id or null",
        "shoes": "item_id or null",
        "accessory": "item_id or null"
    }},
    "reasoning": "Detailed explanation of choices and weather appropriateness",
    "style_score": "1-10 rating based on style coordination",
    "weather_appropriateness": "1-10 rating for weather suitability",
    "recommendations": ["specific styling tips"]
}}

REQUIREMENTS:
- Select items with appropriate warmth levels for {weather_data.get('temperature', 20)}°C
- Ensure weather resistance matches conditions
- Coordinate colors and styles
- Only use item IDs from the wardrobe list
- Prioritize user's preferred styles: {user_preferences.get('preferred_styles', [])}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert fashion stylist with deep knowledge of weather-appropriate dressing and style coordination."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.2
            )
            
            ai_response = response.choices[0].message.content
            return self._parse_outfit_response(ai_response, suitable_items)
            
        except Exception as e:
            print(f"❌ Error generating AI outfit: {e}")
            return self._fallback_outfit_generation(suitable_items, weather_data)
    
    def _pre_filter_wardrobe(self, wardrobe: List[ClothingItem], weather_data: Dict) -> List[ClothingItem]:
        """Pre-filter wardrobe based on weather conditions"""
        temperature = weather_data.get('temperature', 20)
        condition = weather_data.get('condition', 'sunny').lower()
        
        suitable_items = []
        
        for item in wardrobe:
            # Temperature filtering
            if temperature < 10:  # Cold weather
                if item.warmth_level >= 3:
                    suitable_items.append(item)
            elif temperature > 25:  # Hot weather
                if item.warmth_level <= 3:
                    suitable_items.append(item)
            else:  # Moderate weather
                suitable_items.append(item)
            
            # Weather condition filtering
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
            if required_condition in item.weather_resistance:
                if item not in suitable_items:
                    suitable_items.append(item)
        
        return suitable_items
    
    def _create_detailed_wardrobe_context(self, wardrobe: List[ClothingItem]) -> str:
        """Create detailed wardrobe description for AI"""
        context = []
        
        # Group by type for better organization
        items_by_type = {}
        for item in wardrobe:
            if item.type not in items_by_type:
                items_by_type[item.type] = []
            items_by_type[item.type].append(item)
        
        for clothing_type, items in items_by_type.items():
            context.append(f"\n{clothing_type.value.upper()}S:")
            for item in items:
                weather_res = [w.value for w in item.weather_resistance]
                context.append(
                    f"  - ID: {item.id} | {item.name} | Color: {item.color} | "
                    f"Style: {item.style.value} | Warmth: {item.warmth_level}/5 | "
                    f"Weather: {weather_res} | Fit: {item.fitting.value}"
                )
        
        return "\n".join(context)
    
    def _create_weather_context(self, weather_data: Dict) -> str:
        """Create detailed weather description"""
        return f"""
Temperature: {weather_data.get('temperature', 20)}°C
Feels like: {weather_data.get('feels_like', 20)}°C
Condition: {weather_data.get('condition', 'unknown')}
Humidity: {weather_data.get('humidity', 50)}%
Wind: {weather_data.get('wind_speed', 0)} km/h
"""
    
    def _create_preference_context(self, preferences: Dict) -> str:
        """Create user preference description"""
        return f"""
Preferred styles: {preferences.get('preferred_styles', ['casual'])}
Avatar type: {preferences.get('selected_avatar', 'unknown')}
"""
    
    def _parse_outfit_response(self, ai_response: str, wardrobe: List[ClothingItem]) -> Dict:
        """Parse AI outfit response with better error handling"""
        try:
            # Clean response
            clean_response = ai_response.strip()
            if clean_response.startswith('```json'):
                clean_response = clean_response[7:]
            if clean_response.endswith('```'):
                clean_response = clean_response[:-3]
            
            json_start = clean_response.find('{')
            json_end = clean_response.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                json_str = clean_response[json_start:json_end]
                parsed_data = json.loads(json_str)
                
                # Validate item IDs exist in wardrobe
                wardrobe_ids = {item.id for item in wardrobe}
                outfit = parsed_data.get("outfit", {})
                
                for category, item_id in outfit.items():
                    if item_id and item_id not in wardrobe_ids:
                        print(f"⚠️ Invalid item ID {item_id} for {category}")
                        outfit[category] = None
                
                return {
                    "outfit": outfit,
                    "reasoning": parsed_data.get("reasoning", "AI-generated outfit based on weather and style preferences"),
                    "style_score": max(1, min(10, parsed_data.get("style_score", 7))),
                    "weather_appropriateness": max(1, min(10, parsed_data.get("weather_appropriateness", 7))),
                    "recommendations": parsed_data.get("recommendations", [])
                }
                
        except Exception as e:
            print(f"❌ Error parsing outfit response: {e}")
        
        return self._fallback_outfit_generation(wardrobe, {})
    
    def _fallback_outfit_generation(self, wardrobe: List[ClothingItem], weather_data: Dict) -> Dict:
        """Enhanced fallback outfit generation"""
        outfit = {}
        
        # Group items by type
        items_by_type = {}
        for item in wardrobe:
            if item.type not in items_by_type:
                items_by_type[item.type] = []
            items_by_type[item.type].append(item)
        
        # Smart selection based on weather
        temperature = weather_data.get('temperature', 20)
        
        # Select essentials first
        for clothing_type in [ClothingType.TOP, ClothingType.BOTTOM, ClothingType.SHOES]:
            if clothing_type in items_by_type:
                # Filter by temperature appropriateness
                suitable_items = []
                for item in items_by_type[clothing_type]:
                    if temperature < 15 and item.warmth_level >= 2:
                        suitable_items.append(item)
                    elif temperature > 25 and item.warmth_level <= 3:
                        suitable_items.append(item)
                    elif 15 <= temperature <= 25:
                        suitable_items.append(item)
                
                if suitable_items:
                    outfit[clothing_type.value] = suitable_items[0].id
                elif items_by_type[clothing_type]:
                    outfit[clothing_type.value] = items_by_type[clothing_type][0].id
        
        # Add outerwear if cold
        if temperature < 18 and ClothingType.OUTERWEAR in items_by_type:
            warm_outerwear = [item for item in items_by_type[ClothingType.OUTERWEAR] if item.warmth_level >= 3]
            if warm_outerwear:
                outfit[ClothingType.OUTERWEAR.value] = warm_outerwear[0].id
            else:
                outfit[ClothingType.OUTERWEAR.value] = items_by_type[ClothingType.OUTERWEAR][0].id
        
        return {
            "outfit": outfit,
            "reasoning": f"Basic weather-appropriate outfit for {temperature}°C conditions",
            "style_score": 6,
            "weather_appropriateness": 7,
            "recommendations": ["This is a basic outfit recommendation. Add more items to your wardrobe for better suggestions!"]
        }