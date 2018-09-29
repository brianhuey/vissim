# VISSIM Tools

## VISSIM v8.x (/vissim_v8)

### Current VISSIM objects supported:
- VISSIM network attributes and parameters
- Vehicle Inputs
- Links
- Static Route Decisions

### Current methods supported:
- Import data from .INPX file
- Export data to .INPX file
- Get object attributes
- Set object attributes 
- Create objects
- Remove objects

### Install:
``` python
python setup_v8.py install
```

### Usage:
```python
import vissim_v8 as vissim
v = vissim.Vissim('vissim_v8/example/Busmall.inpx')
links = v.Links
```
Access VISSIM object data:
```python
# Will output data for link 2
links[2]
```
Create new VISSIM objects:
```python
# Create link from coord 0,0 to 10,15
coords = {'points3D': [(0,0,0), (10,15,0)]}
links.createLink(**coords)
```
Export VISSIM model to new file:
```python
v.export('example_new.inpx')
```

## VISSIM v5.x (/vissim_v5)

### Current VISSIM objects supported:
- Vehicle Inputs
- Links
- Connectors
- Route Decisions

### Current methods supported:
- Import data from .INP file
- Export data to .INP file
- Get object attributes
- Set object attributes 
- Create objects

### Install:
``` python
python setup.py install
```

### Usage:
```python
import vissim_v5 as vissim

links = vissim.Links('example.inp')
# Create link from coord 0,0 to 10,15
links.create((0,0), (10,15))
# Export loaded link data and new link
links.export('example_new.inp')
```
