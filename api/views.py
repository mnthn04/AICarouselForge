"""
Canva Carousel Generator - AI-Powered Slide Creation
Uses OpenAI APIs (GPT-3.5/4 + DALL-E 3)
"""

import json
import openai
import requests
from PIL import Image
import os
import uuid
import re
import traceback
from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import CarouselProject, Slide

# Initialize OpenAI client
client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

# ==================== VIEWS ====================

def index(request):
    """Home page - Canva Carousel Generator"""
    return render(request, 'api/index.html')

def editor(request, project_id=None):
    """Canva-style Visual Editor"""
    try:
        if project_id:
            project = CarouselProject.objects.get(id=project_id)
            slides = Slide.objects.filter(project=project).order_by('slide_number')
            
            if not slides.exists():
                return render(request, 'api/editor.html', {
                    'project_id': project_id,
                    'error': 'No slides found. Please generate a carousel first.'
                })
            
            # Prepare slide data with image URLs
            slides_data = []
            for slide in slides:
                slide_dict = {
                    'id': slide.id,
                    'slide_number': slide.slide_number,
                    'title': slide.title,
                    'description': slide.description,
                    'image_prompt': slide.image_prompt,
                    'background_color': slide.background_color,
                    'font_color': slide.font_color,
                    'generated_image': slide.generated_image
                }
                
                # Add full image URL if exists
                if slide.generated_image:
                    slide_dict['generated_image_url'] = f"{settings.MEDIA_URL}{slide.generated_image}"
                
                slides_data.append(slide_dict)
            
            return render(request, 'api/editor.html', {
                'project_id': project_id,
                'slides': slides_data
            })
        else:
            return render(request, 'api/editor.html', {
                'error': 'No project ID provided'
            })
    except CarouselProject.DoesNotExist:
        return render(request, 'api/index.html', {
            'error': 'Project not found. Please generate a new carousel.'
        })

def result(request, project_id):
    """Result page"""
    try:
        project = CarouselProject.objects.get(id=project_id)
        slides = Slide.objects.filter(project=project).order_by('slide_number')
        
        # Prepare slides with image URLs
        slides_data = []
        for slide in slides:
            slide_dict = {
                'id': slide.id,
                'slide_number': slide.slide_number,
                'title': slide.title,
                'description': slide.description,
                'background_color': slide.background_color,
                'font_color': slide.font_color,
                'generated_image': slide.generated_image
            }
            
            if slide.generated_image:
                slide_dict['generated_image_url'] = f"{settings.MEDIA_URL}{slide.generated_image}"
            
            slides_data.append(slide_dict)
        
        return render(request, 'api/result.html', {
            'project_id': project_id,
            'slide_count': slides.count(),
            'slides': slides_data
        })
    except CarouselProject.DoesNotExist:
        return render(request, 'api/index.html')

# ==================== UTILITY FUNCTIONS ====================

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
        return '#405DE6'  # Default Instagram blue

