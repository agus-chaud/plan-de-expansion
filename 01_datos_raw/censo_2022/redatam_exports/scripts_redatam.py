"""
Scripts para trabajar con los datos REDATAM del Censo 2022 - CABA
Hay dos enfoques:
1. Generar queries REDATAM para ejecutar en el portal online (redatam.indec.gob.ar)
2. Usar los CSV exportados (una vez que se exporten manualmente o vía RedatamX)
"""

# ============================================================
# PARTE 1: Generador de queries REDATAM (para portal online)
# ============================================================

def arealist_query(area_level, variables, area_filter=None, title=None):
    """Genera una query REDATAM tipo AREALIST."""
    lines = ["RUNDEF Job"]
    
    if area_filter:
        lines.append("    SELECTION INLINE,")
        area_type = list(area_filter.keys())[0]
        areas = area_filter[area_type]
        if not isinstance(areas, list):
            areas = [areas]
        lines.append(f"     {area_type} {', '.join(areas)}")
    
    lines.append("")
    lines.append("TABLE TABLE1")
    if title:
        lines.append(f'    TITLE "{title}"')
    lines.append("    AS AREALIST")
    
    if not isinstance(variables, list):
        variables = [variables]
    lines.append(f"    OF {area_level}, {', '.join(variables)}")
    
    return "\n".join(lines)


def freq_query(variable, area_filter=None, title=None):
    """Genera una query REDATAM tipo FREQ (frecuencias)."""
    lines = ["RUNDEF Job"]
    
    if area_filter:
        lines.append("    SELECTION INLINE,")
        area_type = list(area_filter.keys())[0]
        areas = area_filter[area_type]
        if not isinstance(areas, list):
            areas = [areas]
        lines.append(f"     {area_type} {', '.join(areas)}")
    
    lines.append("")
    lines.append("TABLE TABLE1")
    if title:
        lines.append(f'    TITLE "{title}"')
    lines.append("    AS FREQ")
    lines.append(f"    OF {variable}")
    
    return "\n".join(lines)


# ============================================================
# QUERIES PARA CABA (código provincia: 02) a nivel RADIO
# Pegar estas queries en https://redatam.indec.gob.ar
# usando la base "Base_VP" (Viviendas Particulares)
# ============================================================

QUERIES_CABA = {
    "viviendas_por_radio": arealist_query(
        area_level="RADIO",
        variables=["VIVIENDA.TIPOVIVG", "VIVIENDA.V02"],
        area_filter={"PROV": ["02"]},
        title="Viviendas por tipo y ocupacion - CABA por radio censal"
    ),
    "hogares_nbi": arealist_query(
        area_level="RADIO",
        variables=["HOGAR.NBI", "HOGAR.INMAT", "HOGAR.INCALSERV", "HOGAR.TOTPOBH"],
        area_filter={"PROV": ["02"]},
        title="NBI y condiciones habitacionales hogares - CABA por radio censal"
    ),
    "hogares_hacinamiento": arealist_query(
        area_level="RADIO",
        variables=["HOGAR.H10", "HOGAR.H11_H12", "HOGAR.HACIN"],
        area_filter={"PROV": ["02"]},
        title="Hacinamiento y materiales - CABA por radio censal"
    ),
    "educacion_por_radio": arealist_query(
        area_level="RADIO",
        variables=["PERSONA.NIVEL_ED", "PERSONA.CONDACT", "PERSONA.EDADGRU"],
        area_filter={"PROV": ["02"]},
        title="Nivel educativo y condicion de actividad - CABA por radio censal"
    ),
    "poblacion_basica": arealist_query(
        area_level="RADIO",
        variables=["PERSONA.P02", "PERSONA.EDADGRU", "PERSONA.EDADQUI"],
        area_filter={"PROV": ["02"]},
        title="Poblacion por sexo y edad - CABA por radio censal"
    ),
}

if __name__ == "__main__":
    import os
    
    out_dir = os.path.dirname(os.path.abspath(__file__))
    queries_dir = os.path.join(out_dir, "queries_redatam")
    os.makedirs(queries_dir, exist_ok=True)
    
    print("Queries REDATAM generadas para CABA (a nivel radio censal):")
    print("=" * 60)
    print(f"Guardar cada query en: {queries_dir}/")
    print()
    
    for nombre, query in QUERIES_CABA.items():
        filepath = os.path.join(queries_dir, f"{nombre}.rpf")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(query)
        print(f"✓ {nombre}.rpf")
        print(f"  {query.split(chr(10))[0]}")
    
    print()
    print("INSTRUCCIONES:")
    print("1. Ir a https://redatam.indec.gob.ar")
    print("2. Seleccionar 'Censo 2022' > 'Viviendas Particulares'")
    print("3. Ir a 'Procesador' > 'Editor REDATAM'")
    print("4. Pegar el contenido de cada .rpf y ejecutar")
    print("5. Exportar resultado como CSV y guardar en:")
    print(f"   {out_dir}/csv_output/")


# ============================================================
# PARTE 2: Procesar CSVs exportados (una vez disponibles)
# ============================================================

def cargar_csv_redatam(csv_path, cod_radio_col="REDCODEN"):
    """
    Carga un CSV exportado de REDATAM y filtra solo CABA.
    
    Args:
        csv_path: ruta al CSV exportado
        cod_radio_col: nombre de la columna con el código de radio censal
    
    Returns:
        DataFrame con datos de CABA
    """
    import pandas as pd
    
    df = pd.read_csv(csv_path, encoding="latin-1", sep=",")
    
    # Filtrar CABA (código 02)
    if cod_radio_col in df.columns:
        caba_mask = df[cod_radio_col].astype(str).str.startswith("02")
        df_caba = df[caba_mask].copy()
    else:
        print(f"Columna '{cod_radio_col}' no encontrada. Columnas disponibles: {list(df.columns)}")
        df_caba = df
    
    return df_caba


def merge_radios_caba(df_datos, shapefile_path=None):
    """
    Une datos censales con el shapefile de radios censales para CABA.
    
    Args:
        df_datos: DataFrame con datos por radio (debe tener columna cod_indec o REDCODEN)
        shapefile_path: ruta al shapefile de radios censales MGN 2022
    
    Returns:
        GeoDataFrame con datos + geometría
    """
    import geopandas as gpd
    import pandas as pd
    
    if shapefile_path is None:
        shapefile_path = "../../../cartografia/MGN_2022_radios/radios_censales_MGN2022.zip"
    
    # Cargar shapefile (dentro del zip)
    gdf = gpd.read_file(f"zip://{shapefile_path}")
    
    # Filtrar solo CABA
    gdf_caba = gdf[gdf["cpr"] == "02"].copy()
    
    # Normalizar código de radio
    if "REDCODEN" in df_datos.columns:
        key_datos = "REDCODEN"
    elif "cod_radio" in df_datos.columns:
        key_datos = "cod_radio"
    else:
        raise ValueError(f"No se encontró columna de código. Disponibles: {list(df_datos.columns)}")
    
    # Join por código de radio censal
    gdf_merged = gdf_caba.merge(
        df_datos,
        left_on="cod_indec",
        right_on=key_datos,
        how="left"
    )
    
    return gdf_merged
