def convert_rgb(rgb):
    scale = 0xFF
    adjusted = [max(1, chan) for chan in rgb]
    total = sum(adjusted)
    adjusted = [int(round(chan / total * scale)) for chan in adjusted]

    # Unknown, Red, Blue, Green
    return bytearray([0x1, adjusted[0], adjusted[2], adjusted[1]])


color = convert_rgb([255, 0, 0])

print(bytes.fromhex("aa030701001403e8038cbb"))
print(bytes.fromhex("aa030701") + convert_rgb([255, 0, 0]) + bytes.fromhex("038cbb"))
