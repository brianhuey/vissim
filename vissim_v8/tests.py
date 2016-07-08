import vissim_v8 as vissim

links = vissim.Links('test_networks/Busmall.inpx')

links.getLink(1)

links.getGeometry(1)

links.getLanes(1)