# Author : Minjun J. Choi (mjchoi@nfri.re.kr)
#
# Description : This code reads the KSTAR MDSplus server data
#
# Acknowledgement : Special thanks to Dr. Y.M. Jeon
#

from MDSplus import Connection
# from MDSplus import DisconnectFromMds
# from MDSplus._mdsshr import MdsException

import numpy as np
import matplotlib.pyplot as plt

from kstardata import ep_pos
from kstardata import ece_pos
from kstardata import mc_pos
from kstardata import ts_pos

VAR_NODE = {'NBI11':'NB11_pnb', 'NBI12':'NB12_pnb', 'NBI13':'NB13_pnb', 'ECH':'ECH_VFWD1', 'ECCD':'EC1_RFFWD1',
            'ICRF':'ICRF_FWD', 'LHCD':'LH1_AFWD', 'GASI':'I_GFLOW_IN:FOO', 'GASK':'K_GFLOW_IN:FOO', 'SMBI':'SM_VAL_OUT:FOO',
            'Ip':'RC03', 'neAVGM':'NE_INTER01', 'ECE05':'ECE05', 'ECE35':'ECE35', 'Rp':'LMSR',
            'Zp':'LMSZ', 'VOL':'VOLUME', 'KAP':'KAPPA', 'BETAp':'BETAP', 'BETAn':'BETAN', 'q95':'q95', 'Li':'LI3',
            'GASG':'G_GFLOW_IN:FOO', 'WTkp':'WTOT_KAPPA', 'WTdlm':'WTOT_DLM03', 'DaT11':'TOR_HA11', 'DaT10':'TOR_HA10',
            'DaP02':'POL_HA02', 'DaP04':'POL_HA04', 'neAVGF':'NE_INTER02',
            'RMP_T3':'PCRMPTBULI', 'RMP_T4':'PCRMPTFULI', 'RMP_T1':'PCRMPTJULI', 'RMP_T2':'PCRMPTNULI',
            'RMP_M3':'PCRMPMBULI', 'RMP_M4':'PCRMPMFULI', 'RMP_M1':'PCRMPMJULI', 'RMP_M2':'PCRMPMNULI',
            'RMP_B3':'PCRMPBBULI', 'RMP_B4':'PCRMPBFULI', 'RMP_B1':'PCRMPBJULI', 'RMP_B2':'PCRMPBNULI'}

# nodes in PCS_KSTAR tree
PCS_TREE = ['LMSR', 'LMSZ', 'PCITFMSRD', 'PCRMPTBULI', 'PCRMPTFULI', 'PCRMPTJULI', 'PCRMPTNULI',
            'PCRMPMBULI', 'PCRMPMFULI', 'PCRMPMJULI', 'PCRMPMNULI', 'PCRMPBBULI', 'PCRMPBFULI', 'PCRMPBJULI', 'PCRMPBNULI']

# nodes in CSS tree
CSS_TREE = ['CSS_I{:02d}:FOO'.format(i) for i in range(1,5)] + ['CSS_Q{:02d}:FOO'.format(i) for i in range(1,5)]

# nodes in EFIT01 or EFIT02
EFIT_TREE = ['VOLUME', 'KAPPA', 'BETAP', 'BETAN', 'q95', 'LI3', 'WMHD']

# nodes need postprocessing
POST_NODE = {'ECH_VFWD1':'/1000', 'EC1_RFFWD1':'/1000', 'LH1_AFWD':'/200', 'SM_VAL_OUT:FOO':'/5',
            'RC03':'*(-1)/1000', 'NE_INTER01':'/1.9', 'VOLUME':'/10', 'KAPPA':'-1',
            'NE_INTER02':'/2.7'}

# nodes NOT support segment reading in 2018
NSEG_NODE = ['NB11_pnb', 'NB12_pnb', 'ECH_VFWD1'] # etc

