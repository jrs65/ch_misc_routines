import numpy as np
import ch_pulsar_analysis as chp
import h5py

#data_arr = abs(chd.data.data[:, 2, :].transpose())
#time = (chd.fpga_count - chd.fpga_count[0]) * 0.010 / 3906.

data_arr = 
time = 

time_int = 500 # Integrate in time for 500 samples
freq_int = 16 # Integrate over 16 freq bins

n_freq_bins = np.round(data_arr.shape[0] / freq_int)
n_time_bins = np.round(data_arr.shape[-1] / time_int)
n_phase_bins = 64

folded_arr = np.zeros([n_freq_bins, n_time_bins, n_phase_bins], np.complex128)
print "folded pulsar array has shape", folded_arr.shape

RC = chp.RFI_Clean(data_arr, time)
RC.frequency_clean()

for freq in range(n_freq_bins):
    for tt in range(n_time_bins):
        folded_arr[freq, tt, :] = RC.fold_pulsar(p1, DM, nbins=n_phase_bins, \
                    start_chan=freq_int*freq, end_chan=freq_int*(freq+1), \
                    start_samp=time_int*tt, end_samp=time_int*(tt+1), f_ref=400.0)


f = h5py.File(outfile, 'w')
f.create_dataset('folded_arr', data=folded_arr)
f.close()