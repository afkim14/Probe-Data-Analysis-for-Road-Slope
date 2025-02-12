import csv
import pandas as pd
#import matplotlib.pyplot as plt
import math
import sys
import random
import numpy as np

def latlon_toMeters(lat1,lon1,lat2,lon2):
  from math import sin, cos, sqrt, atan2, radians
  # approximate radius of earth in km
  R = 6373.0
  #Convert to lat lon
  lat1 = radians(lat1)
  lon1 = radians(lon1)
  lat2 = radians(lat2)
  lon2 = radians(lon2)
  dlon = lon2 - lon1
  dlat = lat2 - lat1
  a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
  c = 2 * atan2(sqrt(a), sqrt(1 - a))
  distance = R * c
  distance_meters= distance*1000
  return distance_meters

class ProbeDataPoint:
    def __init__(self, sampleID, dateTime, sourceCode, lat, long, altitude, speed, heading):
        self.sampleID = sampleID
        self.dateTime = dateTime
        self.sourceCode = sourceCode
        self.lat = float(lat)
        self.long = float(long)
        self.altitude = altitude
        self.speed = speed
        self.heading = heading

        ### AFTER MATCHING WITH LINK
        self.linkPVID = ""
        self.direction = ""
        self.distFromRef = ""
        self.distFromLink = ""

        ###
        self.linkNode = ""
        ### TEMPORARY
        self.distFromRefLat = ""
        self.distFromRefLong = ""
        self.distFromLinkLat = ""
        self.distFromLinkLong = ""
    def __str__(self):
        return "Probe ID: " + str(self.sampleID) + "\n" + "\tDateTime: " + str(self.dateTime) + "\n" + "\tSource Code: " + str(self.sourceCode) + "\n" + "\tLatitude: " + str(self.lat) + "\n" + "\tLongitude: " + str(self.long) + "\n" + "\tAltitude: " + str(self.altitude) + "\n" + "\tSpeed: " + str(self.speed) + "\n" + "\tHeading: " + str(self.heading)

class LinkData:
    def __init__(self, linkPVID, refNodeID, nrefNodeID, length, functionalClass, directionOfTravel, speedCategory, fromRefSpeedLimit, toRefSpeedLimit, fromRefNumLanes, toRefNumLanes, multiDigitized, urban, timeZone, shapeInfo, curvatureInfo, slopeInfo):
        self.linkPVID = linkPVID
        self.refNodeID = refNodeID
        self.nrefNodeID = nrefNodeID
        self.length = length
        self.functionalClass = functionalClass
        self.directionOfTravel = directionOfTravel
        self.speedCategory = speedCategory
        self.fromRefSpeedLimit = fromRefSpeedLimit
        self.toRefSpeedLimit = toRefSpeedLimit
        self.fromRefNumLanes = fromRefNumLanes
        self.toRefNumLanes = toRefNumLanes
        self.multiDigitized = multiDigitized
        self.urban = urban
        self.timeZone = timeZone
        self.shapeInfo = create_link_data_points(shapeInfo)
        self.curvatureInfo = curvatureInfo
        self.slopeInfo = slopeInfo
        self.minLat = min(self.shapeInfo, key=lambda l: l.lat).lat
        self.maxLat = max(self.shapeInfo, key=lambda l: l.lat).lat
        self.minLong = min(self.shapeInfo, key=lambda l: l.long).long
        self.maxLong = max(self.shapeInfo, key=lambda l: l.long).long
    def __str__(self):
        shapeInfo = "["
        for point in self.shapeInfo[:-1]:
            shapeInfo += str(point) + "\n"
        shapeInfo += "\t\t\t" + str(self.shapeInfo[-1]) + "]"
        return "Link PVID: " + str(self.linkPVID) + "\n" + "\tLength: " + str(self.length) + "\n" + "\tShapeInfo: " + shapeInfo

class LinkDataPoint:
    def __init__(self, lat, long):
        self.lat = float(lat)
        self.long = float(long)
    def __str__(self):
        return "Latitude: " + str(self.lat) + ", Longitude: " + str(self.long)

