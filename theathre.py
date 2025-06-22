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

def generate_stylized_image(prompt, input_image_path, max_retries=3):
    """
    Generate a stylized image based on text prompt and input image
    
    Args:
        prompt (str): Text description for the image generation
        input_image_path (str): Path to the input image file
        max_retries (int): Maximum number of retry attempts if generation fails
        
    Returns:
        str: URL of the generated image or None if failed after retries
    """
    image_filename = os.path.basename(input_image_path)
    retries = 0
    
    while retries <= max_retries:
        try:
            if retries > 0:
                print(f"Retry attempt {retries} for {image_filename}")
                # Add a small random delay between retries to avoid rate limiting
                time.sleep(random.uniform(1.0, 3.0))
                
            # Convert input image to base64
            input_image_base64 = image_to_base64(input_image_path)
            if not input_image_base64:
                print(f"Failed to process input image: {image_filename}")
                retries += 1
                continue

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
                retries += 1
                continue
                
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
                
            # If we got here, polling didn't result in a successful image
            retries += 1
            
        except Exception as e:
            print(f"{image_filename} - Exception: {str(e)}")
            retries += 1
    
    print(f"Failed to generate image for {image_filename} after {max_retries} retries")
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

def process_image(input_image_path, prompt, output_dir, max_retries=3):
    """Process a single image and save the result"""
    image_filename = os.path.basename(input_image_path)
    print(f"Processing image: {image_filename}")
    
    result_url = generate_stylized_image(prompt, input_image_path, max_retries)
    
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
    max_retries = 1   # Number of retries for failed generations
    
    if not os.path.exists(input_dir):
        os.makedirs(input_dir)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Define the prompt to use for all images
    prompt = '''
    Replace only the stage curtain to #800000 (dark red velvet) and change all the seat in the bottom half to seat color with #000000 (black). Do not modify anything else — preserve the original image pixel-to-pixel in terms of perspective, lighting, architecture, textures, and realism. The scene must remain photorealistic and highly detailed, with consistent lighting and materials. Only the seat fabric and curtain color should change — all other elements should remain exactly the same.
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
                success = process_image(img_path, prompt, output_dir, max_retries)
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


