import spotipy
from spotipy.oauth2 import SpotifyOAuth
from PIL import Image, ImageEnhance
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

# resize_image and retaion aspect ratio
def resize_image(input_path, base_width=None, base_height=None):
    img = Image.open(input_path)

    # Original dimensions
    width, height = img.size

    # Calculate new dimensions
    if base_width:
        wpercent = (base_width / float(width))
        hsize = int((float(height) * float(wpercent)))
        img = img.resize((base_width, hsize), Image.LANCZOS)
    elif base_height:
        hpercent = (base_height / float(height))
        wsize = int((float(width) * float(hpercent)))
        img = img.resize((wsize, base_height), Image.LANCZOS)
    else:
        raise ValueError("Either base_width or base_height must be specified")

    return img

# Function to read the voltage from the I2C device
def read_voltage():
    try:
        # Read the integer part (first register)
        integer_part = bus.read_byte_data(WITTY_PI_DEVICE_ADDRESS, 1)

        # Read the decimal part (second register)
        decimal_part = bus.read_byte_data(
            WITTY_PI_DEVICE_ADDRESS, 2) / 100.0  # Assuming two decimal places

        # Combine integer and decimal parts to get the voltage
        voltage = integer_part + decimal_part
        return voltage
    except Exception as e:
        print(f"Error reading voltage: {str(e)}")
        return None

def is_batt_low():
    return True

bat_low = False

# Read the voltage from the I2C device
voltage = read_voltage()
if voltage is not None:
    print(f"Voltage: {voltage:.2f} V")
    if voltage < 3.6:
        print("Battery voltage is low.")
        bat_low = True
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

enhancer = ImageEnhance.Color(combined_image)
ink_img = enhancer.enhance(2.0)
enhance = ImageEnhance.Contrast(ink_img)
ink_img = enhance.enhance(2.0)

if bat_low:
    # overlay a small battery icon in the top right corner
    battery_image = resize_image('battery_low_strikethrough_boarder_white.png', base_width=80)

    position = (ink_img.width - battery_image.width - 20, 20)

    ink_img.paste(battery_image, position, battery_image)

# ink_img.show();

inky = auto(ask_user=True, verbose=True)
saturation = 1.0

resizedimage = ink_img.resize(inky.resolution).rotate(180)

inky.set_image(resizedimage, saturation=saturation)
inky.show()