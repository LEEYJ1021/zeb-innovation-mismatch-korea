# src/03_address_geocoding.py
import pandas as pd
import geopandas as gpd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from shapely.geometry import Point
import os
from utils import ensure_dir

def main():
    """
    Geocodes addresses and joins them with administrative boundaries.
    """
    raw_path = "data/raw"
    processed_path = "data/processed"
    ensure_dir(processed_path)

    address_file = os.path.join(raw_path, "address_list_to_geocode.xlsx")
    admin_file = os.path.join(processed_path, "LSMD_CONT_ADMIN_ALL.gpkg")
    output_gpkg = os.path.join(processed_path, "geocoded_addresses_with_admin.gpkg")

    if not os.path.exists(address_file):
        print(f"ERROR: Address file not found at '{address_file}'. Please provide it.")
        return
    if not os.path.exists(admin_file):
        print(f"ERROR: Admin boundaries not found at '{admin_file}'. Please run script 01 first.")
        return

    df = pd.read_excel(address_file)
    if 'address' not in df.columns:
        print("ERROR: Excel file must contain a column named 'address'.")
        return

    geolocator = Nominatim(user_agent="zeb_mismatch_analysis_korea_v1")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)
    
    df['location'] = df['address'].apply(geocode)
    df['point'] = df['location'].apply(lambda loc: (loc.longitude, loc.latitude) if loc else None)
    
    df.dropna(subset=['point'], inplace=True)
    df[['longitude', 'latitude']] = pd.DataFrame(df['point'].tolist(), index=df.index)
    
    geometry = [Point(xy) for xy in zip(df['longitude'], df['latitude'])]
    gdf_points = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")
    
    gdf_admin = gpd.read_file(admin_file)
    gdf_points_proj = gdf_points.to_crs(gdf_admin.crs)
    
    gdf_joined = gpd.sjoin(gdf_points_proj, gdf_admin[['SIDO_NM', 'geometry']], how="left", predicate='within')
    
    gdf_joined.to_file(output_gpkg, driver="GPKG")
    print(f"Geocoded addresses with admin info saved to {output_gpkg}")

if __name__ == "__main__":
    main()