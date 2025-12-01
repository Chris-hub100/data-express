import qrcode
from PIL import Image
import os

def create_qr(url, filename):
    # Create the QR object
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H, # High error correction
        box_size=20,
        border=2,
    )
    
    qr.add_data(url)
    qr.make(fit=True)

    # Create image (Black on White)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Ensure directory exists
    save_folder = "static/images"
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)

    # Save
    save_path = os.path.join(save_folder, filename)
    img.save(save_path)
    print(f"✅ Saved {filename} -> Link: {url}")

# --- GENERATE THE TWO CODES ---

# 1. FRONT OF SHIRT ("Do Not Scan")
# The hook: They disobeyed the shirt, so we play with that.
create_qr("https://dataexpress.store/?ref=front", "qr_front.png")

# 2. BACK OF SHIRT ("Curiosity / Following")
# The hook: They are walking behind you.
create_qr("https://dataexpress.store/?ref=back", "qr_back.png")