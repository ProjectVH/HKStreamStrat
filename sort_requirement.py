
list = []

with open("requirements.txt", "r") as f:
    for line in f:
        list.append(line.strip("\n"))
list = sorted(list)

with open("requirements.txt", "w") as f:
    for package in list:
        f.write(package+"\n")