class KstarMds(Connection):
    def __init__(self, shot, clist):
        # from iKSTAR
        super(KstarMds,self).__init__('172.17.100.200:8005')  # call __init__ in Connection
        # from opi to CSS Host PC
        # super(KstarMds,self).__init__('172.17.102.69:8000')  # call __init__ in Connection
        self.shot = shot
        self.clist = clist

        if ('ECE' == self.clist[0][0:3]) or ('CES' == self.clist[0][0:3]) or ('TS' == self.clist[0][0:2]) or \
        ('EP' == self.clist[0][0:2]) or ('MC1' == self.clist[0][0:3]):
            # get channel position
            self.channel_position()

        self.time = None
        self.data = None

    def get_data(self, trange, norm=0, atrange=[1.0, 1.1], res=0, verbose=1):
        if norm == 0:
            if verbose == 1: print('Data is not normalized {:s}'.format(self.clist[0]))
        elif norm == 1:
            if verbose == 1: print('Data is normalized by trange average {:s}'.format(self.clist[0]))
        elif norm == 2:
            if verbose == 1: print('Data is normalized by atrange average {:s}'.format(self.clist[0]))

        self.trange = trange

        # open tree
        tree = find_tree(self.clist[0])
        try:
            self.openTree(tree,self.shot)
            if verbose == 1: print('Open the tree {:s} to get data {:s}'.format(tree, self.clist[0]))
        except:
            if verbose == 1: print('Failed to open the tree {:s} to get data {:s}'.format(tree, self.clist[0]))
            return self.time, self.data

        # --- loop starts --- #
        clist_temp = self.clist[:]
        for i, cname in enumerate(clist_temp):

            # get MDSplus node from channel name
            if cname in VAR_NODE:
                node = VAR_NODE[cname]
            else:
                node = cname

            # resampling, time node
            if res != 0:
                snode = 'resample(\{:s},{:f},{:f},{:f})'.format(node,self.trange[0],self.trange[1],res)  # resampling
                tnode = 'dim_of(resample(\{:s},{:f},{:f},{:f}))'.format(node,self.trange[0],self.trange[1],res)  # resampling                

                if 'ECE' == self.clist[0][0:3]: 
                    snode = 'setTimeContext(*,*,{:f}),\{:s}'.format(res,node)
                    tnode = 'setTimeContext(*,*,{:f}),dim_of(\{:s})'.format(res,node)                
            else:
                snode = 'setTimeContext({:f},{:f},*),\{:s}'.format(self.trange[0],self.trange[1],node)
                tnode = 'setTimeContext({:f},{:f},*),dim_of(\{:s})'.format(self.trange[0],self.trange[1],node)

                if 'ECE' == self.clist[0][0:3]: # do not sub-sample for ECE (KSTAR MDSplus bug?)
                    snode = 'setTimeContext(*,*,*),\{:s}'.format(node)
                    tnode = 'setTimeContext(*,*,*),dim_of(\{:s})'.format(node)

            # simple post processing for data
            if node in POST_NODE:
                pnode = POST_NODE[node]
            else:
                pnode = ''

            # data node name
            dnode = snode + pnode

            try:
                # load data
                v = self.get(dnode).data()
                if verbose == 1: print('Read {:d} : {:s} (number of data points = {:d})'.format(self.shot, dnode, len(v)))

                # load time
                if self.data is None:
                    self.time = self.get(tnode).data()

                    # time in [s]
                    if tree == 'EFIT01': # time unit in sec
                        self.time = self.time*0.001

                    # get fs
                    self.fs = round(1/(self.time[1] - self.time[0])/1000)*1000.0
                    
                    # find index for trange
                    idx = np.where((self.time >= trange[0])*(self.time <= trange[1]))
                    idx1 = int(idx[0][0])
                    idx2 = int(idx[0][-1]+2)

                    # find offest index for ECE
                    if res != 0 and 'ECE' == self.clist[0][0:3]: 
                        oidx = np.where((self.time >= -0.5)*(self.time <= -0.1))
                        oidx1 = int(oidx[0][0])
                        oidx2 = int(oidx[0][-1]+2)

                    self.time = self.time[idx1:idx2]

                # remove offest for ECE
                if res != 0 and 'ECE' == self.clist[0][0:3]: 
                    v = v - np.mean(v[oidx1:oidx2])
                    
                    if np.mean(v) == 0: # bad channel
                        self.clist.remove(cname)
                        self.rpos[i] = -1 
                        print('Null data {:d} : {:s}. {:s} is removed'.format(self.shot, dnode, cname))
                        continue

                # resize data
                v = v[idx1:idx2]

                # normalize if necessary
                if norm == 1:
                    v = v/np.mean(v) - 1

                # expand dimension - concatenate
                v = np.expand_dims(v, axis=0)
                if self.data is None:
                    self.data = v
                else:
                    self.data = np.concatenate((self.data, v), axis=0)

            except:
                self.clist.remove(cname)
                if hasattr(self, 'rpos'):
                    self.rpos[i] = -1
                if verbose == 1: print('Failed {:d} : {:s}. {:s} is removed'.format(self.shot, dnode, cname))
        # --- loop ends --- #

        # remove positions of bad channels
        if hasattr(self, 'rpos'):
            cidx = self.rpos >= 0
            self.rpos = self.rpos[cidx]
            self.zpos = self.zpos[cidx]
            self.apos = self.apos[cidx]

        # get measurement error
        self.meas_error()

        # close tree
        self.closeTree(tree, self.shot)

        return self.time, self.data

    def channel_position(self):  # Needs updates ####################
        # get channel position either from MDSplus server or kstardata
        cnum = len(self.clist)
        self.rpos = np.arange(cnum, dtype=np.float64)  # R [m]
        self.zpos = np.zeros(cnum)  # z [m]
        self.apos = np.arange(cnum, dtype=np.float64)  # angle [rad]

        try: 
            if ('CES' == self.clist[0][0:3]) or ('ECE' == self.clist[0][0:3]):
                pass
            else:
                raise NoPosMdsError()

            # find tree
            tree = find_tree(self.clist[0])

            # open tree
            self.openTree(tree, self.shot)
            print('Open tree {:s} to get channel position {:s}'.format(tree, self.clist[0]))
            
            # read rnode from MDSplus 
            for c in range(cnum):
                # set rnode 
                if 'CES' == self.clist[0][0:3]: # CES
                    rnode = '\{:s}RT{:}'.format(self.clist[c][:4],self.clist[c][6:])
                elif 'ECE' == self.clist[0][0:3]: # ECE
                    rnode = '\{:s}:RPOS2ND'.format(self.clist[c])

                # read rnode
                rpos = self.get(rnode).data()
                if hasattr(rpos, "__len__"):
                    self.rpos[c] = self.get(rnode).data()[0]
                else:
                    self.rpos[c] = rpos

                # post processing
                if 'CES' == self.clist[0][0:3]: # CES
                    self.rpos[c] = self.rpos[c]/1000.0                    

            # close tree
            self.closeTree(tree, self.shot)

            print('The channel position read from MDSplus {:s}'.format(self.clist[0]))
        except:
            print('Failed to read the channel position from MDSplus {:s}'.format(self.clist[0]))
            print('Try to get the position from kstardata {:s}'.format(self.clist[0]))

            if 'ECE' == self.clist[0][0:3]: # ECE 2nd harmonics cold resonance
                ece_rpos = ece_pos.get_ece_pos(self.shot)
            elif 'TS' == self.clist[0][0:2]:
                ts_rpos = ts_pos.get_ts_pos(self.shot)
            elif 'EP' == self.clist[0][0:2]:
                ep_rpos, ep_zpos = ep_pos.get_ep_pos()
            elif 'MC1' == self.clist[0][0:3]:
                mc1t_apos, mc1p_apos = mc_pos.get_mc_pos()

            for c in range(cnum):
                if 'ECE' == self.clist[0][0:3]:
                    self.rpos[c] = ece_rpos[self.clist[c]]
                elif 'TS' == self.clist[0][0:2]:
                    self.rpos[c] = ts_rpos[self.clist[c].split(':')[0]]/1000.0
                elif 'EP' == self.clist[0][0:2]:
                    self.rpos[c] = ep_rpos[self.clist[c][0:4]]
                    self.zpos[c] = ep_zpos[self.clist[c][0:4]]
                    self.apos[c] = float(self.clist[c][2:4])
                elif 'MC1T' == self.clist[0][0:4]:
                    self.apos[c] = mc1t_apos[self.clist[c]]
                elif 'MC1P' == self.clist[0][0:4]:
                    self.apos[c] = mc1p_apos[self.clist[c]]
            
            print('The channel position obtained from kstardata {:s}'.format(self.clist[0]))

    def meas_error(self):  # Needs updates ####################
        # read from MDSplus node
        cnum = len(self.clist)
        self.err = np.zeros(cnum)  # measurement error
        for c in range(cnum):
            if 'CES' in self.clist[0]: # CES
                enode = '\{:s}:err_bar'.format(self.clist[c])

            try:
                self.err[c] = np.mean(self.get(enode).data())
            except:
                pass


def find_tree(cname):
    # cname -> node
    if cname in VAR_NODE:
        node = VAR_NODE[cname]
    else:
        node = cname

    # find tree
    if node in PCS_TREE:
        tree = 'PCS_KSTAR'
    elif node in CSS_TREE:
        tree = 'CSS'
    elif node in EFIT_TREE:
        tree = 'EFIT01'
    else:
        tree = 'KSTAR'

    return tree


class NoPosMdsError(Exception):
    def __init__(self, msg='No position in MDSplus server'):
        self.msg = msg

    def __str__(self):
        return self.msg


if __name__ == "__main__":
    pass

    # g = KstarMds(shot=17245,clist=['neAVGM'])
    # g.get_data(trange=[0,10])
    # plt.plot(g.time, g.data[0,:], color='k')
    # plt.show()
    # g.close

# DisconnectFromMds(g.socket)
