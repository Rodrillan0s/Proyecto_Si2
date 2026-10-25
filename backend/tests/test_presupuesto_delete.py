import unittest
from unittest.mock import patch

from app.services import presupuesto_services as service


TOKEN = {
    "id_empresa": 7,
    "nro_usuario": 21,
    "nombre_rol": "JEFE DE OBRA",
}

OBRA = {
    "id_obra": 9,
    "id_empresa": 7,
    "codigo": "OB-9",
}

PRESUPUESTO = {
    "id_presupuesto": 3,
    "id_obra": 9,
    "id_empresa": 7,
    "codigo": "PRE-3",
    "nombre": "Presupuesto base",
    "estado": "BORRADOR",
}


class PresupuestoDeleteTests(unittest.TestCase):
    def test_elimina_borrador_de_la_obra_y_registra_bitacora(self):
        with patch.object(service, "_validar_obra", return_value=OBRA), patch.object(
            service, "_validar_presupuesto", return_value=PRESUPUESTO
        ), patch.object(
            service.presupuesto_repos, "eliminar_presupuesto", return_value=(3,)
        ) as delete, patch.object(
            service.bitacora_repos, "registrar_bitacora"
        ) as log:
            result = service.eliminar_presupuesto(9, 3, TOKEN, "127.0.0.1")

        self.assertTrue(result["success"])
        delete.assert_called_once_with(3)
        log.assert_called_once()

    def test_rechaza_presupuesto_que_no_pertenece_a_la_obra(self):
        presupuesto_otra_obra = {**PRESUPUESTO, "id_obra": 10}
        with patch.object(service, "_validar_obra", return_value=OBRA), patch.object(
            service, "_validar_presupuesto", return_value=presupuesto_otra_obra
        ), patch.object(service.presupuesto_repos, "eliminar_presupuesto") as delete:
            with self.assertRaises(service.PresupuestoError) as error:
                service.eliminar_presupuesto(9, 3, TOKEN, "127.0.0.1")

        self.assertEqual(error.exception.status_code, 400)
        delete.assert_not_called()

    def test_no_reporta_exito_si_el_borrador_cambio_antes_del_delete(self):
        with patch.object(service, "_validar_obra", return_value=OBRA), patch.object(
            service, "_validar_presupuesto", return_value=PRESUPUESTO
        ), patch.object(
            service.presupuesto_repos, "eliminar_presupuesto", return_value=None
        ), patch.object(service.bitacora_repos, "registrar_bitacora") as log:
            with self.assertRaises(service.PresupuestoError) as error:
                service.eliminar_presupuesto(9, 3, TOKEN, "127.0.0.1")

        self.assertEqual(error.exception.status_code, 409)
        log.assert_not_called()

    def test_rechaza_usuario_sin_empresa_autorizada(self):
        with patch.object(
            service.presupuesto_repos, "obtener_obra_por_id", return_value=OBRA
        ):
            with self.assertRaises(service.PresupuestoError) as error:
                service._validar_obra(9, {"nro_usuario": 21, "nombre_rol": "JEFE DE OBRA"})

        self.assertEqual(error.exception.status_code, 403)


class ApuMaterialCatalogTests(unittest.TestCase):
    MATERIAL = {
        "id_material": 12,
        "nombre_material": "Cemento",
        "id_unidad_medida": 4,
        "precio": 65.0,
        "id_empresa": 7,
        "estado": "ACTIVO",
        "unidad_medida_abreviatura": "bolsa",
    }

    def test_creacion_apu_usa_nombre_unidad_y_precio_del_catalogo(self):
        payload = {
            "codigo": "APU-1",
            "nombre": "Muro",
            "id_unidad_medida": 2,
            "componentes": [{
                "tipo_recurso": "MATERIAL",
                "id_recurso": 12,
                "descripcion_recurso": "Nombre alterado",
                "id_unidad_medida": 99,
                "rendimiento": 0.2,
                "precio_unitario": 999,
            }],
        }
        with patch.object(
            service.presupuesto_repos, "obtener_material_catalogo_apu", return_value=self.MATERIAL
        ), patch.object(
            service.presupuesto_repos, "crear_apu", return_value=30
        ), patch.object(
            service.presupuesto_repos, "agregar_componente_apu", return_value=40
        ) as add_component, patch.object(
            service.presupuesto_repos, "recalcular_costo_unitario_apu"
        ), patch.object(
            service.bitacora_repos, "registrar_bitacora"
        ):
            result = service.crear_apu(payload, TOKEN, "127.0.0.1")

        self.assertTrue(result["success"])
        self.assertEqual(
            add_component.call_args.kwargs,
            {
                "id_apu": 30,
                "tipo_recurso": "MATERIAL",
                "descripcion_recurso": "Cemento",
                "id_unidad_medida": 4,
                "cantidad": 0.2,
                "precio_unitario": 65.0,
                "id_recurso": 12,
                "rendimiento": 0.2,
            },
        )

    def test_rechaza_material_de_otra_empresa_antes_de_crear_apu(self):
        material_otra_empresa = {**self.MATERIAL, "id_empresa": 8}
        payload = {
            "codigo": "APU-1",
            "nombre": "Muro",
            "id_unidad_medida": 2,
            "componentes": [{
                "tipo_recurso": "MATERIAL",
                "id_recurso": 12,
                "rendimiento": 0.2,
            }],
        }
        with patch.object(
            service.presupuesto_repos,
            "obtener_material_catalogo_apu",
            return_value=material_otra_empresa,
        ), patch.object(service.presupuesto_repos, "crear_apu") as create:
            with self.assertRaises(service.PresupuestoError) as error:
                service.crear_apu(payload, TOKEN, "127.0.0.1")

        self.assertEqual(error.exception.status_code, 403)
        create.assert_not_called()

    def test_requiere_cantidad_consumida(self):
        with patch.object(
            service.presupuesto_repos,
            "obtener_material_catalogo_apu",
            return_value=self.MATERIAL,
        ):
            with self.assertRaisesRegex(
                service.PresupuestoError, "cantidad consumida"
            ):
                service._normalizar_material_catalogo_apu(
                    {"id_recurso": 12}, id_empresa=7
                )

    def test_adicion_a_apu_ignora_unidad_y_precio_enviados_por_cliente(self):
        apu = {"id_apu": 30, "id_empresa": 7}
        with patch.object(
            service, "_validar_apu", return_value=apu
        ), patch.object(
            service.presupuesto_repos,
            "obtener_material_catalogo_apu",
            return_value=self.MATERIAL,
        ), patch.object(
            service.presupuesto_repos, "apu_en_uso_por_partidas", return_value=False
        ), patch.object(
            service.presupuesto_repos, "agregar_componente_apu", return_value=40
        ) as add_component, patch.object(
            service.bitacora_repos, "registrar_bitacora"
        ):
            result = service.agregar_componente_apu(
                30,
                {
                    "tipo_recurso": "MATERIAL",
                    "id_recurso": 12,
                    "descripcion_recurso": "Nombre falso",
                    "id_unidad_medida": 99,
                    "rendimiento": 0.2,
                    "precio_unitario": 999,
                },
                TOKEN,
                "127.0.0.1",
            )

        self.assertTrue(result["success"])
        self.assertEqual(add_component.call_args.kwargs["descripcion_recurso"], "Cemento")
        self.assertEqual(add_component.call_args.kwargs["id_unidad_medida"], 4)
        self.assertEqual(add_component.call_args.kwargs["precio_unitario"], 65.0)
        self.assertEqual(add_component.call_args.kwargs["rendimiento"], 0.2)


if __name__ == "__main__":
    unittest.main()
