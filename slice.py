import sys

def slice(input_file, output_file, count):
    o = open(output_file, 'w')
    i = 0
    for line in open(input_file):
        o.write(line)
        if not line.strip():
            i += 1
        if i == count:
            break

    o.close()


if __name__ == '__main__':
    slice(sys.argv[1], sys.argv[2], int(sys.argv[3]))