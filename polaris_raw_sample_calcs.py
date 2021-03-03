import math
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import re
import warnings
warnings.filterwarnings("ignore")

base_directory = "C:/Users/hendr/Documents/WaveForms/2020-12-25_pol500008_raw"

data_directory = os.path.join(base_directory, "data/")
numFiles = len(os.listdir(data_directory))
print(numFiles, 'files in directory.  files: ', os.listdir(data_directory))

sampleStart = 0
sampleStop = 500
samplesPerPeriod = 160          # 60Hz fundamental sampled at 10KSPS

def plot_polaris():
    files = []
    # Create 2 figures for plotting Electric and Magnetic values
    f1 = plt.figure(1, figsize=(10, 10))        # plot window for EMF
    f2 = plt.figure(2, figsize=(10, 10))        # plot window for Debug (cross-correlation)
    f3 = plt.figure(3, figsize=(10, 10))        # plot window for aligned EMF (xcorr)
    subplotCount = 1
#    print("directory contents: ", os.listdir(data_directory))
    for filename in os.listdir(data_directory):
        # Using the regex and length of filename to iterate through the required files
        if re.search('txt',filename) and len(filename) < 40:
            files.append(filename)
            samples = []
            # Only open the files that meet the if-condition of file
            # print("files: ", os.path.join(data_directory,filename))
            with open(os.path.join(data_directory,filename),'r') as f:
                for line in f:
                    if 'Initiating single sample cycle' in line:
                        #print("Initiating condition met")
                        # Convert the lines below into a list
                        for lines in f:
                            inner_list = [line.strip() for line in lines.split(' ')]
                            samples.append(inner_list)
                        # Remove space from the list if any
                        for list in samples:
                            for space in list:
                                while '' in list:
                                    list.remove('')
                        # Convert the list into a dataframe
                        data = pd.DataFrame(samples)
                        #data = pd.DataFrame(samples[sampleStart:sampleStop])
                dataSamples = len(data)
                for i in range(dataSamples-16,dataSamples):  # Remove the unnecessary bottom couple of records
                    data = data.drop(i)
                # Remove the unnecessary first 2 columns
                data.drop(columns=[0, 1], axis=1, inplace=True)
                data.rename(columns={2: "E_z", 3: "E_y", 4: "E_x", 5: "B_z", 6: "B_y", 7: "B_x"}, inplace=True)
                # Convert the dtype of columns to int32 in order to perform the computations
                dataSamples = len(data)

                for i in data.columns:
                    data[i] = data[i].astype('int32')
                # Create the 'Time(ms)' column
                data['Time(ms)'] = np.linspace(0.1, 0.1*dataSamples, dataSamples)
                shift = pow(2,15)
                dataFft = pd.DataFrame()
                # Convert to ADC raw samples
                for i in data.columns[:6]:
                    data[i.lower()] = data[i] - data[i].mean()         # creates new, lowercase column headers
                    dataFft[i] = np.fft.fft(data[i.lower()])
                # Arrange the columns in the below order
                data = data[
                    ['E_z', 'E_y', 'E_x', 'B_z', 'B_y', 'B_x', 'Time(ms)', 'e_z', 'e_y', 'e_x', 'b_z', 'b_y', 'b_x']]
                data['b_y'] = data['b_y']*(-1)
