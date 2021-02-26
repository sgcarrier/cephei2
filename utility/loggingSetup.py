import logging
import sys, os, time


def loggingSetup(name, level, logPath="/tmp/log"):
    # Setup logger
    root = logging.getLogger()
    root.setLevel(level)

    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)
    formatter = logging.Formatter('%(levelname)s :: %(asctime)s :: %(name)s :: %(funcName)s :: %(message)s')
    handler.setFormatter(formatter)

    try:
        os.mkdir(logPath)
    except FileExistsError:
        # directory already exists
        pass
    except OSError:
        print("ERROR :: Could not create log directory, using local directory instead.")
        logPath = "./"

    fileName = str(name) + "_" + time.strftime("%Y%m%d-%H%M%S")
    fileHandler = logging.FileHandler("{0}/{1}.log".format(logPath, fileName))
    fileHandler.setFormatter(formatter)

    root.addHandler(fileHandler)
    root.addHandler(handler)