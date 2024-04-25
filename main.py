import sys
import time
import sqlite3
import csv

#至多保留的小数位，不补齐0，自己写去
keep_decimals = 2

#老天，这简直是屎诗
def calculate_average_speed(cursor, vehicle_dict, lane_type, keep_decimals):
    for vehicle_name in vehicle_dict:
        # 查询数据库，获取对应车辆在指定车道的速度数据
        if lane_type == 2:
            cursor.execute("SELECT AVG(Speed) FROM VehicleData WHERE Vehicle = ?", (vehicle_name,))
        else:
            cursor.execute("SELECT AVG(Speed) FROM VehicleData WHERE Vehicle = ? AND IsLeft = ?", (vehicle_name, lane_type))
        average_speed = cursor.fetchone()[0]
        
        # 保留小数到指定的位数
        if average_speed is not None:
            average_speed = round(average_speed, keep_decimals)
        
        # 将平均值存储到字典中对应的数组的第一个元素
        if lane_type == 1:
            vehicle_dict[vehicle_name][0] = average_speed  # 左车道
        elif lane_type == 0:
            vehicle_dict[vehicle_name][1] = average_speed  # 右车道
        elif lane_type == 2:
            # 如果某车道没有数据，则复制另一个车道的数据
            if not average_speed:
                # 选择左车道或右车道的速度数据来计算总平均速度
                other_lane_speed = vehicle_dict[vehicle_name][1] or vehicle_dict[vehicle_name][0]
                vehicle_dict[vehicle_name][2] = other_lane_speed
            else:
                vehicle_dict[vehicle_name][2] = average_speed  # 全部车道

#酣畅淋漓的屎记
def write_to_csv(vehicle_dict, output_file):
    with open(output_file, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        
        # 写入标题行
        csv_writer.writerow(['车辆ID', '左车道速度', '右车道速度', '总平均速度'])
        
        # 写入数据行
        for vehicle_name, speeds in vehicle_dict.items():
            csv_writer.writerow([vehicle_name, speeds[0], speeds[1], speeds[2]])


# 确保命令行参数正确
if len(sys.argv) != 2:
    print("如下使用范例运行: python script.py input_file.csv")
    sys.exit(1)

input_file = sys.argv[1]
# 从命令行参数中获取 L_Limit 和 R_Limit
#这片大地（1/1)
L_Limit = 30
#就算是海洋沸腾、大气消失，就算我们的卫星接连坠入重力的漩涡，就算我们的太阳凶恶的膨胀，无情地吃掉它的孩子直至万籁俱寂……我们也一样能再见面,你说是吧我的屎山代码和Bug😅😅😅
#佬普你到底干了什么😭😭😭
R_Limit = 30+31


# 连接到 内存SQLite 数据库
conn = sqlite3.connect(':memory:')
cursor = conn.cursor()


# 设置缓存大小为10000页,爆了自己改
cursor.execute("PRAGMA cache_size = 100000")

# 创建 VehicleSpeeds 表
cursor.execute('''CREATE TABLE VehicleData (
                    Vehicle TEXT,
                    IsLeft BOOL,
                    Speed REAL
                )''')

# 读取 CSV 文件并处理数据
with open(input_file, 'r', newline='') as csvfile:
    csv_reader = csv.reader(csvfile)
    # 设置标志变量，表示是否应该开始或停止读取行
    start_reading = False
    for row_number, row in enumerate(csv_reader, start=1):
        # 检查行中是否存在足够的列
        if len(row) >= 4:
            # 检查 C 列和 A 列是否都不为空
            if row[2]:  # C 列不为空

                if start_reading:
                # 解析数据行
                    vehicle = row[2] + str(row[0])  # 显式地将 A 列的值转换为字符串
                    is_left = (row[3] == 'left')
                    speed = float(row[1])

                    # 打印解析后的数据
                    #print("Row:", row_number)
                    #print("Parsed data:", vehicle, is_left, speed)

                    # 插入数据到数据库
                    try:
                        cursor.execute("INSERT INTO VehicleData (Vehicle, IsLeft, Speed) VALUES (?, ?, ?)", (vehicle, is_left, speed))
                        #print("Data inserted successfully")
                    except sqlite3.Error as e:
                        print("Error inserting data:", e)
        else:
            #print("Invalid row:", row)
                            # 如果 Block_ID 大于等于 L_Limit，则开始读取行
            if not start_reading and row and int(row[0]) >= L_Limit:
                start_reading = True
    
            # 如果 Block_ID 大于等于 R_Limit，则停止读取行
            if start_reading and row and int(row[0]) >= R_Limit:
                break
        

# 查询表中的行数
cursor.execute("SELECT COUNT(*) FROM VehicleData")
row_count = cursor.fetchone()[0]

# 检查行数是否为零
if row_count == 0:
    print("Database is empty")
else:
    print(row_count)

cursor.execute("SELECT DISTINCT Vehicle FROM VehicleData ORDER BY Vehicle")
vehicles = cursor.fetchall()

# 创建一个字典，用于存储车辆信息
vehicle_dict = {}

# 遍历每个车辆，并为每个车辆创建一个空的三元素数组作为值
for vehicle in vehicles:
    vehicle_name = vehicle[0]
    vehicle_dict[vehicle_name] = [None, None, None]  # [Left speeds, Right speeds, Total speeds]

# 打印字典
#print("Vehicle dictionary:", vehicle_dict)

# 计算左车道平均速度
calculate_average_speed(cursor, vehicle_dict, lane_type=1, keep_decimals=keep_decimals)

# 计算右车道平均速度
calculate_average_speed(cursor, vehicle_dict, lane_type=0, keep_decimals=keep_decimals)

# 计算全部车道平均速度
calculate_average_speed(cursor, vehicle_dict, lane_type=2, keep_decimals=keep_decimals)


#写入csv
output_file = 'output.csv'
write_to_csv(vehicle_dict, output_file)

# 提交事务并关闭数据库连接
conn.commit()
conn.close()
