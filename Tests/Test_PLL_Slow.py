from scripts.helper_functions import Board

board = Board()
board.slow_oscillator_head_0.set_frequency(250)
board.asic_head_0.disable_all_tdc()
board.asic_head_0.disable_all_quench()
board.asic_head_0.disable_all_ext_trigger()
board.asic_head_0.test_PLL_slow()