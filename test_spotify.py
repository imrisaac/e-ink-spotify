import spotipy
from spotipy.oauth2 import SpotifyOAuth
from PIL import Image, ImageStat, ImageEnhance
import requests

SPOTIPY_CLIENT_ID = 'd3ee96d71f0545909f0529a7e8788bef'
SPOTIPY_CLIENT_SECRET = '182479cb240640638cb0a28a8580f4c4'
SPOTIPY_REDIRECT_URI = 'http://localhost:8000/callback'

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(SPOTIPY_CLIENT_ID, 
                    SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI, scope='user-top-read', open_browser=False, cache_path='.cache'))

top_tracks = sp.current_user_top_tracks(time_range='short_term', limit=6)

images = []

def resize_image(input_path, base_width=None, base_height=None):
    img = Image.open(input_path)

    # Original dimensions
    width, height = img.size

    # Calculate new dimensions
    if base_width:
        wpercent = (base_width / float(width))
        hsize = int((float(height) * float(wpercent)))
        img = img.resize((base_width, hsize), Image.Resampling.LANCZOS)
    elif base_height:
        hpercent = (base_height / float(height))
        wsize = int((float(width) * float(hpercent)))
        img = img.resize((wsize, base_height), Image.Resampling.LANCZOS)
    else:
        raise ValueError("Either base_width or base_height must be specified")

    return img

def enhance_image(img, saturation_factor, contrast_factor):
    # Enhance saturation
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(saturation_factor)

    # Enhance contrast
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(contrast_factor)

def is_batt_low():
    return True

for track in top_tracks['items']:
    album_art_url = track['album']['images'][0]['url']
    images.append(album_art_url)

images = [Image.open(requests.get(url, stream=True).raw) for url in images]
combined_image = Image.new('RGB', (800, 480), (255, 255, 255))

x_offset = 1
y_offset = 0

for image in images:
    combined_image.paste(image.resize((266, 240)), (x_offset, y_offset))
    x_offset += 266
    if x_offset > 750:
        x_offset = 1
        y_offset += 240

combined_image.save('combined_album_art.png')

if is_batt_low():
    # overlay a small battery icon in the top right corner
    battery_image = resize_image('battery_low_strikethrough_boarder_white.png', base_width=100)

    position = (combined_image.width - battery_image.width - 20, 20)

    combined_image.paste(battery_image, position, battery_image)

combined_image.show()

enhancer = ImageEnhance.Color(combined_image)
img = enhancer.enhance(1.5)
enhance = ImageEnhance.Contrast(img)
img = enhance.enhance(1.5)

img.show()

