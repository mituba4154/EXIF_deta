#!/usr/bin/env python3
"""
EXIF Data Viewer - A Python application to extract and display EXIF data from photos
with tag-based selection functionality.
"""

import argparse
import sys
import json
from pathlib import Path
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS


class EXIFViewer:
    """EXIF data viewer with tag-based filtering."""
    
    def __init__(self):
        self.common_tags = {
            'DateTime': 'Date and Time',
            'Make': 'Camera Make',
            'Model': 'Camera Model',
            'Orientation': 'Image Orientation',
            'XResolution': 'X Resolution',
            'YResolution': 'Y Resolution',
            'ResolutionUnit': 'Resolution Unit',
            'Software': 'Software',
            'ExifImageWidth': 'Image Width',
            'ExifImageHeight': 'Image Height',
            'FocalLength': 'Focal Length',
            'FNumber': 'F-Number',
            'ExposureTime': 'Exposure Time',
            'ISOSpeedRatings': 'ISO Speed',
            'Flash': 'Flash',
            'WhiteBalance': 'White Balance',
            'GPS GPSLatitude': 'GPS Latitude',
            'GPS GPSLongitude': 'GPS Longitude'
        }
    
    def extract_exif_data(self, image_path):
        """Extract EXIF data from an image file."""
        try:
            with Image.open(image_path) as image:
                exif_data = image.getexif()
                
                if not exif_data:
                    return None
                
                # Convert numeric tags to readable names
                readable_exif = {}
                for tag_id, value in exif_data.items():
                    tag_name = TAGS.get(tag_id, f"Unknown_{tag_id}")
                    readable_exif[tag_name] = value
                
                # Handle GPS data if present
                if 'GPSInfo' in readable_exif:
                    gps_data = readable_exif['GPSInfo']
                    if isinstance(gps_data, dict):
                        for gps_tag_id, gps_value in gps_data.items():
                            gps_tag_name = GPSTAGS.get(gps_tag_id, f"GPS_{gps_tag_id}")
                            readable_exif[f"GPS {gps_tag_name}"] = gps_value
                
                return readable_exif
                
        except Exception as e:
            print(f"Error reading {image_path}: {e}")
            return None
    
    def filter_tags(self, exif_data, selected_tags=None):
        """Filter EXIF data based on selected tags."""
        if not exif_data:
            return {}
        
        if not selected_tags:
            return exif_data
        
        filtered_data = {}
        for tag in selected_tags:
            # Exact match
            if tag in exif_data:
                filtered_data[tag] = exif_data[tag]
            else:
                # Partial match (case-insensitive)
                matching_keys = [key for key in exif_data.keys() 
                               if tag.lower() in key.lower()]
                for key in matching_keys:
                    filtered_data[key] = exif_data[key]
        
        return filtered_data
    
    def format_value(self, value):
        """Format EXIF values for better readability."""
        if isinstance(value, tuple) and len(value) == 2:
            # Handle rational numbers (e.g., focal length, exposure time)
            if value[1] != 0:
                result = value[0] / value[1]
                if result.is_integer():
                    return str(int(result))
                else:
                    return f"{result:.2f}"
        
        if isinstance(value, bytes):
            try:
                return value.decode('utf-8')
            except:
                return str(value)
        
        if isinstance(value, (list, tuple)) and len(value) > 2:
            # Handle GPS coordinates and other complex data
            return str(value)
        
        return str(value)
    
    def display_exif_data(self, exif_data, image_path, output_format='table'):
        """Display EXIF data in a formatted way."""
        if not exif_data:
            print(f"No EXIF data found in {image_path}")
            return
        
        if output_format == 'json':
            # Convert values to strings for JSON serialization
            json_data = {}
            for tag, value in exif_data.items():
                json_data[tag] = self.format_value(value)
            print(json.dumps(json_data, indent=2, ensure_ascii=False))
            return
        
        # Table format (default)
        print(f"\n{'='*60}")
        print(f"EXIF Data for: {Path(image_path).name}")
        print(f"{'='*60}")
        
        # Sort tags for consistent output
        for tag in sorted(exif_data.keys()):
            value = exif_data[tag]
            formatted_value = self.format_value(value)
            print(f"{tag:25}: {formatted_value}")
        
        print(f"{'='*60}")
        print(f"Total tags found: {len(exif_data)}")
    
    def list_available_tags(self, image_path):
        """List all available EXIF tags in an image."""
        exif_data = self.extract_exif_data(image_path)
        if not exif_data:
            print(f"No EXIF data found in {image_path}")
            return []
        
        tags = list(exif_data.keys())
        print(f"\nAvailable EXIF tags in {Path(image_path).name}:")
        print("-" * 50)
        for i, tag in enumerate(sorted(tags), 1):
            print(f"{i:2d}. {tag}")
        
        print(f"\nTotal: {len(tags)} tags")
        return tags
    
    def show_common_tags(self):
        """Display commonly used EXIF tags."""
        print("\nCommonly used EXIF tags:")
        print("-" * 40)
        for tag, description in self.common_tags.items():
            print(f"{tag:20}: {description}")
        
        print(f"\nTotal: {len(self.common_tags)} common tags")
    
    def search_tags(self, image_path, search_term):
        """Search for tags containing a specific term."""
        exif_data = self.extract_exif_data(image_path)
        if not exif_data:
            print(f"No EXIF data found in {image_path}")
            return
        
        matching_tags = {}
        for tag, value in exif_data.items():
            if search_term.lower() in tag.lower():
                matching_tags[tag] = value
        
        if matching_tags:
            print(f"\nTags containing '{search_term}':")
            print("-" * 40)
            for tag, value in matching_tags.items():
                formatted_value = self.format_value(value)
                print(f"{tag:25}: {formatted_value}")
            print(f"\nFound {len(matching_tags)} matching tags")
        else:
            print(f"No tags found containing '{search_term}'")


