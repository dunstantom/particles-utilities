import os
import argparse
import math

# Field Names
classNumberField = "_rlnClassNumber"
angleField = "_rlnAnglePsi"
originXField = "_rlnOriginX"
originYField = "_rlnOriginY"
fieldList = (angleField, originXField, originYField, classNumberField)

# get star and translation file names from command line
parser = argparse.ArgumentParser(description='Origin Translation for .star files')
parser.add_argument('star', metavar='<star file>', nargs=1,
                    help='.the star file to be corrected')
parser.add_argument('translate', metavar='<translation file>', nargs=1,
                    help='a CSV file with two columns, the class number and the x-axis translation value')

args = parser.parse_args()

# read in translation file
translate_dict = {}
with open(args.translate[0], 'r') as tf:
    for line in tf:
        if len(line) > 0:
            (classNumber, classTranslation) = [x.strip() for x in line.split(',')]
            translate_dict[int(classNumber)] = float(classTranslation)

# open output file
column_dict = {}
missing_classes = {}
class_count = {}
outputFile = os.path.splitext(args.star[0])[0] + ".corrected.star"
verifiedHeader = False

with open(outputFile, 'w') as starOut:
    with open(args.star[0], 'r') as starIn:
        # parse headers
        for line in starIn:
            # parse headers
            if len(line.strip()) == 0 or line[0] != ' ':
                # add header to output file as well
                starOut.write(line)
                # store column names
                if line[0] == '_':
                    (columnName, columnIndex) = [x.strip() for x in line.split('#')]
                    column_dict[columnName] = int(columnIndex) - 1 # columnIndex is base-1 and needs to be base-0

            # verify header after parsing
            elif not verifiedHeader:
                parsedFields = [x for x in fieldList if x in column_dict]
                # check if all fields were found in header
                if len(fieldList) != len(parsedFields):
                    print "Error: Only found the following fields in the header:"
                    print '\n'.join(parsedFields)
                    exit()
                verifiedHeader = True

            # process entries
            else:
                particle = [x.strip() for x in line.split()]
                # get class number
                particleClassNumber = int(particle[column_dict[classNumberField]])
                # look for translation number
                if particleClassNumber not in translate_dict:
                    # track missed particles
                    missing_classes[particleClassNumber] = missing_classes.get(particleClassNumber, 0) + 1
                else:
                    # get particle rotation
                    particleRotation = float(particle[column_dict[angleField]])
                    # get translation
                    particleTranslation = translate_dict[particleClassNumber]
                    # apply reverse rotation to translation
                    particleRotationRadians = math.radians(-1.0 * particleRotation)
                    particleTranslationX = particleTranslation * math.cos(particleRotationRadians)
                    particleTranslationY = particleTranslation * math.sin(particleRotationRadians)
                    # apply translation
                    translatedParticleX = float(particle[column_dict[originXField]]) + particleTranslationX
                    particle[column_dict[originXField]] = str(translatedParticleX)
                    translatedParticleY = float(particle[column_dict[originYField]]) + particleTranslationY
                    particle[column_dict[originYField]] = str(translatedParticleY)
                    # track classNumber particles
                    class_count[particleClassNumber] = class_count.get(particleClassNumber, 0) + 1

                # output line
                starOut.write(' '.join(particle) + "\n")


for classNumber in class_count.keys():
    print "Corrected {0} particles in class number {1}".format(class_count[classNumber], classNumber)

for classNumber in missing_classes.keys():
    print "Skipped {0} particles from class number {1}; no translation provided".format(missing_classes[classNumber], classNumber)