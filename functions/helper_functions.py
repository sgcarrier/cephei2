import math
import time
from platforms.CHARTIER.CHARTIER import CHARTIER
from functions.helper_functions_asic import ASIC

# LMK03318
class PLL:
    def __init__(self, chartier):
        self.b = chartier

    # target_fvco: in MHz and should be between 4800 and 5400.
    def set_frequencies(self, freq_0_1, freq_2_3, target_fvco=5000):
        system_clock = 250   # MHz
        #    F_VCO = (F_REF / R) × D × [(INT + NUM / DEN) / M]
        #    F_OUT = F_VCO / (P × OUTDIV)
    
        if target_fvco < 4800 or target_fvco > 5400:
            raise ValueError("fvco must be between 4800 MHz and 5400 MHz.")
        n_div = int(target_fvco * 2 / system_clock)

        # TODO: flexible F_VCO
        if (target_fvco * 2) % system_clock:
            raise ValueError("Fractionnal N_Div not supported yet. Please adjust target_fvco so that "
                             "target_fvco * 2 / SYSTEM_CLOCK = integer")

        # Find the output divider
        if target_fvco % freq_0_1 != 0:
            raise ValueError("Condition not met: fvco(" + str(target_fvco) + ") MHz / freq_0_1 = integer")
        if target_fvco % freq_2_3 != 0:
            raise ValueError("Condition not met: fvco(" + str(target_fvco) + ") MHz / freq_2_3 = integer")

        total_div_0_1 = target_fvco / freq_0_1
        total_div_2_3 = target_fvco / freq_2_3

        if total_div_0_1 > 2048:  # (max division = 8 * 256)
            raise ValueError("freq_0_1 requires a divider too large. Consider using the LMK01020.")
        if total_div_2_3 > 2048:  # (max division = 8 * 256)
            raise ValueError("freq_2_3 requires a divider too large. Consider using the LMK01020.")

        # Select pll post divider
        pll_post_divider = 1  # Don't use the pll post divider unless required.
        if total_div_0_1 > 256 or total_div_2_3 > 256:
            max_div_required_0_1 = math.ceil(total_div_0_1 / 256)
            max_div_required_2_3 = math.ceil(total_div_2_3 / 256)
            pll_post_divider = max(max_div_required_0_1, max_div_required_2_3)
            if (target_fvco / pll_post_divider) % freq_0_1 != 0:
                raise ValueError(
                    "Unable to apply a common post pll divider (" + str(pll_post_divider) + ""
                    ") because target_fvco / pll_post_divider / freq_0_1 is not an integer."
                )
            if (target_fvco / pll_post_divider) % freq_2_3 != 0:
                raise ValueError(
                    "Unable to apply a common post pll divider (" + str(pll_post_divider) + ""
                    ") because target_fvco / pll_post_divider / freq_2_3 is not an integer."
                )

        # Find the channer divider
        div_0_1 = int((target_fvco / pll_post_divider) / freq_0_1)
        div_2_3 = int((target_fvco / pll_post_divider) / freq_2_3)

        self.b.LMK03318.PLL_P(0, 7)  # Post divider value: 8
        self.b.LMK03318.CH_0_MUTE(0, 0)  # Mute disabled for channel 0
        self.b.LMK03318.CH_2_MUTE(0, 0)  # Mute disabled for channel 2
        self.b.LMK03318.CH_3_MUTE(0, 0)  # Mute disabled for channel 3
        self.b.LMK03318.INSEL_PLL(0, 2)  # Input select: Primary input selected
        self.b.LMK03318.OUT_3_MODE1(0, 0)  # Output Mode: 0 = LVDS
        self.b.LMK03318.OUT_3_SEL(0, 1)  # Driver format select: 1 = AC-LVDS/AC-CML/AC-LVPECL

        ## Config de base pour le output
        self.b.LMK03318.PRIBUFSEL(0, 1)  # Input termination: 1 = Differential Input
        self.b.LMK03318.AC_MODE_PRI(0, 0)  # Input AC mode: 0 = No AC term
        self.b.LMK03318.DIFFTERM_PRI(0, 1)  # Termination: 1 = 100 ohm termination
        self.b.LMK03318.TERM2GND_PRI(0, 0)  # Termination to GND: 0 = No 50 ohm terminations to GND
        self.b.LMK03318.SECBUFSEL(0, 3)  # Secondary input sel: 3 = disabled

        self.b.LMK03318.OUT_0_SEL(0, 1)  # Driver format select: 1 = AC-LVDS/AC-CML/AC-LVPECL
        self.b.LMK03318.OUT_0_MODE1(0, 0)  # Output Mode: 0 = LVDS
        self.b.LMK03318.OUT_2_SEL(0, 1)  # Driver format select: 1 = AC-LVDS/AC-CML/AC-LVPECL
        self.b.LMK03318.OUT_2_MODE1(0, 0)  # Output Mode: 0 = LVDS
        self.b.LMK03318.OUT_3_SEL(0, 1)  # Driver format select: 1 = AC-LVDS/AC-CML/AC-LVPECL
        self.b.LMK03318.OUT_3_MODE1(0, 0)  # Output Mode: 0 = LVDS

        # F_VCO = (80 MHz / 1)  × 1 × [(125 + 0)/2] = 5 GHz
        # By default NUM = 0, DEN = 1
        self.b.LMK03318.PLL_NDIV(0, n_div)  # N divider (integer divider): 125, fract. div can be set with NUM and DEN
        self.b.LMK03318.PLLRDIV(0, 0)  # R divider (input divider before smart mux): 0 = Bypassed = 250 MHz
        self.b.LMK03318.PLLMDIV(0, 1)  # M divider (input divider after smart mux): 1 = div by 2 = 125 MHz
        self.b.LMK03318.OUT_0_1_DIV(0, div_0_1)
        self.b.LMK03318.OUT_2_3_DIV(0, div_2_3)  # 1 à 256: Div de sortie
        self.b.LMK03318.PRI_D(0, 0)  # Input frequency doubler: 0 = Frequency doubler disabled
        self.b.LMK03318.PLL_P(0, pll_post_divider-1)  # PLL post divider: 7 = 8 (2 à 8)

        self.b.LMK03318.PLL_PDN(0, 1)
        self.b.LMK03318.PLL_PDN(0, 0)

        # Send a sync to enable the outputs
        self.b.LMK03318.gpio_set(0, "SYNC", False)
        self.b.LMK03318.gpio_set(0, "SYNC", True)

    def set_6_25mhz(self):
        self.b.LMK03318.PLL_P(0, 7)  # Post divider value: 8
        self.b.LMK03318.CH_0_MUTE(0, 0)  # Mute disabled for channel 0
        self.b.LMK03318.CH_2_MUTE(0, 0)  # Mute disabled for channel 2
        self.b.LMK03318.CH_3_MUTE(0, 0)  # Mute disabled for channel 3
        self.b.LMK03318.INSEL_PLL(0, 2)  # Input select: Primary input selected
        self.b.LMK03318.OUT_3_MODE1(0, 0)  # Output Mode: 0 = LVDS
        self.b.LMK03318.OUT_3_SEL(0, 1)  # Driver format select: 1 = AC-LVDS/AC-CML/AC-LVPECL

        ## Config de base pour le output
        self.b.LMK03318.PRIBUFSEL(0, 1)  # Input termination: 1 = Differential Input
        self.b.LMK03318.AC_MODE_PRI(0, 0)  # Input AC mode: 0 = No AC term
        self.b.LMK03318.DIFFTERM_PRI(0, 1)  # Termination: 1 = 100 ohm termination
        self.b.LMK03318.TERM2GND_PRI(0, 0)  # Termination to GND: 0 = No 50 ohm terminations to GND
        self.b.LMK03318.SECBUFSEL(0, 3)  # Secondary input sel: 3 = disabled

        self.b.LMK03318.OUT_0_SEL(0, 1)  # Driver format select: 1 = AC-LVDS/AC-CML/AC-LVPECL
        self.b.LMK03318.OUT_0_MODE1(0, 0)  # Output Mode: 0 = LVDS
        self.b.LMK03318.OUT_2_SEL(0, 1)  # Driver format select: 1 = AC-LVDS/AC-CML/AC-LVPECL
        self.b.LMK03318.OUT_2_MODE1(0, 0)  # Output Mode: 0 = LVDS
        self.b.LMK03318.OUT_3_SEL(0, 1)  # Driver format select: 1 = AC-LVDS/AC-CML/AC-LVPECL
        self.b.LMK03318.OUT_3_MODE1(0, 0)  # Output Mode: 0 = LVDS

        # F_VCO = (80 MHz / 1)  × 1 × [(125 + 0)/2] = 5 GHz
        # By default NUM = 0, DEN = 1
        self.b.LMK03318.PLL_NDIV(0, 40)  # N divider (integer divider): 125, fract. div can be set with NUM and DEN
        self.b.LMK03318.PLLRDIV(0, 0)  # R divider (input divider before smart mux): 0 = Bypassed = 250 MHz
        self.b.LMK03318.PLLMDIV(0, 1)  # M divider (input divider after smart mux): 1 = div by 2 = 125 MHz
        self.b.LMK03318.OUT_0_1_DIV(0, 99)
        self.b.LMK03318.OUT_2_3_DIV(0, 99)  # 1 à 256: Div de sortie
        self.b.LMK03318.PRI_D(0, 0)  # Input frequency doubler: 0 = Frequency doubler disabled
        self.b.LMK03318.PLL_P(0, 7)  # PLL post divider: 7 = 8 (2 à 8)

        self.b.LMK03318.PLL_PDN(0, 1)
        self.b.LMK03318.PLL_PDN(0, 0)

        # Send a sync to enable the outputs
        self.b.LMK03318.gpio_set(0, "SYNC", False)
        self.b.LMK03318.gpio_set(0, "SYNC", True)

