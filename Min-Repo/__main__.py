import numpy as np
import myModule


a = np.arange(12.0, dtype=np.single)
a = np.resize(a, (2,2,3))
print(a)
print(myModule.addition(a*2, a))

