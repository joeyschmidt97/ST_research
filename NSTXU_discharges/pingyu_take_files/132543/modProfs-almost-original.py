import sys
import numpy as np
import matplotlib.pyplot as plt
from write_iterdb import *
from read_iterdb_file import *
from interp import *
from finite_differences import *
from read_pfile import *
from write_pfile import *
import copy
from subprocess import call

#modes of operation:
#mode = 'eta': increase omt(e,i) by alpha, decrease omn to keep pressure fixed
#mode = 'etaTe': increase omte by alpha, decrease omti 
#mode = 'coll': vary collisionality at fixed pressure by decreasing/increasing temperature/density by alpha
#mode = 'TiTe': increase Te by alpha, decrease Ti by alpha
#mode = 'omnz': increase omnz (i.e. impurity density gradient) by alpha and decrease omni 
#mode = 'omte': increase omte without compensation
#mode = 'omti': increase omti without compensation
#mode = 'omt': modify both omti and omte without compensation
#mode = 'omne': increase omne without compensation
#mode = 'broaden_profiles': broaden ne by factor alpha
#mode = 'setup_pfile': set up a new pfile from a template pfile using the given temperature and density profiles (from profiles files), getting ptot from an efit file, and extracting pb (fast ion pressure) from the combination of ptot (from efit) and profiles (from profiles files).  Outputs the new pfile, which now includes fast ion pressure for the given scenario.  This fast ion pressure can be used in future runs be selecting include_fast_ion_pressure_from_pfile = True.

mode = 'omt'
efit_file_name ='g132543.00700'
Z = 6  #Z of impurity species
alpha = 0.9 #Factor setting the profile change
#Data is output as gene profiles files and an iterdb file. Set flag below to also output in pfile format, which is needed for equilibrium reconstruction
output_pfile = True  #Used for equilibrium reconstruction.  
profilesName_e = 'profiles_e'
profilesName_i = 'profiles_i'
profilesName_z = 'profiles_z'

pfile = 'p132543.00700'
rhotMidPed = 1.0  #Setting this equal to 1 keeps the separatrix parameters fixed
rhotTopPed = 0.0  #0.3 Works well for a gradual change to match the core
file_out_base = 'NSTX132543_alpha'+str(alpha)+'_omne'
base_number = '132543'  #Used only for iterdb output
include_fast_ion_pressure_from_pfile = True   #This gets the fast ion pressure from the pfile and includes it in the total pressure that is output to a new pfile

#Other options:
set_tz_eq_ti = True  #Sets impurity temperature equal to main ion temperature
const_zeff = False  
Zeff = 2.35 #Zeff is used when const_zeff = True

#Use the last four parameters if you want to set the separatrix Te to some value
set_Tesep = False
Tesep_target = 80  #Separatrix electron temperature in eV
x0_Tsep = 0.993 #radial location at which to send Tsep to target
lambda_Tsep = 0.016  #scale length over which to smooth to Tsep

target_factor = alpha
e = 1.602e-19

#rhot, te, ti, ne, ni, nz, omega_tor = read_iterdb_file(fileName)
datae = np.genfromtxt(profilesName_e)
datai = np.genfromtxt(profilesName_i)
dataz = np.genfromtxt(profilesName_z)

rhot = datae[:,0]
#rhop = datae[:,1]
call(['my_efit_tools.py','-c',efit_file_name])
rtrp = np.genfromtxt('rt_rp_'+efit_file_name) #direc
rhot_conv = rtrp[:,0]
rhop_conv = rtrp[:,1]
rhop = interp(rhot_conv,rhop_conv,rhot)

te = datae[:,2]*1e3
ne = datae[:,3]*1e19

rhoti = datai[:,0]
ti = datai[:,2]*1e3
ni = datai[:,3]*1e19

rhotz = dataz[:,0]
tz = dataz[:,2]*1e3
nz = dataz[:,3]*1e19

if const_zeff:
    dummy = input("Warning: adapting ni and nz so that (Z,Zeff) = ("+str(Z)+','+str(Zeff)+")\nPress any key.")
    ni_new = (Z-Zeff)*ne/(Z-1) 
    nz_new = (ne-ni_new)/Z
    plt.plot(rhotz,nz,label='nz old')
    plt.plot(rhotz,nz_new,label='nz new')
    plt.legend()
    plt.show()
    plt.plot(rhoti,ni,label='ni old')
    plt.plot(rhoti,ni_new,label='ni new')
    plt.legend()
    plt.show()
    ni = ni_new
    nz = nz_new
    dummy = input("Verifying quasineutrality (should be <<<1):"+str(np.sum(Z*nz+ni-ne)))
    