def main():
    """Main function to handle command line interface."""
    parser = argparse.ArgumentParser(
        description="Extract and display EXIF data from photos with tag-based selection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python exif_viewer.py photo.jpg                        # Show all EXIF data
  python exif_viewer.py photo.jpg -t DateTime Make       # Show only DateTime and Make
  python exif_viewer.py photo.jpg --list-tags            # List all available tags
  python exif_viewer.py photo.jpg --search GPS           # Search for GPS-related tags
  python exif_viewer.py photo.jpg --format json          # Output in JSON format
  python exif_viewer.py --common-tags                    # Show common EXIF tags
        """
    )
    
    parser.add_argument('image_path', nargs='?', help='Path to the image file')
    parser.add_argument('-t', '--tags', nargs='+', 
                       help='Specific EXIF tags to display')
    parser.add_argument('--list-tags', action='store_true', 
                       help='List all available EXIF tags in the image')
    parser.add_argument('--common-tags', action='store_true', 
                       help='Show commonly used EXIF tags')
    parser.add_argument('--search', metavar='TERM', 
                       help='Search for tags containing the specified term')
    parser.add_argument('--format', choices=['table', 'json'], default='table',
                       help='Output format (default: table)')
    
    args = parser.parse_args()
    
    viewer = EXIFViewer()
    
    # Show common tags
    if args.common_tags:
        viewer.show_common_tags()
        return
    
    # Check if image path is provided
    if not args.image_path:
        parser.print_help()
        return
    
    image_path = Path(args.image_path)
    
    # Check if file exists
    if not image_path.exists():
        print(f"Error: File '{image_path}' not found.")
        sys.exit(1)
    
    # Check if it's a file
    if not image_path.is_file():
        print(f"Error: '{image_path}' is not a file.")
        sys.exit(1)
    
    # List available tags
    if args.list_tags:
        viewer.list_available_tags(image_path)
        return
    
    # Search for tags
    if args.search:
        viewer.search_tags(image_path, args.search)
        return
    
    # Extract and display EXIF data
    exif_data = viewer.extract_exif_data(image_path)
    
    if args.tags:
        exif_data = viewer.filter_tags(exif_data, args.tags)
    
    viewer.display_exif_data(exif_data, image_path, args.format)


if __name__ == "__main__":
    main()