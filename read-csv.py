import json
import itertools
from datetime import timedelta, time

import dateutil.parser
import numpy as np


MEASURE_DIM = 10
PM1_DIM = 0
PM10_DIM = 1
PM25_DIM = 2
NO2_DIM = 3
CO_DIM = 4
PRESSURE = 5
HUMIDITY = 6
TEMPERATURE = 7
SO2 = 8
O3 = 9
AIRLY_CAQI = 6
HOURS = 24

def read_json(path):
    with open(path) as json_file:
        content = json.load(json_file)
        return content

def read_stations(content):
    grouped = itertools.groupby(content, lambda e: e['id'])
    station_map = {}
    for i in grouped:
        for j in i[1]:
            station_map[j['id']] = j
    return station_map
def group(col, by):
    values = set(map(lambda e: e[by], col))
    return [[y for y in col if y[by] == x] for x in values]

def read_first_measure_ids(content):
    return [m['id'] for m in (sorted(group(content, 'date'), key=lambda e: e[0]['date'])[0])]

def read_mea(content):
    grouped = itertools.groupby(content, lambda e: e['id'])
    # x - stations, y - timestamp, z - measure

def get_cords(stations_map, STATION_IDS):
    return [(station, stations_map[station]['location']) for station in STATION_IDS]

def extract_days(content, station):
    history = [json.loads(e['measure']).get('history') for e in list(filter(lambda x:
                                                                  x[0]['id'] == station,
                                                                  group(content, 'id')))[0]]
    dates = [[dateutil.parser.parse(d['fromDateTime']).date() for d in h] for h in filter(None, history)]
    return sorted(set(itertools.chain.from_iterable(dates)))



def triangulate(station_with_cords):
    points = np.array([[station[1]['latitude'], station[1]['longitude']] for station in station_with_cords])
    from scipy.spatial import Delaunay
    tri = Delaunay(points)
    import matplotlib.pyplot as plt
    fig = plt.figure()
    ax = fig.add_subplot(111)
    X = points[:, 0]
    Y = points[:, 1]
    for s in tri.simplices:
        print(s)
    plt.triplot(X, Y, tri.simplices.copy())
    plt.plot(X, Y, 'o')
    i = 0
    for xy in zip(X, Y):  # <--
        ax.annotate('%s' % i, xy=xy, textcoords='data')
        i = i + 1
    plt.show()

    return tri.simplices.copy()

def draw_for(measure_matrix, triangles, station_with_cords, day, hour,m,i,DAYS):
    import matplotlib.pyplot as plt
    points = np.array([[station[1]['latitude'], station[1]['longitude']] for station in station_with_cords])

    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.set_title("{} {}".format(DAYS[day], h))
    X = points[:, 0]
    Y = points[:, 1]
    Z = measure_matrix[:, day, hour,m,i]
    tpc = plt.tripcolor(X, Y, Z, triangles)
    fig.colorbar(tpc)
    plt.plot(X, Y, 'o')
    i = 0
    for xy in zip(X, Y):  # <--
        ax.annotate('%s' % i, xy=xy, textcoords='data')
        i = i + 1
    plt.show()
    pass

def get_prev(day, hour):
    if hour > 0:
        return day, hour - 1
    else:
        return day - timedelta(days=1), 23

def count_measure(stations, measures_groupped, DAYS):
    avgs = [measures_groupped[station] for station in stations]
    for station in stations:
        by_hour = np.shape((len(DAYS), HOURS))

        for measures in measures_groupped[station]:
            for measure in json.loads(measures['measure']):
                print(measure)


    for d_i, day in enumerate(DAYS):
        pass



