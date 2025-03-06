from PIL import Image, ImageDraw
import os

def create_placeholder_image():
    """Create a placeholder image for researchers without profile pictures"""
    # Create a directory for images if it doesn't exist
    os.makedirs('images', exist_ok=True)
    
    # Create a 200x200 image with a blue background
    img = Image.new('RGB', (200, 200), color=(74, 111, 165))
    draw = ImageDraw.Draw(img)
    
    # Draw a circle in the center
    center = (100, 100)
    radius = 70
    draw.ellipse((center[0] - radius, center[1] - radius, 
                  center[0] + radius, center[1] + radius), 
                 fill=(255, 255, 255))
    
    # Draw a silhouette
    draw.ellipse((center[0] - 30, center[1] - 50, 
                  center[0] + 30, center[1] + 10), 
                 fill=(200, 200, 200))
    draw.rectangle((center[0] - 50, center[1] + 10, 
                   center[0] + 50, center[1] + 80), 
                  fill=(200, 200, 200))
    
    # Save the image
    img.save('images/placeholder.jpg')
    print("Created placeholder image at images/placeholder.jpg")

if __name__ == "__main__":
    create_placeholder_image() 