rhot0 = datae[:,0]
#rhop0 = datae[:,1]
#rhop = interp(rhot0,rhop0,rhot)
#plt.plot(rhot,rhop)
#plt.xlabel('rhot')
#plt.ylabel('rhop')
#plt.show()
Ptot = te * ne + ti * (ni + nz)

##*************start modification from max*************************
##************Hyperbolic tangent is applies so that only parameter in pedestal region will be inflected**********
if not mode == 'broaden_profiles':
    width=rhotMidPed-rhotTopPed
    weight = ((np.exp((rhot-rhotTopPed)*2/width)-1)/(np.exp((rhot-rhotTopPed)*2/width)+1)+1)/2 
    alpha0=alpha
    alpha=1+(alpha-1)*weight


#print alpha
#*************end modification from max*************************



# broaden profiles
if mode == 'broaden_profiles':
    alpha0 = alpha
    ipedtop = np.argmin(abs(rhot-rhotTopPed))
    nind_pedtop = len(rhot) - ipedtop
    ped_domain = 1-rhotTopPed
    ped_domain_broad = alpha*ped_domain
    rhotTopPed_broad = 1-ped_domain_broad
    xtemp_ped = np.linspace(rhotTopPed_broad,1,nind_pedtop)
    xtemp_core = np.linspace(0,rhotTopPed_broad,len(rhot)-nind_pedtop,endpoint=False)
    rhot_new = np.concatenate([xtemp_core,xtemp_ped])
    newNe = interp(rhot_new,ne,rhot)
    newNi = interp(rhot_new,ni,rhot)
    Z = float(input('Enter Z of impurity:\n'))
    newNz = (newNe - newNi)/Z
    newTe = interp(rhot_new,te,rhot)
    newTi = interp(rhot_new,ti,rhot)
    newTz = interp(rhot_new,tz,rhot)
    newPtot = newNe * newTe + newTi * newNi + newTz*newNz
    #plt.plot(rhot,ne_new)
    #plt.show()
    #plt.plot(rhot,ne)
    #plt.plot(rhot,ne_new,label='new on even grid')
    #plt.legend()
    #plt.show()
    #stop
    

# collisionality scan
if mode == 'coll':
   newTe = 1./alpha * te
   newTi = 1./alpha * ti
   newNe = alpha * ne
   newNi = alpha * ni
   newNz = alpha * nz
   newPtot = newTe * newNe + newTi * newNi + tz*newNz
   plt.title('alpha = '+str(alpha))
   plt.plot(rhot,ne*te**-1.5,label='ne*Te**-1.5 old')
   plt.plot(rhot,newNe*newTe**-1.5,label='ne*Te**-1.5 new')
   plt.plot(rhot,target_factor*ne*te**-1.5,'--',color='black',label='target')
   ax = plt.axis()
   plt.axis([0.9,1.0,0.0,ax[3]])
   plt.legend()
   plt.show()
   
# alpha times omte & omti
if mode == 'eta':
    midPedIndex = np.argmin(abs(rhot - rhotMidPed))
    teMidPed = te[midPedIndex]
    tiMidPed = ti[midPedIndex]
    print ('rhot ='+str (rhotMidPed))
    print ('te ='+str(teMidPed))
    print ('ti ='+str( tiMidPed))

    newTe = teMidPed*np.power(te/teMidPed,alpha)
    newTi = tiMidPed*np.power(ti/tiMidPed,alpha)

    Ptemp = ne * newTe + newTi * (ni + nz)
    #new density profile to keep total pressure the same
    newNe = ne*Ptot/Ptemp
    newNi = ni*Ptot/Ptemp
    newNz = nz*Ptot/Ptemp
    
    #total pressure with new density and tempeturate profiles
    newPtot = newNe * newTe + newTi * newNi + tz*newNz

    etae0 = ne/te*fd_d1_o4_uneven(te,rhot)/fd_d1_o4_uneven(ne,rhot)
    newetae = newNe/newTe*fd_d1_o4_uneven(newTe,rhot)/fd_d1_o4_uneven(newNe,rhot)
    plt.title('alpha='+str(alpha))
    plt.plot(rhot,etae0,label='etae old')
    plt.plot(rhot,target_factor*etae0,'--',color='black',label='target')
    plt.plot(rhot,newetae,label='etae new')
    ax = plt.axis()
    plt.axis([0.9,1.0,0.0,6])
    plt.legend()
    plt.show()

