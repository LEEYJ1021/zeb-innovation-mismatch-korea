# src/01_geospatial_preprocessing.py
import os
import geopandas as gpd
import pandas as pd
import zipfile
import shutil
from utils import fix_korean, ensure_dir

def process_shapefiles_in_dir(target_dir, source_label, target_crs="EPSG:5179"):
    """
    Processes all shapefiles within a directory of zip files.
    - Extracts shapefiles from zips.
    - Reads, re-projects to a unified CRS.
    - Merges them into a single GeoDataFrame.
    """
    print(f"--- Processing directory: {target_dir} ---")
    if not os.path.isdir(target_dir):
        print(f"!!! WARNING: Directory not found: {target_dir}. Skipping.")
        return None

    gdf_list = []
    # Create a temporary extraction path inside the target directory
    extract_path = os.path.join(target_dir, "temp_extract")
    ensure_dir(extract_path)

    zip_files = [f for f in os.listdir(target_dir) if f.lower().endswith(".zip")]
    if not zip_files:
        print(f"No .zip files found in {target_dir}.")
        shutil.rmtree(extract_path)
        return None

    for item in zip_files:
        zip_path = os.path.join(target_dir, item)
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
                
                # Walk through the extracted files to find shapefiles
                for root, _, files in os.walk(extract_path):
                    for file in files:
                        if file.lower().endswith(".shp"):
                            shp_path = os.path.join(root, file)
                            try:
                                # Try reading with euc-kr, fallback to utf-8
                                try:
                                    gdf = gpd.read_file(shp_path, encoding="euc-kr")
                                except Exception:
                                    gdf = gpd.read_file(shp_path, encoding="utf-8")

                                # Unify CRS
                                if gdf.crs is None or gdf.crs.to_epsg() != 5179:
                                    gdf = gdf.to_crs(target_crs)
                                
                                gdf['SOURCE'] = source_label
                                gdf['ZIP_FILE'] = item
                                gdf_list.append(gdf)
                                print(f"  + Successfully loaded and processed {file}")
                            except Exception as e:
                                print(f"  - ERROR reading {file}: {e}")

        except (zipfile.BadZipFile, NotImplementedError) as e:
            print(f"Could not process zip file {item}: {e}")
        finally:
            # Clean up extracted files for the next zip
            shutil.rmtree(extract_path)
            ensure_dir(extract_path)

    if os.path.exists(extract_path):
        shutil.rmtree(extract_path)  # Final cleanup
    
    if not gdf_list:
        print(f"No shapefiles were successfully processed in {target_dir}.")
        return None
        
    merged_gdf = pd.concat(gdf_list, ignore_index=True)
    print(f"✅ Successfully merged {len(merged_gdf)} features from {source_label}.")
    return merged_gdf

def main():
    """
    Main function to run the geospatial preprocessing pipeline.
    This script generates the necessary GeoPackage (.gpkg) files from raw downloaded data.
    """
    base_raw_path = "data/raw"
    processed_path = "data/processed"
    ensure_dir(processed_path)

    print("STEP 1: Processing main geospatial layers (Supply, Demand, Environment)...")
    # Define directories for main layers
    dirs_to_process = {
        "Supply": os.path.join(base_raw_path, "02_geospatial_layers", "supply"),
        "Demand": os.path.join(base_raw_path, "02_geospatial_layers", "demand"),
        "Environment": os.path.join(base_raw_path, "02_geospatial_layers", "environment"),
    }

    # Process each category of geospatial layers
    all_gdfs = []
    for source, path in dirs_to_process.items():
        gdf = process_shapefiles_in_dir(path, source)
        if gdf is not None:
            all_gdfs.append(gdf)

    # Combine all layers into a single master file if any were processed
    if all_gdfs:
        all_layers = pd.concat(all_gdfs, ignore_index=True)
        output_gpkg_all = os.path.join(processed_path, "LSMD_CONT_ALL.gpkg")
        all_layers.to_file(output_gpkg_all, driver="GPKG", layer="all_layers")
        print(f"\n>>> All layers saved to {output_gpkg_all}\n")
    else:
        print("\n!!! ERROR: No main geospatial layers were processed. Cannot create LSMD_CONT_ALL.gpkg. Please check your raw data folders.\n")
        return

    print("STEP 2: Processing administrative boundaries...")
    admin_dir = os.path.join(base_raw_path, "03_administrative_boundaries")
    admin_gdf = process_shapefiles_in_dir(admin_dir, "AdminBoundary")
    
    if admin_gdf is not None:
        # Fix broken Korean characters in the administrative data
        for col in admin_gdf.select_dtypes(include=['object']).columns:
            admin_gdf[col] = fix_korean(admin_gdf[col])
        
        output_gpkg_admin = os.path.join(processed_path, "LSMD_CONT_ADMIN_ALL.gpkg")
        admin_gdf.to_file(output_gpkg_admin, driver="GPKG", layer="admin_boundaries")
        print(f"\n>>> Administrative boundaries saved to {output_gpkg_admin}\n")
    else:
        print("\n!!! ERROR: No administrative boundaries were processed. Please check the 'data/raw/03_administrative_boundaries' folder.\n")

if __name__ == "__main__":
    main()