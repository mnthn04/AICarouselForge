"""
Utility functions for Canva Carousel Generator
"""
import re
import os
import uuid
import requests
from django.conf import settings
import openai

# Initialize OpenAI client
client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

def validate_hex_color(color):
    """Validate and format hex color"""
    if not color:
        return '#FFFFFF'
    
    color = str(color).strip().upper()
    
    # Add # if missing
    if not color.startswith('#'):
        color = '#' + color
    
    # Validate format
    if re.match(r'^#[0-9A-F]{6}$', color):
        return color
    elif re.match(r'^#[0-9A-F]{3}$', color):
        # Expand shorthand
        return f'#{color[1]}{color[1]}{color[2]}{color[2]}{color[3]}{color[3]}'
    else:
        return '#405DE6'

def save_image_from_url(image_url, filename_prefix="slide"):
    """Download and save image from URL"""
    try:
        # Download image
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        
        # Generate filename
        filename = f"{filename_prefix}_{uuid.uuid4().hex[:8]}.png"
        filepath = os.path.join(settings.MEDIA_ROOT, filename)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Save image
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        return filename
        
    except Exception as e:
        print(f"❌ Error saving image: {e}")
        return None

def generate_simple_slides(topic, slide_count):
    """Generate simple slides without OpenAI (fallback)"""
    slides = []
    for i in range(slide_count):
        slides.append({
            'title': f"{topic} - Part {i+1}",
            'description': f"Learn about {topic} in this comprehensive guide.",
            'image_prompt': f"Canva template background for {topic}",
            'background_color': '#405DE6',
            'font_color': '#FFFFFF'
        })
    return slides

def check_openai_connection():
    """Check if OpenAI API is working"""
    try:
        client.models.list()
        return True
    except:
        return False

def get_color_palette(platform):
    """Get color palette for specific platform"""
    palettes = {
        'instagram': ['#405DE6', '#8A2BE2', '#FF6B6B', '#4ECDC4', '#FFD166'],
        'linkedin': ['#0A66C2', '#333333', '#666666', '#999999', '#CCCCCC'],
        'twitter': ['#1DA1F2', '#14171A', '#657786', '#AAB8C2', '#E1E8ED'],
        'presentation': ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#6BAA75']
    }
    return palettes.get(platform, palettes['instagram'])

def create_slide_image_url(filename):
    """Create full URL for slide image"""
    if not filename:
        return None
    return f"{settings.MEDIA_URL}{filename}"