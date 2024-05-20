#!/usr/bin/env python3
"""
Dynamic analyser of a cart controller.
"""
# konfigurace vozíku a stanic
cart_slots = 4
cart_weight = 150
stations = ['A', 'B', 'C', 'D']
number_of_stations = len(stations)

slots_coverage_max = cart_slots * number_of_stations
slots_coverage = slots_coverage_max * [False]


def report_coverage():

    coverage_counter = 0
    for slot in slots_coverage:
        coverage_counter = coverage_counter + 1 if slot else coverage_counter

    print('CartCoverage %d%%' % ((coverage_counter / slots_coverage_max) * 100))


# pomocné proměnné pro monitorování vlastností
slots_loaded = cart_slots * [False]
items_loaded = []
items_to_unload = []
current_weight = 0
requested_origin = {}           # klíč - stanice, hodnota - pole předmětů, které se z ní musí vyzvednout
requested_destinations = {}     # klíč - stanice, hodnota - pole předmětů, které se do ní mají převést
for station in stations:
    requested_origin[station] = []
    requested_destinations[station] = []
error_occurred = False


def onloading(time, pos, content, weight, slot):
    global current_weight, requested_origin, error_occurred
    slot, weight, time = int(slot), int(weight), int(time)

    if current_weight + weight > cart_weight:
        print('%s:error: Vozík nesmí být přetížen.' % (time))               # 7
        error_occurred = True

    if slot > cart_slots:
        print('%s:error: Nesmí být naloženo více než 4 náklady.' % (time))  # 6
        error_occurred = True

    if slots_loaded[slot] == True:
        print('%s:error: Vozík nesmí nakládat na obsazený slot.' % (time))  # 1
        error_occurred = True

    if content not in requested_origin[pos]:
        print('%s:error:Vozík nesmí nakládat ve stanici, pokud na to neexistovala žádost.' % (time))    # 5
        error_occurred = True

    try:
        requested_origin[pos].pop(requested_origin[pos].index(content))
    except:
        pass

    slots_loaded[slot] = True
    items_loaded.append(content)
    current_weight = current_weight + weight

    slots_coverage[stations.index(pos) * 4 + slot] = True


def onunloading(time, pos, content, weight, slot):
    global current_weight, items_to_unload, requested_destinations, error_occurred
    slot, weight, time = int(slot), int(weight), int(time)

    if slots_loaded[slot] == False:
        print('%s:error: Vozík nesmí vykládat z volného slotu.' % (time))   # 2
        error_occurred = True

    try:
        items_to_unload.pop(items_to_unload.index(content))
        requested_destinations[pos].pop(requested_destinations[pos].index(content))
        items_loaded.pop(items_loaded.index(content))
    except:
        pass

    slots_loaded[slot] = False
    current_weight = current_weight - weight


def onmoving(time, pos1, pos2):
    global error_occurred
    time = int(time)

    if len(items_to_unload) != 0:
        print('%s:error: Náklad se musí vyložit, pokud je vozík v cílové stanici daného nákladu.' % (time))     # 3
        error_occurred = True

    # vytvoří požadavek na vyložení všech předmětů, které už naložil a mají se v cílové stanici vyložit
    if len(items_to_unload) == 0 and len(requested_destinations[pos2]) != 0:
        for item in items_loaded:
            if item in requested_destinations[pos2]:
                items_to_unload.append(item)


def onrequesting(time, pos1, pos2, content, weight):

    requested_origin[pos1].append(content)
    requested_destinations[pos2].append(content)


def onevent(event):

    event_id = event[1]
    del(event[1])

    if event_id == 'moving':
        onmoving(*event)
    elif event_id == 'loading':
        onloading(*event)
    elif event_id == 'unloading':
        onunloading(*event)
    elif event_id == 'requesting':
        onrequesting(*event)


def monitor(reader):
    "Main function"
    for line in reader:
        line = line.strip()
        onevent(line.split())
    if not error_occurred:
        print("Všechny vlastnosti splněny.")
    report_coverage()


if __name__ == "__main__":
    import sys
    monitor(sys.stdin)
