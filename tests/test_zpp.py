from scripts.helper_functions import Board

# Configure ZPP mode
# Disable all pixels but 1
board = Board()
board.asic_head_0.configure_zpp_mode(0, 3000, 50, 50)
board.asic_head_0.disable_all_quench_but(0, [0])

# Acquire data
