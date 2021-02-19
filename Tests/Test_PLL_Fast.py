from scripts.helper_functions import Board

board = Board()
board.fast_oscillator_head_0.set_frequency(250)
board.asic_head_0.test_PLL_fast()