if mode == 'omte':
    midPedIndex = np.argmin(abs(rhot - rhotMidPed))
    teMidPed = te[midPedIndex]
    print ('rhot ='+str( rhotMidPed))
    print ('te ='+str( teMidPed))

    newTe = teMidPed*np.power(te/teMidPed,alpha)
    newTi = ti

    newNe = ne
    newNi = ni
    newNz = nz
    
    #total pressure with new density and tempeturate profiles
    newPtot = newNe * newTe + newTi * newNi + tz*newNz

    newomte = -1.0/newTe*fd_d1_o4_uneven(newTe,rhot)
    omte0 = -1.0/te*fd_d1_o4_uneven(te,rhot)
    #plt.plot(omte0)
    #plt.show()

    plt.title('alpha='+str(alpha))
    plt.plot(rhot,omte0,label='omte old')
    plt.plot(rhot,target_factor*omte0,'--',color='black',label='target')
    plt.plot(rhot,newomte,label='omte new')
    ax = plt.axis()
    print ("ax"+str(ax))
    plt.axis([0.9,1.0,0.0,ax[3]])
    plt.legend()
    plt.show()

if mode == 'omt':
    midPedIndex = np.argmin(abs(rhot - rhotMidPed))
    teMidPed = te[midPedIndex]
    tiMidPed = ti[midPedIndex]
    print ('rhot ='+str( rhotMidPed))
    print ('te ='+str( teMidPed))
    print ('ti ='+str( tiMidPed))

    newTe = teMidPed*np.power(te/teMidPed,alpha)
    newTi = tiMidPed*np.power(ti/tiMidPed,alpha)

    newNe = ne
    newNi = ni
    newNz = nz
    
    #total pressure with new density and tempeturate profiles
    newPtot = newNe * newTe + newTi * newNi + tz*newNz

    newomte = -1.0/newTe*fd_d1_o4_uneven(newTe,rhot)
    omte0 = -1.0/te*fd_d1_o4_uneven(te,rhot)
    newomti = -1.0/newTi*fd_d1_o4_uneven(newTi,rhot)
    omti0 = -1.0/ti*fd_d1_o4_uneven(ti,rhot)

    plt.title('alpha='+str(alpha))
    plt.plot(rhot,omte0,label='omte old')
    plt.plot(rhot,target_factor*omte0,'--',color='black',label='target')
    plt.plot(rhot,newomte,label='omte new')
    ax = plt.axis()
    print ("ax"+str(ax))
    plt.axis([0.0,1.0,0.0,ax[3]])
    plt.legend()
    plt.show()

    plt.title('alpha='+str(alpha))
    plt.plot(rhot,omti0,label='omti old')
    plt.plot(rhot,target_factor*omti0,'--',color='black',label='target')
    plt.plot(rhot,newomti,label='omti new')
    ax = plt.axis()
    print ("ax"+str(ax))
    plt.axis([0.0,1.0,0.0,ax[3]])
    plt.legend()
    plt.show()


if mode == 'omne':
    midPedIndex = np.argmin(abs(rhot - rhotMidPed))
    neMidPed = ne[midPedIndex]
    print('rhot ='+str(rhotMidPed))
    print('ne ='+ str(neMidPed))

    newNe = neMidPed*np.power(ne/neMidPed,alpha)
    newNi = newNe/ne*ni
    #newNz = newNe/ne*nz
    qz = float(input("Enter charge of impurity species:"))
    newNz = (newNe - newNi)/qz

    newTe = te
    newTi = ti

    newomne = -1.0/newNe*fd_d1_o4_uneven(newNe,rhot)
    omne0 = -1.0/ne*fd_d1_o4_uneven(ne,rhot)
    
    #total pressure with new density and tempeturate profiles
    newPtot = newNe * newTe + newTi * newNi + tz*newNz

    #qz = float(input("Enter charge of impurity species:"))

    qltest = np.sum(newNi-newNe+qz*newNz)/np.sum(newNe)
    print("Test of quasineutrality (should be <<1):"+str(qltest))
 
    plt.plot(rhot,newNe,label='new ne')
    plt.plot(rhot,newNi,label='new ni')
    plt.plot(rhot,newNz,label='new nz')
    plt.plot(rhot,newNi-newNe+qz*newNz,label='Test of quasineut.')
    plt.legend()
    plt.show()

    plt.title('alpha='+str(alpha))
    plt.plot(rhot,omne0,label='omn old')
    plt.plot(rhot,target_factor*omne0,'--',color='black',label='target')
    plt.plot(rhot,newomne,label='omne new')
    ax = plt.axis()
    plt.axis([0.9,1.0,0.0,ax[3]])
    plt.legend()
    plt.show()


