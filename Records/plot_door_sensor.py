from matplotlib import pyplot as plt

def main():
    file = open("record.csv", "r")
    first_line = file.readline()
    headers = first_line.split(",")
    num_indexes = len(headers)
    data = list()
    for x in range(num_indexes):
        data.append(list())
    # do first line or headers

    for i in range(num_indexes):
        data[i].append(headers[i])

    read_line = file.readline()
    while read_line is not "":
        split_data = read_line.split(",")
        for i in range(num_indexes):
            data[i].append(split_data[i])
    print(data)

if __name__ == "__main__":
    main()