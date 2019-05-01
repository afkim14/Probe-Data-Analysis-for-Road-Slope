import csv
import pickle

class ProbeDataPoint:
    def __init__(self, sampleID, dateTime, sourceCode, lat, long, altitude, speed, heading):
        self.sampleID = sampleID
        self.dateTime = dateTime
        self.sourceCode = sourceCode
        self.lat = lat
        self.long = long
        self.altitude = altitude
        self.speed = speed
        self.heading = heading
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
    def __str__(self):
        shapeInfo = "["
        for point in self.shapeInfo[:-1]:
            shapeInfo += str(point) + "\n"
        shapeInfo += "\t\t\t" + str(self.shapeInfo[-1]) + "]"
        return "Link PVID: " + str(self.linkPVID) + "\n" + "\tLength: " + str(self.length) + "\n" + "\tShapeInfo: " + shapeInfo

class LinkDataPoint:
    def __init__(self, lat, long):
        self.lat = lat
        self.long = long
    def __str__(self):
        return "Latitude: " + str(self.lat) + ", Longitude: " + str(self.long)

def create_data(probe_data_file, link_data_file):
    probe_data = []
    link_data = []
    with open(probe_data_file) as probe_csvfile:
        reader = csv.reader(probe_csvfile)
        for row in reader:
            probe_data.append(ProbeDataPoint(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7]))
    with open(link_data_file) as link_csvfile:
        reader = csv.reader(link_csvfile)
        for row in reader:
            link_data.append(LinkData(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[12], row[13], row[14], row[15], row[16]))
    return probe_data, link_data

### SAVING AND LOADING PROBE AND LINK DATA (NOTE: NOT THAT MUCH FASTER THAN JUST CREATING THE DATA SETS AGAIN)###
def save_data(probe_data, link_data):
    probe_filehandler = open('./saved_probe_data.txt', 'wb')
    link_filehandler = open('./saved_link_data.txt', 'wb')
    pickle.dump(probe_data, probe_filehandler)
    pickle.dump(link_data, link_filehandler)

def load_data():
    probe_filehandler = open('./saved_probe_data.txt', 'rb')
    link_filehandler = open('./saved_link_data.txt', 'rb')
    return pickle.load(probe_filehandler), pickle.load(link_filehandler)

def create_link_data_points(shapeInfo):
    parsedPoints = []
    points = shapeInfo.split("|")
    for point in points:
        coordinates = point.split("/")
        parsedPoints.append(LinkDataPoint(coordinates[0], coordinates[1]))
    return parsedPoints

if __name__ == '__main__':
    # if (len(sys.argv) < 3):
    #     print("Please supply the probe points data and the link data. Usage: python3 map_matching.py [probe_data.csv] [link_data.csv]")
    #     exit(0)

    ### FIRST TIME RUNNING ###
    (probe_data, link_data) = create_data("./probe_data_map_matching/Partition6467ProbePoints.csv", "./probe_data_map_matching/Partition6467LinkData.csv")
    #save_data(probe_data, link_data)

    ### LOADING SAVED PROBE AND LINK DATA ###
    #(probe_data, link_data) = load_data()
    #print(len(probe_data), len(link_data))