def create_data(probe_data_file, link_data_file):
    probe_data = {}
    link_data = []
    with open(probe_data_file) as probe_csvfile:
        reader = csv.reader(probe_csvfile)
        for row in reader:
            #TODO: PROBES WITH SAME ID ARE NOT YET SEPARATED BY TRIP
            if (str(row[0]) not in probe_data):
                probe_data[str(row[0])] = [[]]
            batch_size = 10
            if (len(probe_data[str(row[0])][-1]) < batch_size):
                probe_data[str(row[0])][-1].append(ProbeDataPoint(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7]))
            else:
                probe_data[str(row[0])].append([ProbeDataPoint(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7])])
    with open(link_data_file) as link_csvfile:
        reader = csv.reader(link_csvfile)
        for row in reader:
            link_data.append(LinkData(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[12], row[13], row[14], row[15], row[16]))
    link_data.sort(key=lambda x: x.shapeInfo[0].lat, reverse=True)
    return probe_data, link_data

def map_match(probe_data, link_data):
    print("START MAP MATCHING")
    matched_probes = []
    probe_index = 0
    total_probe_ids = len(probe_data)

    with open('Partition6467MatchedPoints.csv', 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["sampleID", "dateTime", "sourceCode", "Latitude", "Longitude", "Altitude", "Speed", "Heading", "linkPVID", "linkRefNode", "direction", "distFromNode", "distFromLinkLine"])
        for probe_id in probe_data:
            probe_index+=1
            sys.stdout.write('\r')
            sys.stdout.write('[ ' + str(probe_index) + "/" + str(total_probe_ids) + ' ]')
            batches = probe_data[probe_id]
            for batch in batches:
                links = {}
                link_counts = {}
                for probe in batch:
                    closestLink = None
                    closestLinkPoint = None
                    closestLinkPointDistance = math.inf
                    for link in link_data:
                        if (probe.lat < link.minLat or probe.lat > link.maxLat or probe.long < link.minLong or probe.long > link.maxLong):
                            continue
                        for linkPoint in link.shapeInfo:
                            distance = latlon_toMeters(linkPoint.long,linkPoint.lat,probe.long,probe.lat)
                            if (distance < closestLinkPointDistance):
                                closestLinkPointDistance = distance
                                closestLinkPoint = linkPoint
                                closestLink = link
                    if (closestLink == None): closestLink = link_data[random.randint(0, len(link_data)-1)]
                    if (closestLink.linkPVID not in link_counts):
                        link_counts[closestLink.linkPVID] = 0
                    link_counts[closestLink.linkPVID] += 1
                    if (closestLink.linkPVID not in links):
                        links[closestLink.linkPVID] = closestLink

                best_link = ""
                best_count = 0
                for linkPVID in link_counts:
                    if (link_counts[linkPVID] > best_count):
                        best_count = link_counts[linkPVID]
                        best_link = linkPVID
                for p in batch:
                    p.linkPVID = best_link
                    p.direction = links[best_link].directionOfTravel
                    refNode = None
                    nonRefNode = None
                    if (len(links[best_link].shapeInfo) > 0):
                        refNode = links[best_link].shapeInfo[0]
                        p.linkNode = str(refNode.lat) + ", " + str(refNode.long)
                        nonRefNode = links[best_link].shapeInfo[-1]
                    p.distFromRef = -1
                    if (refNode != None):
                        #p.distFromRefLat = abs(refNode.lat - p.lat)
                        #p.distFromRefLong = abs(refNode.long - p.long)
                        #p.distFromRef = math.sqrt((refNode.long - p.long)**2 + (refNode.lat - p.lat)**2)
                        p.distFromRef=latlon_toMeters(refNode.lat,refNode.long,p.lat,p.long)
                    p.distFromLink = -1
                    if (refNode != None and nonRefNode != None):
                        perp_point = []
                        if (nonRefNode.lat - refNode.lat == 0):
                            perp_point = [nonRefNode.lat, p.long]
                        elif (nonRefNode.long - refNode.long == 0):
                            perp_point = [p.lat, nonRefNode.long]
                        else:
                            lineSlope = (nonRefNode.long - refNode.long) / (nonRefNode.lat - refNode.lat)
                            constant = (lineSlope * nonRefNode.lat) - nonRefNode.long
                            perpLineSlope = float(1.0/lineSlope) * -1.0
                            perpConstant = (perpLineSlope * p.lat) - p.long
                            a = np.array([[lineSlope, -1],[perpLineSlope,-1]])
                            b = np.array([constant, perpConstant])
                            perp_point = np.linalg.solve(a,b)

                        p.distFromLink=latlon_toMeters(perp_point[0],perp_point[1],p.lat,p.long)
                        #p.distFromLink = abs((lineSlope * p.lat + 1 * p.long + constant)) / (math.sqrt(lineSlope * lineSlope + 1 * 1))
                    writer.writerow([p.sampleID, p.dateTime, p.sourceCode, str(p.lat), str(p.long), p.altitude, p.speed, p.heading, p.linkPVID, p.linkNode, p.direction, str(p.distFromRef), str(p.distFromLink)])

    print("\nMAP MATCHING FINISHED")
    return 'Partition6467MatchedPoints.csv'

