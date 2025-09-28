# src/02_zeb_opportunity_analysis.py
import geopandas as gpd
import pandas as pd
import numpy as np
import os
from sklearn.preprocessing import minmax_scale
import matplotlib.pyplot as plt
from utils import add_north_arrow, add_scale_bar, ensure_dir

def enhanced_topsis(matrix, weights, benefit_criteria):
    """Performs TOPSIS analysis with normalized data."""
    norm_matrix = matrix / np.sqrt(np.sum(matrix**2, axis=0))
    weighted_matrix = norm_matrix * weights
    
    pis = np.zeros(matrix.shape[1])
    nis = np.zeros(matrix.shape[1])
    
    for i in range(matrix.shape[1]):
        if i in benefit_criteria:
            pis[i] = np.max(weighted_matrix[:, i])
            nis[i] = np.min(weighted_matrix[:, i])
        else: # Cost criteria
            pis[i] = np.min(weighted_matrix[:, i])
            nis[i] = np.max(weighted_matrix[:, i])
            
    dist_pis = np.sqrt(np.sum((weighted_matrix - pis)**2, axis=1))
    dist_nis = np.sqrt(np.sum((weighted_matrix - nis)**2, axis=1))
    
    closeness = dist_nis / (dist_pis + dist_nis)
    return closeness

def main():
    """Main function to run the ZEB opportunity analysis."""
    processed_path = "data/processed"
    output_path = "output"
    reports_path = os.path.join(output_path, "reports")
    figures_path = os.path.join(output_path, "figures")
    ensure_dir(reports_path)
    ensure_dir(figures_path)

    # Load data
    try:
        gdf_layers = gpd.read_file(os.path.join(processed_path, "LSMD_CONT_ALL.gpkg"))
        gdf_admin = gpd.read_file(os.path.join(processed_path, "LSMD_CONT_ADMIN_ALL.gpkg"))
    except Exception as e:
        print(f"Error loading data: {e}. Please run script '01_geospatial_preprocessing.py' first.")
        return

    # Calculate indicators per administrative region
    results = []
    for index, region in gdf_admin.iterrows():
        region_geom = region.geometry
        
        supply_area = gpd.overlay(gdf_layers[gdf_layers['SOURCE'] == 'Supply'], gpd.GeoDataFrame([region], columns=['geometry'], crs=gdf_admin.crs), how='intersection').area.sum()
        demand_area = gpd.overlay(gdf_layers[gdf_layers['SOURCE'] == 'Demand'], gpd.GeoDataFrame([region], columns=['geometry'], crs=gdf_admin.crs), how='intersection').area.sum()
        env_area = gpd.overlay(gdf_layers[gdf_layers['SOURCE'] == 'Environment'], gpd.GeoDataFrame([region], columns=['geometry'], crs=gdf_admin.crs), how='intersection').area.sum()
        
        results.append({
            'SIDO_NM': region['SIDO_NM'],
            'supply_ratio': supply_area / region_geom.area if region_geom.area > 0 else 0,
            'demand_ratio': demand_area / region_geom.area if region_geom.area > 0 else 0,
            'env_constraint_ratio': env_area / region_geom.area if region_geom.area > 0 else 0,
        })
    
    df_analysis = pd.DataFrame(results)
    
    indicator_matrix = df_analysis[['supply_ratio', 'demand_ratio', 'env_constraint_ratio']].values
    
    subjective_weights = np.array([0.4, 0.4, 0.2])
    benefit_criteria = [0, 1] # supply_ratio, demand_ratio
    
    zeb_index = enhanced_topsis(indicator_matrix, subjective_weights, benefit_criteria)
    df_analysis['ZEB_Opportunity_Index'] = minmax_scale(zeb_index, feature_range=(0, 100))
    
    gdf_results = gdf_admin.merge(df_analysis, on='SIDO_NM')
    
    output_csv = os.path.join(reports_path, "zeb_opportunity_index.csv")
    gdf_results.drop(columns='geometry').to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f"ZEB Opportunity Index saved to {output_csv}")
    
    fig, ax = plt.subplots(1, 1, figsize=(12, 12))
    gdf_results.plot(column='ZEB_Opportunity_Index', cmap='viridis', linewidth=0.8, ax=ax, edgecolor='0.8', legend=True)
    ax.set_title('ZEB Opportunity Index by Region', fontdict={'fontsize': '16', 'fontweight': '3'})
    ax.set_axis_off()
    add_north_arrow(ax)
    add_scale_bar(ax)
    plt.savefig(os.path.join(figures_path, "zeb_opportunity_map.png"), dpi=300)
    print(f"Map saved to {os.path.join(figures_path, 'zeb_opportunity_map.png')}")
    plt.close()

if __name__ == "__main__":
    main()