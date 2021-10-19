# coding=utf-8
import pickle
from processing.ICYSHSR1_transfer_function_ideal import TransferFunctions
from matplotlib import pyplot as plt
from matplotlib.ticker import MaxNLocator

# TDC_VISUALIZED = 2
TOTAL_PERIOD = 4000




def main():
    number_of_tdc = 16
    out_filename_prefix = "H7_M1_255"
    # ARR 0
    # Fichier 40 go
    #filename = "/home2/cars2019/Documents/DATA/NON_CORR_TEST_ALL-20210324-210211.hdf5"
    filename = "/CMC/partage/GRAMS/DATA/ICYSHSR1/ASIC_07/raw_data/NON_CORR_M1_H7.hdf5"
    path = "CHARTIER/ASIC7/TDC/M1/ALL_TDC_ACTIVE/PLL/FAST_255/SLOW_250/NON_CORR/EXT/ADDR_ALL/RAW"


    # Fichier Pascal
    #filename = "./data/ARR0/EXP_NON_CORR_CALIB_COEF.hdf5"
    #path = "CHARTIER/ASIC0/TDC/M0/ALL_TDC_ACTIVE/PLL/FAST_255/SLOW_250/NON_CORR/EXT/ADDR_ALL/RAW"

    # Fichier Mich
    #filename = "./data/ARR0/NON_CORR_TEST_ALL-20210414-212030.hdf5"
    #path = "CHARTIER/ASIC0/TDC/M0/ALL_TDC_ACTIVE/PLL/FAST_255/SLOW_250/NON_CORR/EXT/ADDR_ALL/RAW"
    # ARR 1
    #filename = "./data/ARR1/NON_CORR_TEST_ALL-20210319-203909.hdf5"
    coefficients_lin = {}
    coefficients_lin_bias = {}
    coefficients_lin_bias_slope = {}
    for i in range(number_of_tdc):
        tf = TransferFunctions(filename=filename, basePath=path, pixel_id=i*4, filter_lower_than=0.05)

        tf.linear_regression_algorithm()
        coefficients_lin[i] = tf.get_coefficients()

        tf.linear_regression_algorithm(True, False, False)
        coefficients_lin_bias[i] = tf.get_coefficients()

        tf.linear_regression_algorithm(True, True, False)
        coefficients_lin_bias_slope[i] = tf.get_coefficients()

    plt.figure(1)
    ax = plt.subplot(1, 1, 1)
    ax.plot(tf.ideal_tf, label="Ideal")
    ax.plot(tf.bias_reg, label="Bias")
    ax.plot(tf.lin_reg, label="Linear")
    ax.plot(tf.bias_slope_reg, label="Bias+Slope")
    ax.plot(tf.tf_recon_alt, label="Smooth_trans")

    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, labels)

    plt.show()


    print(coefficients_lin)
    with open(out_filename_prefix+'_lin.pickle', 'wb') as f:
        pickle.dump(coefficients_lin, f)

    print(coefficients_lin_bias)
    with open(out_filename_prefix+'_lin_bias.pickle', 'wb') as f:
        pickle.dump(coefficients_lin_bias, f)

    print(coefficients_lin_bias_slope)
    with open(out_filename_prefix+'_lin_bias_slope.pickle', 'wb') as f:
        pickle.dump(coefficients_lin_bias_slope, f)

main()
