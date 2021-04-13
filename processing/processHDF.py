import h5py
from processing.rawDataProcessor import RawDataProcessor




if __name__ == '__main__':


    filename = "/home2/cars2019/Documents/DATA/SERIAL_COMM_TEST-20210408-130458.hdf5"
    FORMAT_NUM = 0

    RDP = RawDataProcessor()

    with h5py.File(filename, "a") as h:
        def visitor_func(name, node):
            if isinstance(node, h5py.Dataset):
                print(name)
                if (('ADDR_ALL' == name[-8:])):
                    return name


            else:
                print("Not a dataset")
                return None


        name = h.visititems(visitor_func)
        data = {}
        data['DATA'] = h[name]
        data['LEN'] = len(data['DATA'])
        dataArr = RDP.raw2compArray(data, FORMAT_NUM)
        if dataArr is not None:
            path = name[:-8] + "PROCESSED"
            print(path)
            if (path) not in h.keys():
                h.create_dataset(path, (0,), maxshape=(None,), dtype=dataArr.dtype, compression=None)
                L = dataArr.shape[0]
                h[path].resize((h[path].shape[0] + L), axis=0)
                h[path][-L:] = dataArr
                h.flush()
                print("Found unprocessed data and create dataset")
            else:
                print("Already done")
        print("Done!")