def create_default_slides(topic, slide_count, platform, style):
    """Create default slides when OpenAI fails"""
    print(f"🔄 Creating default slides for {topic}")
    
    # Color palettes for different platforms
    color_palettes = {
        'instagram': [
            ('#405DE6', '#FFFFFF'),  # Instagram blue
            ('#8A2BE2', '#FFFFFF'),  # Blue violet  
            ('#FF6B6B', '#FFFFFF'),  # Coral red
            ('#4ECDC4', '#000000'),  # Turquoise
            ('#FFD166', '#000000'),  # Yellow
        ],
        'linkedin': [
            ('#0A66C2', '#FFFFFF'),  # LinkedIn blue
            ('#333333', '#FFFFFF'),  # Dark gray
            ('#666666', '#FFFFFF'),  # Medium gray
            ('#999999', '#000000'),  # Light gray
            ('#CCCCCC', '#000000'),  # Very light gray
        ],
        'twitter': [
            ('#1DA1F2', '#FFFFFF'),  # Twitter blue
            ('#14171A', '#FFFFFF'),  # Dark
            ('#657786', '#FFFFFF'),  # Gray
            ('#AAB8C2', '#000000'),  # Light gray
            ('#E1E8ED', '#000000'),  # Very light gray
        ],
        'presentation': [
            ('#2E86AB', '#FFFFFF'),  # Professional blue
            ('#A23B72', '#FFFFFF'),  # Purple
            ('#F18F01', '#000000'),  # Orange
            ('#C73E1D', '#FFFFFF'),  # Red
            ('#6BAA75', '#000000'),  # Green
        ]
    }
    
    # Get color palette for platform
    colors = color_palettes.get(platform, color_palettes['instagram'])
    
    # Slide templates
    templates = [
        {
            'title': f"Introduction to {topic}",
            'description': f"Learn the fundamentals of {topic} and why it matters in today's world.",
            'suffix': "introduction slide"
        },
        {
            'title': f"Key Principles of {topic}",
            'description': f"Discover the core principles that drive success in {topic}.",
            'suffix': "key principles slide"
        },
        {
            'title': f"Practical Strategies for {topic}",
            'description': f"Implement effective strategies to achieve your goals in {topic}.",
            'suffix': "strategies slide"
        },
        {
            'title': f"Action Steps for {topic} Success",
            'description': f"Follow these actionable steps to excel in {topic}.",
            'suffix': "action steps slide"
        },
        {
            'title': f"Advanced Techniques in {topic}",
            'description': f"Master advanced techniques to take your {topic} skills to the next level.",
            'suffix': "advanced techniques slide"
        },
        {
            'title': f"{topic} Best Practices",
            'description': f"Learn industry best practices and avoid common mistakes in {topic}.",
            'suffix': "best practices slide"
        },
        {
            'title': f"Future Trends in {topic}",
            'description': f"Explore emerging trends and future opportunities in {topic}.",
            'suffix': "future trends slide"
        },
        {
            'title': f"Your {topic} Success Plan",
            'description': f"Create a personalized plan to achieve success in {topic}.",
            'suffix': "success plan slide"
        }
    ]
    
    # Generate slides
    slides = []
    for i in range(min(slide_count, len(templates))):
        color_idx = i % len(colors)
        bg_color, font_color = colors[color_idx]
        
        template = templates[i]
        
        slides.append({
            'title': template['title'],
            'description': template['description'],
            'image_prompt': f"Canva {platform} template, {style} style, {template['suffix']}, professional design",
            'background_color': bg_color,
            'font_color': font_color
        })
    
    return slides

def create_fallback_slide(topic, slide_number, platform, style):
    """Create a single fallback slide"""
    color_palette = [
        ('#405DE6', '#FFFFFF'),  # Instagram blue
        ('#8A2BE2', '#FFFFFF'),  # Blue violet
        ('#00BFFF', '#000000'),  # Deep sky blue
        ('#FF6B6B', '#FFFFFF'),  # Coral red
        ('#4ECDC4', '#000000'),  # Turquoise
        ('#FFD166', '#000000'),  # Yellow
        ('#06D6A0', '#000000'),  # Emerald
        ('#EF476F', '#FFFFFF'),  # Pink
        ('#118AB2', '#FFFFFF'),  # Blue
        ('#073B4C', '#FFFFFF')   # Navy
    ]
    
    color_idx = (slide_number - 1) % len(color_palette)
    bg_color, font_color = color_palette[color_idx]
    
    titles = [
        f"Introduction to {topic}",
        f"Key Principles of {topic}",
        f"Strategies for {topic} Success",
        f"Practical {topic} Techniques",
        f"Advanced {topic} Insights",
        f"{topic} Implementation Guide",
        f"Mastering {topic} Skills",
        f"{topic} Action Plan",
        f"{topic} Best Practices",
        f"Future of {topic}"
    ]
    
    descriptions = [
        f"Learn the essential concepts and fundamentals of {topic}.",
        f"Discover the core principles that drive success in {topic}.",
        f"Implement effective strategies to achieve your {topic} goals.",
        f"Master practical techniques for excelling in {topic}.",
        f"Gain advanced insights to take your {topic} skills further.",
        f"Follow this step-by-step guide to implement {topic}.",
        f"Develop the skills needed to master {topic}.",
        f"Create a personalized plan for {topic} success.",
        f"Learn industry best practices for {topic}.",
        f"Explore future trends and opportunities in {topic}."
    ]
    
    title_idx = min(slide_number - 1, len(titles) - 1)
    desc_idx = min(slide_number - 1, len(descriptions) - 1)
    
    return {
        'title': titles[title_idx],
        'description': descriptions[desc_idx],
        'image_prompt': f"Canva {platform} template with {style} style, professional design for slide {slide_number}, {topic}",
        'background_color': bg_color,
        'font_color': font_color
    }

