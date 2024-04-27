from collections import defaultdict
import sys
import os
import sqlite3
import csv
import time

# 至多保留的小数位，不补齐0，自己写去
keep_decimals = 3
# 存储位置
output_file = 'output.csv'

# 老天，这曾经简直是屎诗,现在它是史诗了
# 算了，还是精彩的屎山
# 我是史学家，这旧事史


def calculate_all_speeds(cursor, vehicle_name, start_tick, end_tick):
    start_block_id = 30 + start_tick * 30
    end_block_id = 30 + end_tick * 30 + 29

    query = """
    SELECT IsLeft, AVG(Speed) 
    FROM VehicleData 
    WHERE Vehicle = ? AND BlockID BETWEEN ? AND ?
    GROUP BY IsLeft
    """
    cursor.execute(query, (vehicle_name, start_block_id, end_block_id))
    results = cursor.fetchall()

    # 初始化速度数据
    speeds = [None, None, None]  # [左侧车道, 右侧车道, 全部车道]
    index_map = {1: 0, 0: 1}  # 数据库中1代表左车道，映射到索引0；0代表右车道，映射到索引1

    # 处理查询结果
    valid_speeds = []
    for is_left, avg_speed in results:
        if avg_speed is not None:
            rounded_speed = round(avg_speed, keep_decimals)
            speeds[index_map[is_left]] = rounded_speed
            valid_speeds.append(rounded_speed)

    # 计算总体平均速度
    if valid_speeds:
        speeds[2] = sum(valid_speeds) / len(valid_speeds)

    return speeds


def write_to_csv(tick_data, max_block_id, output_file):
    with open(output_file, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)

        # 写入标题行
        csv_writer.writerow(['Tick', '车辆ID', '左车道速度', '右车道速度', '总平均速度'])

        # 遍历每个Tick
        for tick_index, vehicle_dict in enumerate(tick_data):
            start_block_id = 30 + tick_index * 30
            end_block_id = min(start_block_id + 29, max_block_id)

            # 写入当前Tick的BlockID范围
            csv_writer.writerow(
                [f'Tick {tick_index + 1}: Block {start_block_id} to {end_block_id}'])

            # 写入每辆车的数据
            for vehicle_name, speeds in vehicle_dict.items():
                csv_writer.writerow(
                    [tick_index + 1, vehicle_name, speeds[0], speeds[1], speeds[2]])

            # 在每个Tick之后添加一个空行，如果不是最后一个Tick
            if tick_index < len(tick_data) - 1:
                csv_writer.writerow([])


# 删除现有的数据库文件
if os.path.exists(r'vehicle_speeds.db'):
    os.remove(r'vehicle_speeds.db')

# 确保命令行参数正确
if len(sys.argv) != 2:
    print("如下使用范例运行: python script.py input_file.csv")
    sys.exit(1)

input_file = sys.argv[1]
# 从命令行参数中获取 L_Limit 和 R_Limit
# 这片大地（1/1)
L_Limit = int(input("输入起始块 (空白则从头开始读取): ") or 0)
# 就算是海洋沸腾、大气消失，就算我们的卫星接连坠入重力的漩涡，就算我们的太阳凶恶的膨胀，无情地吃掉它的孩子直至万籁俱寂……我们也一样能再见面,你说是吧我的屎山代码和Bug😅😅😅
# 佬普你到底干了什么😭😭😭
R_Limit = int(input("输入结束块 (空白则到文件尾部结束读取): ") or sys.maxsize)

start_time = time.time()

# 连接到 SQLite 数据库
conn = sqlite3.connect(r'vehicle_speeds.db')
cursor = conn.cursor()
# 增加缓存大小
conn.execute('PRAGMA cache_size = 10000;')
# 启用内存映射IO
conn.execute('PRAGMA mmap_size = 41943040;')
# 调整同步模式
conn.execute('PRAGMA synchronous = NORMAL;')

# 创建 VehicleSpeeds 表
cursor.execute('''CREATE TABLE VehicleData (
                    Vehicle TEXT,
                    IsLeft BOOL,
                    Speed REAL,
                    BlockID INTEGER DEFAULT 0
                )''')

