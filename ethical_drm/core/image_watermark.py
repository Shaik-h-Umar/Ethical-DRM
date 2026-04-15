import cv2
import random

# 🔗 Import your DB functions
from database.db import (
    insert_image_if_not_exists,
    insert_distribution,
    fetch_users_by_image,
    insert_leak
)


# =========================
# Helper: string -> binary
# =========================
def string_to_binary(text):
    return ''.join(format(ord(c), '08b') for c in text)


# =========================
# Helper: binary -> string
# =========================
def binary_to_string(binary):
    chars = []
    for i in range(0, len(binary), 8):
        byte = binary[i:i+8]
        chars.append(chr(int(byte, 2)))
    return ''.join(chars)


# =========================
# EMBED WATERMARK
# =========================
def embed_image_watermark(input_path, output_path, user_id):
    img = cv2.imread(input_path)
    if img is None:
        raise ValueError(f"Failed to read image: {input_path}")

    payload = user_id + "###END###"
    binary_data = string_to_binary(payload)

    h, w, _ = img.shape

    random.seed(user_id)
    used_positions = set()

    for bit in binary_data:
        while True:
            x = random.randint(0, h - 1)
            y = random.randint(0, w - 1)

            if (x, y) not in used_positions:
                used_positions.add((x, y))
                break

        blue = int(img[x, y][0])
        blue = (blue & 0xFE) | int(bit)
        img[x, y][0] = blue

    success = cv2.imwrite(output_path, img)
    if not success:
        raise RuntimeError("Failed to save image")

    return output_path


# =========================
# EXTRACT WATERMARK
# =========================
def extract_image_watermark(image_path, user_id, max_chars=100):
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Failed to read image: {image_path}")

    h, w, _ = img.shape

    random.seed(user_id)
    used_positions = set()

    binary_data = ""

    for _ in range(max_chars * 8):
        while True:
            x = random.randint(0, h - 1)
            y = random.randint(0, w - 1)

            if (x, y) not in used_positions:
                used_positions.add((x, y))
                break

        bit = img[x, y][0] & 1
        binary_data += str(bit)

    extracted_text = binary_to_string(binary_data)

    if "###END###" in extracted_text:
        return extracted_text.split("###END###")[0]

    return None


# =========================
# DISTRIBUTE IMAGE (IMPORTANT)
# =========================
def distribute_image(original_path, user_id, uploaded_by="admin"):
    """
    Creates watermarked image + records in DB
    """

    # 1. Save image record (if not already saved)
    image_id = insert_image_if_not_exists(original_path, uploaded_by)

    # 2. Create user-specific version
    output_path = f"protected_{user_id}.png"
    embed_image_watermark(original_path, output_path, user_id)

    # 3. Record distribution
    insert_distribution(image_id, user_id)

    return output_path, image_id


# =========================
# DETECT LEAK
# =========================
def detect_leak(image_path, image_id):
    """
    Detect who leaked the image
    """

    users = fetch_users_by_image(image_id)

    for user_id in users:
        try:
            extracted = extract_image_watermark(image_path, user_id)
            if extracted == user_id:
                insert_leak(image_path, user_id)
                return user_id
        except:
            continue

    return None


# =========================
# EXAMPLE USAGE
# =========================
if __name__ == "__main__":

    original = "original.png"

    users = ["userA", "userB", "userC"]

    print("=== DISTRIBUTION ===")

    image_id = None

    # Distribute image to users
    for u in users:
        output, image_id = distribute_image(original, u)
        print(f"Sent to {u}: {output}")

    print("\n=== LEAK DETECTION ===")

    leaked_image = "protected_userB.png"

    culprit = detect_leak(leaked_image, image_id)

    if culprit:
        print(f"🚨 Leaked by: {culprit}")
    else:
        print("No watermark detected")