from app.utils.security import es_admin_sistema


def test_empresa_obratec_es_global():
    token_data = {
        "nombre_rol": "ADMINISTRADOR",
        "nombre_empresa": "CONSTRUCTORA OBRATEC",
    }
    assert es_admin_sistema(token_data) is True


def test_empresa_distinta_no_es_global():
    token_data = {
        "nombre_rol": "ADMINISTRADOR",
        "nombre_empresa": "CONSTRUCTORA EL GRAN PIRAI",
    }
    assert es_admin_sistema(token_data) is False


def test_admin_empresa_no_es_global():
    token_data = {
        "nombre_rol": "ADMINISTRADOR_EMPRESA",
        "nombre_empresa": "CONSTRUCTORA OBRATEC",
    }
    assert es_admin_sistema(token_data) is False
