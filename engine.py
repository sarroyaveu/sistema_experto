"""Motor de inferencia: encadenamiento hacia adelante con resolución de conflictos.

Formato de la base de conocimiento (JSON):
{
  "dominio": "...", "titulo": "...",
  "hechos": { "id": {"texto": "...", "tipo": "entrada|intermedio|recomendacion",
                     "grupo": "...", "detalle": "(solo recomendaciones)"} },
  "reglas": [ {"id": "R01", "nombre": "...", "antecedentes": [...],
               "consecuentes": [...], "prioridad": 0, "excluye": [...]} ]
}
"""
import json
from pathlib import Path


class KBError(ValueError):
    """Error de formato en la base de conocimiento."""


def _leer_json(origen):
    if isinstance(origen, (dict, list)):
        return origen
    if isinstance(origen, (str, Path)):
        with open(origen, encoding="utf-8") as f:
            return json.load(f)
    return json.loads(origen.read())  # archivo subido (file-like)


def cargar_kb(origen):
    kb = _leer_json(origen)
    for clave in ("dominio", "hechos", "reglas"):
        if clave not in kb:
            raise KBError(f"Falta la clave '{clave}' en la base de conocimiento")
    ids = set()
    for r in kb["reglas"]:
        for clave in ("id", "nombre", "antecedentes", "consecuentes"):
            if clave not in r:
                raise KBError(f"Una regla no tiene la clave '{clave}': {r}")
        if r["id"] in ids:
            raise KBError(f"Regla duplicada: {r['id']}")
        ids.add(r["id"])
        for h in r["antecedentes"] + r["consecuentes"] + r.get("excluye", []):
            if h not in kb["hechos"]:
                raise KBError(f"Regla {r['id']}: el hecho '{h}' no está declarado")
    return kb


def cargar_hechos(origen):
    """Acepta {"hechos": [...]}, una lista, o un dict {hecho: true/false}."""
    datos = _leer_json(origen)
    if isinstance(datos, dict) and "hechos" in datos:
        datos = datos["hechos"]
    if isinstance(datos, dict):
        return [h for h, v in datos.items() if v]
    return list(datos)


class MotorInferencia:
    def __init__(self, kb):
        self.kb = kb
        self.reglas = kb["reglas"]
        self.catalogo = kb["hechos"]

    # ---------- utilidades ----------
    def texto(self, h):
        return self.catalogo.get(h, {}).get("texto", h)

    def _es_recomendacion(self, r):
        return all(self.catalogo[c].get("tipo") == "recomendacion" for c in r["consecuentes"])

    def _aplicable(self, r, hechos):
        return (all(a in hechos for a in r["antecedentes"])
                and not any(x in hechos for x in r.get("excluye", []))
                and any(c not in hechos for c in r["consecuentes"]))  # aporta algo nuevo

    def _evaluar(self, i, r, hechos):
        recencia = tuple(sorted((hechos[a] for a in r["antecedentes"]), reverse=True))
        prio = r.get("prioridad", 0)
        esp = len(r["antecedentes"])
        return {"idx": i, "id": r["id"], "nombre": r["nombre"], "prioridad": prio,
                "recencia": recencia, "especificidad": esp,
                "clave": (prio, recencia, esp, -i)}

    @staticmethod
    def _motivo(ordenadas):
        if len(ordenadas) == 1:
            return "Es la única regla aplicable."
        a, b = ordenadas[0], ordenadas[1]
        if a["prioridad"] != b["prioridad"]:
            return f"Mayor prioridad explícita ({a['prioridad']} frente a {b['prioridad']})."
        if a["recencia"] != b["recencia"]:
            return "Usa hechos más recientes (criterio de recencia)."
        if a["especificidad"] != b["especificidad"]:
            return f"Es más específica ({a['especificidad']} antecedentes)."
        return "Empate total: se aplica el orden de definición en la base de conocimiento."

    # ---------- inferencia ----------
    def ejecutar(self, hechos_iniciales, max_pasos=500):
        no_reconocidos = [h for h in hechos_iniciales if h not in self.catalogo]
        hechos = {h: 0 for h in hechos_iniciales if h in self.catalogo}  # hecho -> paso en que apareció
        origen, disparadas, pasos = {}, set(), []

        while len(pasos) < max_pasos:
            candidatas = [self._evaluar(i, r, hechos) for i, r in enumerate(self.reglas)
                          if i not in disparadas and self._aplicable(r, hechos)]
            inferencia = [c for c in candidatas if not self._es_recomendacion(self.reglas[c["idx"]])]
            fase = "Inferencia" if inferencia else "Recomendación"
            conflicto = inferencia or candidatas
            if not conflicto:
                break

            conflicto.sort(key=lambda c: c["clave"], reverse=True)
            ganadora = conflicto[0]
            r = self.reglas[ganadora["idx"]]
            n = len(pasos) + 1
            disparadas.add(ganadora["idx"])

            nuevos = []
            for c in r["consecuentes"]:
                if c not in hechos:
                    hechos[c] = n
                    origen[c] = {"regla": r["id"], "nombre": r["nombre"],
                                 "antecedentes": list(r["antecedentes"]),
                                 "prioridad": r.get("prioridad", 0)}
                    nuevos.append(c)

            pasos.append({
                "paso": n, "fase": fase,
                "conflicto": [{k: v for k, v in c.items() if k not in ("clave", "idx")} for c in conflicto],
                "elegida": f"{ganadora['id']} · {ganadora['nombre']}",
                "motivo": self._motivo(conflicto),
                "nuevos": nuevos,
            })

        recomendaciones = [{
            "id": h, "texto": self.texto(h), "detalle": self.catalogo[h].get("detalle", ""),
            "regla": o["regla"], "prioridad": o["prioridad"], "paso": hechos[h],
        } for h, o in origen.items() if self.catalogo[h].get("tipo") == "recomendacion"]
        recomendaciones.sort(key=lambda x: (-x["prioridad"], x["paso"]))

        return {"iniciales": list(hechos_iniciales), "derivados": list(origen),
                "recomendaciones": recomendaciones, "pasos": pasos,
                "origen": origen, "no_reconocidos": no_reconocidos}

    def cadena(self, resultado, hecho, nivel=0):
        """Explica por qué se llegó a un hecho (trazabilidad hacia atrás)."""
        pad = "    " * nivel
        o = resultado["origen"].get(hecho)
        if not o:
            return [f"{pad}• {self.texto(hecho)}  [dato inicial]"]
        lineas = [f"{pad}• {self.texto(hecho)}  ⟵ {o['regla']} {o['nombre']}"]
        for a in o["antecedentes"]:
            lineas += self.cadena(resultado, a, nivel + 1)
        return lineas


if __name__ == "__main__":  # prueba rápida por consola
    import sys
    if len(sys.argv) != 3:
        sys.exit("Uso: python engine.py knowledge_base/nube.json examples/caso_nube.json")
    motor = MotorInferencia(cargar_kb(sys.argv[1]))
    res = motor.ejecutar(cargar_hechos(sys.argv[2]))
    for p in res["pasos"]:
        print(f"Paso {p['paso']} [{p['fase']}] -> {p['elegida']} | {p['motivo']} | nuevos: {p['nuevos']}")
    print("\nRECOMENDACIONES:")
    for r in res["recomendaciones"]:
        print(f"- {r['texto']}: {r['detalle']}")