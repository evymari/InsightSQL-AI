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
            result = await run_pipeline(test["message"], test["session_id"])
            
            # Validate intention decomposition
            if result.intencion.metrica:
                print(f"✅ Métrica detectada: {result.intencion.metrica}")
            else:
                print("❌ No se detectó métrica")
                
            if result.intencion.dimension:
                print(f"✅ Dimensión detectada: {result.intencion.dimension}")
            else:
                print("ℹ️ No se detectó dimensión")
                
            if result.intencion.filtro:
                print(f"✅ Filtro detectado: {result.intencion.filtro}")
            else:
                print("ℹ️ No se detectó filtro")
                
            if result.intencion.granularidad:
                print(f"✅ Granularidad detectada: {result.intencion.granularidad}")
            else:
                print("ℹ️ No se detectó granularidad")
            
            # Validate SQL generation
            if result.sql.query:
                print(f"✅ SQL generado: {result.sql.query[:100]}...")
                print(f"   Tiene LIMIT: {result.sql.tiene_limit}")
            else:
                print("❌ No se generó SQL")
            
            # Validate insights
            if result.insight.resumen_ejecutivo:
                print(f"✅ Resumen: {result.insight.resumen_ejecutivo[:80]}...")
            
            if result.advertencias:
                print(f"⚠️ Advertencias: {result.advertencias}")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    print("\n🎉 Testing completed!")


if __name__ == "__main__":
    asyncio.run(test_pipeline())