if mode == 'omti':
    print("alpha",alpha)
    midPedIndex = np.argmin(abs(rhot - rhotMidPed))
    tiMidPed = ti[midPedIndex]
    print ('rhot ='+str(rhotMidPed))
    print ('ti ='+str (tiMidPed))

    newTi = tiMidPed*np.power(ti/tiMidPed,alpha)
    newTe = te

    newNe = ne
    newNi = ni
    newNz = nz
    
    #total pressure with new density and tempeturate profiles
    newPtot = newNe * newTe + newTi * newNi + tz*newNz

    newomti = -1.0/newTi*fd_d1_o4_uneven(newTi,rhot)
    omti0 = -1.0/ti*fd_d1_o4_uneven(ti,rhot)
    #plt.plot(omte0)
    #plt.show()

    plt.title('alpha='+str(alpha))
    plt.plot(rhot,omti0,label='omti old')
    plt.plot(rhot,target_factor*omti0,'--',color='black',label='target')
    plt.plot(rhot,newomti,label='omti new')
    ax = plt.axis()
    print ("ax"+str(ax))
    plt.axis([0.9,1.0,0.0,ax[3]])
    plt.legend()
    plt.show()

if mode == 'etaTe':
    midPedIndex = np.argmin(abs(rhot - rhotMidPed))
    teMidPed = te[midPedIndex]
    tiMidPed = ti[midPedIndex]
    print ('rhot ='+str(rhotMidPed))
    print ('te ='+str (teMidPed))
    print ('ti ='+str (tiMidPed))

    newTe = teMidPed*np.power(te/teMidPed,alpha)
    #new Ti profile to keep total pressure the same
    newTi = (te*ne+ti*(nz+ni) - newTe*ne)/(ni+nz)

    newNe = ne
    newNi = ni
    newNz = nz
    
    #total pressure with new density and tempeturate profiles
    newPtot = newNe * newTe + newTi * newNi + tz*newNz

    etae0 = ne/te*fd_d1_o4_uneven(te,rhot)/fd_d1_o4_uneven(ne,rhot)
    newetae = newNe/newTe*fd_d1_o4_uneven(newTe,rhot)/fd_d1_o4_uneven(newNe,rhot)
    plt.title('alpha='+str(alpha))
    plt.plot(rhot,etae0,label='etae old')
    plt.plot(rhot,target_factor*etae0,'--',color='black',label='target')
    plt.plot(rhot,newetae,label='etae new')
    ax = plt.axis()
    plt.axis([0.9,1.0,0.0,6])
    plt.legend()
    plt.show()

if mode == 'omnz':
    Z = float(input('Enter Z of impurity:\n'))
    print ("Using Z= "+str(Z))
    midPedIndex = np.argmin(abs(rhot - rhotMidPed))
    nzMidPed = nz[midPedIndex]

    newNz = nzMidPed*np.power(nz/nzMidPed,alpha)
    #Must satisfy quasineutrality and constant pressure
    newNe = (Ptot - ti*newNz*(1-Z))/(ti+te)
    newNi = newNe-Z*newNz

    newTe = te
    newTi = ti
    
    #total pressure with new density and tempeturate profiles
    newPtot = newNe * newTe + newTi * newNi + tz*newNz

    omnz0 = fd_d1_o4_uneven(nz,rhot)/nz
    newomnz = fd_d1_o4_uneven(newNz,rhot)/newNz
    plt.title('alpha='+str(alpha))
    plt.plot(rhot,omnz0,label='omnz old')
    plt.plot(rhot,target_factor*omnz0,'--',color='black',label='target')
    plt.plot(rhot,newomnz,label='omnz new')
    ax = plt.axis()
    plt.axis([0.9,1.0,ax[2],ax[3]])
    plt.legend()
    plt.show()