# LMK01020
class Divider:
    MUX_CORR = 1
    MUX_NOT_CORR = 0

    def __init__(self, chartier, device_id):
        self.device_id = device_id
        self.b = chartier
        if self.device_id == 1:
            self.sync = "WIND_SYNC"
            self.goe = "WIND_GOE"
        else:
            self.sync = "TRIG_SYNC"
            self.goe = "TRIG_GOE"

    # mux_select: 1 = corr, 0 = not corr
    def set_divider(self, divider, mux_select):
        if divider % 2 != 0:
            print("WARNING: divider not divisible by 2. The output won't be the exact one given")

        # The Clock division is actually 2x what you put in CLKoutX_DIV
        divider = int(divider/2)
        if divider < 0 or divider > 255:
            raise ValueError("Divider must be between 0 and 255")

        # Output the same thing on both the test point and the real output
        self.b.LMK01020.CLKOUT5_DIV(self.device_id, divider)
        self.b.LMK01020.CLKOUT5_MUX(self.device_id, 1)
        self.b.LMK01020.CLKOUT5_EN(self.device_id, 1)

        self.b.LMK01020.CLKOUT0_DIV(self.device_id, divider)
        self.b.LMK01020.CLKOUT0_MUX(self.device_id, 1)
        self.b.LMK01020.CLKOUT0_EN(self.device_id, 1)

        self.b.LMK01020.CLKIN_SELECT(self.device_id, mux_select)
        self.b.LMK01020.EN_CLKOUT_GLOBAL(self.device_id, 1)
        self.b.LMK01020.POWERDOWN(self.device_id, 0)

        # Toggle Global Output Enable and Sync
        self.b.LMK01020.gpio_set(0, self.goe, False)
        self.b.LMK01020.gpio_set(0, self.sync, False)
        time.sleep(1)
        self.b.LMK01020.gpio_set(0, self.goe, True)
        self.b.LMK01020.gpio_set(0, self.sync, True)


