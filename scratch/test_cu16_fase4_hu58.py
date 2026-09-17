import sys
import requests

BASE_URL = "http://127.0.0.1:5000"

def run_test():
    print("=================================================================")
    print("TEST E2E CU16 FASE 4: HU58 PRESUPUESTO CONSOLIDADO, LÍNEA BASE & VERSIONADO")
    print("=================================================================")

    # 1. Login
    login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
        "login": "admin",
        "contrasena": "admin123"
    })
    if login_res.status_code != 200:
        print(f"FAILED LOGIN: {login_res.status_code} - {login_res.text}")
        sys.exit(1)

    token = login_res.json().get("token")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    print("1. Login exitoso como Administrador.")

    # 2. Obtener una obra activa
    obras_res = requests.get(f"{BASE_URL}/api/proyectos/", headers=headers)
    obras = obras_res.json().get("data", [])
    if not obras:
        print("FAILED: No hay obras registradas.")
        sys.exit(1)
    
    obra = obras[0]
    id_obra = obra["id_obra"]
    id_empresa = obra["id_empresa"]
    print(f"2. Obra seleccionada: ID {id_obra} - '{obra['nombre_obra']}' (Empresa: {id_empresa})")

    # Obtener una unidad de medida
    mats_res = requests.get(f"{BASE_URL}/api/materiales/unidades-medida", headers=headers)
    unidades = mats_res.json().get("data", [])
    id_unidad = unidades[0]["id_unidad_medida"] if unidades else 1

    # 3. Crear Presupuesto con Estimación Paramétrica
    presupuesto_payload = {
        "codigo": f"TEST-HU58-{id_obra}",
        "nombre": "Presupuesto Paramétrico y Analítico Edificio",
        "descripcion": "Prueba E2E HU58 de Consolidado y Aprobación",
        "superficie_m2": 500.0,
        "tipo_suelo": "Arcilloso Compacto",
        "costo_m2_estimado": 350.0,
        "monto_estimado_inicial": 175000.0,
        "observaciones": "Estimación preliminar 500 m2 a 350 USD/m2"
    }
    p_res = requests.post(f"{BASE_URL}/api/proyectos/{id_obra}/presupuestos/", json=presupuesto_payload, headers=headers)
    assert p_res.status_code == 200, f"Error creando presupuesto: {p_res.status_code} - {p_res.text}"
    p_data = p_res.json()["data"]
    id_presupuesto = p_data["id_presupuesto"]
    print(f"3. Presupuesto v{p_data['version']} creado con éxito. ID: {id_presupuesto}, Estado: {p_data['estado']}")

    # 4. Crear un APU con componentes desglosados (Material, Mano de Obra, Equipo)
    apu_payload = {
        "codigo": f"APU-HU58-{id_obra}",
        "nombre": "Hormigón Armado Columnas",
        "descripcion": "Dosificación 1:2:3",
        "id_unidad_medida": id_unidad,
        "id_obra": id_obra
    }
    apu_res = requests.post(f"{BASE_URL}/api/apus/", json=apu_payload, headers=headers)
    assert apu_res.status_code == 200, f"Error creando APU: {apu_res.text}"
    id_apu = apu_res.json()["id_apu"]

    # Agregar componentes: 1 Material, 1 Mano de obra, 1 Equipo
    requests.post(f"{BASE_URL}/api/apus/{id_apu}/componentes", json={
        "tipo_recurso": "MATERIAL",
        "descripcion_recurso": "Cemento Portland IP-30",
        "id_unidad_medida": id_unidad,
        "cantidad": 7.0,
        "precio_unitario": 55.0
    }, headers=headers) # Subtotal: 385.0

    requests.post(f"{BASE_URL}/api/apus/{id_apu}/componentes", json={
        "tipo_recurso": "MANO_OBRA",
        "descripcion_recurso": "Cuadrilla Especializada",
        "id_unidad_medida": id_unidad,
        "cantidad": 4.0,
        "precio_unitario": 120.0
    }, headers=headers) # Subtotal: 480.0

    requests.post(f"{BASE_URL}/api/apus/{id_apu}/componentes", json={
        "tipo_recurso": "EQUIPO",
        "descripcion_recurso": "Mezcladora 350L + Vibrador",
        "id_unidad_medida": id_unidad,
        "cantidad": 2.0,
        "precio_unitario": 60.0
    }, headers=headers) # Subtotal: 120.0
    # Costo unitario total del APU: 385 + 480 + 120 = 985.0
    print(f"4. APU ID {id_apu} configurado con 3 componentes (Material, Mano de Obra, Equipo).")

    # 5. Agregar 2 Partidas al presupuesto
    # Partida 1: con APU
    partida1_res = requests.post(f"{BASE_URL}/api/proyectos/{id_obra}/presupuestos/{id_presupuesto}/partidas", json={
        "codigo": "EST-01",
        "nombre": "Columnas de PB",
        "id_unidad_medida": id_unidad,
        "cantidad": 50.0, # 50 * 985 = 49250.0
        "id_apu": id_apu,
        "orden": 1
    }, headers=headers)
    assert partida1_res.status_code == 200, f"Error partida 1: {partida1_res.text}"

    # Partida 2: sin APU directo (costo alzado/otros)
    partida2_res = requests.post(f"{BASE_URL}/api/proyectos/{id_obra}/presupuestos/{id_presupuesto}/partidas", json={
        "codigo": "PRE-01",
        "nombre": "Replanteo y Nivelación Topográfica",
        "id_unidad_medida": id_unidad,
        "cantidad": 1.0,
        "precio_unitario": 5000.0,
        "orden": 2
    }, headers=headers)
    assert partida2_res.status_code == 200, f"Error partida 2: {partida2_res.text}"
    print("5. Dos partidas registradas en el presupuesto.")

    # 6. HU58: Obtener Presupuesto Consolidado
    cons_res = requests.get(f"{BASE_URL}/api/proyectos/{id_obra}/presupuestos/{id_presupuesto}/consolidado", headers=headers)
    assert cons_res.status_code == 200, f"Error consolidado: {cons_res.text}"
    cons_data = cons_res.json()["data"]
    
    tot = cons_data["total_presupuesto"]
    # Total esperado: 49250.0 + 5000.0 = 54250.0
    print(f"6. Consolidado obtenido exitosamente:")
    print(f"   - Total Presupuesto Analítico: {tot} BOB")
    print(f"   - Total Partidas: {cons_data['total_partidas']}")
    print(f"   - Desglose de Recursos:")
    for r in cons_data["desglose_recursos"]:
        print(f"     * {r['tipo_recurso']}: {r['monto_total']} BOB ({r['porcentaje']}%)")
    print(f"   - Comparativa Paramétrica:")
    param = cons_data["metricas_parametricas"]
    print(f"     * Superficie: {param['superficie_m2']} m2")
    print(f"     * Estimado Inicial: {param['monto_estimado_inicial']} BOB")
    print(f"     * Costo Real Analítico por m2: {param['costo_m2_analitico_real']} BOB/m2")
    print(f"     * Desviación respecto al preliminar: {param['desviacion_monto']} BOB ({param['desviacion_porcentaje']}%)")
    
    assert tot == 54250.0, f"Total esperado 54250.0, obtenido {tot}"
    assert len(cons_data["partidas"]) == 2

    # 7. Cambiar estado a EN_REVISION
    st_res = requests.patch(f"{BASE_URL}/api/proyectos/{id_obra}/presupuestos/{id_presupuesto}/estado", json={
        "estado": "EN_REVISION"
    }, headers=headers)
    assert st_res.status_code == 200, f"Error cambiando estado: {st_res.text}"
    print("7. Estado del presupuesto actualizado a 'EN_REVISION'.")

    # 8. Aprobar Línea Base (HU58)
    aprob_res = requests.post(f"{BASE_URL}/api/proyectos/{id_obra}/presupuestos/{id_presupuesto}/aprobar", headers=headers)
    assert aprob_res.status_code == 200, f"Error aprobando presupuesto: {aprob_res.text}"
    aprob_data = aprob_res.json()["data"]
    assert aprob_data["estado"] == "APROBADO"
    assert aprob_data["es_vigente"] is True
    print(f"8. Presupuesto v{aprob_data['version']} APROBADO como Línea Base Vigente.")

    # 9. Intentar modificar partidas de presupuesto aprobado (Debe bloquearse)
    mod_partida_res = requests.post(f"{BASE_URL}/api/proyectos/{id_obra}/presupuestos/{id_presupuesto}/partidas", json={
        "codigo": "BLOQ-01",
        "nombre": "Partida Ilegal en Presupuesto Aprobado",
        "id_unidad_medida": id_unidad,
        "cantidad": 1.0,
        "precio_unitario": 100.0,
        "orden": 3
    }, headers=headers)
    assert mod_partida_res.status_code in (400, 422), f"Se esperaba rechazo en presupuesto aprobado: {mod_partida_res.status_code}"
    print("9. Bloqueo de mutaciones sobre presupuesto aprobado verificado con éxito.")

    # 10. HU58: Versionar Presupuesto (Crear Versión 2)
    ver_res = requests.post(f"{BASE_URL}/api/proyectos/{id_obra}/presupuestos/{id_presupuesto}/versionar", json={
        "nombre": "Presupuesto Ajustado v2"
    }, headers=headers)
    assert ver_res.status_code == 200, f"Error versionando presupuesto: {ver_res.text}"
    v2_data = ver_res.json()["data"]
    id_v2 = v2_data["id_presupuesto"]
    assert v2_data["version"] == 2
    assert v2_data["estado"] == "BORRADOR"
    assert v2_data["es_vigente"] is False
    assert v2_data["total_presupuesto"] == 54250.0
    print(f"10. Nueva Versión clonada con éxito: ID {id_v2}, v{v2_data['version']}, Estado: {v2_data['estado']}, es_vigente: {v2_data['es_vigente']}.")

    # 11. Aprobar Versión 2 y verificar alternancia atómica de vigencia (Línea Base v2)
    aprob_v2_res = requests.post(f"{BASE_URL}/api/proyectos/{id_obra}/presupuestos/{id_v2}/aprobar", headers=headers)
    assert aprob_v2_res.status_code == 200, f"Error aprobando v2: {aprob_v2_res.text}"
    print("11. Versión 2 aprobada con éxito.")

    # Verificar que v1 ahora es es_vigente = False y v2 es es_vigente = True
    p1_check = requests.get(f"{BASE_URL}/api/proyectos/{id_obra}/presupuestos/{id_presupuesto}", headers=headers).json()["data"]
    p2_check = requests.get(f"{BASE_URL}/api/proyectos/{id_obra}/presupuestos/{id_v2}", headers=headers).json()["data"]
    assert p1_check["es_vigente"] is False, "v1 debería haber perdido la vigencia."
    assert p2_check["es_vigente"] is True, "v2 debería ser la nueva versión vigente."
    print("12. Verificación de índice único y alternancia de vigencia superada con éxito (v1 inactiva, v2 vigente).")

    # Cleanup de prueba
    from app.classes.postgres import PostgreSQL
    db = PostgreSQL()
    db.create_connection()
    try:
        cur = db.conn.cursor()
        cur.execute("DELETE FROM obras.t_presupuesto WHERE id_presupuesto IN (%s, %s);", (id_presupuesto, id_v2))
        cur.execute("DELETE FROM obras.t_apu WHERE id_apu = %s;", (id_apu,))
        db.conn.commit()
        print("13. Limpieza de datos de prueba completada.")
    finally:
        db.close_connection()

    print("\n>>> TODOS LOS TESTS DE HU58 (CONSOLIDADO, APROBACIÓN LÍNEA BASE Y VERSIONADO) PASARON EXITOSAMENTE! <<<")

if __name__ == "__main__":
    run_test()
