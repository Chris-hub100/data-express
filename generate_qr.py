import qrcode
from PIL import Image

# 1. THE LINK
# We add the ?ref=tshirt tracker so you know if the shirt is working!
link = "https://dataexpress.store/?ref=tshirt"

# 2. CREATE THE QR CODE
qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_H, # High error correction (Good for fabric wrinkles)
    box_size=20, # Makes it high resolution
    border=2,
)

qr.add_data(link)
qr.make(fit=True)

# 3. CUSTOMIZE COLORS
# Black on White is safest for scanning
img = qr.make_image(fill_color="black", back_color="white")

# 4. SAVE IT
filename = "static/images/tshirt_qr.png"
img.save(filename)

print(f"✅ QR Code saved to {filename}")
print("Send this file to your T-Shirt printer!")