# ==================== CORE OPENAI FUNCTIONS ====================

@csrf_exempt
def generate_canva_carousel(request):
    """
    Generate complete Canva-style carousel
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            topic = data.get('topic', '').strip()
            platform = data.get('platform', 'instagram')
            style = data.get('style', 'modern')
            slide_count = int(data.get('slide_count', 5))
            profile_image_base64 = data.get('profile_image')
            brand_logo_base64 = data.get('brand_logo')
            profile_handle = data.get('profile_handle', '').strip()
            
            if not topic:
                return JsonResponse({'error': 'Topic is required'}, status=400)
            
            print(f"\n🎨 GENERATING CANVA CAROUSEL")
            print(f"📌 Topic: {topic}")
            print(f"📱 Platform: {platform}")
            print(f"✨ Style: {style}")
            print(f"📊 Slides: {slide_count}")
            
            # Create project
            project = CarouselProject.objects.create(
                topic=topic,
                platform=platform,
                style=style,
                slide_count=slide_count,
                profile_handle=profile_handle
            )
            
            # Save branding images if provided
            if profile_image_base64:
                try:
                    import base64
                    from django.core.files.base import ContentFile
                    
                    header, data = profile_image_base64.split(',')
                    file_content = ContentFile(base64.b64decode(data))
                    project.profile_image.save(f'profile_{project.id}.png', file_content)
                    print(f"✅ Profile image saved")
                except Exception as e:
                    print(f"⚠️ Error saving profile image: {e}")
            
            if brand_logo_base64:
                try:
                    import base64
                    from django.core.files.base import ContentFile
                    
                    header, data = brand_logo_base64.split(',')
                    file_content = ContentFile(base64.b64decode(data))
                    project.brand_logo.save(f'logo_{project.id}.png', file_content)
                    print(f"✅ Brand logo saved")
                except Exception as e:
                    print(f"⚠️ Error saving brand logo: {e}")
            
            # Step 1: Generate slide content
            print(f"\n🤖 STEP 1: Generating slide content...")
            slides_content = generate_canva_slides_content(topic, slide_count, platform, style)
            
            # Step 2: Create slides and generate images
            print(f"\n🎨 STEP 2: Creating slides and generating images...")
            slides_data = []
            generated_images_count = 0
            
            for i, content in enumerate(slides_content):
                # Create the slide with content
                slide = Slide.objects.create(
                    project=project,
                    slide_number=i + 1,
                    title=content['title'],
                    description=content['description'],
                    image_prompt=content['image_prompt'],
                    background_color=content['background_color'],
                    font_color=content['font_color']
                )
                
                # Generate Canva-style image for this slide
                print(f"\n🖼️ Generating image for Slide {i+1}...")
                try:
                    image_filename = generate_canva_image(
                        content['image_prompt'],
                        platform,
                        style,
                        slide.id,
                        bg_color=slide.background_color,
                        profile_image_path=project.profile_image.path if project.profile_image else None,
                        brand_logo_path=project.brand_logo.path if project.brand_logo else None
                    )
                    
                    if image_filename:
                        slide.generated_image = image_filename
                        slide.save()
                        generated_images_count += 1
                        print(f"✅ Image generated for Slide {i+1}")
                    else:
                        print(f"⚠️ Image generation failed for Slide {i+1}")
                        
                except Exception as img_error:
                    print(f"❌ Image generation error: {img_error}")
                
                # Prepare response data
                slide_data = {
                    'id': slide.id,
                    'slide_number': slide.slide_number,
                    'title': slide.title,
                    'description': slide.description,
                    'image_prompt': slide.image_prompt,
                    'background_color': slide.background_color,
                    'font_color': slide.font_color,
                    'generated_image': slide.generated_image
                }
                
                if slide.generated_image:
                    slide_data['generated_image_url'] = f"{settings.MEDIA_URL}{slide.generated_image}"
                
                slides_data.append(slide_data)
                print(f"✅ Slide {i+1}: {slide.title[:40]}...")
            
            print(f"\n🎉 CAROUSEL GENERATION COMPLETE!")
            print(f"✅ Created {len(slides_data)} slides")
            print(f"✅ Generated {generated_images_count} images")
            
            return JsonResponse({
                'success': True,
                'project_id': project.id,
                'slides': slides_data,
                'message': f'Canva carousel with {len(slides_data)} slides generated successfully!'
            })
            
        except Exception as e:
            print(f"❌ Error generating carousel: {str(e)}")
            traceback.print_exc()
            return JsonResponse({
                'error': f'Failed to generate carousel: {str(e)}',
                'details': 'Please check your OpenAI API key and try again.'
            }, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

def generate_canva_slides_content(topic, slide_count, platform, style):
    """
    Generate Canva-style slide content using OpenAI API
    """
    print(f"📝 Generating {slide_count} Canva slides...")
    
    try:
        # Use gpt-4.0-mini for reliability
        prompt = f"""Create {slide_count} slides for a carousel about "{topic}".

