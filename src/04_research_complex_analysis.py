# src/04_research_complex_analysis.py
import geopandas as gpd
import os
from utils import ensure_dir

def main():
    """
    Processes research complex data and calculates distances.
    """
    raw_path = "data/raw/04_research_complexes"
    processed_path = "data/processed"
    output_path = "output/reports"
    ensure_dir(output_path)
    
    geocoded_addresses_file = os.path.join(processed_path, "geocoded_addresses_with_admin.gpkg")
    
    if not os.path.isdir(raw_path):
        print(f"ERROR: Research complex data directory not found at '{raw_path}'.")
        return
    if not os.path.exists(geocoded_addresses_file):
        print(f"ERROR: Geocoded addresses not found. Run script 03 first.")
        return

    # We re-use the processing function from script 01
    from src.s01_geospatial_preprocessing import process_shapefiles_in_dir
    gdf_complexes = process_shapefiles_in_dir(raw_path, "ResearchComplex")
    
    if gdf_complexes is None:
        print("No research complexes were processed. Exiting.")
        return

    gdf_addresses = gpd.read_file(geocoded_addresses_file)
    gdf_addresses = gdf_addresses.to_crs(gdf_complexes.crs)
    
    gdf_joined = gpd.sjoin_nearest(gdf_addresses, gdf_complexes, distance_col="distance_to_complex")
    
    output_file = os.path.join(output_path, "addresses_with_distance_to_complex.csv")
    gdf_joined.drop(columns='geometry').to_csv(output_file, index=False, encoding='utf-8-sig')
    
    print(f"Analysis complete. Results saved to {output_file}")

if __name__ == "__main__":
    main()