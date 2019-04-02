import sys, os
sys.path.append(os.pardir)
from fluctana import *

shot = int(sys.argv[1]) # shot
trange = eval(sys.argv[2])
clist = sys.argv[3].split(',')

A = FluctAna()
if clist[0][0:4] == 'ECEI':
    A.add_data(KstarEcei(shot=shot, clist=clist), trange=trange, norm=1)
else:
    A.add_data(KstarMds(shot=shot, clist=clist), trange=trange, norm=0)

# list data
A.list_data()

## over plane
A.skplane(dnum=0, cnl=range(len(A.Dlist[0].clist)), detrend=1, verbose=1)

# ## skewness only
# A.skewness(dnum=0, cnl=range(len(A.Dlist[0].clist)), detrend=1, verbose=1)
# A.mplot(dnum=0, cnl=range(len(A.Dlist[0].clist)), type='val')
# A.cplot(dnum=0, snum=0, vlimits=[-0.5,0.5])

# ## kurtosis only
# A.kurtosis(dnum=0, cnl=range(len(A.Dlist[0].clist)), detrend=1, verbose=1)
# A.mplot(dnum=0, cnl=range(len(A.Dlist[0].clist)), type='val')
# A.cplot(dnum=0, snum=0, vlimits=[-0.5,0.5])