if mode == 'TiTe':

    newTe = te*alpha
    #new Ti profile to keep total pressure the same
    newTi = (te*ne+ti*(nz+ni) - newTe*ne)/(ni+nz)

    newNe = ne
    newNi = ni
    newNz = nz
    
    #total pressure with new density and tempeturate profiles
    newPtot = newNe * newTe + newTi * newNi + tz*newNz

    plt.title('alpha='+str(alpha))
    plt.plot(rhot,te/ti,label='Te/Ti old')
    plt.plot(rhot,target_factor*te/ti,'--',color='black',label='target')
    plt.plot(rhot,newTe/newTi,label='Te/Ti new')
    ax = plt.axis()
    plt.axis([0.9,1.0,0.0,ax[3]])
    plt.legend()
    plt.show()

if mode == "setup_pfile":  #Get ptot from efit file and calculate fast ion component
    dummy = input("This mode of operation sets up a new template pfile with ptot and pb consistent with the profiles and efit file. \n \'pfile\' should be from a previous template and the efit file should be for the new case.\n (Press a key)")
    call(['my_efit_tools.py','-p','-n',efit_file_name])
    call(['my_efit_tools.py','-c',efit_file_name])
    pdata = np.genfromtxt('pressure_q_from_efit')
    psi_efit = pdata[:,0]
    ptot_efit = pdata[:,1]
    rtrp = np.genfromtxt('rt_rp_'+efit_file_name)
    rhot_conv = rtrp[:,0]
    psi_conv = rtrp[:,1]**2
    profe = np.genfromtxt(profilesName_e)
    rhote = profe[:,0]
    te_setup = profe[:,2] 
    ne_setup = profe[:,3] 
    te_psi = full_interp(te_setup,rhote,rhot_conv,psi_conv,psi_efit)
    ne_psi = full_interp(ne_setup,rhote,rhot_conv,psi_conv,psi_efit)
    profi = np.genfromtxt(profilesName_i)
    rhoti = profi[:,0]
    ti_setup = profi[:,2] 
    ni_setup = profi[:,3] 
    ti_psi = full_interp(ti_setup,rhoti,rhot_conv,psi_conv,psi_efit)
    ni_psi = full_interp(ni_setup,rhoti,rhot_conv,psi_conv,psi_efit)
    profz = np.genfromtxt(profilesName_z)
    rhotz = profz[:,0]
    tz_setup = profz[:,2] 
    nz_setup = profz[:,3] 
    tz_psi = full_interp(tz_setup,rhotz,rhot_conv,psi_conv,psi_efit)
    nz_psi = full_interp(nz_setup,rhotz,rhot_conv,psi_conv,psi_efit)
    ptot_profiles = te_psi*1000*e*ne_psi*1e19+ti_psi*1000*e*ni_psi*1e19+tz_psi*1000*e*nz_psi*1e19
    plt.plot(psi_efit,ptot_efit,label = 'Ptot from efit')
    plt.plot(psi_efit,ptot_profiles,label = 'Ptot from profiles')
    plt.xlabel('psi')
    plt.legend()
    plt.show()

    pb = ptot_efit - ptot_profiles  #Fast ion pressure
    plt.plot(psi_efit,pb,label = 'Pb (fast ions)')
    plt.plot(psi_efit,psi_efit-psi_efit,color = 'black')
    plt.xlabel('psi')
    plt.legend()
    plt.show()
    psi_cutoff = float(input("Enter psi valu at pedestal top.  A tanh function will be used to set Pb to zero roughly beyond this point..\n"))
    #ipsi_cutoff = np.argmin(abs(psi_efit-psi_cutoff))
    lam = 0.075
    delx = 0.03
    pbtanh = 0.5*(np.tanh((-psi_efit+(psi_cutoff-delx))/lam)+1)
    plt.plot(psi_efit,pbtanh)
    plt.show()

    pb *= pbtanh
    plt.plot(psi_efit,pb,label = 'Pb (fast ions)')
    plt.xlabel('psi')
    plt.legend()
    plt.show()
    pb = pb/1.0e3 #convert to kPa
    ptot_efit = ptot_efit/1.0e3

    pdict = read_pfile_direct(pfile)
    pdict2 = copy.deepcopy(pdict)
    print(pdict2.keys())

    psi_name = 'psinorm_pb(kPa)' 
    psi_pb = pdict2[psi_name]
    pbname = 'pb(kPa)'
    psi_ptot = pdict2['psinorm_ptot(kPa)']
    ptotname = 'ptot(kPa)'
    pb_out = interp(psi_efit,pb,psi_pb)
    ptot_out = interp(psi_efit,ptot_efit,psi_ptot)
    plt.plot(psi_ptot,ptot_out)
    plt.xlabel('psi')
    plt.title('ptot_out(psi_pfile)')
    plt.show()
    dptot = fd_d1_o4_uneven(ptot_out,psi_ptot)
    dpb = fd_d1_o4_uneven(pb_out,psi_pb)
    pdict2[ptotname] = ptot_out
    pdict2['dptot/dpsiN'] = dptot
    pdict2[pbname] = pb_out
    pdict2['dpb/dpsiN'] = dpb
    filename_out = 'pfile_setup_'+file_out_base
    dummy = input("\n\n\nOutputing file: "+filename_out+". Reminder modify \'pfile\' at the beginning of this script!!! \n(Press any key)\n")
    write_pfile(pdict2,filename_out)    

