# coding=utf-8
import pickle
from ICYSHSR1_transfer_function_ideal import TransferFunctions


# TDC_VISUALIZED = 2
TOTAL_PERIOD = 4000




def main():
    number_of_tdc = 16
    out_filename_prefix = "H5_M1_1v28"
    # ARR 0
    # Fichier 40 go
    # filename = "/home2/cars2019/Documents/DATA/NON_CORR_TEST_ALL-20210324-210211.hdf5"
    filename = "/home/simonc/Documents/Programming/cephei2/GUI/H5_non_corr_data.hdf5"
    path = "CHARTIER/H5/NON_CORR/RAW"

    # Fichier Mich
    #filename = "./data/ARR0/NON_CORR_TEST_ALL-20210414-212030.hdf5"
    #path = "CHARTIER/ASIC0/TDC/M0/ALL_TDC_ACTIVE/PLL/FAST_255/SLOW_250/NON_CORR/EXT/ADDR_ALL/RAW"
    # ARR 1
    #filename = "./data/ARR1/NON_CORR_TEST_ALL-20210319-203909.hdf5"
    calcCoef(number_of_tdc, out_filename_prefix, filename, path)

def calcCoef(number_of_tdc, out_filename_prefix, filename, path):
    coefficients_lin = {}
    coefficients_lin_bias = {}
    coefficients_lin_bias_slope = {}
    for i in range(number_of_tdc):
        tf = TransferFunctions(filename=filename, basePath=path, pixel_id=i*4, filter_lower_than=0.05)

        tf.linear_regression_algorithm()
        coefficients_lin[i] = tf.get_coefficients()

        tf.linear_regression_algorithm(True, False)
        coefficients_lin_bias[i] = tf.get_coefficients()

        tf.linear_regression_algorithm(True, True)
        coefficients_lin_bias_slope[i] = tf.get_coefficients()

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

