#VISSIM Tools

##VISSIM v8.x (/vissim_v8)

###Current VISSIM objects supported:
- Vehicle Inputs
- Links
- Static Route Decisions

###Current methods supported:
- Import data from .INPX file
- Export data to .INPX file
- Get object attributes
- Set object attributes 
- Create objects
- Remove objects

###Install:
``` python
python setup.py install
```

###Usage:
```python
import vissim_v8 as vissim

links = vissim.Links('example.inpx')
# Create link from coord 0,0 to 10,15
coords = {'points3D': [(0,0,0), (10,15,0)]}
links.create(**coords)
# Export loaded link data and new link
links.export('example_new.inpx')
```

##VISSIM v5.x (/vissim_v5)

###Current VISSIM objects supported:
- Vehicle Inputs
- Links
- Connectors
- Route Decisions

###Current methods supported:
- Import data from .INP file
- Export data to .INP file
- Get object attributes
- Set object attributes 
<<<<<<< HEAD
=======
- Create objects

###Install:
``` python
python setup.py install
```

###Usage:
```python
import vissim_v5 as vissim

links = vissim.Links('example.inp')
# Create link from coord 0,0 to 10,15
links.create((0,0), (10,15))
# Export loaded link data and new link
links.export('example_new.inp')
```
