from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List
from arcgis.gis import GIS

app = FastAPI(title="ArcGIS Online Cloner API")

# Servir los archivos web estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

class CloneParams(BaseModel):
    url_origen: str = "https://www.arcgis.com"
    user_origen: str
    pass_origen: str
    url_destino: str = "https://www.arcgis.com"
    user_destino: str
    pass_destino: str
    item_ids: List[str]
    folder_destino: str = "Cloned_Content"

@app.get("/")
async def serve_index():
    return FileResponse("static/index.html")

@app.post("/api/clone")
async def process_clone(params: CloneParams):
    try:
        # 1. Autenticación en la organización de Origen
        gis_source = GIS(params.url_origen, params.user_origen, params.pass_origen)
        
        # 2. Autenticación en la organización de Destino
        gis_target = GIS(params.url_destino, params.user_destino, params.pass_destino)
        
        # 3. Validar y recuperar los elementos a clonar
        items_to_clone = []
        for item_id in params.item_ids:
            item = gis_source.content.get(item_id.strip())
            if item:
                items_to_clone.append(item)
            else:
                raise HTTPException(status_code=404, detail=f"Item ID no encontrado en origen: {item_id}")

        if not items_to_clone:
            raise HTTPException(status_code=400, detail="No se proporcionaron elementos válidos para clonar.")

        # 4. Clonar el contenido hacia el destino
        cloned_results = gis_target.content.clone_items(
            items=items_to_clone,
            folder=params.folder_destino,
            copy_data=True,
            search_existing_items=True
        )

        # Extraer información básica de los elementos creados
        result_summary = [
            {"id": item.id, "title": item.title, "type": item.type}
            for item in cloned_results
        ]

        return {
            "status": "exito",
            "mensaje": f"Se clonaron {len(cloned_results)} elementos correctamente.",
            "elementos_clonados": result_summary
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error durante el proceso: {str(e)}")