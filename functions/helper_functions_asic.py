import time
import numpy as np


class ConstantsASIC:
    # MUX
    SEL_ARRAY_0 = 0
    SEL_ARRAY_1 = 1
    SEL_REGISTER_READ = 2
    # Post processing MUX
    SEL_RAW = 0
    SEL_TIME_CONVERSION = 1
    SEL_SORTED = 2
    SEL_DARK_COUNT_FILTERED = 3
    SEL_BLUE = 4
    SEL_GATED_COUNT = 5
    SEL_GATED_BITMAP = 6
    SEL_GATED_EVENT_DETECT = 7
    SEL_ZPP = 8
    SEL_QKD_ABS_TIMESTAMP = 10
    SEL_QKD_TIME_BIN = 11
    SEL_QKD_DCA_FLAG = 12
    SEL_QKD_AVG_PIXEL_POS = 13
    SEL_QKD_AVG_UNIFORM_TIMESTAMP = 14
    # Trigger type
    TRIG_TIME_DRIVEN = 0
    TRIG_EVENT_DRIVEN = 1
    TRIG_WINDOW_DRIVEN = 0x10


class ASIC:

    def __init__(self, chartier, head_id):
        self.b = chartier
        self.head_id = head_id
        self.c = ConstantsASIC

    # This function doesn't reset multiple chips at the same time.
    def reset(self):
        self.b.ICYSHSR1.GPIO(self.head_id, "REINIT", False)
        time.sleep(1)
        self.b.ICYSHSR1.GPIO(self.head_id, "REINIT", True)
        time.sleep(1)

    # This function doesn't sync multiple chips together.
    def sync(self):
        self.b.ICYSHSR1.GPIO(self.head_id, "SYNC", True)
        time.sleep(1)
        self.b.ICYSHSR1.GPIO(self.head_id, "SYNC", False)

    def read_asic_id(self):
        self.b.ICYSHSR1.OUTPUT_MUX_SELECT(self.head_id, self.c.SEL_REGISTER_READ, 0)
        self.b.ICYSHSR1.ASIC_ID(self.head_id, 0)

    #
    # Register set
    #
    def mux_select(self, array, post_processing):
        self.b.ICYSHSR1.OUTPUT_MUX_SELECT(self.head_id, array, 0)
        self.b.ICYSHSR1.POST_PROCESSING_SELECT(self.head_id, post_processing, 0)

    def set_trigger_type(self, trigger_type):
        self.b.ICYSHSR1.TRIGGER_TYPE(self.head_id, trigger_type, 0)

    def set_time_driven_period(self, read_every):
        self.b.ICYSHSR1.TRIGGER_TIME_DRIVEN_PERIOD(self.head_id, read_every, 0)

    def set_window_size(self, window_size, reference=0):
        self.b.ICYSHSR1.WINDOW(self.head_id, window_size, 0)
        self.b.ICYSHSR1.WINDOW_REFERENCE(self.head_id, reference, 0)

    def set_individual_spad_access(self, individual_access=1):
        self.b.ICYSHSR1.INDIVIDUAL_SPAD_ACCESS(self.head_id, individual_access, 0)

    def set_zpp_interval_width(self, width):
        self.b.ICYSHSR1.DCR_INTERVAL_WIDTH(self.head_id, width, 0)

    def set_zpp_interval_spacing(self, spacing):
        self.b.ICYSHSR1.DCR_INTERVAL_SPACING(self.head_id, spacing, 0)

    def set_integration_time(self, integration_time, column_threshold):
        self.b.ICYSHSR1.EVENT_DETECTION_BIT_INTEGRATION_TIME(self.head_id, integration_time, 0)
        self.b.ICYSHSR1.EVENT_DETECTION_BIT_COLUMN_THRESHOLD(self.head_id, column_threshold, 0)

    def read_untriggered_tdc(self, read_all=True):
        if read_all:
            self.b.ICYSHSR1.READ_UNTRIGGERED_TDCS(self.head_id, 1, 0)
        else:
            self.b.ICYSHSR1.READ_UNTRIGGERED_TDCS(self.head_id, 0, 0)

    def enable_dark_count_reset(self, enabled=True):
        if enabled:
            self.b.ICYSHSR1.PIXELS_DARK_COUNT_RESET_EN(self.head_id, 1, 0)
        else:
            self.b.ICYSHSR1.PIXELS_DARK_COUNT_RESET_EN(self.head_id, 0, 0)

    def set_energy_discrimination(self, time_threshold, photon_order, always_out=1):
        self.b.ICYSHSR1.ENERGY_DISCRIMINATION_TIME_THRESHOLD(self.head_id, time_threshold, 0)
        self.b.ICYSHSR1.ENERGY_DISCRIMINATION_PHOTON_ORDER(self.head_id, photon_order, 0)
        self.b.ICYSHSR1.ENERGY_DISCRIMINATION_ALWAYS_OUTPUT(self.head_id, always_out, 0)

    def set_skew_correction(self, array, pixel_id, skew_correction):
        register_offset = int(pixel_id / 2)
        if array == 0:
            if pixel_id % 2 == 0:
                self.b.ICYSHSR1.SPAD_LOCAL_SKEW_EVEN_0(self.head_id, skew_correction, register_offset)
            else:
                self.b.ICYSHSR1.SPAD_LOCAL_SKEW_ODD_0(self.head_id, skew_correction, register_offset)
        else:
            if pixel_id % 2 == 0:
                self.b.ICYSHSR1.SPAD_LOCAL_SKEW_EVEN_1(self.head_id, skew_correction, register_offset)
            else:
                self.b.ICYSHSR1.SPAD_LOCAL_SKEW_ODD_1(self.head_id, skew_correction, register_offset)

    def set_coarse_correction(self, array, tdc_id, coarse_correction):
        register_offset = int(tdc_id / 2)
        if array == 0:
            if tdc_id % 2 == 0:
                self.b.ICYSHSR1.TDC_LOCAL_CORRECTION_COARSE_EVEN_0(self.head_id, coarse_correction, register_offset)
            else:
                self.b.ICYSHSR1.TDC_LOCAL_CORRECTION_COARSE_ODD_0(self.head_id, coarse_correction, register_offset)
        else:
            if tdc_id % 2 == 0:
                self.b.ICYSHSR1.TDC_LOCAL_CORRECTION_COARSE_EVEN_1(self.head_id, coarse_correction, register_offset)
            else:
                self.b.ICYSHSR1.TDC_LOCAL_CORRECTION_COARSE_ODD_1(self.head_id, coarse_correction, register_offset)

    def set_fine_correction(self, array, tdc_id, fine_correction):
        register_offset = int(tdc_id / 2)
        if array == 0:
            if tdc_id % 2 == 0:
                self.b.ICYSHSR1.TDC_LOCAL_CORRECTION_FINE_EVEN_0(self.head_id, fine_correction, register_offset)
            else:
                self.b.ICYSHSR1.TDC_LOCAL_CORRECTION_FINE_ODD_0(self.head_id, fine_correction, register_offset)
        else:
            if tdc_id % 2 == 0:
                self.b.ICYSHSR1.TDC_LOCAL_CORRECTION_FINE_EVEN_1(self.head_id, fine_correction, register_offset)
            else:
                self.b.ICYSHSR1.TDC_LOCAL_CORRECTION_FINE_ODD_1(self.head_id, fine_correction, register_offset)

    def set_lookup_tables(self, array, tdc_id, bias_lookup, slope_lookup):
        # Pad bias with zeros (16)
        # Pad slope with zeros (16)
        # TODO
        register_offset_bias = tdc_id * 4
        register_offset_slope = tdc_id * 2
        if array == 0:
            for i in range(4):
                self.b.ICYSHSR1.COARSE_BIAS_LOOKUP_TABLE_0_0(self.head_id, bias_lookup[(i*4)+0], register_offset_bias)
                self.b.ICYSHSR1.COARSE_BIAS_LOOKUP_TABLE_1_0(self.head_id, bias_lookup[(i*4)+1], register_offset_bias)
                self.b.ICYSHSR1.COARSE_BIAS_LOOKUP_TABLE_2_0(self.head_id, bias_lookup[(i*4)+2], register_offset_bias)
                self.b.ICYSHSR1.COARSE_BIAS_LOOKUP_TABLE_3_0(self.head_id, bias_lookup[(i*4)+3], register_offset_bias)

            for i in range(2):
                self.b.ICYSHSR1.COARSE_SLOPE_LOOKUP_TABLE_0_0(self.head_id, slope_lookup[(i*8)+0], register_offset_slope)
                self.b.ICYSHSR1.COARSE_SLOPE_LOOKUP_TABLE_1_0(self.head_id, slope_lookup[(i*8)+1], register_offset_slope)
                self.b.ICYSHSR1.COARSE_SLOPE_LOOKUP_TABLE_2_0(self.head_id, slope_lookup[(i*8)+2], register_offset_slope)
                self.b.ICYSHSR1.COARSE_SLOPE_LOOKUP_TABLE_3_0(self.head_id, slope_lookup[(i*8)+3], register_offset_slope)
                self.b.ICYSHSR1.COARSE_SLOPE_LOOKUP_TABLE_4_0(self.head_id, slope_lookup[(i*8)+4], register_offset_slope)
                self.b.ICYSHSR1.COARSE_SLOPE_LOOKUP_TABLE_5_0(self.head_id, slope_lookup[(i*8)+5], register_offset_slope)
                self.b.ICYSHSR1.COARSE_SLOPE_LOOKUP_TABLE_6_0(self.head_id, slope_lookup[(i*8)+6], register_offset_slope)
                self.b.ICYSHSR1.COARSE_SLOPE_LOOKUP_TABLE_7_0(self.head_id, slope_lookup[(i*8)+7], register_offset_slope)
        else:
            for i in range(4):
                self.b.ICYSHSR1.COARSE_BIAS_LOOKUP_TABLE_0_1(self.head_id, bias_lookup[(i*4)+0], register_offset_bias)
                self.b.ICYSHSR1.COARSE_BIAS_LOOKUP_TABLE_1_1(self.head_id, bias_lookup[(i*4)+1], register_offset_bias)
                self.b.ICYSHSR1.COARSE_BIAS_LOOKUP_TABLE_2_1(self.head_id, bias_lookup[(i*4)+2], register_offset_bias)
                self.b.ICYSHSR1.COARSE_BIAS_LOOKUP_TABLE_3_1(self.head_id, bias_lookup[(i*4)+3], register_offset_bias)

            for i in range(2):
                self.b.ICYSHSR1.COARSE_SLOPE_LOOKUP_TABLE_0_1(self.head_id, slope_lookup[(i*8)+0], register_offset_slope)
                self.b.ICYSHSR1.COARSE_SLOPE_LOOKUP_TABLE_1_1(self.head_id, slope_lookup[(i*8)+1], register_offset_slope)
                self.b.ICYSHSR1.COARSE_SLOPE_LOOKUP_TABLE_2_1(self.head_id, slope_lookup[(i*8)+2], register_offset_slope)
                self.b.ICYSHSR1.COARSE_SLOPE_LOOKUP_TABLE_3_1(self.head_id, slope_lookup[(i*8)+3], register_offset_slope)
                self.b.ICYSHSR1.COARSE_SLOPE_LOOKUP_TABLE_4_1(self.head_id, slope_lookup[(i*8)+4], register_offset_slope)
                self.b.ICYSHSR1.COARSE_SLOPE_LOOKUP_TABLE_5_1(self.head_id, slope_lookup[(i*8)+5], register_offset_slope)
                self.b.ICYSHSR1.COARSE_SLOPE_LOOKUP_TABLE_6_1(self.head_id, slope_lookup[(i*8)+6], register_offset_slope)
                self.b.ICYSHSR1.COARSE_SLOPE_LOOKUP_TABLE_7_1(self.head_id, slope_lookup[(i*8)+7], register_offset_slope)

    def set_lookup_tables_fast(self, array, tdc_id, bias_lookup, slope_lookup):
        # Pad bias with zeros (16)
        # Pad slope with zeros (16)
        # TODO
        register_offset_bias = tdc_id * 4
        register_offset_slope = tdc_id * 2
        if array == 0:
            for i in range(4):
                reg_val = 0
                for j in range(4):
                    reg_val += bias_lookup[(i * 4) + j] << (j * 8)
                self.b.ICYSHSR1.COARSE_BIAS_LOOKUP_TABLE_ALL_0(self.head_id, reg_val, register_offset_bias + i)
            for i in range(2):
                reg_val = 0
                for j in range(8):
                    reg_val += slope_lookup[(i * 8) + j] << (j * 4)
                self.b.ICYSHSR1.COARSE_SLOPE_LOOKUP_TABLE_ALL_0(self.head_id, reg_val, register_offset_slope + i)

        else:
            for i in range(4):
                reg_val = 0
                for j in range(4):
                    reg_val += bias_lookup[(i * 4) + j] << (j * 8)
                self.b.ICYSHSR1.COARSE_BIAS_LOOKUP_TABLE_ALL_1(self.head_id, reg_val, register_offset_bias + i)
            for i in range(2):
                reg_val = 0
                for j in range(8):
                    reg_val += slope_lookup[(i * 8) + j] << (j * 4)
                self.b.ICYSHSR1.COARSE_SLOPE_LOOKUP_TABLE_ALL_1(self.head_id, reg_val, register_offset_slope + i)



    # Dark_count_filter must be an array of 6 integers.
    def set_dcr_filter(self, array, dark_count_filter=None):
        if dark_count_filter is None:
            dark_count_filter = [0, 0, 0, 0, 0, 0]
        if array == 0:
            self.b.ICYSHSR1.DARK_COUNT_FILTER_DELTA_0_0(self.head_id, dark_count_filter[0], 0)
            self.b.ICYSHSR1.DARK_COUNT_FILTER_DELTA_1_0(self.head_id, dark_count_filter[1], 0)
            self.b.ICYSHSR1.DARK_COUNT_FILTER_DELTA_2_0(self.head_id, dark_count_filter[2], 0)
            self.b.ICYSHSR1.DARK_COUNT_FILTER_DELTA_3_0(self.head_id, dark_count_filter[3], 0)
            self.b.ICYSHSR1.DARK_COUNT_FILTER_DELTA_4_0(self.head_id, dark_count_filter[4], 0)
            self.b.ICYSHSR1.DARK_COUNT_FILTER_DELTA_5_0(self.head_id, dark_count_filter[5], 0)
        else:
            self.b.ICYSHSR1.DARK_COUNT_FILTER_DELTA_0_1(self.head_id, dark_count_filter[0], 0)
            self.b.ICYSHSR1.DARK_COUNT_FILTER_DELTA_1_1(self.head_id, dark_count_filter[1], 0)
            self.b.ICYSHSR1.DARK_COUNT_FILTER_DELTA_2_1(self.head_id, dark_count_filter[2], 0)
            self.b.ICYSHSR1.DARK_COUNT_FILTER_DELTA_3_1(self.head_id, dark_count_filter[3], 0)
            self.b.ICYSHSR1.DARK_COUNT_FILTER_DELTA_4_1(self.head_id, dark_count_filter[4], 0)
            self.b.ICYSHSR1.DARK_COUNT_FILTER_DELTA_5_1(self.head_id, dark_count_filter[5], 0)

    def set_tdc_disable(self, array, disable_map):
        disable_words = np.zeros(2, dtype=np.int)
        for i in range(len(disable_map)):
            word_index = int(i / 32)
            if disable_map[i]:
                disable_words[word_index] |= (0x1 << (i % 32))
        if array == 0:
            for i in range(2):
                self.b.ICYSHSR1.PIXEL_DISABLE_TDC_ARRAY_0(self.head_id, disable_words[i], i)
        else:
            for i in range(2):
                self.b.ICYSHSR1.PIXEL_DISABLE_TDC_ARRAY_1(self.head_id, disable_words[i], i)

    def set_quench_disable(self, array, disable_map):
        disable_words = np.zeros(7, dtype=np.int)
        for i in range(len(disable_map)):
            word_index = int(i / 32)
            if disable_map[i]:
                disable_words[word_index] |= (0x1 << (i % 32))
        if array == 0:
            for i in range(7):
                self.b.ICYSHSR1.PIXEL_DISABLE_QUENCH_ARRAY_0(self.head_id, disable_words[i], i)
        else:
            for i in range(7):
                self.b.ICYSHSR1.PIXEL_DISABLE_QUENCH_ARRAY_1(self.head_id, disable_words[i], i)

    def set_ext_trigger_disable(self, array, disable_map):
        disable_words = np.zeros(7, dtype=np.int)
        for i in range(len(disable_map)):
            word_index = int(i / 32)
            if disable_map[i]:
                disable_words[word_index] |= (0x1 << (i % 32))
        if array == 0:
            for i in range(7):
                self.b.ICYSHSR1.DISABLE_EXTERNAL_TRIGGER_ARRAY_0(self.head_id, disable_words[i], i)
        else:
            for i in range(7):
                self.b.ICYSHSR1.DISABLE_EXTERNAL_TRIGGER_ARRAY_1(self.head_id, disable_words[i], i)

    def set_weighted_average(self, array, weights):
        # TODO
        pass

    # There are either 16 or 49 tdc by matrix (configuration 4 pixels to 1 tdc)
    def enable_all_tdc_but(self, array, enabled_tdc):
        array_size = 16
        if array == 0:
            array_size = 49
        disable_map = np.zeros(array_size, dtype=np.int)
        for i in enabled_tdc:
            disable_map[i] = 1
        self.set_tdc_disable(array, disable_map)

    # There are either 16 or 49 tdc by matrix (configuration 4 pixels to 1 tdc)
    def disable_all_tdc_but(self, array, disabled_tdc):
        array_size = 16
        if array == 0:
            array_size = 49
        disable_map = np.ones(array_size, dtype=np.int)
        for i in disabled_tdc:
            disable_map[i] = 0
        self.set_tdc_disable(array, disable_map)

    def enable_all_quench_but(self, array, enabled_quench):
        array_size = 64
        if array == 0:
            array_size = 196
        disable_map = np.zeros(array_size, dtype=np.int)
        for i in enabled_quench:
            disable_map[i] = 1
        self.set_quench_disable(array, disable_map)

    def disable_all_quench_but(self, array, disabled_quench):
        array_size = 64
        if array == 0:
            array_size = 196
        disable_map = np.ones(array_size, dtype=np.int)
        for i in disabled_quench:
            disable_map[i] = 0
        self.set_quench_disable(array, disable_map)

    def enable_all_ext_trigger_but(self, array, enabled_ext_trig):
        array_size = 64
        if array == 0:
            array_size = 196
        disable_map = np.zeros(array_size, dtype=np.int)
        for i in enabled_ext_trig:
            disable_map[i] = 1
        self.set_ext_trigger_disable(array, disable_map)

    def disable_all_ext_trigger_but(self, array, disabled_ext_trig):
        array_size = 64
        if array == 0:
            array_size = 196
        disable_map = np.ones(array_size, dtype=np.int)
        for i in disabled_ext_trig:
            disable_map[i] = 0
        self.set_ext_trigger_disable(array, disable_map)

    def enable_all_tdc(self):
        self.enable_all_tdc_but(0, [])
        self.enable_all_tdc_but(1, [])

    def enable_all_quench(self):
        self.enable_all_quench_but(0, [])
        self.enable_all_quench_but(1, [])

    def enable_all_ext_trigger(self):
        self.enable_all_ext_trigger_but(0, [])
        self.enable_all_ext_trigger_but(1, [])

    def disable_all_tdc(self):
        self.disable_all_tdc_but(0, [])
        self.disable_all_tdc_but(1, [])

    def disable_all_quench(self):
        print("Disable all quench")
        self.disable_all_quench_but(0, [])
        self.disable_all_quench_but(1, [])

    def disable_all_ext_trigger(self):
        self.disable_all_ext_trigger_but(0, [])
        self.disable_all_ext_trigger_but(1, [])

    #
    # Configurations
    #
    def configure_tep_energy_discrimination_mode(self, array):
        pass

    #Use the PLL to control the arrays TDC frequency and disable the external Voltage
    def enable_PLL(self):
        self.b.ICYSHSR1.PLL_ENABLE(self.head_id, 1, 0)

    #Disable the PLL and use the external Voltage to set the arrays TDC frequency
    def enable_Vext(self):
        self.b.ICYSHSR1.PLL_ENABLE(self.head_id, 0, 0)

    def enable_trig_test(self):
        self.b.ICYSHSR1.PLL_DISABLE_EXTERNAL_TRIGGER(self.head_id, 0)

    def disable_trig_test(self):
        self.b.ICYSHSR1.PLL_DISABLE_EXTERNAL_TRIGGER(self.head_id, 1)

    #Setup pour test de la PLL lente; Input: Ref_Freq_Slow; Output: Div_Freq_Slow_PLL_Test
    def test_PLL_slow(self):
        self.b.ICYSHSR1.PLL_ENABLE(self.head_id, 0, 0) # Disable Array PLL
        self.b.ICYSHSR1.PLL_ENABLE_TEST(self.head_id, 1, 0) # Enable Test PLL
        self.b.ICYSHSR1.PLL_SELECT_TEST(self.head_id, 1, 0) # Use PLL for test
        self.b.ICYSHSR1.PLL_TEST_SECTION_MUX(self.head_id, 0x0001, 0) # Output freq_slow

    # Setup pour test de la PLL Rapide; Input: Ref_Freq_Fast; Output: Div_Freq_Fast_PLL_Test
    def test_PLL_fast(self):
        self.b.ICYSHSR1.PLL_ENABLE(self.head_id, 0, 0) # Disable Array PLL
        self.b.ICYSHSR1.PLL_ENABLE_TEST(self.head_id, 1, 0) # Enable Test PLL
        self.b.ICYSHSR1.PLL_SELECT_TEST(self.head_id, 1, 0) # Use PLL for test
        self.b.ICYSHSR1.PLL_TEST_SECTION_MUX(self.head_id, 0x0002, 0) # Output freq_fast

    # Setup pour test du TDC Test avec PLL de Test; Input: Ref_Freq_Slow, Ref_Freq_Fast; Output: o_serialiseur_test
    def test_TDC_PLL(self):
        self.b.ICYSHSR1.PLL_ENABLE(self.head_id, 0, 0) # Disable Array PLL
        self.b.ICYSHSR1.PLL_ENABLE_TEST(self.head_id, 1, 0) # Enable Test PLL
        self.b.ICYSHSR1.PLL_SELECT_TEST(self.head_id, 1, 0) # Use PLL for test
        self.b.ICYSHSR1.PLL_TEST_SECTION_MUX(self.head_id, 0x0003, 0) # Output TDC output

    # Setup pour test du TDC Test avec tension externe; Input: V_Fast, V_Slow; Output: o_serialiseur_test
    def test_TDC_ext(self):
        self.b.ICYSHSR1.PLL_ENABLE(self.head_id, 0, 0) # Disable Array PLL
        self.b.ICYSHSR1.PLL_ENABLE_TEST(self.head_id, 1, 0) # Enable Test PLL
        self.b.ICYSHSR1.PLL_SELECT_TEST(self.head_id, 0, 0) # Use Vext for test
        self.b.ICYSHSR1.PLL_TEST_SECTION_MUX(self.head_id, 0x0003, 0) # Output TDC output

    # Reset the TDC mux. If this isn't reset, you can't read from registers or anything
    def reset_TDC_mux(self):
        self.b.ICYSHSR1.PLL_TEST_SECTION_MUX(self.head_id, 0x0000, 0)  # Output TDC output

    # Readout_time is in clk cycle (4ns)
    def configure_ct_counting_mode(self, array, readout_time):
        self.set_individual_spad_access(1)              # No sharing since no TDC used
        self.mux_select(array, self.c.SEL_GATED_COUNT)  # Set the output mux
        self.set_trigger_type(self.c.TRIG_TIME_DRIVEN)  # Set time driven
        self.set_time_driven_period(readout_time)       # Set the readout time

    # Readout_time is in clk cycle (4ns)
    def configure_ct_bitmap_mode(self, array, readout_time):
        self.set_individual_spad_access(1)                  # No sharing since no TDC used
        self.mux_select(array, self.c.SEL_GATED_BITMAP)     # Set the output mux
        self.set_trigger_type(self.c.TRIG_TIME_DRIVEN)      # Set time driven
        self.set_time_driven_period(readout_time)           # Set the readout time

    # Readout_time is in clk cycle (4ns)
    def configure_ct_integration_mode(self, array, readout_time, width, integration_time, column_threshold):
        self.set_zpp_interval_width(width)                      # Zpp counter is used in this mode
        self.set_zpp_interval_spacing(0)                        # Zpp counter is used in this mode
        # Set the column threshold and how long to allow  before that happens from the first hit
        self.set_integration_time(integration_time, column_threshold)
        self.set_individual_spad_access(1)                      # No sharing since no TDC used
        self.mux_select(array, self.c.SEL_GATED_EVENT_DETECT)   # Set the output mux
        self.set_trigger_type(self.c.TRIG_TIME_DRIVEN)          # Set time driven
        self.set_time_driven_period(readout_time)               # Set the readout time

    # Readout_time is in clk cycle (4ns)
    def configure_zpp_mode(self, array, readout_time, width, spacing):
        self.set_zpp_interval_width(width)
        self.set_zpp_interval_spacing(spacing)
        self.set_time_driven_period(readout_time)
        self.mux_select(array, self.c.SEL_ZPP)

    def confgure_QKD_mode(self, array, timeBins, threshold):
        self.mux_select(array, self.c.SEL_QKD_TIME_BIN)  # Set the output mux
        self.set_trigger_type(self.c.TRIG_WINDOW_DRIVEN)  # Set time driven
        self.b.ICYSHSR1.TDC_GATING_MODE(self.head_id, 1, 0)
        self.b.ICYSHSR1.TRIGGER_WINDOW_DRIVEN_THRESHOLD(self.head_id, threshold, 0)  # Set the readout time
        self.window_is_stop()
        self.set_time_bins(timeBins)

    def set_time_bins(self, timeBins):
        self.b.ICYSHSR1.TIME_BIN_BOUNDS_0(self.head_id, timeBins[0], 0)
        self.b.ICYSHSR1.TIME_BIN_BOUNDS_0_1(self.head_id, timeBins[1], 0)
        self.b.ICYSHSR1.TIME_BIN_BOUNDS_1_2(self.head_id, timeBins[2], 0)
        self.b.ICYSHSR1.TIME_BIN_BOUNDS_2(self.head_id, timeBins[3], 0)

    def clock_is_stop(self):
        self.b.ICYSHSR1.TDC_STOP_SIGNAL(self.head_id, 0, 0)

    def window_is_stop(self):
        self.b.ICYSHSR1.TDC_STOP_SIGNAL(self.head_id, 1, 0)


    def frame_type_short(self):
        self.b.GEN_GPIO.GPIO("SHORT_FRAME", True)

    def frame_type_normal(self):
        self.b.GEN_GPIO.GPIO("SHORT_FRAME", False)

    def single_frame_mode(self):
        self.b.ICYSHSR1.SERIAL_READOUT_TYPE(self.head_id, 1)

    def multi_frame_mode(self):
        # This is the default
        self.b.ICYSHSR1.SERIAL_READOUT_TYPE(self.head_id, 0)
