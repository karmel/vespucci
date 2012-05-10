'''
Created on Apr 27, 2012

@author: karmel
'''
bmdc_up = set(['Pdlim4', 'Nrcam', 'Tmem26', 'Msl3l2', 'Pde5a', 'Mid1', 'Mfsd7c', 'Ctso', 'H2-M2', 'Mtap1b', 'Tspan32', 'Slc39a2', 'Msx3', 'Cyr61', 'Gja1', 'Dpys', 'Slc16a14', 'Fggy', 'Mertk', 'Cav1', 'Mrvi1', 'Plcb4', 'Cebpe', 'Arhgef18', 'Ifi204', 'Pard3b', 'Cxcl14', 'Col27a1,Mir455', 'E330020D12Rik', 'Cd97', '1600014C10Rik', 'Masp1', 'Pde3b', 'Fam110c', 'Trim6', 'Adra1a', 'Tmeff1', 'Iqgap2', 'Gpr98', 'Gata6', 'Tgm2', 'Ckb', 'Mett11d1', 'Abca5', 'Fblim1', 'Ica1', 'A930005I04Rik', 'Lrrc63', '1810010D01Rik', 'Zdhhc14', 'Dut', 'Tjp2', 'Hspa2', 'Tjp1', 'Bnc2', 'Nlrp10', 'Kalrn', 'Acp5', 'St3gal5', '9030425E11Rik', 'Gde1', 'Ms4a7', 'Gm4951', 'F3', 'Slc4a4', 'Fabp4', 'Isg15', 'Rab15', 'Fbp1', 'Slc24a5', 'Mpp7', 'Id3', 'Ctnnd2', 'Arid4a', 'Npl', 'Shroom4', 'Myo16', 'Havcr2', 'Siglec1', 'Col6a6', 'Fam59a', '2900041M22Rik', 'D630042F21Rik', 'Myo1d', 'Chrm3', 'Spns1', 'Adamts14', 'Prox2'])

bmdc_down = set(['Clec10a', 'Lyl1', '2310061I04Rik', 'Psap', 'Adora2b', 'BC049349', 'Tnfrsf9', 'Chek2', '1600029D21Rik', 'Ctsk', 'Ctsl', 'Cd244', 'Ccdc88c,Mir1190', 'Cd247', 'A730008H23Rik,Hjurp', 'Lrrc57', 'Gpr171', 'Nov', 'Ctss', 'Fam40b', 'Arhgap9', 'Csf3r', 'Tpp1', 'Tcfe3', 'Thbs1', 'Tiam2', 'Myadm', 'Igsf8', 'Slc26a11', 'Cdipt', 'Dock8', 'B930041F14Rik', 'Auts2', 'Gpr141', 'Cd22', 'Arg2', 'Zfp36l1', 'AA467197,Mir147', 'C230096C10Rik', 'Fn1', 'Dhrs9', 'Tyrobp', 'Il12rb2', 'Mylk', 'Runx3', 'Psmb8', 'Gpr52,Rabgap1l', 'Speg', 'Lgals1', 'Fkbp8', 'Gprc5a', 'H2-T23', 'Acap1', 'Lyz2', 'Tarm1', 'Xrcc1', 'Mmd', 'Syn3', 'Adcy6', 'Stat4', 'Fam65b', '1700029J11Rik', 'Fam20a', 'Cd83', 'Samd4', 'Tmem180', '5830416P10Rik', 'Stxbp6', 'Limd2', 'F10', 'Il1r2', 'Fam49a', 'Rasgrp4', 'Commd3', 'Egr1', 'Plcl1', 'Rcsd1', 'Stc2', 'Nos1ap', 'Ifitm3', 'Tox', '2410001C21Rik', 'Gbp1', 'Srgap3', 'Coro1a', 'Gfra2', 'Mmp25', 'Serpinb2', 'Traf1', 'Gja5', 'Tifab', 'Ltb4r1', 'Atp6ap1', 'Reep4', 'Sh3bp4', 'Slc22a23', 'Gpr132', 'Cd200', 'Miip', 'Fscn1', 'Ccbe1,Mir694', 'Igsf9b', 'Syne1', 'Tspan13', 'H2-Aa', 'Dpp4', 'Pid1', 'Taf10', 'Ccr5', 'Ccr7', 'Batf3', 'Gdpd3,Mapk3', 'Crip1', 'Abcb1b', 'Tmem123', 'F7', 'Tmem158', 'Gpr183', 'Vcan', 'Cd69', 'Fhl3', 'Adam23', 'Nrg1', 'Ikzf4', 'Ccl22', 'Slc4a8', 'Clec12a', 'Ccdc109b', 'Fstl1', 'Sgsh', '4930420K17Rik', 'Mavs', 'Cd52', 'H2-K2', 'Icosl', 'Cacnb3', 'H2-Ea-ps', 'P2ry10', 'Treml2', 'Rab3d', 'Adam15', 'Mmp8', 'Armc6', 'Cep70', 'Cdh2', 'Kif3a', 'Lrrc33', 'Glrp1', 'Cass4', 'Wnk2', 'Jmjd8', 'Rassf2', 'Htr7', 'Eps8', 'Hebp2', '5031414D18Rik', 'F630028O10Rik,Mir223', 'Cd200r4', 'Ahrr', 'F2rl2', 'Gpr160', 'Rap1gap2'])