# LMK61E2
class Oscillator:
    # FVCO = FREF × D × [(INT + NUM/DEN)]
    # FVCO: PLL/VCO Frequency (4.6 GHz to 5.6 GHz)
    # FREF: 50-MHz reference input
    # FOUT = FVCO / OUTDIV

    def __init__(self, chartier, device_id):
        self.device_id = device_id
        self.b = chartier
        if device_id == 0 or device_id == 1:
            self.oe = "PLL_H0_OE"
        elif device_id == 3 or device_id == 4:
            self.oe = "PLL_H1_OE"
        elif device_id == 2:
            self.oe = "WIND_OSC_OE"
        else:
            self.oe = "TDC_OSC_OE"

    # Frequency in MHz
    def set_frequency(self, frequency):
        # 1 - Target FVCO around 5.1 GHz
        approx_out_div = 5100 / frequency
        out_div = math.floor(approx_out_div)
        if out_div > 511:
            raise ValueError("Frequency too loo. The output divider exceeds its range.")

        # 2 - Estimate the best FVCO and the multiplier to achieve that
        ideal_fvco = frequency * out_div
        multiplier_total = ideal_fvco / (2 * 50)
        if ideal_fvco < 4600:
            raise ValueError("F_VCO too low. Either readjust the frequency or the function algorithm.")

        # 3 - Retrieve register values
        n_div = math.floor(multiplier_total)
        frac = multiplier_total - n_div     # frac is between 0 and 1
        # Assuming DEN = 4194303 for max dynamic range
        num = math.floor(frac * 4194303)

        # 4 - Setup the registers
        self.b.LMK61E2.OUT_DIV(self.device_id, out_div)     # Output divider 19
        self.b.LMK61E2.NDIV(self.device_id, n_div)          # 47   12 bits
        self.b.LMK61E2.PLL_NUM(self.device_id, num)         # 2097151
        self.b.LMK61E2.PLL_DEN(self.device_id, 4194303)     # Set to the maximum for max dynamic range
        self.b.LMK61E2.PLL_D(self.device_id, 1)             # Doubler: 1 = Doubler
        self.b.LMK61E2.PLL_ENABLE_C3(self.device_id, 1)     # Enable C3: third order loop filter
        self.b.LMK61E2.PLL_CP_PHASE_SHIFT(self.device_id, 1)    # 1 = 1.3 ns for 100 MHz fPD
        self.b.LMK61E2.PLL_ORDER(self.device_id, 3)         # 3rd order
        self.b.LMK61E2.PLL_DTHRMODE(self.device_id, 3)      # Dither Disabled
        self.b.LMK61E2.SWR2PLL(self.device_id, 1)           # Software reset. Automatically cleared to 0
        self.b.LMK61E2.gpio_set(0, self.oe, True)


