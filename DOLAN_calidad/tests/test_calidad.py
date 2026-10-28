from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestCalidad(TransactionCase):

    def setUp(self):
        super().setUp()
        self.punto = self.env["dolan.calidad.punto_control"].create({
            "name": "Peso de carga", "ambito": "producto",
        })
        self.ctrl = self.env["dolan.calidad.control"].create({
            "name": "CTRL-1", "punto_id": self.punto.id,
        })

    def test_ok_sin_nc(self):
        self.ctrl.action_marcar_ok()
        self.assertEqual(self.ctrl.resultado, "ok")
        self.assertFalse(self.ctrl.nc_ids)

    def test_ko_crea_nc(self):
        self.ctrl.action_marcar_ko()
        self.assertEqual(self.ctrl.resultado, "ko")
        self.assertEqual(len(self.ctrl.nc_ids), 1)
        nc = self.ctrl.nc_ids
        self.assertEqual(nc.estado, "abierta")
        # cerrar sin solucion no puede
        with self.assertRaises(UserError):
            nc.action_cerrar()
        nc.solucion = "Ajuste de balanza"
        nc.action_cerrar()
        self.assertEqual(nc.estado, "cerrada")

    def test_ko_no_duplica_nc(self):
        self.ctrl.action_marcar_ko()
        self.ctrl.action_marcar_ko()
        self.assertEqual(len(self.ctrl.nc_ids), 1)