Platform: {platform}
Style: {style}

Return ONLY a JSON array with exactly {slide_count} objects. Each object must have:
- title: Engaging title (5-8 words)
- description: Informative description (1-2 sentences)
- image_prompt: Description for Canva background image
- background_color: Hex color code (e.g., "#405DE6")
- font_color: Hex color code (e.g., "#FFFFFF")

Make it professional and suitable for {platform} with {style} design."""
        
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system", 
                    "content": f"You are a professional Canva designer. Return ONLY a valid JSON array. No explanations."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        content = response.choices[0].message.content.strip()
        print(f"✅ Response received ({len(content)} chars)")
        
        # Clean the response
        content = content.strip()
        if content.startswith('```json'):
            content = content[7:]
        elif content.startswith('```'):
            content = content[3:]
        if content.endswith('```'):
            content = content[:-3]
        content = content.strip()
        
        # Parse JSON
        try:
            parsed = json.loads(content)
            
            slides_data = []
            if isinstance(parsed, list):
                slides_data = parsed
            elif isinstance(parsed, dict):
                # Look for slides in common keys
                for key in ['slides', 'content', 'data', 'carousel']:
                    if key in parsed and isinstance(parsed[key], list):
                        slides_data = parsed[key]
                        break
                
                # If dict has required keys, treat as one slide
                if not slides_data:
                    required_keys = ['title', 'description', 'image_prompt', 'background_color', 'font_color']
                    if all(key in parsed for key in required_keys):
                        slides_data = [parsed]
            
            # Validate and format slides
            validated_slides = []
            for i, slide in enumerate(slides_data[:slide_count]):
                try:
                    validated_slide = {
                        'title': str(slide.get('title', f"{topic} - Part {i+1}")).strip(),
                        'description': str(slide.get('description', f"Learn about {topic}.")).strip(),
                        'image_prompt': str(slide.get('image_prompt', 
                            f"Canva {platform} template with {style} style")).strip(),
                        'background_color': validate_hex_color(slide.get('background_color', '#405DE6')),
                        'font_color': validate_hex_color(slide.get('font_color', '#FFFFFF'))
                    }
                    validated_slides.append(validated_slide)
                except Exception as slide_error:
                    print(f"⚠️ Error processing slide {i+1}: {slide_error}")
                    validated_slides.append(create_fallback_slide(topic, i+1, platform, style))
            
            # Ensure we have requested number of slides
            while len(validated_slides) < slide_count:
                i = len(validated_slides)
                validated_slides.append(create_fallback_slide(topic, i+1, platform, style))
            
            print(f"✅ Generated {len(validated_slides)} slides")
            return validated_slides
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
            print(f"📄 Raw content: {content[:200]}...")
            return create_default_slides(topic, slide_count, platform, style)
            
    except Exception as e:
        print(f"❌ OpenAI API error: {str(e)}")
        return create_default_slides(topic, slide_count, platform, style)

def generate_canva_image(prompt, platform, style, slide_id, bg_color=None, profile_image_path=None, brand_logo_path=None, profile_handle=None):
    """
    Generate Canva-style background image using DALL-E 3
    """
    print(f"🎨 Generating Canva image: {prompt[:50]}...")
    
    # Create enhanced prompt for DALL-E
    canva_prompt = f"""Create a MINIMAL, CLEAN Canva template background for a {platform} carousel slide.

Theme: {prompt}
Platform: {platform}
Style: {style}