thio_up = set(['Pdlim4', 'Plekhg1', 'Mir297-1', 'Cyp4f16', 'Cxcl2', 'D330045A20Rik', 'Selp', 'Tm7sf4', 'Isoc2b', 'Met', 'Eef1a2', 'H2-M2', 'Clec2g', 'Snph', 'Spp1', '1810011O10Rik', 'Gramd1b', 'Steap3', 'Nlrc5', 'Sumf2', 'Slc16a14', 'Fggy', 'Ptgs2', '9130008F23Rik', 'Enpp4', 'B430306N03Rik', 'Tnip3', 'Trem1', 'Col23a1', 'Lpcat1', 'Ptprm', 'Cxcl14', 'Adam33,Siglec1', 'Zdhhc14', 'Ttc23l', 'Naip1', 'Cd14', 'C5ar1', 'Itgax', 'Zranb3', 'Olr1', 'Tmeff1', 'Ryr2', 'Trim79', 'Gpc1,Mir149', 'Pglyrp2', 'Fkbp1a', 'Wfs1', 'H2-Q7', 'Olfr111', 'Chi3l1', 'BC046404', 'Ugt1a1,Ugt1a10,Ugt1a2,Ugt1a5,Ugt1a6a,Ugt1a6b,Ugt1a7c,Ugt1a9', 'Gpr77', 'Marco', 'Tnfrsf11b', 'Fblim1', '4930422G04Rik', 'Ms4a8a', 'Slc7a2', 'Tlr2', 'Abca5', 'BC021614', 'Cxcl1', 'Pdgfc', 'Htr2a', 'Tmem195', 'Abcb4', 'Tjp2', 'Gbgt1', 'Rgs20', 'Bcl2a1a', 'Ltbp1', 'Nlrp10', '9030425E11Rik', 'Plxnd1', 'Gdf15', 'BC018473', 'Abca8b', 'Acp5', '9330175E14Rik', 'Gde1', 'F3', 'Nlrp1a', 'Timp1', 'Tnfsf9', '9030625A04Rik', '1700054N08Rik', 'Gnb4', 'Ctnnd2', 'Mylk2', 'Ass1', 'Dapk1', 'Arhgap19', 'Dennd3', 'Sik1', 'Retsat', 'Clec4e', 'Mmp9', 'Mgll', 'Slpi', 'Akap2', 'Npl', 'Tmem221', 'Irg1', '1810033B17Rik', '1190002H23Rik', 'Ccdc88a', 'Myo1d', 'Mpp7', 'Lrrc27', 'Kcnn4', '5830417I10Rik'])

thio_down = set(['Cyp7b1', 'H28', 'Dhrs9', 'Kitl', 'Gbp1', 'Il12rb2', 'Fcgr2b', 'Mylk', 'Akr1e1', 'Sgsh', 'Speg', 'Gprc5a', 'Pppde2', 'Ctsk', 'Gm10345', 'Trim16', 'C230055K05Rik', 'H2-T23', 'Ntn1', 'Man2a2', 'Cd247', 'A730008H23Rik,Hjurp', 'Nr1h4', 'Syne1', 'Ifi44', 'Ccbe1,Mir694', 'Glrp1', 'Arsb', 'Acacb', 'H2-Q6', 'D10Bwg1379e', 'AI118078', 'Ndrg1', 'Tifab', 'Fstl1', 'Hoxa3,Hoxa4,Hoxa5,Hoxa6', 'Abcb1b', 'B930041F14Rik', 'Pcdh15', 'Pcnxl2', 'Arg2', 'Enpp2', 'Pls3', 'Trim68', 'Myo18b', 'Slco2b1', 'A630001G21Rik', 'Kdr', 'Nckap5l'])


print ','.join(bmdc_up & thio_up)
print ','.join(bmdc_down & thio_down)



'''
Pdlim4,Zdhhc14,F3,Npl,Tmeff1,H2-M2,Mpp7,Fggy,Tjp2,Abca5,Ctnnd2,Gde1,Cxcl14,Myo1d,Nlrp10
Abcb1b,Ctsk,Tifab,Glrp1,Dhrs9,Syne1,Gbp1,Il12rb2,Mylk,Fstl1,Cd247,A730008H23Rik,Hjurp,Arg2,Sgsh,Speg,Ccbe1,Mir694,B930041F14Rik,Gprc5a,H2-T23

Pdlim4: lots of NOD snps, 2x PU.1
Zdhhc14: lots of NOD snps 
F3: Some NOD snps
Npl: NOD + DBA snps, 2x PU.1
Tmeff1: less interesting
H2-M2: increased PU.1
Mpp7: rule out; lots of BALBc snps
Fggy: very long gene
Tjp2: lots of BALB snps; rule out
Abca5: very long, lots of NOD snps
Ctnnd2: very long, lots of snps
Gde1: lots of BALB snps; rule out
Cxcl14: 2x PU.1
Myo1d: lots of BALB snps; rule out
Nlrp10: 5x PU.1, NOD snps

Abcb1b: lots of NOD snps, 1/2 PU.1
Ctsk: lots of snps, total loss of intergenic PU.1 peak
Tifab: BALB snps, but not too many...
Glrp1: NOD and DBA snps. Total loss of NOD signal
Speg: much less PU.1, a few NOD snps
Ccbe1: Partial transcript?
H2-T23: Dupey, but less PU.1, and NOD snps



'''