from visualisation.CoarseFineHeatmap import *
from visualisation.basicHistogram import *
from visualisation.skewCalc import *

from matplotlib.collections import LineCollection
from matplotlib import colors as mcolors
import os

import logging
logging.basicConfig(level=logging.DEBUG)

_logger = logging.getLogger(__name__)





class AllNonCorrelatedTest():
    
    def __init__(self, filename, basepath, HEAD_ID, ARRAY, PLL_FAST, PLL_SLOW, DAC_FAST, DAC_SLOW, MODE, saveFileTypes):
        """USER SET"""
        self.filename=filename
        self.basepath=basepath
        
        self.HEAD_ID = HEAD_ID
        self.ARRAY = ARRAY
        self.PLL_FAST = PLL_FAST
        self.PLL_SLOW = PLL_SLOW
        self.DAC_FAST = DAC_FAST
        self.DAC_SLOW = DAC_SLOW
        
        self.MODE = MODE
        
        self.saveFileTypes = saveFileTypes

        self.genSettings()



    def genSettings(self):
        """ GENERATED SETTINGS """
        
        if (self.PLL_FAST is not None) and (self.PLL_SLOW is not None):
            self.PLL_FAST_str = str(self.PLL_FAST).replace('.', 'v')
            self.PLL_SLOW_str = str(self.PLL_SLOW).replace('.', 'v')
            self.prefix = f"H{self.HEAD_ID}_M{self.ARRAY}_PLL_F{self.PLL_FAST_str}_S{self.PLL_SLOW_str}_"
            self.MODE = "PLL"
            self.folderPath = f"ASIC{self.HEAD_ID}/M{self.ARRAY}/{self.MODE}/FAST_{self.PLL_FAST_str}/SLOW_{self.PLL_SLOW_str}/"
        elif (self.DAC_FAST is not None) and (self.DAC_SLOW is not None):
            self.DAC_FAST_str = str(self.DAC_FAST).replace('.', 'v')
            self.DAC_SLOW_str = str(self.DAC_SLOW).replace('.', 'v')
            self.prefix = f"H{self.HEAD_ID}_M{self.ARRAY}_DAC_F{self.DAC_FAST_str}_S{self.DAC_SLOW_str}_"
            self.MODE = "DAC"
            self.folderPath = f"ASIC{self.HEAD_ID}/M{self.ARRAY}/{self.MODE}/FAST_{self.DAC_FAST_str}/SLOW_{self.DAC_SLOW_str}/"
        else:
            exit("No PLL or DAC settings set correctly")
        
        
        if self.ARRAY == 0:
            self.NUM_OF_TDCS = 49
        else:
            self.NUM_OF_TDCS = 16
        
        
        for type in self.saveFileTypes:
            os.makedirs(self.folderPath+type, exist_ok=True)
    
    def run_coarse_fine_heatmap(self):
        _logger.info(" ==== Maximum coarse and fine counters ==== ")
    
        if self.MODE == "DAC":
            title = f"Coarse and Fine Resolution Heatmap \n Head \#{self.HEAD_ID}, ARRAY \#{self.ARRAY}, DAC FAST={self.DAC_FAST}V, SLOW={self.DAC_SLOW}V"
        else:
            title = f"Coarse and Fine Resolution Heatmap \n Head \#{self.HEAD_ID}, ARRAY \#{self.ARRAY}, PLL FAST={self.PLL_FAST}MHz, SLOW={self.PLL_SLOW}MHz"
    
        BH = CoarseFineHeatmap()
        BH.heatmap_from_transfer_function(filename=self.filename,
                                basePath=self.basepath,
                                formatNum=0,
                                figureNum=1,
                                numberOfTDCs=self.NUM_OF_TDCS,
                                title=title)
    
        suffix = "Coarse_Fine_Heatmap"
        plt.subplots_adjust(top=0.9, hspace=0.35)
        for type in self.saveFileTypes:
            plt.savefig(self.folderPath+type+'/'+self.prefix+suffix+"."+type)
    
        _logger.info("Maximum coarse and fine counters DONE")
    
    def run_density_function(self):
        _logger.info(" ==== Density function ====  ")
    
    
        BH = BasicHistogram()
    
        for tdcNum in range(self.NUM_OF_TDCS):
    
    
            if self.MODE == "DAC":
                title = f"Density Code for TDC \#{tdcNum} \n Head \#{self.HEAD_ID}, ARRAY \#{self.ARRAY}, DAC FAST={self.DAC_FAST}V, SLOW={self.DAC_SLOW}V"
            else:
                title = f"Density Code for TDC \#{tdcNum} \n Head \#{self.HEAD_ID}, ARRAY \#{self.ARRAY}, PLL FAST={self.PLL_FAST}MHz, SLOW={self.PLL_SLOW}MHz"
    
            BH.hist_norm(filename=self.filename,
                         basePath=self.basepath,
                         formatNum=0,
                         tdcNums=[tdcNum],
                         title=title)
    
            suffix = f"Density_code_TDC{tdcNum}"
            plt.subplots_adjust(top=0.9, hspace=0.25)
            for type in self.saveFileTypes:
                plt.savefig(self.folderPath + type + '/' + self.prefix + suffix + "." + type)
    
            plt.close("all")
    
        _logger.info("Density function DONE")
    
    
    def run_wide_density_function(self):
        _logger.info(" ==== Wide Density function ====  ")
    
    
        BH = BasicHistogram()
    
        for tdcNum in range(self.NUM_OF_TDCS):
            if self.MODE == "DAC":
                title = f"Density Code for TDC \#{tdcNum} \n Head \#{self.HEAD_ID}, ARRAY \#{self.ARRAY}, DAC FAST={self.DAC_FAST}V, SLOW={self.DAC_SLOW}V"
            else:
                title = f"Density Code for TDC \#{tdcNum} \n Head \#{self.HEAD_ID}, ARRAY \#{self.ARRAY}, PLL FAST={self.PLL_FAST}MHz, SLOW={self.PLL_SLOW}MHz"
    
            BH.wide_hist_from_transfer_function(filename=self.filename,
                                                basePath=self.basepath,
                                                formatNum=0,
                                                tdcNum=tdcNum,
                                                title=title)
    
            suffix = f"Wide_Density_code_TDC_{tdcNum}_thres0_5"
            plt.subplots_adjust(top=0.8)
            for type in self.saveFileTypes:
                plt.savefig(self.folderPath + type + '/' + self.prefix + suffix + "." + type)
    
            plt.close("all")
    
            BH.wide_hist_from_transfer_function(filename=self.filename,
                                                basePath=self.basepath,
                                                formatNum=0,
                                                tdcNum=tdcNum,
                                                maxFineMethod="ZeroMode",
                                                title=title)
    
            suffix = f"Wide_Density_code_TDC_{tdcNum}_ZeroMode"
            plt.subplots_adjust(top=0.8)
            for type in self.saveFileTypes:
                plt.savefig(self.folderPath + type + '/' + self.prefix + suffix + "." + type)
    
            plt.close("all")
    
    
        _logger.info("Wide Density function DONE")
    
    
    def run_transfer_function(self):
        _logger.info(" ==== Transfer Function ====  ")
        for tdcNum in range(self.NUM_OF_TDCS):
            if self.MODE == "DAC":
                title = f"Transfer Functions for TDC \#{tdcNum} \n Head \#{self.HEAD_ID}, ARRAY \#{self.ARRAY}, DAC FAST={self.DAC_FAST}V, SLOW={self.DAC_SLOW}V"
            else:
                title = f"Transfer Functions  for TDC \#{tdcNum} \n Head \#{self.HEAD_ID}, ARRAY \#{self.ARRAY}, PLL FAST={self.PLL_FAST}MHz, SLOW={self.PLL_SLOW}MHz"
            tf = TransferFunctions(filename=self.filename,
                                   basePath=self.basepath,
                                   pixel_id=tdcNum*4,
                                   filter_lower_than=0.05)
            ideal = tf.ideal_tf
            lin_reg = tf.linear_regression_algorithm()
    
            lin_bias_reg = tf.linear_regression_algorithm(True, False)
    
            lin_bias_slope_reg = tf.linear_regression_algorithm(True, True)
    
            fig = plt.figure(tdcNum, figsize=(10,10))
            fig.suptitle(title)
            ax = plt.subplot(1, 1, 1)
            ax.plot(ideal, label="Ideal")
            ax.plot(lin_reg, label="Linear Regression", alpha=0.6, linestyle="--")
            ax.plot(lin_bias_reg, label="Linear+Bias", alpha=0.6, linestyle=":")
            ax.plot(lin_bias_slope_reg, label="Linear+Bias+Slope", alpha=0.6, linestyle="-.")
            plt.xlabel("TDC Code")
            plt.ylabel("Timestamp (ps)")

    
            plt.legend(loc='upper right')
    
            suffix = f"Transfer_Function_TDC{tdcNum}"
            plt.subplots_adjust(top=0.9, hspace=0.25)
            for type in self.saveFileTypes:
                plt.savefig(self.folderPath + type + '/' + self.prefix + suffix + "." + type)
    
            plt.close('all')

            if self.MODE == "DAC":
                title = f"Transfer Functions correction performance for TDC \#{tdcNum} \n Head \#{self.HEAD_ID}, ARRAY \#{self.ARRAY}, DAC FAST={self.DAC_FAST}V, SLOW={self.DAC_SLOW}V"
            else:
                title = f"Transfer Functions correction performance for TDC \#{tdcNum} \n Head \#{self.HEAD_ID}, ARRAY \#{self.ARRAY}, PLL FAST={self.PLL_FAST}MHz, SLOW={self.PLL_SLOW}MHz"


            fig = plt.figure(tdcNum, figsize=(10, 10))
            fig.suptitle(title)
            ax = plt.subplot(1, 1, 1)

            plt.axhline(y=0, linestyle='-', label="Ideal")
            ax.plot((lin_reg - ideal), label="Linear Regression Error", alpha=0.9, linestyle="--")
            ax.plot((lin_bias_reg - ideal), label="Linear+Bias Error", alpha=0.9, linestyle=":")
            ax.plot((lin_bias_slope_reg - ideal), label="Linear+Bias+Slope Error", alpha=0.9, linestyle="-.")

            plt.xlabel("TDC Code")
            plt.ylabel("Error from ideal (ps)")

            plt.legend(loc='upper right')

            suffix = f"Transfer_Function_corr_perf_TDC{tdcNum}"
            plt.subplots_adjust(top=0.9, hspace=0.25)
            for type in self.saveFileTypes:
                plt.savefig(self.folderPath + type + '/' + self.prefix + suffix + "." + type)

            plt.close('all')

    
    def run_skew_correction(self):
        skewCalc(filename, basepath, 0, figureNum=1, numberOfTDCs=self.NUM_OF_TDCS, title=None)
    
    
    """ Window size """
    def run_window_size(self):
        pass


    def run_DNL_INL(self):
        _logger.info(" ==== DNL and INL ====  ")

        if self.MODE == "DAC":
            title = f"Differential nonlinearity \n Head \#{self.HEAD_ID}, ARRAY \#{self.ARRAY}, DAC FAST={self.DAC_FAST}V, SLOW={self.DAC_SLOW}V"
        else:
            title = f"Differential nonlinearity \n Head \#{self.HEAD_ID}, ARRAY \#{self.ARRAY}, PLL FAST={self.PLL_FAST}MHz, SLOW={self.PLL_SLOW}MHz"

        fig = plt.figure(0, figsize=(14, 10))
        fig.suptitle(title)
        ax = plt.subplot(1, 1, 1)
        plt.xlabel("Timestamp (ps)")
        plt.ylabel("DNL (LSBs)")
        DNL_lines = []
        INL_lines = []

        Dmax_y = 0
        Dmin_y = 0
        Imax_y = 0
        Imin_y = 0

        for tdcNum in range(self.NUM_OF_TDCS):

            tf = TransferFunctions(filename=self.filename,
                                   basePath=self.basepath,
                                   pixel_id=tdcNum * 4,
                                   filter_lower_than=0.05)

            DNL, INL, LSB, c = tf.get_DNL_INL_LSB()

            DNL_lines.append(list(zip((np.arange(0, c, 1)) * LSB,  DNL)))

            INL_lines.append(list(zip((np.arange(0, c, 1)) * LSB,  INL)))

            if np.max(DNL) > Dmax_y:
                Dmax_y = np.max(DNL)
            if np.min(DNL) < Dmin_y:
                Dmin_y = np.min(DNL)

            if np.max(INL) > Imax_y:
                Imax_y = np.max(INL)
            if np.min(INL) < Imin_y:
                Imin_y = np.min(INL)

        line_segments = LineCollection(DNL_lines,
                                       linewidths=(1.0),
                                       linestyles='solid', alpha=0.8, cmap='gnuplot')
        line_segments.set_array(np.arange(0,self.NUM_OF_TDCS, 1))
        ax.add_collection(line_segments)
        axcb = fig.colorbar(line_segments)
        axcb.set_label('TDC Number')
        ax.set_xlim(0, 4100)
        ax.set_ylim(Dmin_y, Dmax_y)

        plt.legend(loc='upper right')

        suffix = f"DNL"
        plt.subplots_adjust(top=0.9, hspace=0.25)
        for type in self.saveFileTypes:
            plt.savefig(self.folderPath + type + '/' + self.prefix + suffix + "." + type)

        plt.close('all')

        if self.MODE == "DAC":
            title = f"Integral nonlinearity \n Head \#{self.HEAD_ID}, ARRAY \#{self.ARRAY}, DAC FAST={self.DAC_FAST}V, SLOW={self.DAC_SLOW}V"
        else:
            title = f"Integral nonlinearity \n Head \#{self.HEAD_ID}, ARRAY \#{self.ARRAY}, PLL FAST={self.PLL_FAST}MHz, SLOW={self.PLL_SLOW}MHz"

        fig = plt.figure(0, figsize=(14, 10))
        fig.suptitle(title)
        ax = plt.subplot(1, 1, 1)
        plt.xlabel("Timestamp (ps)")
        plt.ylabel("INL (LSBs)")

        line_segments = LineCollection(INL_lines,
                                       linewidths=(1.0),
                                       linestyles='solid', alpha=0.8, cmap='gnuplot')
        line_segments.set_array(np.arange(0, self.NUM_OF_TDCS, 1))
        ax.add_collection(line_segments)
        axcb = fig.colorbar(line_segments)
        axcb.set_label('TDC Number')
        ax.set_xlim(0, 4100)
        ax.set_ylim(Imin_y, Imax_y)

        plt.legend(loc='upper right')

        suffix = f"INL"
        plt.subplots_adjust(top=0.9, hspace=0.25)
        for type in self.saveFileTypes:
            plt.savefig(self.folderPath + type + '/' + self.prefix + suffix + "." + type)

        plt.close('all')

    
    def run_correlation_matrix(self):
        _logger.info("Correlation Matrix")
    
    
        if self.MODE == "DAC":
            title = f"Correlation Matrix \n Head \#{self.HEAD_ID}, ARRAY \#{self.ARRAY}, DAC FAST={self.DAC_FAST}V, SLOW={self.DAC_SLOW}V"
        else:
            title = f"Correlation Matrix \n Head \#{self.HEAD_ID}, ARRAY \#{self.ARRAY}, PLL FAST={self.PLL_FAST}MHz, SLOW={self.PLL_SLOW}MHz"
    
        BH = CoarseFineHeatmap()
        BH.covariance_with_filtering(filename=self.filename,
                                     basePath=self.basepath,
                                     formatNum=0,
                                     figureNum=10,
                                     numberOfTDCs=self.NUM_OF_TDCS,
                                     title=title)
    
        suffix = f"Correlation_Matrix"
        plt.subplots_adjust(top=0.8, hspace=0.25)
        for type in self.saveFileTypes:
            plt.savefig(self.folderPath + type + '/' + self.prefix + suffix + "." + type)
    
        _logger.info("Correlation Matrix DONE")
    

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)

    matplotlib.use("pgf")
    matplotlib.rcParams.update({
        "pgf.texsystem": "pdflatex",
        'font.family': 'serif',
        'text.usetex': True,
        'pgf.rcfonts': False,
    })

    CT = AllNonCorrelatedTest(
        filename="/home/simonc/Documents/DATA/18_mars_2022/H7_M0_DAC_NON_CORR.hdf5",
        basepath="/CHARTIER/ASIC7/TDC/M0/ALL_TDC_ACTIVE/DAC/FAST_1.278/SLOW_1.263/NON_CORR/EXT/ADDR_ALL/RAW",
        HEAD_ID=7,
        ARRAY=0,
        PLL_FAST=None,
        PLL_SLOW=None,
        DAC_FAST=1.278,
        DAC_SLOW=1.263,
        MODE="DAC",
        saveFileTypes=["pgf"])

    # CT.run_wide_density_function()
    # CT.run_coarse_fine_heatmap()
    # CT.run_density_function()
    #CT.run_transfer_function()
    # CT.run_correlation_matrix()
    CT.run_DNL_INL()

    #
    # CT = AllNonCorrelatedTest(
    #     filename="/CMC/partage/GRAMS/DATA/ICYSHSR1/ASIC_07/raw_data/18_mars_2022/H7_M1_DAC_NON_CORR.hdf5",
    #     basepath="/CHARTIER/ASIC7/TDC/M1/ALL_TDC_ACTIVE/DAC/FAST_1.278/SLOW_1.263/NON_CORR/EXT/ADDR_ALL/RAW",
    #     HEAD_ID=7,
    #     ARRAY=1,
    #     PLL_FAST=None,
    #     PLL_SLOW=None,
    #     DAC_FAST=1.278,
    #     DAC_SLOW=1.263,
    #     MODE="DAC",
    #     saveFileTypes=["svg", "png"])
    #
    # CT.run_wide_density_function()
    # CT.run_coarse_fine_heatmap()
    # CT.run_density_function()
    # CT.run_transfer_function()
    # CT.run_correlation_matrix()
    #
    # CT = AllNonCorrelatedTest(
    #     filename="/CMC/partage/GRAMS/DATA/ICYSHSR1/ASIC_07/raw_data/18_mars_2022/H7_M0_PLL_NON_CORR.hdf5",
    #     basepath="/CHARTIER/ASIC7/TDC/M0/ALL_TDC_ACTIVE/PLL/FAST_255/SLOW_250/NON_CORR/EXT/ADDR_ALL/RAW",
    #     HEAD_ID=7,
    #     ARRAY=0,
    #     PLL_FAST=255,
    #     PLL_SLOW=250,
    #     DAC_FAST=None,
    #     DAC_SLOW=None,
    #     MODE="PLL",
    #     saveFileTypes=["svg", "png"])
    #
    # CT.run_wide_density_function()
    # CT.run_coarse_fine_heatmap()
    # CT.run_density_function()
    # CT.run_transfer_function()
    # CT.run_correlation_matrix()
    #
    # CT = AllNonCorrelatedTest(
    #     filename="/CMC/partage/GRAMS/DATA/ICYSHSR1/ASIC_07/raw_data/18_mars_2022/H7_M1_PLL_NON_CORR.hdf5",
    #     basepath="/CHARTIER/ASIC7/TDC/M1/ALL_TDC_ACTIVE/PLL/FAST_255/SLOW_250/NON_CORR/EXT/ADDR_ALL/RAW",
    #     HEAD_ID=7,
    #     ARRAY=1,
    #     PLL_FAST=255,
    #     PLL_SLOW=250,
    #     DAC_FAST=None,
    #     DAC_SLOW=None,
    #     MODE="PLL",
    #     saveFileTypes=["svg", "png"])
    #
    # CT.run_wide_density_function()
    # CT.run_coarse_fine_heatmap()
    # CT.run_density_function()
    # CT.run_transfer_function()
    # CT.run_correlation_matrix()