# 读取 CSV 文件并处理数据
with open(input_file, 'r', newline='') as csvfile:
    csv_reader = csv.reader(csvfile)
    # 设置标志变量，表示是否应该开始或停止读取行
    start_reading = False
    block_id = 0  # 初始的 BlockID
    for row_number, row in enumerate(csv_reader, start=1):
        # 检查行中是否存在足够的列
        if len(row) >= 4:
            if row[2]:  # C 列不为空
                if start_reading:
                    # 解析数据行
                    vehicle = row[2] + str(row[0])  # 显式地将 A 列的值转换为字符串
                    is_left = (row[3] == 'left')
                    speed = float(row[1])

                    # 打印解析后的数据
                    # print("Row:", row_number)
                    # print("Parsed data:", vehicle, is_left, speed)

                    # 插入数据到数据库
                    try:
                        cursor.execute("INSERT INTO VehicleData (Vehicle, IsLeft, Speed, BlockID) VALUES (?, ?, ?, ?)",
                                    (vehicle, is_left, speed, block_id))
                        # print("Data inserted successfully")
                    except sqlite3.Error as e:
                        print("Error inserting data:", e)
        else:
            block_id = int(row[0])
            # print("Invalid row:", row)
            # 如果 Block_ID 大于等于 L_Limit，则开始读取行
            if not start_reading and row and int(row[0]) >= L_Limit:
                start_reading = True

            # 如果 Block_ID 大于等于 R_Limit，则停止读取行
            if start_reading and row and int(row[0]) >= R_Limit:
                break

conn.commit()

end0_time = time.time()

# 计算用时
elapsed_time0 = end0_time - start_time

# 打印时间差
print(f"读出并且写入数据库用时: {elapsed_time0} 秒")

# 查询表中的行数
cursor.execute("SELECT COUNT(*) FROM VehicleData")
row_count = cursor.fetchone()[0]

# 检查行数是否为零
if row_count == 0:
    print("Database is empty")
else:
    print(f"数据库内总条目数：{row_count}")


# 查询数据库以获取最大的 BlockID
cursor.execute("SELECT MAX(BlockID) FROM VehicleData")
max_block_id = cursor.fetchone()[0]

# 计算Tick的数量
num_ticks = (max_block_id - 30) // 30 + \
    1 if max_block_id and max_block_id >= 30 else 0

# 初始化tick_data列表
tick_data = [{} for _ in range(num_ticks)]

# 查询所有车辆，按BlockID分组
cursor.execute(
    "SELECT BlockID, Vehicle FROM VehicleData WHERE BlockID >= ? AND BlockID <= ? ORDER BY BlockID, Vehicle", (30, max_block_id))
rows = cursor.fetchall()

# 在Python中处理数据分组
vehicle_groups = defaultdict(list)
for block_id, vehicle in rows:
    tick_index = (block_id - 30) // 30
    vehicle_groups[tick_index].append(vehicle)

# 初始化tick_data
for tick_index, vehicles in vehicle_groups.items():
    for vehicle in set(vehicles):  # 使用set去重
        tick_data[tick_index][vehicle] = [None, None, None]

end1_time = time.time()

# 计算用时
elapsed_time1 = end1_time - end0_time

# 打印时间差
print(f"初始化列表用时: {elapsed_time1} 秒")

# 遍历每个Tick
# 遍历每个Tick
for i in range(num_ticks):
    # 获取当前Tick的字典
    tick_dict = tick_data[i]

    # 遍历当前Tick字典中的每辆车
    for vehicle_name in tick_dict.keys():
        # 计算所有车道的平均速度
        speeds = calculate_all_speeds(cursor, vehicle_name, i, i)

        # 更新tick_dict中对应车辆的速度数据
        tick_dict[vehicle_name] = speeds


end2_time = time.time()

# 计算用时
elapsed_time2 = end2_time - end1_time

# 打印时间差
print(f"完成遍历和计算用时: {elapsed_time2} 秒")

# 写入csv

write_to_csv(tick_data, max_block_id, output_file)

# 提交事务并关闭数据库连接

end_time = time.time()

# 计算用时
elapsed_time = end_time - start_time

# 打印时间差
print(f"全程用时: {elapsed_time} 秒")

conn.close()
# 删除现有的数据库文件
if os.path.exists(r'vehicle_speeds.db'):
    os.remove(r'vehicle_speeds.db')
