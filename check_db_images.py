import pymysql

conn = pymysql.connect(
    host='localhost',
    user='root',
    password='Kra@211314',
    database='spare_management'
)

cur = conn.cursor()
cur.execute("""
    SELECT id, part_code, image_url, thumbnail_url, side_image_url, 
           detail_image_url, circuit_image_url, perspective_image_url 
    FROM spare_part 
    WHERE part_code = 'SKF-A-001'
""")

row = cur.fetchone()
if row:
    print(f"ID: {row[0]}")
    print(f"备件代码：{row[1]}")
    print(f"image_url: '{row[2]}'")
    print(f"thumbnail_url: '{row[3]}'")
    print(f"side_image_url: '{row[4]}'")
    print(f"detail_image_url: '{row[5]}'")
    print(f"circuit_image_url: '{row[6]}'")
    print(f"perspective_image_url: '{row[7]}'")
else:
    print("未找到备件 SKF-A-001")

conn.close()