# SY89296 controlled through TCA9539 and AD5668
class DelayLine:
    def __init__(self, chartier, device_id):
        self.device_id = device_id
        self.b = chartier
        self.ftune_slope = -30/0.5   # 30 ps / 0.5 V
        self.ftune_value = 0
        self.dac_id = 0
        if device_id == 0:
            self.dac_id = 5  # Wind delay H0
        elif device_id == 1:
            self.dac_id = 3  # Wind delay H1
        elif device_id == 2:
            self.dac_id = 7  # Trig delay H0
        else:
            self.dac_id = 1  # Trig delay H1

        self.b.TCA9539.CONFIGURATIONPORT0(self.device_id, 0x0)
        self.b.TCA9539.CONFIGURATIONPORT1(self.device_id, 0x0)
        self.b.TCA9539.OUTPUTPORT0(self.device_id, 0)
        self.b.TCA9539.OUTPUTPORT1(self.device_id, 0)

        # Setup ftune via AD5668
        # Ftune lineaire between 0 and 0.5V
        self.b.AD5668.WRITE_TO_AND_UPDATE_DAC(1, self.dac_id, 0)

    @staticmethod
    def delay_to_bit_code(delay):
        delays_by_bit = [4610, 2300, 1150, 575, 290, 145, 70, 35, 15, 10]
        delay_code = 0

        # Convert target delay to code to set on the delay line
        for i in range(10):
            if delay > delays_by_bit[i]:
                delay_code |= 1 << i
                delay -= delays_by_bit[i]

        return delay_code

    # Max delay =
    def set_delay(self, delay):
        code = self.delay_to_bit_code(delay)
        self.set_delay_code(code)

    def set_delay_code(self, delay_code):
        disable = 0
        length = 0  # When high latches D[9:0] and D[10] bits. When low, the D[9:0] and D[10] are transparent.
        d10 = 0     #
        low_config = 0 | (delay_code << 1) & 0xFE | d10
        high_config = 0 | ((delay_code >> 7) & 0x7) | (disable << 3) | (length << 4)

        self.b.TCA9539.CONFIGURATIONPORT0(self.device_id, 0x0)
        self.b.TCA9539.CONFIGURATIONPORT1(self.device_id, 0x0)
        self.b.TCA9539.OUTPUTPORT0(self.device_id, low_config)
        self.b.TCA9539.OUTPUTPORT1(self.device_id, high_config)

    def reset_ftune(self):
        self.ftune_value = 0
        # TODO Update DAC

    def set_fine_tune(self, ftune):
        self.ftune_value = ftune
        value = int(ftune * (2**16 - 1) / 2.5)
        if value < 0 or value >= 2**16:
            raise ValueError("ftune value " + str(value) + " (in volt) is outside of range 0 to 2.5V")
        self.b.AD5668.WRITE_TO_AND_UPDATE_DAC(1, self.dac_id, value)

    def increment_fine_delay(self):
        self.ftune_value += 1
        if self.ftune_value > (2**16 - 1):
            self.ftune_value = (2 ** 16 - 1)
            return False
        # TODO: Set DAC
        return True

    def decrement_fine_delay(self):
        self.ftune_value -= 1
        if self.ftune_value < 0:
            self.ftune_value = 0
            return False
        # TODO: Set DAC
        return True


