#This plot out the spectrogram needed for the 

tmin = 1900
tmax = 4500
fmin = 0
fmax = 20

shots = [139057]#[174871,174872,174873,174874,174875]#OMFIT['DATA']['shot_info']['oshts']
ifplot = True # plot the data
reload = True # load in fresh data (SLOW!)

for shot in shots:
    if reload: # load in new data and crop to times (SLOW!)
        BB = OMFITmdsValue('NSTX', treename=None, shot=shot, TDI='B6')
        sel = (BB.dim_of(0)<tmax) * (BB.dim_of(0)>tmin)

    # compute spectrogram
    x = BB.data()[sel] # time series of measurement values
    fs = 1 / ((BB.dim_of(0)[sel][1] - BB.dim_of(0)[sel][0])/1e3)# sampling frequency of x

    nperseg = 2**12
    f, t, Sxx = scipy.signal.spectrogram(x,fs,nperseg=nperseg,noverlap=nperseg//2,nfft=nperseg*4)
    time = t*1e3 + BB.dim_of(0)[sel][0] # convert time to ms and offset

    if ifplot:
        figure(shot)
        ax = subplot(111)
        vmin=np.min(Sxx)*1e6; vmax=np.max(Sxx)/1e2
        #Sxx=25+np.log(Sxx)
        #print(Sxx)
        plt.pcolormesh(time, f/1e3, Sxx, norm=mpl.colors.LogNorm(vmin=vmin,vmax=vmax))#, cmap='binary')
        ax.set_ylim(fmin,fmax)
        ax.set_xlim(tmin,tmax)
    f_list=[17+4,31+8,44+12,57+16]
    t_range=np.arange(3000,3100,0.1)
    #for f in f_list:
    #    ax.plot(t_range,[f]*len(t_range),color='red')
    ax.set_title('NSTX ' +str(shot)+' Magnetic')
    ax.ticklabel_format(useOffset=False, style='plain')
    ax.set_xlabel('Time (ms)')
    ax.set_ylabel('Frequency (kHz)')


