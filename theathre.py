import os
import requests
import base64
import time
import dotenv
from PIL import Image
import io
import glob
# concurrent.futures removed as we're processing sequentially
import random

# Load environment variables
dotenv.load_dotenv(".env", override=True)

def image_to_base64(image_path):
    """
    Convert an image file to base64 string
    """
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    except Exception as e:
        print(f"Error converting image to base64: {e}")
        return None

def generate_stylized_image(prompt, input_image_path):
    """
    Generate a stylized image based on text prompt and input image
    
    Args:
        prompt (str): Text description for the image generation
        input_image_path (str): Path to the input image file
        
    Returns:
        str: URL of the generated image or None if failed
    """
    image_filename = os.path.basename(input_image_path)
    
    try:
        # Convert input image to base64
        input_image_base64 = image_to_base64(input_image_path)
        if not input_image_base64:
            print(f"Failed to process input image: {image_filename}")
            return None

        # Make API request to generate stylized image
        request = requests.post(
                'https://api.bfl.ai/v1/flux-kontext-pro',
                headers={
                    'accept': 'application/json',
                    'x-key': os.environ.get("BFL_HACKIN_API_KEY"),
                    'Content-Type': 'application/json',
                },
                json={
                    'prompt': prompt,
                    'input_image': input_image_base64,
                    'quality': 'high',
                    'seed': 1,
                },
                timeout=30  # Add timeout to avoid hanging requests
            ).json()

        print(f"{image_filename} - Request: {request}")
        
        # Get the request ID from the response
        request_id = request.get("id")
        if not request_id:
            print(f"Error: No id in response for {image_filename}")
            return None
                
        # Wait for the image to be generated
        poll_count = 0
        max_polls = 20  # Avoid infinite polling
        
        while poll_count < max_polls:
            time.sleep(1.5)
            # Use the exact URL from the example that worked
            result = requests.get(
                    f'https://api.bfl.ai/v1/get_result',
                    headers={
                        'accept': 'application/json',
                        'x-key': os.environ.get("BFL_API_KEY"),
                    },
                    params={'id': request_id},
                    timeout=30  # Add timeout to avoid hanging requests
                ).json()
                
            status = result.get("status")
            print(f"{image_filename} - Status: {status}")

            if status == "Ready":
                image_url = result.get('result', {}).get('sample')
                if image_url:
                    print(f"{image_filename} - Success: {image_url}")
                    return image_url
                else:
                    print(f"{image_filename} - Error: No image URL in result")
                    break
                    
            elif status not in ["Processing", "Queued", "Pending"]: 
                print(f"{image_filename} - Error: {result}")
                break
                
            poll_count += 1
            
    except Exception as e:
        print(f"{image_filename} - Exception: {str(e)}")
    
    print(f"Failed to generate image for {image_filename}")
    return None

def save_image_from_url(url, filename, output_dir="output"):
    """Download and save an image from a URL"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    response = requests.get(url)
    if response.status_code == 200:
        output_path = os.path.join(output_dir, filename)
        with open(output_path, "wb") as f:
            f.write(response.content)
        print(f"Image saved as {output_path}")
        return True
    else:
        print(f"Failed to download image: {response.status_code}")
        return False

def process_image(input_image_path, prompt, output_dir):
    """Process a single image and save the result"""
    image_filename = os.path.basename(input_image_path)
    print(f"Processing image: {image_filename}")
    
    result_url = generate_stylized_image(prompt, input_image_path)
    
    if result_url:
        # Save the image with original filename plus timestamp
        base_name, ext = os.path.splitext(image_filename)
        timestamp = int(time.time())
        output_filename = f"{base_name}_stylized_{timestamp}{ext}"
        success = save_image_from_url(result_url, output_filename, output_dir)
        return success
    else:
        print(f"Failed to generate stylized image for {image_filename}")
        return False


if __name__ == "__main__":
    # Create input and output directories if they don't exist
    input_dir = "input_theatre"
    output_dir = "output_theatre"
    # Sequential processing - no workers needed
    
    if not os.path.exists(input_dir):
        os.makedirs(input_dir)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    #Lastly, change it to a 3D cartoon model look

    # Define the prompt to use for all images
    prompt = '''
    - Replace any glowing or abstract stage backdrops with a dark red velvet curtain hex code: #770F0F.
    - Remove all textures and make the image flat
    - All surfaces and textures should be flat
    - Remove all light fixtures adn light sources
    - 3D toy model look without any textures

    Preserve:
    - Camera angle
    - Architecture
    - Balcony structure
    - Floor and walls
    '''
    
    # Get all image files from the input directory
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']
    input_images = []
    
    for ext in image_extensions:
        input_images.extend(glob.glob(os.path.join(input_dir, f'*{ext}')))
        input_images.extend(glob.glob(os.path.join(input_dir, f'*{ext.upper()}')))
    
    if not input_images:
        print(f"No images found in {input_dir}. Please add some images and run again.")
    else:
        print(f"Found {len(input_images)} images in {input_dir}")
        print(f"Using prompt: {prompt}")
        print("Processing images sequentially")
        
        # Process images sequentially
        results = {}
        for img_path in input_images:
            img_name = os.path.basename(img_path)
            try:
                success = process_image(img_path, prompt, output_dir)
                results[img_name] = success
            except Exception as e:
                print(f"Error processing {img_name}: {str(e)}")
                results[img_name] = False
        
        # Report results
        successful = sum(1 for success in results.values() if success)
        print(f"\nProcessing complete! {successful} of {len(input_images)} images processed successfully.")
        print(f"Check {output_dir} for the stylized images.")
        
        # Report any failures
        failures = [name for name, success in results.items() if not success]
        if failures:
            print(f"\nFailed to process {len(failures)} images:")
            for name in failures:
                print(f"  - {name}")


