import csv
import datetime
import os
import re

import matplotlib.pyplot as plt


def get_search_terms():
    result = []

    while True:
        pos = input('Word position:\n> ')

        if pos == "":
            break

        try:
            pos = int(pos)
        except ValueError:
            print("That's not an integer, please enter a valid integer")
            continue

        text = input('Search text:\n> ')

        if text == "":
            break

        result.append((pos, text))

    return result


def get_data_points():
    result = []

    while True:
        pos = input('Data position:\n> ')

        if pos == "":
            break

        try:
            pos = int(pos)
        except ValueError:
            print("That's not an integer, please enter a valid integer")
            continue

        name = input('Data point name:\n> ')

        if name == "":
            break

        result.append((pos, name))

    return result


search_path = input('Enter path to search files from:\n> ')
search_terms = get_search_terms()
plot_values = get_data_points()

results = {}

with open("data/output.csv", 'w', newline='') as file:
    writer = csv.writer(file)

    writer.writerow(["Date", "Commit", *[name for pos, name in plot_values]])

    lst = os.listdir(search_path)
    lst.sort()

    for output_file in lst:
        file_path = f"{search_path}/{output_file}"

        if os.path.getsize(file_path) > 0:
            file_name, file_extension = os.path.splitext(output_file)
            commit_time, commit_id = output_file.split('_')

            commit_id, file_ext = commit_id.split('.')

            with open(file_path, 'r') as fp:

                for line in fp:
                    values = " ".join(line.split()).split(' ')

                    try:
                        for pos, text in search_terms:
                            if values[pos] != text:
                                break
                        else:
                            commit_time_object = datetime.datetime.utcfromtimestamp(int(commit_time))
                            data = {}

                            print(f"{commit_id} at {commit_time_object.isoformat(' ')}:")

                            for pos, name in plot_values:
                                x = values[pos]
                                data[name] = int(re.sub('[^0-9]', '', x))
                                print(f"> {values[pos]}: {name}")

                            results[commit_time_object] = data

                            writer.writerow([commit_time_object.isoformat(' '), commit_id, *[val for val in data.values()]])

                            break
                    except IndexError:
                        pass


fig = plt.figure()
ax1 = fig.add_subplot(111)

for pos, name in plot_values:
    ax1.scatter([result for result in results.keys()], [result[name] for result in results.values()], s=10, label=name)

plt.legend(loc='upper left')
plt.xlabel('Time')
plt.savefig('data/output.png')