# Controlled through TCA9539
class MUX:
    LASER_INPUT = 0
    DIVIDER_INPUT = 1
    EXTERNAL_INPUT = 0
    PCB_INPUT = 1
    NON_INVERTED = 0
    INVERTED = 1
    MONOSTABLE = 0
    DELAYED_LASER = 1

    def __init__(self, chartier, mux_id):
        self.device_id = 2
        self.mux_id = 1 << mux_id
        self.b = chartier
        # Set everything as output (all outputs are on port 0, port 1 is empty)
        self.b.TCA9539.OUTPUTPORT0(self.device_id, 0x0)
        self.b.TCA9539.OUTPUTPORT1(self.device_id, 0x0)
        self.b.TCA9539.CONFIGURATIONPORT0(self.device_id, 0x0)
        self.b.TCA9539.CONFIGURATIONPORT1(self.device_id, 0x0)

    def select_input(self, sel):
        # Read the current config and update only the bit of the target mux
        current_config = self.b.TCA9539.OUTPUTPORT0(self.device_id)
        # Update the config
        new_config = current_config & ~self.mux_id  # Clear the bit
        if sel:
            new_config = new_config | self.mux_id   # Set bit if sel is true
        # Write back
        self.b.TCA9539.OUTPUTPORT0(self.device_id, new_config)
        self.b.TCA9539.CONFIGURATIONPORT0(self.device_id, 0x0)


class HV:
    def __init__(self, chartier, hv_id):
        self.b = chartier
        self.hv_id = hv_id

    # Voltage between 3.3 and -15
    def set_voltage(self, voltage):
        value = int((-(voltage-3.3) * (2**16 - 1)) / 18.3)
        if value < 0 or value >= 2**16:
            raise ValueError("HV value " + str(voltage) + " outside of range 3.3V to -15V")
        self.b.AD5668.INTERNAL_REF_SETUP(1, 1, 1)
        self.b.AD5668.WRITE_TO_AND_UPDATE_DAC(1, self.hv_id, value)


class CurrentSource:
    def __init__(self, chartier, current_source_id):
        self.b = chartier
        self.current_source_id = current_source_id

    # Current in uA. Between 0 and 100 uA
    def set_current(self, current):
        value = int(current * (2**16 - 1) / 100)
        if value < 0 or value >= 2**16:
            raise ValueError("Current value " + str(current) + " outside of range 0 to 100uA")
        self.b.AD5668.WRITE_TO_AND_UPDATE_DAC(1, self.current_source_id, value)


