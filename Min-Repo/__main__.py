import numpy as np
import myModule


a = np.arange(12.0, dtype=np.single)
a = np.resize(a, (2,2,3))

print(myModule.addition(a*2, a))
print(10*(a*2+a) + 10*(a*2+a*2))

