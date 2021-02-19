

class ASIC:

    def __init__(self, chartier, head_id):
        self.b = chartier
        self.head_id = head_id

    def read_asic_id(self):
        pass

    def mux_select(self, array, post_processing):
        pass

    def configure_window_size(self, window_size):
        pass

    def configure_energy(self):
        pass

    def set_lookup_tables(self):
        pass

    def set_corrections(self):
        pass

    def set_dcr_filter(self):
        pass

    #Use the PLL to control the arrays TDC frequency and disable the external Voltage
    def enable_PLL(self):
        self.b.ICYSHSR1.PLL_ENABLE(self.head_id, 1)
    #Disable the PLL and use the external Voltage to set the arrays TDC frequency
    def enable_Vext(self):
        self.b.ICYSHSR1.PLL_ENABLE(self.head_id, 0)
    #Setup pour test de la PLL lente; Input: Ref_Freq_Slow; Output: Div_Freq_Slow_PLL_Test
    def test_PLL_slow(self):
        self.b.ICYSHSR1.PLL_ENABLE(self.head_id, 0)
        self.b.ICYSHSR1.PLL_ENABLE_TEST(self.head_id, 1)
        self.b.ICYSHSR1.PLL_SELECT_TEST(self.head_id, 1)
        self.b.ICYSHSR1.PLL_TEST_SECTION_MUX(self.head_id, 0x0001)
    # Setup pour test de la PLL Rapide; Input: Ref_Freq_Fast; Output: Div_Freq_Fast_PLL_Test
    def test_PLL_fast(self):
        self.b.ICYSHSR1.PLL_ENABLE(self.head_id, 0)
        self.b.ICYSHSR1.PLL_ENABLE_TEST(self.head_id, 1)
        self.b.ICYSHSR1.PLL_SELECT_TEST(self.head_id, 1)
        self.b.ICYSHSR1.PLL_TEST_SECTION_MUX(self.head_id, 0x0002)
    # Setup pour test du TDC Test avec PLL de Test; Input: Ref_Freq_Slow, Ref_Freq_Fast; Output: o_serialiseur_test
    def test_TDC_PLL(self):
        self.b.ICYSHSR1.PLL_ENABLE(self.head_id, 0)
        self.b.ICYSHSR1.PLL_ENABLE_TEST(self.head_id, 1)
        self.b.ICYSHSR1.PLL_SELECT_TEST(self.head_id, 1)
        self.b.ICYSHSR1.PLL_TEST_SECTION_MUX(self.head_id, 0x0003)
    # Setup pour test du TDC Test avec tension externe; Input: V_Fast, V_Slow; Output: o_serialiseur_test
    def test_TDC_ext(self):
        self.b.ICYSHSR1.PLL_ENABLE(self.head_id, 0)
        self.b.ICYSHSR1.PLL_ENABLE_TEST(self.head_id, 1)
        self.b.ICYSHSR1.PLL_SELECT_TEST(self.head_id, 0)
        self.b.ICYSHSR1.PLL_TEST_SECTION_MUX(self.head_id, 0x0003)
