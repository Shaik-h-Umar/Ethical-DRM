import cv2


def embed_image_watermark(input_path, output_path, user_id):
    """
    Add invisible watermark to image using pixel manipulation.
    """
    img = cv2.imread(input_path)
    if img is None:
        raise ValueError(f"Failed to read image: {input_path}")
    if not user_id:
        raise ValueError("user_id cannot be empty")

    user_token = user_id[:3].ljust(3, "_")
    ascii_vals = [ord(c) for c in user_token]
    for i in range(3):
        img[0, i] = [ascii_vals[i]] * 3

    ok = cv2.imwrite(output_path, img)
    if not ok:
        raise RuntimeError(f"Failed to write watermarked image: {output_path}")

    return output_path


def extract_image_watermark(image_path):
    """
    Extract watermark from image.
    """
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Failed to read image: {image_path}")

    chars = []
    for i in range(3):
        val = int(img[0, i][0])
        chars.append(chr(val))

    return "".join(chars)
