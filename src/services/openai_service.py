import base64
import logging
from openai import OpenAI
from typing import Optional, Dict, Any

from ..utils.config import config

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
    
    def analyze_food_image(self, image_data: bytes) -> Optional[Dict[str, Any]]:
        """Analyze an image to detect food items using OpenAI Vision"""
        try:
            # Encode image to base64
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            # Create the vision API request
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Analyze this image and identify any food items. If no food is detected, respond with 'NO_FOOD'. If food is detected, provide the name of the main food item(s) in a concise format."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=150
            )
            
            food_description = response.choices[0].message.content.strip()
            
            if food_description.upper() == "NO_FOOD":
                logger.info("No food detected in image")
                return None
            
            logger.info(f"Food detected: {food_description}")
            return {
                "food_name": food_description,
                "detected": True
            }
            
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            return None
    
    def generate_recipe(self, food_name: str) -> Optional[str]:
        """Generate a recipe based on the food name"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful cooking assistant. Provide concise, practical recipes."
                    },
                    {
                        "role": "user",
                        "content": f"Create a simple recipe for {food_name}. Include ingredients and brief steps. Keep it under 200 words."
                    }
                ],
                max_tokens=300
            )
            
            recipe = response.choices[0].message.content.strip()
            logger.info(f"Generated recipe for {food_name}")
            return recipe
            
        except Exception as e:
            logger.error(f"Error generating recipe: {e}")
            return None
    
    def analyze_and_generate_recipe(self, image_data: bytes) -> Optional[Dict[str, Any]]:
        """Analyze image and generate recipe if food is detected"""
        # First, analyze the image
        food_info = self.analyze_food_image(image_data)
        
        if not food_info:
            return None
        
        # Generate recipe for detected food
        recipe = self.generate_recipe(food_info['food_name'])
        
        if recipe:
            food_info['recipe'] = recipe
        
        return food_info