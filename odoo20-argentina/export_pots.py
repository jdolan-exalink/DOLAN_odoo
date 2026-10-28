import io
MODULES = ["DOLAN_theme", "DOLAN_ai", "DOLAN_alquileres", "DOLAN_calidad", "DOLAN_codigo_barras",
           "DOLAN_contabilidad", "DOLAN_declaracion", "DOLAN_flotilla", "DOLAN_mantenimiento",
           "DOLAN_suscripciones", "DOLAN_taller", "DOLAN_bancos", "dolan_dash", "dolan_ui"]
def run(env):
    from odoo.tools.translate import TranslationModuleReader, TranslationFileWriter
    out = []
    for m in MODULES:
        try:
            reader = TranslationModuleReader(env.cr, modules=[m], lang=None)
            rows = list(reader)
            buf = io.BytesIO()
            writer = TranslationFileWriter(buf, "po", "pot")
            writer.write_rows(rows)
            with open("/tmp/%s.pot" % m, "wb") as fh:
                fh.write(buf.getvalue())
            out.append("%s OK (%d términos)" % (m, len(rows)))
        except Exception as e:
            out.append("%s FALLÓ: %s: %s" % (m, type(e).__name__, str(e)[:100]))
    print("POTS:\n" + "\n".join(out))
