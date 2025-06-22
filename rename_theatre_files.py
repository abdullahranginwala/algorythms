import os
import re
import glob

def rename_theatre_files(directory):
    """
    Rename files in the specified directory from format 'Stalls-R2-preview_stylized_timestamp.jpg'
    to 'stalls_r2.jpg'
    """
    # Create a pattern to match the files and extract the row number
    pattern = re.compile(r'stalls_r(\d+).*\.jpg', re.IGNORECASE)
    
    # Get all jpg files in the directory
    files = glob.glob(os.path.join(directory, "*.jpg"))
    
    renamed_count = 0
    for file_path in files:
        filename = os.path.basename(file_path)
        match = pattern.match(filename)
        
        if match:
            row_number = match.group(1)
            new_filename = f"stalls_w{row_number}.jpg"
            new_path = os.path.join(directory, new_filename)
            
            # Check if destination file already exists
            if os.path.exists(new_path):
                print(f"Warning: {new_filename} already exists, skipping {filename}")
                continue
                
            try:
                os.rename(file_path, new_path)
                print(f"Renamed: {filename} → {new_filename}")
                renamed_count += 1
            except Exception as e:
                print(f"Error renaming {filename}: {str(e)}")
    
    print(f"\nRenamed {renamed_count} files in {directory}")

if __name__ == "__main__":
    output_dir = "output_theatre"
    
    if not os.path.exists(output_dir):
        print(f"Directory {output_dir} does not exist!")
    else:
        rename_theatre_files(output_dir)
