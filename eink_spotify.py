import spotipy
from spotipy.oauth2 import SpotifyOAuth
from PIL import Image
import requests
import smbus
from inky.auto import auto

SPOTIPY_CLIENT_ID = 'd3ee96d71f0545909f0529a7e8788bef'
SPOTIPY_CLIENT_SECRET = '182479cb240640638cb0a28a8580f4c4'
SPOTIPY_REDIRECT_URI = 'http://localhost:8000/callback'

WITTY_PI_DEVICE_ADDRESS = 0x08

bus = smbus.SMBus(1)

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(SPOTIPY_CLIENT_ID, 
                    SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI, scope='user-top-read', open_browser=False, cache_path='/home/pi/spotipy/.cache'))


# Function to read the voltage from the I2C device
def read_voltage():
    try:
        # Read the integer part (first register)
        integer_part = bus.read_byte_data(WITTY_PI_DEVICE_ADDRESS, 0x17)

        # Read the decimal part (second register)
        decimal_part = bus.read_byte_data(
            WITTY_PI_DEVICE_ADDRESS, 0x18) / 100.0  # Assuming two decimal places

        # Combine integer and decimal parts to get the voltage
        voltage = integer_part + decimal_part
        return voltage
    except Exception as e:
        print(f"Error reading voltage: {str(e)}")
        return None

# Read the voltage from the I2C device
voltage = read_voltage()
if voltage is not None:
    print(f"Voltage: {voltage:.2f} V")
else:
    print("Failed to read voltage.")

top_tracks = sp.current_user_top_tracks(time_range='short_term', limit=6)

images = []

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

# combined_image.show();

inky = auto(ask_user=True, verbose=True)
saturation = 1.0

resizedimage = combined_image.resize(inky.resolution).rotate(180)

inky.set_image(resizedimage, saturation=saturation)