if set_Tesep:
    ix_Ts = np.argmin(abs(rhot-x0_Tsep)) 
    print ("ix_Ts"+str(ix_Ts))
    dtedx_ts = fd_d1_o4_uneven(newTe,rhot)
    dtedx0 = dtedx_ts[ix_Ts]
    c0 = newTe[ix_Ts] - lambda_Tsep * abs(dtedx0)
    for i in range(len(newTe)-ix_Ts):
       #print "i",i
       #print "rhot[ix_Ts+i]",rhot[ix_Ts+i]
       newTe[ix_Ts+i] = lambda_Tsep*abs(dtedx0)*np.e**((x0_Tsep-rhot[ix_Ts+i])/lambda_Tsep) + c0
    plt.plot(rhot[ix_Ts:],newTe[ix_Ts:])
    plt.show()

if mode != 'setup_pfile':
    plt.plot(rhot,ne,label='ne')
    plt.plot(rhot,newNe,label='new ne')
    plt.legend()
    plt.show()

    plt.plot(rhot,te,label='te')
    plt.plot(rhot,newTe,label='new te')
    plt.legend()
    plt.show()

    plt.plot(rhot,ti,label='ti')
    plt.plot(rhot,newTi,label='new ti')
    plt.legend()
    plt.show()

    plt.plot(rhot,Ptot,label='total P')
    plt.plot(rhot,newPtot,label='new total P')
    plt.legend()
    plt.show()

if mode != 'setup_pfile':
    time_str = '9999'
    add_string = '_alpha'+str(alpha0)+'_'+mode+'_x0_'+str(rhotMidPed)
    output_iterdb(rhot,rhop,newNe*1.E-19,newTe*1.E-3,newNi*1.E-19,newTi*1.E-3,file_out_base+add_string,base_number,time_str,nimp=newNz*1.E-19)
    f=open(profilesName_i+add_string,'w')
    f.write('# 1.rhot 2.rhop 3.T(kev) 4.n(10^19m^-3)\n#\n')
    np.savetxt(f,np.column_stack((rhot,rhop,newTi*1.0e-3,newNi*1.0e-19)))
    f.close()
    #f=open('gene_profiles_e'+file_out_base+add_string,'w')
    f=open(profilesName_e+add_string,'w')
    f.write('# 1.rhot 2.rhop 3.T(kev) 4.n(10^19m^-3)\n#\n')
    np.savetxt(f,np.column_stack((rhot,rhop,newTe*1.0e-3,newNe*1.0e-19)))
    f.close()
    #f=open('gene_profiles_z'+file_out_base+add_string,'w')
    f=open(profilesName_z+add_string,'w')
    f.write('# 1.rhot 2.rhop 3.T(kev) 4.n(10^19m^-3)\n#\n')
    if set_tz_eq_ti:
        np.savetxt(f,np.column_stack((rhot,rhop,newTi*1.0e-3,newNz*1.0e-19)))
    else:
        np.savetxt(f,np.column_stack((rhot,rhop,tz*1.0e-3,newNz*1.0e-19)))
    f.close()

