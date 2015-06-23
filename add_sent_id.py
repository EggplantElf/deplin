import sys

def add(input_file, output_file):
    o = open(output_file, 'w')
    i = 1
    for line in open(input_file):
        if line.strip():
            o.write('%d_%s' % (i, line))
        else:
            o.write('\n')
            i += 1
    o.close()


if __name__ == '__main__':
    add(sys.argv[1], sys.argv[2])