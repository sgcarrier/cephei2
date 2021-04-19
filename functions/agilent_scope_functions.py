import visa, sys
import time

class delayLineAgilent():


    def __init__(self, VISA_ADDRESS, dataFolder, setupFile):
        try:
            # Create a connection (session) to the instrument
            self.resourceManager = visa.ResourceManager('@py')
            self.session = self.resourceManager.open_resource(VISA_ADDRESS)
        except visa.Error as ex:
            print("Couldn't connect to '%s', exiting now..." % VISA_ADDRESS)
            sys.exit()

        # For Serial and TCP/IP socket connections enable the read Termination Character, or read's will timeout
        if self.session.resource_name.startswith('ASRL') or self.session.resource_name.endswith('SOCKET'):
            self.session.read_termination = '\n'

        # Send Clear, *IDN? and read the response
        self.session.write("*CLS")
        self.session.write('*IDN?')
        self.idn = self.session.read()

        print('*IDN? returned: %s' % self.idn.rstrip('\n'))

        self.setupFile = setupFile
        self.dataFolder = dataFolder

        # Check if data folder exists and create it if required
        self.session.write(":DISK:DIR? \"" + dataFolder + "\"")
        dir_exists = self.session.read()
        if dir_exists == 0:
            self.session.write(":DISK:MDIR \"" + dataFolder + "\"")

    def __del__(self):
        # Close the connection to the instrument
        self.session.close()
        self.resourceManager.close()
        print('Done.')


    def start_acq(self, numberOfHits, histFilename):

        setupCommand = ":DISK:LOAD \"" + self.setupFile + "\""

        # Reset the measurements
        self.session.write(setupCommand)

        n_hits = 0

        while n_hits < numberOfHits:
            # Wait a bit
            time.sleep(0.5)


            # Get the number of bins in the histogram
            self.session.write(":MEAS:HIST:HITS? HIST")
            n_hits = float(self.session.read())

            # If nothing is appening
            if n_hits < 10:
                print("Nothing happening, skipping")
                break

        # Stopping scope, acquisition is done
        self.session.write(":STOP")

        # Save an image of the data, the histogram as a CSV
        self.session.write(":DISK:SAVE:IMAG \"" + self.dataFolder + "/" + histFilename + "\",PNG")
        self.session.write(":DISK:SAVE:WAV HIST,\"" + self.dataFolder + "/" + histFilename + "_hist" + "\", CSV, ON")

        # Getting Standard deviation from histogram
        self.session.write(":MEAS:HIST:STDD? HIST")
        std_dev = float(self.session.read())

        # Getting Mean from histogram
        self.session.write(":MEAS:HIST:MEAN? HIST")
        mean = float(self.session.read())

        return n_hits, mean, std_dev
