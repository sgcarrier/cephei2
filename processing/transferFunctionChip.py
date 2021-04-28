import pickle


class TransferFunction:
    def __init__(self):
        with open('corr_coef.pickle', 'rb') as f:
            self.coefficients = pickle.load(f)
            #print(self.coefficients)

    def evaluate(self, fine, coarse, tdc):
        coef = self.coefficients[tdc]
        coarse_time = coef[0]
        fine_time = coef[1]
        offset = coef[2]
        slope = coef[3]
        return coarse * coarse_time + offset[coarse] + fine * (fine_time + slope[coarse])


tf = TransferFunction()