CRITICAL DESIGN REQUIREMENTS:
- MINIMAL and CLEAN design with lots of whitespace
- Keep 60% of the image as EMPTY SPACE for text overlay
- Simple, subtle gradient background (soft transitions)
- Small decorative elements only (abstract shapes, simple icons at edges)
- NO busy patterns, NO cluttered details, NO photo-heavy content
- Professional, modern, professional look
- Looks like premium Canva template (simple and elegant)
- Text-friendly: center area completely clear for readable text
- Use soft colors, gradients, or simple abstract geometric shapes
- Minimize details to ensure text is always readable"""
    
    try:
        response = client.images.generate(
            model="gpt-image-1",
            prompt=canva_prompt[:4000],
            size="1024x1024",
            quality="auto",
            n=1
        )
        
        # The image API may return either a URL or base64 data depending on model/version.
        image_entry = response.data[0]
        image_url = None
        image_b64 = None
        try:
            # Try dict-like access first
            if isinstance(image_entry, dict):
                image_url = image_entry.get('url')
                image_b64 = image_entry.get('b64_json') or image_entry.get('b64')
            else:
                # Object with attributes
                image_url = getattr(image_entry, 'url', None)
                image_b64 = getattr(image_entry, 'b64_json', None) or getattr(image_entry, 'b64', None)
        except Exception:
            image_url = None
            image_b64 = None

        # Generate filename and path
        filename = f"canva_slide_{slide_id}_{uuid.uuid4().hex[:8]}.png"
        filepath = os.path.join(settings.MEDIA_ROOT, filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        if image_url:
            print(f"✅ DALL-E image generated (URL)")
            # Download image
            img_response = requests.get(image_url, timeout=30)
            img_response.raise_for_status()
            with open(filepath, 'wb') as f:
                f.write(img_response.content)
        elif image_b64:
            print(f"✅ DALL-E image generated (base64)")
            import base64
            try:
                image_bytes = base64.b64decode(image_b64)
                with open(filepath, 'wb') as f:
                    f.write(image_bytes)
            except Exception as e:
                print(f"❌ Error decoding base64 image: {e}")
                return None
        else:
            print(f"❌ Error: image response did not contain URL or base64 data: {response}")
            return None

        # If a background color was requested, composite/tint the image
        try:
            if bg_color:
                # Normalize color
                bg_color = str(bg_color).strip()
                if not bg_color.startswith('#'):
                    bg_color = '#' + bg_color
                # Open saved image
                img = Image.open(filepath).convert('RGBA')

                # Convert hex to RGB tuple
                try:
                    r = int(bg_color[1:3], 16)
                    g = int(bg_color[3:5], 16)
                    b = int(bg_color[5:7], 16)
                except Exception:
                    r, g, b = (255, 255, 255)

                bg = Image.new('RGBA', img.size, (r, g, b, 255))

                # Detect transparency
                has_transparency = False
                try:
                    a_extrema = img.getchannel('A').getextrema()
                    if a_extrema and a_extrema[0] < 255:
                        has_transparency = True
                except Exception:
                    has_transparency = False

                if has_transparency:
                    # If transparent areas exist, place image over solid background
                    result = Image.alpha_composite(bg, img)
                else:
                    # Otherwise, gently blend the background color to tint the image
                    result = Image.blend(img, bg, alpha=0.15)

                # Save composited image (overwrite)
                result.convert('RGBA').save(filepath, format='PNG')

        except Exception as proc_err:
            print(f"⚠️ Warning processing background color: {proc_err}")

        # Add branding elements (profile image and logo)
        try:
            if profile_image_path or brand_logo_path:
                from PIL import ImageDraw, ImageFont
                img = Image.open(filepath).convert('RGBA')
                
                # Add profile image (LEFT BOTTOM corner, small)
                if profile_image_path and os.path.exists(profile_image_path):
                    profile = Image.open(profile_image_path).convert('RGBA')
                    profile_size = 60  # Small size for bottom-left
                    profile.thumbnail((profile_size, profile_size), Image.Resampling.LANCZOS)
                    
                    # Position: bottom-left with padding
                    pos_x = 15  # Left padding
                    pos_y = img.height - profile_size - 15  # Bottom padding
                    img.paste(profile, (pos_x, pos_y), profile)
                    print(f"✅ Profile image embedded (bottom-left)")
                
                # Add brand logo (RIGHT BOTTOM corner) - Make it circular
                if brand_logo_path and os.path.exists(brand_logo_path):
                    logo = Image.open(brand_logo_path).convert('RGBA')
                    logo_size = 70  # Slightly larger for brand logo
                    logo.thumbnail((logo_size, logo_size), Image.Resampling.LANCZOS)

                    # Create circular mask
                    mask = Image.new('L', (logo_size, logo_size), 0)
                    draw = ImageDraw.Draw(mask)
                    draw.ellipse((0, 0, logo_size, logo_size), fill=255)

                    # Apply circular mask to logo
                    circular_logo = Image.new('RGBA', (logo_size, logo_size))
                    circular_logo.paste(logo, (0, 0), mask)

                    # Position: bottom-right with padding
                    pos_x = img.width - logo_size - 15  # Right padding
                    pos_y = img.height - logo_size - 15  # Bottom padding
                    img.paste(circular_logo, (pos_x, pos_y), circular_logo)
                    print(f"✅ Circular brand logo embedded (bottom-right)")
                
                # Save final image
                img.convert('RGB').save(filepath, format='PNG')
        
        except Exception as brand_err:
            print(f"⚠️ Warning adding branding: {brand_err}")

        print(f"💾 Image saved: {filename}")
        return filename
        
    except Exception as e:
        print(f"❌ Error generating image: {str(e)}")
        return None

# ==================== EDITOR FUNCTIONS ====================

@csrf_exempt
def generate_slide_image(request):
    """
    Generate and apply Canva image to specific slide
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            slide_id = data.get('slide_id')
            prompt = data.get('prompt', '').strip()
            
            if not slide_id:
                return JsonResponse({'error': 'Slide ID is required'}, status=400)
            
            if not prompt:
                return JsonResponse({'error': 'Image prompt is required'}, status=400)
            
            slide = Slide.objects.get(id=slide_id)
            project = slide.project
            
            print(f"\n🖼️ GENERATING CANVA IMAGE FOR SLIDE")
            print(f"📝 Slide: {slide.title}")
            print(f"🎨 Prompt: {prompt}")
            
            # Generate Canva image with branding
            image_filename = generate_canva_image(
                prompt,
                project.platform,
                project.style,
                slide_id,
                bg_color=slide.background_color,
                profile_image_path=project.profile_image.path if project.profile_image else None,
                brand_logo_path=project.brand_logo.path if project.brand_logo else None
            )
            
            if image_filename:
                # Update slide
                slide.generated_image = image_filename
                slide.image_prompt = prompt
                slide.save()
                
                return JsonResponse({
                    'success': True,
                    'image_url': f"{settings.MEDIA_URL}{image_filename}",
                    'filename': image_filename,
                    'slide_id': slide.id,
                    'message': 'Canva image generated and applied successfully!'
                })
            else:
                return JsonResponse({
                    'error': 'Failed to generate image'
                }, status=500)
                
        except Slide.DoesNotExist:
            return JsonResponse({'error': 'Slide not found'}, status=404)
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            traceback.print_exc()
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def regenerate_slide_content(request):
    """
    Regenerate slide content with OpenAI
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            slide_id = data.get('slide_id')
            
            if not slide_id:
                return JsonResponse({'error': 'Slide ID is required'}, status=400)
            
            slide = Slide.objects.get(id=slide_id)
            project = slide.project
            
            print(f"\n🔄 REGENERATING SLIDE CONTENT")
            print(f"📝 Slide: {slide.title}")
            
            # Generate new content for this slide
            prompt = f"""Create new content for one carousel slide about "{project.topic}" for {project.platform}.

