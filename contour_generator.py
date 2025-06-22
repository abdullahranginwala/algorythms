#!/usr/bin/env python3
"""
Contour Generator
----------------
This script takes input.png and generates contours using OpenCV.
"""

import cv2
import numpy as np
import os
import matplotlib.pyplot as plt


def generate_contours(threshold1=100, threshold2=200, blur_kernel_size=5):
    """
    Generate contours from input.png using OpenCV.
    
    Args:
        threshold1 (int): First threshold for Canny edge detector
        threshold2 (int): Second threshold for Canny edge detector
        blur_kernel_size (int): Kernel size for Gaussian blur
        
    Returns:
        numpy.ndarray: The contour image
    """
    # Read the image
    img = cv2.imread("input.png")
    if img is None:
        raise FileNotFoundError("Could not read image: input.png")
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (blur_kernel_size, blur_kernel_size), 0)
    
    # Detect edges using Canny
    edges = cv2.Canny(blurred, threshold1, threshold2)
    
    # Find contours
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Create a blank image for drawing contours
    contour_img = np.zeros_like(img)
    
    # Draw all contours
    cv2.drawContours(contour_img, contours, -1, (255, 255, 255), 1)
    
    # Save the result
    output_path = "contour_output.png"
    cv2.imwrite(output_path, contour_img)
    print(f"Contour image saved to {output_path}")
    
    # Display the result
    plt.figure(figsize=(12, 6))
    
    plt.subplot(1, 2, 1)
    plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    plt.title('Original Image')
    plt.axis('off')
    
    plt.subplot(1, 2, 2)
    plt.imshow(contour_img, cmap='gray')
    plt.title('Contour Image')
    plt.axis('off')
    
    plt.tight_layout()
    plt.show()
    
    return contour_img


def main():
    print("Generating contours from input.png...")
    # Generate contours with default parameters
    generate_contours()


if __name__ == "__main__":
    main()
