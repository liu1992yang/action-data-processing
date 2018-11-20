import pandas as pd
import numpy as np
import matplotlib 
import matplotlib.pyplot as plt
import re
import sys
import os
import subprocess 
engine = 'python'

"""usage:
python process_code_dcc.py input.d PSdir 
"""

if len(sys.argv) < 3 :
  print("Usage: python process_code_dcc.py input.d psdir")
  sys.exit()


inputdir=sys.argv[1]

def find_input(inputdir):
  for file in os.listdir(inputdir):
    if file.endswith('.csv'):
      return os.path.join(inputdir,file)
  print('action file not found')
  sys.exit()  


def find_ps(psdir):
  power_files={}
  i=0
  for file in os.listdir(psdir):
    if file.endswith(".CSV"):
      i+=1
      power_files["PS"+str(i)]= os.path.join(psdir,file)
  if len(power_files) == 0:
    raise FileNotFoundError
  print('found ' + str(len(power_files)) + 'power scans')
  return power_files
  

""" find powerscans"""  
psdir=sys.argv[2]
power_file_dict=find_ps(psdir)
 

"""read power scan files"""
  
def get_power(PS_key):
    ps_file= pd.read_csv(power_file_dict.get(PS_key), header=None)
    ps_file.columns=['wavelength','power']
    return ps_file
    
powerscan= pd.DataFrame(dict({'wavelength': get_power(list(power_file_dict.keys())[0])['wavelength']}, **{key : get_power(key)['power'] for key in power_file_dict.keys()}))

powerscan = powerscan.iloc[:,[-1]+list(range(len(powerscan.columns)-1))]
#print(powerscan)
powerscan['average_power']=powerscan.iloc[:,1:].mean(axis=1)
powerscan['normalized_power']=powerscan['average_power']/(powerscan['average_power'].max())
powerscan[['wavelength']]=powerscan[['wavelength']].astype('int64') #change data type

powerscan.to_csv(os.path.join(psdir,'PS_norml' + '.csv'), index=False) #save averaged power scan


""" find input .csv and make outputdir, read input.csv file"""
inputdir=sys.argv[1]
inputfile = find_input(inputdir)
outputdir=inputdir[:-3]+'process'
print("output will save in "+ outputdir)      
subprocess.call(['mkdir', outputdir])
df = pd.read_csv(inputfile, sep=",+", na_filter=False, index_col=False)
print("shape is " + str(df.shape))
print(list(df)) #print current column names

### Data Cleaning
"""find how many lines to skip in the beginning if User value 1 is not 0 """ 
skip_headlines=df['User Value 1'].idxmin()
print("skip headline=" + str(skip_headlines))
data=pd.concat([df.iloc[skip_headlines:,1],df.iloc[skip_headlines:,5:]], axis=1) #remove columns that's not informative

edit_name = lambda ion_name: ion_name.strip().replace(": ", "-")
data.columns=['wavelength']+[edit_name(i) for i in data.columns[1:]]#data.columns is iterable
temp=data.groupby('wavelength').size().reset_index(name='count')

""" when the last wavelength has or equal to minimum number of scan, keep all rows, otherwise the difference in
scan numbers comparing to other wavelength should be removed"""
def skip_tail(counts):
    if min(counts) == counts[-1]:
        return 0
    return max(counts) - min(counts)
skip_taillines=skip_tail(list(temp['count']))
print("skip tail ="+str(skip_taillines))

data=data.iloc[:data.shape[0]-skip_taillines,:]
print("shape is "+str(data.shape))
print(list(data))
### Finish Data Cleaning

"""group data by wavelength and merge data"""
grouped_data=data.groupby('wavelength',as_index=False).mean()

tic_w_power=powerscan.iloc[:,[0,-1]].merge(grouped_data,how='left', left_on='wavelength', right_on='wavelength')
tic_w_power.to_csv(os.path.join(outputdir, 'tic_w_norm_power.csv'),index=False) #save to outputdir


"""tic divided by normalized power """
tic_w_power= tic_w_power.dropna() #drop NA
tic_by_power=pd.concat([tic_w_power.iloc[:, [0,1]], np.divide(tic_w_power.iloc[:,2:],pd.DataFrame(tic_w_power.iloc[:,1]))], axis=1)
tic_by_power.columns=list(tic_by_power)[0:2] + [i+'-by_power' for i in list(tic_by_power)[2:]] #
tic_by_power.to_csv(os.path.join(outputdir , 'tic_by_power.csv'), index=False)


"""plot figure, optional"""
plt.figure()
for i in range(2,tic_by_power.shape[1]//2):
    plt.scatter(tic_by_power.iloc[:,0], tic_by_power.iloc[:,i], marker = 'x')
    plt.legend(loc='upper right',bbox_to_anchor = (1.3,1.05))
    plt.title("firsthalf")
plt.savefig(os.path.join(outputdir ,'tic_by_power_plot_p1.png'))

plt.figure()
for i in range(tic_by_power.shape[1]//2, tic_by_power.shape[1]-1):
    plt.scatter(tic_by_power.iloc[:,0], tic_by_power.iloc[:,i], marker='x')
    plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.05))
    plt.title("secondhalf")
plt.savefig(os.path.join(outputdir ,"tic_by_power_plot_p2.png"))
     
for i in range(2, tic_by_power.shape[1]-1):
    plt.figure()
    plt.scatter(tic_by_power.iloc[:,0], tic_by_power.iloc[:,i], marker='x')
    plt.title(str(list(tic_by_power)[i]))
    plt.savefig(os.path.join(outputdir ,str(list(tic_by_power)[i])+".png"))




