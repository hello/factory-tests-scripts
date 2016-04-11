import os
import tarfile
#NOTE: This is really only used for initially creating tar files with a properly organized directory structure.
#Since this has been done you should probably be using the jabil html thingy to properly add to files and whatnot
rootDir = '/Users/brandon/proddata'
os.chdir(rootDir)
rootOutput = '/Users/brandon/testTars'

productLookup ={'Bottom Board':'bottomBoard',
                'LED Board':'ledBoard',
                'Middle Board':'middleBoard',
                'Morpheus':'morpheus',
                'Pill':'pill',
                'Pill Board':'pillBoard',
                'Top Board':'topBoard'}

for productName in os.listdir(rootDir):
    productDir = os.path.join(rootDir, productName)
    if not os.path.isdir(productDir):
        continue
    if productName == "Unknown" or productName == "html":
        continue
    for yearName in os.listdir(productDir):
        yearDir = os.path.join(productDir,yearName)
        if not os.path.isdir(yearDir):
            continue
        for monthName in os.listdir(yearDir):
            monthDir = os.path.join(yearDir, monthName)
            if not os.path.isdir(monthDir):
                continue
            for dayName in os.listdir(monthDir):
                dayDir = os.path.join(monthDir,dayName)
                if not os.path.isdir(dayDir):
                    continue
                tarName = "%s%s%s_%s.tar.gz" % (yearName,monthName,dayName,productLookup[productName])
                manifestName = "%s%s%s_%s.manifest" % (yearName,monthName,dayName,productLookup[productName])
                outputFolder = os.path.join(rootOutput,yearName,monthName,dayName)
                try:
                    os.makedirs(outputFolder)
                except OSError:
                    pass
                with tarfile.open(os.path.join(outputFolder,tarName),'w:gz') as tar:
                    with open(os.path.join(outputFolder,manifestName),'w') as mani:
                        for fileName in os.listdir(dayDir):
                            if fileName.endswith(".htm"):
                                tar.add(os.path.join(productName,yearName,monthName,dayName,fileName))
                                mani.write(fileName+'\n')

                print "%s complete" % tarName