def calculate_slope(file):
    data = []
    with open('Partition6467MatchedPoints_Slopes.csv', 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["sampleID", "dateTime", "sourceCode", "Latitude", "Longitude", "Altitude", "Speed", "Heading", "linkPVID", "linkRefNode", "direction", "distFromNode", "distFromLinkLine", "slope"])
        with open(file) as probe_csvfile:
            reader = csv.reader(probe_csvfile)
            rows = list(reader)
            for i in range(len(rows)):
                if (i == 0):
                    continue
                if (i < len(rows)-1):
                    currProbe = rows[i]
                    nextProbe = rows[i+1]
                    distance = latlon_toMeters(float(nextProbe[3]),float(nextProbe[4]),float(currProbe[3]),float(currProbe[4]))
                    altitude_diff = float(nextProbe[5]) - float(currProbe[5])
                    degree = "N/A"
                    if (distance != 0):
                        slope = float(altitude_diff / distance)
                        degree = math.degrees(math.atan(slope))
                    writer.writerow([currProbe[0], currProbe[1], currProbe[2], currProbe[3], currProbe[4], currProbe[5], currProbe[6], currProbe[7], currProbe[8], currProbe[9], currProbe[10], currProbe[11], currProbe[12], degree])


### SAVING AND LOADING PROBE AND LINK DATA (NOTE: NOT THAT MUCH FASTER THAN JUST CREATING THE DATA SETS AGAIN)###
# def save_data(probe_data, link_data):
#     probe_filehandler = open('./saved_probe_data.txt', 'wb')
#     link_filehandler = open('./saved_link_data.txt', 'wb')
#     pickle.dump(probe_data, probe_filehandler)
#     pickle.dump(link_data, link_filehandler)
#
# def load_data():
#     probe_filehandler = open('./saved_probe_data.txt', 'rb')
#     link_filehandler = open('./saved_link_data.txt', 'rb')
#     return pickle.load(probe_filehandler), pickle.load(link_filehandler)

def create_link_data_points(shapeInfo):
    parsedPoints = []
    points = shapeInfo.split("|")
    for point in points:
        coordinates = point.split("/")
        parsedPoints.append(LinkDataPoint(coordinates[0], coordinates[1]))
    return parsedPoints

if __name__ == '__main__':
    if (len(sys.argv) < 3):
        print("Please supply the probe points data and the link data. Usage: python3 map_matching.py [probe_data.csv] [link_data.csv]")
        exit(0)

    ### FIRST TIME RUNNING ###
    (probe_data, link_data) = create_data(sys.argv[1], sys.argv[2])
    output_file = map_match(probe_data, link_data)
    calculate_slope(output_file)
    #save_data(probe_data, link_data)

    ### LOADING SAVED PROBE AND LINK DATA ###
    #(probe_data, link_data) = load_data()
    #print(len(probe_data), len(link_data))