def build_measure_matrix(triangles, STATION_IDS, DAYS, MEASURES):
    measures_groupped = {}
    for item in MEASURES:
        measures_groupped.setdefault(item['id'], []).append(item)

    matrix = np.full((len(STATION_IDS), len(DAYS), HOURS, MEASURE_DIM), np.nan)
    for s_idx, station in enumerate(STATION_IDS):
        for measures in measures_groupped[station]:
            if measures is not None:
                m = json.loads(measures['measure'])

                if 'history' in m:
                    for measure in m.get('history'):
                        fromDate = dateutil.parser.parse(measure['fromDateTime'])
                        hour = fromDate.hour
                        date = fromDate.date()
                        if 'values' in measure:
                            for v in measure['values']:
                                if v['name'] == 'PM1':
                                    matrix[s_idx, DAYS.index(date), hour, PM1_DIM] = v['value']
                                elif v['name'] == 'PM10':
                                    matrix[s_idx, DAYS.index(date), hour, PM10_DIM]= v['value']
                                elif v['name'] == 'PM25':
                                    matrix[s_idx, DAYS.index(date), hour, PM25_DIM]= v['value']
                                elif v['name'] == 'PRESSURE':
                                    matrix[s_idx, DAYS.index(date), hour, PRESSURE]= v['value']
                                elif v['name'] == 'HUMIDITY':
                                    matrix[s_idx, DAYS.index(date), hour, HUMIDITY]= v['value']
                                elif v['name'] == 'TEMPERATURE':
                                    matrix[s_idx, DAYS.index(date), hour, TEMPERATURE]= v['value']
                                elif v['name'] == 'CO':
                                    matrix[s_idx, DAYS.index(date), hour, CO_DIM]= v['value']
                                elif v['name'] == 'NO2':
                                    matrix[s_idx, DAYS.index(date), hour, NO2_DIM]= v['value']
                                elif v['name'] == 'SO2':
                                    matrix[s_idx, DAYS.index(date), hour, SO2]= v['value']
                                elif v['name'] == 'O3':
                                    matrix[s_idx, DAYS.index(date), hour, O3]= v['value']
                                else:

                                    print(v)
    t_matrix = np.full((len(triangles), len(DAYS), HOURS, MEASURE_DIM, 2), np.nan)
    for t_idx, triangle in enumerate(triangles):
        print('{} / {}'.format(t_idx, len(triangles)))
        for d_idx, day in enumerate(DAYS):
            for h in range(HOURS):
                d_prev, h_prev = get_prev(day, h)
                d_prev_idx = DAYS.index(d_prev) if d_prev in DAYS else -1
                if d_prev_idx > 0:
                    for m in range(MEASURE_DIM):
                        mean_now = np.nanmean([matrix[s, d_idx, h, m] for s in triangle])
                        mean_prev = np.nanmean([matrix[s, d_prev_idx, h_prev, m] for s in triangle])
                        delta = mean_now - mean_prev
                        t_matrix[t_idx, d_idx, h, m, 0] = delta
                        t_matrix[t_idx, d_idx, h, m, 1] = mean_now
    return t_matrix





if __name__ == "__main__":

    stations = read_json('/Users/pmoskala/Agh/s9/eksploracja/krk-air/stations.json')
    stations_map = read_stations(stations)
    #
    # print(stations_map.keys())
    measures = read_json('/Users/pmoskala/Agh/s9/eksploracja/krk-air/measures-4weeks.json')
    STATION_IDS = read_first_measure_ids(measures)
    DAYS = extract_days(measures, STATION_IDS[0])
    print('days', DAYS)
    station_with_cords = get_cords(stations_map, STATION_IDS)
    triangles = triangulate(station_with_cords)
    # measure_matrix = build_measure_matrix(triangles, STATION_IDS, DAYS,  measures)
    # np.save('measure_mat.mat', measure_matrix)
    measure_matrix =  np.load('/Users/pmoskala/Agh/s9/eksploracja/krk-air/measure_mat.mat.npy')
    for d in range(2, len(DAYS)):
        for h in range(24):
            draw_for(measure_matrix, triangles, station_with_cords, d, h, PM10_DIM, 1, DAYS)
            import time
            time.sleep(0.2)


    print(measure_matrix.shape)
