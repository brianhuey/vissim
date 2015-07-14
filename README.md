###VISSIM Tools
------------

Load, manipulate and create VISSIM v5.x networks using Python.

#Current VISSIM objects supported:
- Vehicle Inputs
- Links
- Connectors
- Route Decisions
- Parking Zones
- Transit
- Nodes

#Current methods supported:
- Import data from .INP file
- Export data to .INP file
- Create objects

#Install:
    - Copy folder to ~/Library/Python/<version>/lib/python/site-packages

#Usage:
```python
import vissim

Links = vissim.Links('file.inp')
# Loaded link data
Links.links_data
```
