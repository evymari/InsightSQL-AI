#!/usr/bin/env python3
"""
Script de prueba para validar el endpoint /api/chat
"""
import asyncio
import json
from app.agent.pipeline import run_pipeline


async def test_pipeline():
    """Test the pipeline without HTTP"""
    print("🧪 Testing InsightSQL Pipeline...")
    
    test_cases = [
        {
            "message": "ventas por mes en 2017",
            "session_id": "test-1",
            "expected_metrica": "ventas_totales",
            "expected_granularidad": "mensual"
        },
        {
            "message": "productos más vendidos por categoría",
            "session_id": "test-2", 
            "expected_metrica": "cantidad_ventas",
            "expected_dimension": "categoria_producto"
        },
        {
            "message": "promedio de calificación por estado",
            "session_id": "test-3",
            "expected_metrica": "promedio_calificacion",
            "expected_dimension": "estado"
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n--- Test {i}: {test['message']} ---")
        try:
            final_data = None
            async for event in run_pipeline(test["message"], test["session_id"]):
                event_type = event.get("type")
                stage = event.get("stage", "")
                if event_type == "stage":
                    print(f"⏳ {stage}: {event.get('message', '')}")
                elif event_type == "warning":
                    print(f"⚠️ {stage}: {event.get('message', '')}")
                elif event_type == "error":
                    print(f"❌ {stage}: {event.get('message', '')}")
                elif event_type == "final":
                    final_data = event.get("data")

            if not final_data:
                print("❌ El pipeline no emitió evento final")
                continue

            intencion = final_data.get("intencion", {})
            sql = final_data.get("sql", {})
            insight = final_data.get("insight", {})
            
            # Validate intention decomposition
            if intencion.get("metrica"):
                print(f"✅ Métrica detectada: {intencion.get('metrica')}")
            else:
                print("❌ No se detectó métrica")
                
            if intencion.get("dimension"):
                print(f"✅ Dimensión detectada: {intencion.get('dimension')}")
            else:
                print("ℹ️ No se detectó dimensión")
                
            if intencion.get("filtro"):
                print(f"✅ Filtro detectado: {intencion.get('filtro')}")
            else:
                print("ℹ️ No se detectó filtro")
                
            if intencion.get("granularidad"):
                print(f"✅ Granularidad detectada: {intencion.get('granularidad')}")
            else:
                print("ℹ️ No se detectó granularidad")
            
            # Validate SQL generation
            if sql.get("query"):
                print(f"✅ SQL generado: {sql.get('query')[:100]}...")
                print(f"   Tiene LIMIT: {sql.get('tiene_limit')}")
            else:
                print("❌ No se generó SQL")
            
            # Validate insights
            if insight.get("resumen_ejecutivo"):
                print(f"✅ Resumen: {insight.get('resumen_ejecutivo')[:80]}...")
            
            if final_data.get("advertencias"):
                print(f"⚠️ Advertencias: {final_data.get('advertencias')}")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    print("\n🎉 Testing completed!")


if __name__ == "__main__":
    asyncio.run(test_pipeline())
