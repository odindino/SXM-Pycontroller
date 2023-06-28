'''
 * (C) Copyright 02/2017 
 *
 * Anfatec Instruments AG 
 * Melanchthonstr. 28 
 * 08606 Oelsnitz/i.V.
 * Germany
 * http://www.anfatec.de/
 *
 * Feel free to use it.
 *
 
'''

class MyClass(object):
    def __init__(self):
        """Create a connection to a service/topic."""
        print("init")
		
    def __del__(self):
        print("del")
		
    def Test(sel, st):
        st=st+1.0
        print("Test used", st)
        st=st+1.0
        return st
		
print('start')		

MyInst=MyClass() #instance of MyClass
j=MyInst.Test(2.0)
print ('Input was 2.0, Output is '+str(j))



		
		