#                print(data.head(5))
                # ADC raw samples to volts, and create squares columns
                for i in data.columns[7:13]:
                    data[i] = data[i] * 2.56 * 74.5108 / pow(2, 15)
                    data[i+'^2'] = pow(data[i], 2)
                all_rms = []
                # Calculate the RMS values for Bx,By,Bz
                for i in data.columns[13:19]:
                    rms = round(math.sqrt(data[i].mean()), 5)
                    all_rms.append(rms)

                ###############
                # Phase Calcs #
                ###############
                
                # Phase Calc 1: phase = acos( sumProd(A*B) / sqrt(norm(A) * norm(B)))
                EzChan = 13
                for i in range(16,19):
                    sumA = data[data.columns[i]].sum()
                    sumB = data[data.columns[EzChan]].sum()
                    sumProd = np.dot(data[data.columns[i-6]], data[data.columns[EzChan-6]])
                    phaseRatio = sumProd / math.sqrt(sumA*sumB)
                    phaseDeg = (180/math.pi) * math.acos(phaseRatio)
                    print("phase calc1:", i, data.columns[i],"sumA: %.3f" %sumA,"sumB: %.3f" %sumB,"sumProd: %.3f" %sumProd,"phaseRatio: %.3f" %phaseRatio,"data.columns[EzChan]","phaseDeg: %.3f" %phaseDeg)

                # Phase Calc 2: cross-correlation alignment
                xCorrSamples = 500      # be smarter about this number later
                xCorrSamplesStop = dataSamples - xCorrSamples + 1
                numFields = 6
                fieldOffset = 7
                tempEz = data['e_z'][0:xCorrSamplesStop]
                tempEz = tempEz.to_numpy()                
                xCorr = np.zeros((numFields,xCorrSamples))
                xCorrMax = np.zeros(numFields)
                xCorrMaxIndex = np.zeros(numFields)
                xCorrMaxEzDiff = np.zeros(numFields)
                xCorrPhase = np.zeros(numFields)
                for i in range(0,numFields):    # loop to create all cross-correlations and then find the phases
                    xCorr[i] = np.correlate(tempEz, data[data.columns[i+fieldOffset]].to_numpy())
                    xCorrMax[i] = np.amax(xCorr[i])
                    xCorrMaxIndex[i] = int(str(np.argmax(xCorr[i])))
                    nCycles = math.floor(xCorrMaxIndex[i]/samplesPerPeriod)
                    xCorrMaxIndex[i] = xCorrMaxIndex[i] - samplesPerPeriod*nCycles
                    xCorrMaxEzDiff[i] = xCorrMaxIndex[0] - xCorrMaxIndex[i]
                    if xCorrMaxEzDiff[i] < 0:
                        xCorrMaxEzDiff[i] = xCorrMaxEzDiff[i] + samplesPerPeriod
                    xCorrPhase[i] = xCorrMaxEzDiff[i]*360/samplesPerPeriod
                    print("phase calc2:",i, i+fieldOffset, data.columns[i+fieldOffset], "xCorrMax: %i" %xCorrMax[i], "xCorrMaxIndex: %i" %xCorrMaxIndex[i],'xCorrMaxEzDiff %i' %xCorrMaxEzDiff[i],'len(xCorr[i]) %i' %len(xCorr[i]), 'xCorrPhase: %i' %xCorrPhase[i])
                    
                # Phase Calc 3: distance-between zero-crossings
                print("len(data) %i" %len(data))
                zeroCrossings = np.zeros((3,6))
                zeroCount = 0
                movingAvgN = 5
                for i in range(10,13):
                    print("i: %i" %i, data.columns[i])
                    zeroCount = 0
                    for sampleCount in range(1,len(data)-1):
                        if (data[data.columns[i]][sampleCount-1] * data[data.columns[i]][sampleCount] < 0) and (data[data.columns[i]][sampleCount] < 0): # finds falling zero-crossings
                            if zeroCount < 6:
                                zeroCrossings[i-10][zeroCount] = sampleCount
                            #print("zero found! i=%i" %i, "sampleCount=%i" %sampleCount, "zeroCount=%i" %zeroCount)
                            zeroCount = zeroCount + 1
                print("zeroCrossings: ", zeroCrossings)

                ##############
                # Plot Setup #
                ##############
                # Start adding subplots into rows and columns, subplot number based on total number of data files (filename).
                numPlotRow = math.floor(math.sqrt(numFiles))
                numPlotCol = math.ceil(math.sqrt(numFiles))
                if numPlotCol*numPlotRow < numFiles:
                    numPlotRow = math.ceil(math.sqrt(numFiles))

                # Plot1: EMFs
                ax1 = f1.add_subplot(numPlotRow, numPlotCol, subplotCount)
                f1.subplots_adjust(left=0.20, bottom=0.05, right=0.99, top=0.80, wspace=0.1, hspace = 0.19) # adjust the subplot size to fit the figure
                p1 = ax1.plot(data['Time(ms)'].tolist(), data['b_x'].tolist(), label='b_x')
                p2 = ax1.plot(data['Time(ms)'].tolist(), data['b_y'].tolist(), label='b_y')
                p3 = ax1.plot(data['Time(ms)'].tolist(), data['b_z'].tolist(), label='b_z')
                p4 = ax1.plot(data['Time(ms)'].tolist(), data['e_z'].tolist(), label='e_z',lw=1)
                f1.text(0.43, 0.006, "Time(ms)", ha="center", va="center")                                  # x-label
                f1.text(0.05, 0.5, "EMF Field Amplitude (mG, V)", ha="center", va="center", rotation=90)  # y-label
                ax1.text(0.5, 0.001, 'V_Bx: '+str(all_rms[3])+', V_By: '+str(all_rms[4])+', V_Bz: '+str(all_rms[5]),verticalalignment='bottom',
                         horizontalalignment='center',color='black', transform = ax1.transAxes, fontsize=8)
                plot1Labels = ['Bx(Cross-range)','By(Down-range)','Bz(Vertical)', 'Ez(Vertical)']
                f1.legend([p1, p2, p3, p4],  # The data columns
                           labels = plot1Labels,  # The labels for each line
                           loc = "upper left",  # Position of legPolend
                           borderaxespad = 0.01,  # Small spacing around legend box
                           title = "Columns")  # Title for the legend
                ax1.set_title(str(filename[:-4]), loc='center', y=0.80, size=8)               
                ax1.grid(True)
                
                # Plot2: Cross Correlations
                ax2 = f2.add_subplot(numPlotRow, numPlotCol, subplotCount)
                f2.subplots_adjust(left=0.20, bottom=0.05, right=0.97, top=0.70, wspace=0.27, hspace = 0.24)
                p5 = ax2.plot(xCorr[5], label='xCorr(ez_bx)',lw=1)
                p6 = ax2.plot(xCorr[4], label='xCorr(ez_by)',lw=1)
                p7 = ax2.plot(xCorr[3], label='xCorr(ez_bz)',lw=1)
                p8 = ax2.plot(xCorr[0], label='xCorr(ez_ez)',lw=1)
                f2.text(0.43, 0.006, "Time(ms)", ha="center", va="center")
                f2.text(0.05, 0.5, "Electric Field (xV/m)", ha="center", va="center", rotation=90)
                xCorrLineLabels = ['EzToBx','EzToBy','EzToBz', 'EzToEz']
                f2.legend([p5, p6, p7, p8],  # The line objects
                          labels=xCorrLineLabels,  # The labels for each line
                          loc="upper left",  # Position of legend
                          borderaxespad=0.01,  # Small spacing around legend box
                          title="Columns"  # Title for the legend
                          )
                ax2.set_title(str(filename[:-4]), loc='center', y=0.80, size=8)                # Adding the x-label and y-label
                ax2.grid(True)
                
                # Plot3: xCorr-aligned EMFs
                ax3 = f3.add_subplot(numPlotRow, numPlotCol, subplotCount)
                f3.subplots_adjust(left=0.20, bottom=0.05, right=0.99, top=0.80, wspace=0.1, hspace = 0.19) # adjust the subplot size to fit the figure
                p9 = ax3.plot(data['b_x'][int(xCorrMaxEzDiff[5]):len(xCorr[5])].tolist(), label='b_x')
                p10 = ax3.plot(data['b_y'][int(xCorrMaxEzDiff[4]):len(xCorr[4])].tolist(), label='b_y')
                p11 = ax3.plot(data['b_z'][int(xCorrMaxEzDiff[3]):len(xCorr[3])].tolist(), label='b_z')
                p12 = ax3.plot(data['e_z'][int(xCorrMaxEzDiff[0]):len(xCorr[0])].tolist(), label='e_z',lw=1)
                f1.text(0.43, 0.006, "Time(ms)", ha="center", va="center")                                  # x-label
                f1.text(0.05, 0.5, "xCorr Aligned EMFs (mG, V)", ha="center", va="center", rotation=90)  # y-label
                ax1.text(0.5, 0.001, 'V_Bx: '+str(all_rms[3])+', V_By: '+str(all_rms[4])+', V_Bz: '+str(all_rms[5]),verticalalignment='bottom',
                         horizontalalignment='center',color='black', transform = ax1.transAxes, fontsize=8)
                plot3Labels = ['Bx(Cross-range)','By(Down-range)','Bz(Vertical)', 'Ez(Vertical)']
                f3.legend([p9, p10, p11, p12],  # The data columns
                           labels = plot3Labels,  # The labels for each line
                           loc = "upper left",  # Position of legPolend
                           borderaxespad = 0.01,  # Small spacing around legend box
                           title = "Columns")  # Title for the legend
                ax3.set_title(str(filename[:-4]), loc='center', y=0.80, size=8)               
                ax3.grid(True)

                subplotCount = subplotCount + 1
    # Adding figure title
    f1.suptitle('Polaris EMF (mG, V)', x=0.4, y=1.0, horizontalalignment='left', verticalalignment='top', fontsize = 12)
    f1.tight_layout(pad=4.0, w_pad=0.7, h_pad=1.0)
    f1.savefig(os.path.join(base_directory,'PolarisEmf.png'))

    f2.suptitle('Polaris CrossCorrelation Ez to B(x,y,z)', x=0.4, y=1.0, horizontalalignment='left', verticalalignment='top', fontsize = 12)
    f2.tight_layout(pad=4.0, w_pad=0.7, h_pad=1.0)
    f2.savefig(os.path.join(base_directory,'PolarisEzCorr.png'))

    f3.suptitle('Aligned EMF (mG, V)', x=0.4, y=1.0, horizontalalignment='left', verticalalignment='top', fontsize = 12)
    f3.tight_layout(pad=4.0, w_pad=0.7, h_pad=1.0)
    f3.savefig(os.path.join(base_directory,'PolarisAlignedEmf.png'))

    plt.show()

def moving_avg(x, n):
    cumsum = np.cumsum(np.insert(x, 0, 0)) 
    return (cumsum[n:] - cumsum[:-n]) / float(n)


plot_polaris()


