import re
from itertools import product
from operator import mul
from pandas import DataFrame

class Dimension(object):

    def __init__(self, title, values):
        self.title = title
        self.values = values

    def __len__(self):
        return len(self.values)


class Table(object):

    def __init__(self):
        self.dimensions = []
        self.data = None

    def add_dimension(self, dimension):
        self.dimensions.append(dimension)

    def get_by(self, title, value):
        #FIXME does not work!!!
        title_index = [dim.title for dim in self.dimensions].index(title)
        dims = [dim.values for dim in self.dimensions]
        dims[title_index] = [value]
        table = Table()
        table.dimension = [d for d in self.dimensions if d.title != title]
        table.data = [self.get(*criteria) for criteria in reversed(list(product(*dims)))]
        return table

    def get(self, *criteria):
        dim_lenghts = [len(dim) for dim in self.dimensions]
        dim_indices = [dim.values.index(c) for (dim, c)
                       in zip(self.dimensions, criteria)]
        return self.data[sum(reduce(mul, dim_lenghts[i+1:], 1) * index
                         for i, index in enumerate(dim_indices))]


def parse(path):
    data = read_data(path)
    value_regex = re.compile(r'VALUES\(\"(.*)\"\)')
    table = Table()
    for item in data:
        if not item:
            continue
        name, values = [t.strip() for t in item.split('=', 1)]
        value_match = value_regex.match(name)
        if value_match:
            title = value_match.group(1)
            table.add_dimension(create_dimension(title, values))
        if name == 'DATA':
            table.data = [i.strip() for i in values.split(' ')]
    return table


def read_data(path):
    return [t.strip() for t in
            open(path).read().decode('IBM850').replace(';\r\n', ';\n').split(';\n')]


def create_dimension(title, values):
    # values are defined like: "foo","bar","zap"
    values = values.replace('\r\n', '').replace('\n', '')[1:-1].split('","')
    return Dimension(title, values)

def to_pandas_df(table):
    """Creates a Pandas DataFrame with the data in the table"""
    largs = table.dimensions
    total = 1
    ldims = []

    for dim in largs:
        ldims.append(len(dim))
        total *= len(dim)

    vresult = total * [0]
    
    for i, dim in enumerate(largs):
        ldim = ldims[i]
        tblo = total / ldim
        if i < (len(ldims) - 1):
            rdim = 1
            for x in range(i, len(ldims) - 1):
                rdim *= ldims[x+1]
        else:
            rdim = 1
        for udi in range(ldim):
            if i == 0:
                for j in range(rdim):
                    vresult[j+(udi * rdim)]=[dim.values[udi]]
            else:
                for j in range(0, total, ldim * rdim):
                    for k in range(rdim):
                        vresult[j + k + (udi * rdim)].extend([dim.values[udi]])
    for i, fila in enumerate(vresult):
        fila.extend([table.data[i]])

    colnames = [dim.title for dim in table.dimensions]
    colnames.extend(['values'])

    return DataFrame(vresult, columns=colnames)
    


if __name__ == '__main__':
    table = parse('examples/tulot.px')
    print table.get('2008', 'Tuusula - Tusby', 'Veronalaiset tulot, mediaani')
    print table.get('2009', 'Tuusula - Tusby', 'Veronalaiset tulot, mediaani')
    print table.get('2007', u'Hyvink\xe4\xe4 - Hyvinge', 'Tulonsaajia')
    print table.get_by('Vuosi', '2007').get(u'Hyvink\xe4\xe4 - Hyvinge', 'Tulonsaajia')
    print table.get('2008', 'Tuusula - Tusby', 'Veronalaiset tulot, mediaani')
    table = parse('examples/vaalit.px')
    print table.get('Uudenmaan vaalipiiri', 'VIHR', u'Yhteens\xe4', u'78 vuotta')