class VoltageSource5V:
    def __init__(self, chartier, source_id):
        self.b = chartier
        self.source_id = source_id

    # 0 to 5V
    def set_voltage(self, voltage):
        value = int(voltage * (2 ** 16 - 1) / 5)
        if value < 0 or value >= 2 ** 16:
            raise ValueError("Voltage value " + str(voltage) + " outside of range 0 to 5V")
        self.b.AD5668.WRITE_TO_AND_UPDATE_DAC(1, self.source_id, value)


class VoltageSourceLaserThreshold:
    def __init__(self, chartier, source_id):
        self.b = chartier
        self.source_id = source_id

    # -1.25V to 2.5V
    def set_voltage(self, voltage):
        value = int(((voltage + 1.25) * (2 ** 16 - 1)) / 3.75)
        if value < 0 or value >= 2 ** 16:
            raise ValueError("Voltage value " + str(voltage) + " outside of range -1.25V to 2.5V")
        self.b.AD5668.WRITE_TO_AND_UPDATE_DAC(1, self.source_id, value)


class VoltageSource2V5:
    def __init__(self, chartier, source_id):
        self.b = chartier
        self.source_id = source_id

    # 0 to 2.5V
    def set_voltage(self, voltage):
        value = int(voltage * (2 ** 16 - 1) / 2.5)
        if value < 0 or value >= 2 ** 16:
            raise ValueError("Voltage value " + str(voltage) + " outside of range 0 to 2V5")
        self.b.AD5668.WRITE_TO_AND_UPDATE_DAC(0, self.source_id, value)


class Board:
    def __init__(self):
        self.b = CHARTIER()
        # Instantiate all the circuit on the board for easy access
        # This way, the end user doesn't have to worry about the device's id
        self.pll = PLL(self.b)
        self.window_divider = Divider(self.b, 1)
        self.trigger_divider = Divider(self.b, 0)
        self.window_oscillator = Oscillator(self.b, 2)
        self.trigger_oscillator = Oscillator(self.b, 5)
        self.slow_oscillator_head_0 = Oscillator(self.b, 0)
        self.fast_oscillator_head_0 = Oscillator(self.b, 1)
        self.slow_oscillator_head_1 = Oscillator(self.b, 3)
        self.fast_oscillator_head_1 = Oscillator(self.b, 4)
        self.window_delay_head_0 = DelayLine(self.b, 0)
        self.window_delay_head_1 = DelayLine(self.b, 1)
        self.trigger_delay_head_0 = DelayLine(self.b, 3)
        self.trigger_delay_head_1 = DelayLine(self.b, 4)
        self.mux_window_laser = MUX(self.b, 2)
        self.mux_trigger_laser = MUX(self.b, 3)
        self.mux_window_external = MUX(self.b, 4)
        self.mux_trigger_external = MUX(self.b, 5)
        self.mux_coarse_delay = MUX(self.b, 0)
        self.mux_laser_polarity = MUX(self.b, 1)
        self.hv_head_0 = HV(self.b, 4)
        self.hv_head_1 = HV(self.b, 6)
        self.recharge_current = CurrentSource(self.b, 0)
        self.holdoff_current = CurrentSource(self.b, 1)
        self.comparator_threshold = VoltageSource5V(self.b, 2)
        self.laser_threshold = VoltageSourceLaserThreshold(self.b, 3)
        self.DAC_testpoint = VoltageSource5V(self.b, 7)
        self.v_fast_head_0 = VoltageSource2V5(self.b, 0)
        self.v_fast_head_1 = VoltageSource2V5(self.b, 6)
        self.v_slow_head_0 = VoltageSource2V5(self.b, 2)
        self.v_slow_head_1 = VoltageSource2V5(self.b, 4)
        self.asic_head_0 = ASIC(self.b, 0)
        self.asic_head_1 = ASIC(self.b, 1)
