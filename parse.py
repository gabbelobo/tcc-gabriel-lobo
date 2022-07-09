import csv

with open('RawData_MetMast_DE7505.txt') as f:
    lines = f.readlines()
    header = lines[8].split("\t")[:-1]
    new_header = []

    for i in header:
        header_item = i.split(';')
        for j in header_item:
            new_header.append(j)

    # print(new_header)
    num_data_rows = int(len(lines[9:]) / 6)

    data_rows = []
    data_rows.append(new_header)
    for i in range(num_data_rows):
        rows = lines[((i*6) + 9):((i*6) + 15)]
        new_rows = []
        date = rows[0].split("\t")[0]
        for j in rows:
            split = j.split("\t")
            split[-1] = split[-1].replace('\n', '')
            split = list(map(lambda x: float(x.replace(",", ".")), split[1:]))
            new_rows.append(split)
        data_row = []
        len_row = len(new_rows[0])
        for j in range(len_row):
            sum = 0
            for k in range(6):
                # print(j,k)
                sum += new_rows[k][j]
            data_row.append(round(sum / 6, 3))
        
        final_row = [date] + data_row
        data_rows.append(final_row)
        
with open('output.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerows(data_rows)