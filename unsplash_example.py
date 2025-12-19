"""
Example script demonstrating how to use the Unsplash API.
This requires installing the pyunsplash library:
    pip install pyunsplash

Documentation: https://github.com/salvoventura/pyunsplash
"""

from config import UnsplashConfig


def test_unsplash_connection():
    """Test connection to Unsplash API."""
    try:
        from pyunsplash import PyUnsplash

        # Check if configured
        if not UnsplashConfig.is_configured():
            print("Error: Unsplash API is not configured.")
            print("Please ensure .env file contains UNSPLASH_ACCESS_KEY and UNSPLASH_SECRET_KEY")
            return False

        # Initialize API
        api = PyUnsplash(api_key=UnsplashConfig.get_access_key())

        # Test: Search for photos
        print("Testing Unsplash API connection...")
        print(f"Application ID: {UnsplashConfig.get_application_id()}")

        # Search for 'business' photos
        search = api.search(type_='photos', query='business')
        photos = search.entries

        print(f"\nSuccessfully connected to Unsplash API!")
        print(f"Found {search.total} photos for 'business' query")

        # Display first 3 photos
        print("\nFirst 3 photos:")
        for i, photo in enumerate(photos[:3], 1):
            print(f"{i}. {photo.id} by {photo.photographer_name}")
            print(f"   URL: {photo.link_html}")
            print(f"   Download: {photo.link_download}")

        return True

    except ImportError:
        print("Error: pyunsplash library not installed.")
        print("\nTo install, run:")
        print("  source venv/bin/activate")
        print("  pip install pyunsplash")
        return False

    except Exception as e:
        print(f"Error connecting to Unsplash API: {e}")
        return False


def example_download_photo():
    """Example: Download a random photo."""
    try:
        from pyunsplash import PyUnsplash
        import requests

        api = PyUnsplash(api_key=UnsplashConfig.get_access_key())

        # Get a random photo
        photos = api.photos(type_='random', count=1, query='office')
        photo = photos.entries[0]

        print(f"\nRandom photo: {photo.id}")
        print(f"Photographer: {photo.photographer_name}")
        print(f"Description: {photo.description or 'No description'}")
        print(f"Download URL: {photo.link_download}")

        # Download the photo
        response = requests.get(photo.link_download)
        if response.status_code == 200:
            filename = f"unsplash_{photo.id}.jpg"
            with open(filename, 'wb') as f:
                f.write(response.content)
            print(f"\nPhoto downloaded successfully: {filename}")
        else:
            print(f"Failed to download photo: {response.status_code}")

    except ImportError:
        print("Required libraries not installed. Run:")
        print("  pip install pyunsplash requests")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == '__main__':
    print("=" * 60)
    print("Unsplash API Example")
    print("=" * 60)

    # Test connection
    if test_unsplash_connection():
        print("\n" + "=" * 60)

        # Ask user if they want to download a sample photo
        response = input("\nWould you like to download a random photo? (y/n): ")
        if response.lower() == 'y':
            example_download_photo()
