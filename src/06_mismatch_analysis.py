# src/06_mismatch_analysis.py
import pandas as pd
import geopandas as gpd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import matplotlib.pyplot as plt
import os
from utils import ensure_dir

def main():
    """
    Integrates demand and supply indices to analyze the mismatch.
    """
    reports_path = "output/reports"
    figures_path = "output/figures"
    processed_path = "data/processed"
    ensure_dir(figures_path)

    demand_file = os.path.join(reports_path, "zeb_opportunity_index.csv")
    supply_file = os.path.join(reports_path, "comprehensive_paper_analysis.xlsx")
    admin_file = os.path.join(processed_path, "LSMD_CONT_ADMIN_ALL.gpkg")

    if not all(os.path.exists(f) for f in [demand_file, supply_file, admin_file]):
        print("ERROR: One or more required input files not found. Please run previous scripts first.")
        return

    df_demand = pd.read_csv(demand_file)
    df_supply_papers = pd.read_excel(supply_file)
    gdf_admin = gpd.read_file(admin_file)

    # For this example, we create a dummy 'SIDO_NM' column for papers.
    # In a real project, you would geocode institution addresses to get this information.
    if 'SIDO_NM' not in df_supply_papers.columns:
        print("Warning: 'SIDO_NM' column not found in paper data. Assigning regions randomly for demonstration.")
        sido_list = df_demand['SIDO_NM'].unique()
        df_supply_papers['SIDO_NM'] = np.random.choice(sido_list, size=len(df_supply_papers))

    df_supply_agg = df_supply_papers.groupby('SIDO_NM')['Technology_Supply_Index'].mean().reset_index()

    df_mismatch = pd.merge(df_demand, df_supply_agg, on='SIDO_NM', how='left').fillna(0)

    scaler = MinMaxScaler()
    df_mismatch['Demand_Normalized'] = scaler.fit_transform(df_mismatch[['ZEB_Opportunity_Index']])
    df_mismatch['Supply_Normalized'] = scaler.fit_transform(df_mismatch[['Technology_Supply_Index']])

    df_mismatch['Mismatch_Index'] = df_mismatch['Demand_Normalized'] - df_mismatch['Supply_Normalized']

    output_file = os.path.join(reports_path, "zeb_mismatch_analysis_results.xlsx")
    df_mismatch.to_excel(output_file, index=False)
    print(f"Mismatch analysis complete. Results saved to {output_file}")

    gdf_mismatch = gdf_admin.merge(df_mismatch, on='SIDO_NM')
    fig, ax = plt.subplots(1, 1, figsize=(12, 12))
    gdf_mismatch.plot(column='Mismatch_Index', cmap='RdBu_r', linewidth=0.8, ax=ax, edgecolor='0.8', legend=True,
                      legend_kwds={'label': "Mismatch Index (Demand - Supply)", 'orientation': "horizontal"})
    ax.set_title('Spatiotemporal Innovation Mismatch', fontdict={'fontsize': '16', 'fontweight': '3'})
    ax.set_axis_off()
    plt.savefig(os.path.join(figures_path, "mismatch_analysis_charts.png"), dpi=300)
    print(f"Mismatch map saved to {os.path.join(figures_path, 'mismatch_analysis_charts.png')}")
    plt.close()

if __name__ == "__main__":
    main()