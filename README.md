`suraida` is a lightweight package facilitating
interactive plotting similar to Mathematica's `Manipulate`.
Given a function with multiple parameters, you want to
visualize the function and "play" with the parameters?
Jump into a jupyter notebook, import `suraida` and use
its `Manipulate` class like this:
```python
import suraida as sr
import numpy as np

def func(z, amplitude, omega, phase):
    return amplitude * np.sin(omega * z + phase)

sr.Manipulate(func,                          # the numerical function we wish to plot and manipulate parameters via sliders
              var_def=["z", 0, 7, 0.1],      # definition of the variable against which to plot `func`, specifying min, max and step
              param_defs=[
                  ["phase", [i*np.pi/5 for i in range(5)]],      # phase as list of allowed values
                  ["amplitude", 0, 2, 0.1],                # amplitude with min, max and step, default initial value is midpoint between min and max
                  ["omega", 0, 4, 0.1, 1.0]                # omega with min, max, step, ini
              ]
             )
```
<img src="https://github.com/scqubits/suraida/blob/main/display.gif" width="400" />


