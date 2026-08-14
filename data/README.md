# Data drop zone

The local application reads `data/parcels/sa-parcels.gpkg`. GeoPackages are ignored by Git because the source dataset is large.

- `data/parcels/` ? parcel boundaries, parcel IDs, addresses, land area, frontage/depth, and geometry references.
- `data/planning/` ? zoning, overlays, maximum height/storeys, site coverage, floor-area ratio, minimum lot sizes, and any other controls.

The current GeoPackage contains parcel polygons, area, estimated zone, zone category, storeys, minimum lot size, and heritage/restriction flags. Frontage, depth, address, and suburb are not included in this source.