Current slide: {slide.title} - {slide.description}

Return a JSON object with:
- title: New engaging title
- description: New informative description
- image_prompt: New prompt for Canva background
- background_color: Hex color
- font_color: Hex color

Make it fresh and suitable for {project.platform} Canva template."""
            
            response = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "Return ONLY a valid JSON object."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=500
            )
            
            content = response.choices[0].message.content.strip()
            content = re.sub(r'```json\s*', '', content)
            content = re.sub(r'```\s*', '', content).strip()
            
            new_data = json.loads(content)
            
            # Update slide
            slide.title = new_data.get('title', slide.title)
            slide.description = new_data.get('description', slide.description)
            slide.image_prompt = new_data.get('image_prompt', slide.image_prompt)
            slide.background_color = validate_hex_color(new_data.get('background_color', slide.background_color))
            slide.font_color = validate_hex_color(new_data.get('font_color', slide.font_color))
            slide.save()
            
            print(f"✅ Slide regenerated: {slide.title}")
            
            return JsonResponse({
                'success': True,
                'slide': {
                    'id': slide.id,
                    'title': slide.title,
                    'description': slide.description,
                    'image_prompt': slide.image_prompt,
                    'background_color': slide.background_color,
                    'font_color': slide.font_color,
                    'generated_image': slide.generated_image,
                    'generated_image_url': f"{settings.MEDIA_URL}{slide.generated_image}" if slide.generated_image else None
                },
                'message': 'Slide content regenerated successfully'
            })
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            traceback.print_exc()
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def update_slide(request):
    """
    Update slide content and design
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            slide_id = data.get('slide_id')
            slide_data = data.get('slide_data', {})
            
            if not slide_id:
                return JsonResponse({'error': 'Slide ID is required'}, status=400)
            
            slide = Slide.objects.get(id=slide_id)
            
            # Update fields
            if 'title' in slide_data:
                slide.title = slide_data['title']
            if 'description' in slide_data:
                slide.description = slide_data['description']
            if 'image_prompt' in slide_data:
                slide.image_prompt = slide_data['image_prompt']
            if 'background_color' in slide_data:
                slide.background_color = validate_hex_color(slide_data['background_color'])
            if 'font_color' in slide_data:
                slide.font_color = validate_hex_color(slide_data['font_color'])
            
            slide.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Slide updated successfully',
                'slide': {
                    'id': slide.id,
                    'title': slide.title,
                    'description': slide.description,
                    'image_prompt': slide.image_prompt,
                    'background_color': slide.background_color,
                    'font_color': slide.font_color
                }
            })
            
        except Slide.DoesNotExist:
            return JsonResponse({'error': 'Slide not found'}, status=404)
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def generate_all_images(request):
    """
    Generate images for all slides in a project
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            project_id = data.get('project_id')
            
            if not project_id:
                return JsonResponse({'error': 'Project ID is required'}, status=400)
            
            project = CarouselProject.objects.get(id=project_id)
            slides = Slide.objects.filter(project=project).order_by('slide_number')
            
            print(f"\n🖼️ GENERATING IMAGES FOR ALL SLIDES")
            print(f"📊 Project: {project.topic}")
            print(f"📈 Total slides: {slides.count()}")
            
            generated_count = 0
            failed_count = 0
            
            for slide in slides:
                try:
                    # Skip if already has image
                    if slide.generated_image:
                        print(f"⏩ Slide {slide.slide_number}: Already has image")
                        continue
                    
                    print(f"🎨 Generating image for Slide {slide.slide_number}...")
                    
                    image_filename = generate_canva_image(
                        slide.image_prompt,
                        project.platform,
                        project.style,
                        slide.id,
                        bg_color=slide.background_color
                    )
                    
                    if image_filename:
                        slide.generated_image = image_filename
                        slide.save()
                        generated_count += 1
                        print(f"✅ Image generated for Slide {slide.slide_number}")
                    else:
                        failed_count += 1
                        print(f"❌ Failed to generate image for Slide {slide.slide_number}")
                        
                except Exception as e:
                    failed_count += 1
                    print(f"❌ Error for Slide {slide.slide_number}: {str(e)}")
            
            return JsonResponse({
                'success': True,
                'generated': generated_count,
                'failed': failed_count,
                'total': slides.count(),
                'message': f'Generated {generated_count} images, {failed_count} failed'
            })
            
        except CarouselProject.DoesNotExist:
            return JsonResponse({'error': 'Project not found'}, status=404)
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

def get_project_slides(request, project_id):
    """Get all slides for a project"""
    try:
        project = CarouselProject.objects.get(id=project_id)
        slides = Slide.objects.filter(project=project).order_by('slide_number')
        
        slides_data = []
        for slide in slides:
            slide_dict = {
                'id': slide.id,
                'slide_number': slide.slide_number,
                'title': slide.title,
                'description': slide.description,
                'image_prompt': slide.image_prompt,
                'background_color': slide.background_color,
                'font_color': slide.font_color,
                'generated_image': slide.generated_image
            }
            
            if slide.generated_image:
                slide_dict['generated_image_url'] = f"{settings.MEDIA_URL}{slide.generated_image}"
            
            slides_data.append(slide_dict)
        
        # Include project data with profile_handle
        project_data = {
            'id': project.id,
            'profile_handle': project.profile_handle or '',
            'topic': project.topic,
            'platform': project.platform,
            'style': project.style
        }
        
        return JsonResponse({
            'success': True,
            'project_id': project.id,
            'project': project_data,
            'slides': slides_data
        })
        
    except CarouselProject.DoesNotExist:
        return JsonResponse({'error': 'Project not found'}, status=404)

@csrf_exempt
def test_openai(request):
    """Simple test of OpenAI API"""
    if request.method == 'POST':
        try:
            print("\n🧪 TESTING OPENAI CONNECTION")
            
            # Check API key
            if not settings.OPENAI_API_KEY:
                return JsonResponse({
                    'success': False,
                    'error': 'OPENAI_API_KEY not set in settings.py'
                }, status=400)
            
            print(f"📋 API Key: {settings.OPENAI_API_KEY[:10]}...")
            
            # Test GPT-3.5
            print(f"\n🤖 Testing GPT-4.1-mini...")
            response = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "user", "content": "Say 'Canva Carousel Generator is working!'"}
                ],
                max_tokens=50
            )
            
            gpt_response = response.choices[0].message.content
            print(f"✅ GPT-3.5 Test Successful!")
            print(f"📄 Response: {gpt_response}")
            
            return JsonResponse({
                'success': True,
                'gpt_response': gpt_response,
                'message': 'OpenAI API is working!'
            })
            
        except Exception as e:
            print(f"❌ Test Failed: {str(e)}")
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def debug_generate(request):
    """
    Debug endpoint to test slide generation
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            topic = data.get('topic', 'Test Topic')
            slide_count = int(data.get('slide_count', 3))
            
            print(f"\n🔧 DEBUG GENERATION")
            print(f"📌 Topic: {topic}")
            
            # Test with simple prompt
            prompt = f"Create {slide_count} slides about {topic}. Return JSON array."
            
            response = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "Return JSON array."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500
            )
            
            content = response.choices[0].message.content
            print(f"✅ Debug response received")
            
            return JsonResponse({
                'success': True,
                'raw_response': content,
                'model_used': 'gpt-4.1-mini'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
def generate_and_apply_image(request):
    """
    Generate an image from a user description and apply it to the slide.
    Request JSON: { slide_id, description }
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            slide_id = data.get('slide_id')
            description = data.get('description', '').strip()

            if not slide_id:
                return JsonResponse({'error': 'Slide ID is required'}, status=400)
            if not description:
                return JsonResponse({'error': 'Description is required'}, status=400)

            slide = Slide.objects.get(id=slide_id)
            project = slide.project

            print(f"\n🖼️ GENERATE AND APPLY IMAGE")
            print(f"📝 Slide: {slide.title}")
            print(f"🧾 Description: {description}")

            # Build a Canva-friendly prompt from user description
            prompt = f"Canva-style minimal background for: {description}. Make it clean, leave a clear center area for text, flat/vector style, subtle colors."

            image_filename = generate_canva_image(
                prompt,
                project.platform,
                project.style,
                slide.id,
                bg_color=slide.background_color,
                profile_image_path=project.profile_image.path if project.profile_image else None,
                brand_logo_path=project.brand_logo.path if project.brand_logo else None
            )

            if image_filename:
                slide.generated_image = image_filename
                slide.image_prompt = description
                slide.save()

                return JsonResponse({
                    'success': True,
                    'image_url': f"{settings.MEDIA_URL}{image_filename}",
                    'filename': image_filename,
                    'slide_id': slide.id,
                    'message': 'Image generated from description and applied to slide.'
                })
            else:
                return JsonResponse({'error': 'Failed to generate image'}, status=500)

        except Slide.DoesNotExist:
            return JsonResponse({'error': 'Slide not found'}, status=404)
        except Exception as e:
            print(f"❌ Error in generate_and_apply_image: {e}")
            traceback.print_exc()
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Method not allowed'}, status=405)