#quants = ['ne(10^20/m^3)']
#grads = ['dne/dpsiN']
#quants.append('te(KeV)')
#grads.append('dte/dpsiN')
#quants.append('ni(10^20/m^3)')
#grads.append('dni/dpsiN')
#quants.append('ti(KeV)')
#quants.append('ti(keV)')
#grads.append('dti/dpsiN')
#grads.append('dti/dpsiN')
#quants.append('nb(10^20/m^3)')
#grads.append('dnb/dpsiN')
#quants.append('pb(kPa)')
#grads.append('dpb/dpsiN')
#quants.append('ptot(kPa)') 
#grads.append('dptot/dpsiN')
#quants.append('nz1(10^20/m^3)') 
#grads.append('dnz1/dpsiN')

if output_pfile and mode != 'setup_pfile':
    pdict = read_pfile_direct(pfile)
    pdict2 = copy.deepcopy(pdict)
    print('keys',pdict2.keys())
    call(['my_efit_tools.py','-c',efit_file_name])
    rtrp_file = 'rt_rp_'+efit_file_name
    rtrp = np.genfromtxt(rtrp_file)
    dummy = input("Reading rhot rhop conversion from : "+rtrp_file)
    rhot_conv = rtrp[:,0]
    psi_conv = rtrp[:,1]**2
    psi0 = interp(rhot_conv,psi_conv,rhot)

    psi_name = 'psinorm_ne(10^20/m^3)' 
    psi = pdict2[psi_name]
    ne_new = interp(psi0,newNe,psi)
    ne_new = ne_new*1e-20
    dnedpsi = fd_d1_o4_uneven(ne_new,psi)
    pdict2['ne(10^20/m^3)'] = ne_new
    pdict2['dne/dpsiN'] = dnedpsi

    psi_name = 'psinorm_ni(10^20/m^3)' 
    psi = pdict2[psi_name]
    ni_new = interp(psi0,newNi,psi)
    ni_new = ni_new*1e-20
    dnidpsi = fd_d1_o4_uneven(ni_new,psi)
    pdict2['ni(10^20/m^3)'] = ni_new
    pdict2['dni/dpsiN'] = dnidpsi

    psi_name = 'psinorm_nz1(10^20/m^3)' 
    psi = pdict2[psi_name]
    nz_new = interp(psi0,newNz,psi)
    nz_new = nz_new*1e-20
    dnzdpsi = fd_d1_o4_uneven(nz_new,psi)
    pdict2['nz1(10^20/m^3)'] = nz_new
    pdict2['dnz1/dpsiN'] = dnzdpsi

    psi_name = 'psinorm_te(KeV)' 
    psi = pdict2[psi_name]
    te_new = interp(psi0,newTe,psi)
    te_new = te_new*1e-3
    dtedpsi = fd_d1_o4_uneven(te_new,psi)
    pdict2['te(KeV)'] = te_new
    pdict2['dte/dpsiN'] = dtedpsi

    psi_name = 'psinorm_ti(KeV)' 
    psi = pdict2[psi_name]
    ti_new = interp(psi0,newTi,psi)
    ti_new = ti_new*1e-3
    dtidpsi = fd_d1_o4_uneven(ti_new,psi)
    pdict2['ti(KeV)'] = ti_new
    pdict2['dti/dpsiN'] = dtidpsi

    dummy = input("Warning: not writing separate tz in pfile!!!")

    psi_name = 'psinorm_ptot(kPa)' 
    psi = pdict2[psi_name]
    ptot_new = interp(psi0,newPtot,psi)*e/1e3
    pb_add = interp(pdict2['psinorm_pb(kPa)'],pdict2['pb(kPa)'],pdict2[psi_name])
    if include_fast_ion_pressure_from_pfile:
        ptot_new += pb_add
    ptot_old = pdict2['ptot(kPa)']

    dptotdpsi = fd_d1_o4_uneven(ptot_new,psi)
    plt.plot(psi,ptot_old,label='old ptot(psi) from '+pfile)
    plt.plot(psi,ptot_new,label='new ptot(psi)')
    plt.xlabel('psi')
    plt.legend()
    plt.show()
    pdict2['ptot(kPa)'] = ptot_new
    pdict2['dptot/dpsiN'] = dptotdpsi

    filename_out = str(pfile)+'_alpha'+str(alpha0)+'_'+mode
    if include_fast_ion_pressure_from_pfile:
        filename_out += 'with_pb'
    print(pdict2.keys())
    write_pfile_mod(pdict2,filename_out)
    #write_pfile(pdict2,filename_out)    


