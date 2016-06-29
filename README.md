#VISSIM Tools
Load, manipulate and create VISSIM v5.x networks using Python.

##Current VISSIM objects supported:
- Vehicle Inputs
- Links
- Connectors
- Route Decisions
- Parking Zones
- Transit
- Nodes

##Current methods supported:
- Import data from .INP file
- Export data to .INP file
- Create objects

##Install:
    ``` python
    python setup.py install

##Usage:
```python
import vissim

Links = vissim.Links('example.inp')
# Loaded link data
Links.links_data
# Create link from coord 0,0 to 10,15
Links.create_link((0,0), (10,15))
# Export loaded link data and new link
Links.export_links('example_new.inp')
```
