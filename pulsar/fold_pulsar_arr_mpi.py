import numpy as np
import ch_pulsar_analysis as chp
import h5py
import misc_data_io as misc
import glob

from mpi4py import MPI
comm = MPI.COMM_WORLD
print comm.rank, comm.size

DM = 26.833 # B0329 dispersion measure
p1 = 0.7145817552986237 # B0329 period
dec = 54.57876944444

ncorr = 36
nnodes = 64
file_chunk = 8

"""
parser = argparse.ArgumentParser(description="This programs tries to fit beam from point-source trans\
its.")
parser.add_argument("Data", help="Directory containing acquisition files.")
parser.add_argument("--Objects", help="Celestial objects to fit", default='All')
parser.add_argument("--minfile", help="Minfile number e.g. 0051", default="")
parser.add_argument("--correlations", help="Maxfile number e.g. 0051", default="")
args = parser.parse_args()
"""

outdir = '/scratch/k/krs/connor/'
list = glob.glob('/scratch/k/krs/connor/chime/chime_data/20131210T060233Z/20131210T060233Z.h5.*')
list.sort()
list = list[:file_chunk * nnodes]

nchunks = len(list) / file_chunk

print "Total of %i files" % len(list)

jj = comm.rank

print "Starting chunk %i of %i" % (jj+1, nchunks)
print "Getting", file_chunk*jj, ":", file_chunk*(jj+1)

data_arr, time_full, RA = misc.get_data(list[file_chunk*jj:file_chunk*(jj+1)])[1:]
data_arr = data_arr[:, :10, :]
ncorr = 10

ntimes = len(time_full)

g = h5py.File('/scratch/k/krs/connor/psr_fpga.hdf5','r')
fpga = g['fpga'][:]
time_full = (fpga - fpga[0]) * 0.01000 / 3906.0
time = time_full[jj * ntimes : (jj+1) * ntimes]

time_int = 1000 # Integrate in time over time_int samples
freq_int = 2 # Integrate over freq bins

ntimes = len(time)

g = h5py.File('/scratch/k/krs/connor/psr_fpga.hdf5','r')
fpga = g['fpga'][:]
times = (fpga - fpga[0]) * 0.01000 / 3906.0
time = times[jj * ntimes : (jj+1) * ntimes]

n_freq_bins = np.round( data_arr.shape[0] / freq_int )
n_time_bins = np.round( data_arr.shape[-1] / time_int )
n_phase_bins = 64
    

folded_arr = np.zeros([n_freq_bins, ncorr, n_time_bins, n_phase_bins], np.complex128)

print "folded pulsar array has shape", folded_arr.shape

RC = chp.RFI_Clean(data_arr, time)
RC.dec = dec
RC.RA = RA
RC.frequency_clean(threshold=1e6)
#RC.fringe_stop() 

for freq in range(n_freq_bins):
    print "Folding freq %i" % freq 
    for tt in range(n_time_bins):
        folded_arr[freq, :, tt, :] = RC.fold_pulsar(p1, DM, nbins=n_phase_bins, \
                    start_chan=freq_int*freq, end_chan=freq_int*(freq+1), start_samp=time_int*tt, end_samp=time_int*(tt+1), f_ref=400.0)

fullie = []
final_list = []

for corr in range(ncorr):
    
    folded_corr = comm.gather(folded_arr[:, corr, :, :], root=0)
    if jj == 0:
        print "Done gathering arrays for corr", corr
        final_array = np.concatenate(folded_corr, axis=1)
        
        outfile = outdir + 'B0329_Dec10_psr_phase' + np.str(len(list)) + np.str(corr) + '.hdf5'
        print "Writing folded array to", outfile, "with shape:", final_array.shape

        f = h5py.File(outfile, 'w')
        f.create_dataset('folded_arr', data=final_array) 
        f.create_dataset('times', data=time_full)
        f.close()

