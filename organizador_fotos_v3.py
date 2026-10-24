"""
organizador_fotos_v3.py
=======================
Programa todo-en-uno para gestionar fotos y videos:

  Pestaña 1 - ORGANIZAR
    · Copia o mueve archivos de origen a destino
    · Organiza en carpetas YYYY/MM-Mes/
    · Fotos e imagenes -> carpeta de fotos destino
    · Videos          -> carpeta de videos destino (opcional, separada)
    · Usa fecha EXIF -> fecha de creacion -> fecha de modificacion
    · Si el archivo ya existe en destino (por hash) NO lo vuelve a copiar

  Pestaña 2 - LIMPIAR DUPLICADOS
    · Busca duplicados dentro de una carpeta (y subcarpetas)
    · Conserva el de mayor tamanyo, borra el resto

  Pestaña 3 - SIMULACION
    · Antes de cualquier operacion real, muestra exactamente que haria

Requisitos:
    python -m pip install Pillow
    tkinter viene incluido con Python en Windows/macOS/Linux
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import hashlib
import shutil
import os
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# -- Pillow opcional (para EXIF) ----------------------------------------------
try:
    from PIL import Image
    from PIL.ExifTags import TAGS
    PIL_OK = True
except ImportError:
    PIL_OK = False

# -- Constantes ---------------------------------------------------------------
EXT_FOTO  = {'.jpg','.jpeg','.png','.gif','.bmp','.tiff','.tif',
             '.heic','.heif','.raw','.cr2','.nef','.arw','.webp'}
EXT_VIDEO = {'.mp4','.mov','.avi','.mkv','.m4v','.wmv','.flv','.3gp'}
EXT_TODO  = EXT_FOTO | EXT_VIDEO

MESES = {
    1:"01-Enero", 2:"02-Febrero", 3:"03-Marzo", 4:"04-Abril",
    5:"05-Mayo",  6:"06-Junio",   7:"07-Julio", 8:"08-Agosto",
    9:"09-Septiembre", 10:"10-Octubre", 11:"11-Noviembre", 12:"12-Diciembre"
}

# -- Paleta neomorfica minimalista 2026 ---------------------------------------
C = {
    "bg":         "#F0EBE8",   # crema calido fondo principal
    "panel":      "#EDE8E5",   # panel ligeramente mas claro
    "neo_bg":     "#EDE8E5",   # superficie elevada neomorfica
    "neo_shadow":  "#D4CEC9",  # sombra neomorfica
    "card":       "#F0EBE8",   # cabecera mismo fondo
    "accent":     "#7A3B4A",   # acento principal (burdeos oscuro)
    "accent2":    "#7A3B4A",
    "accent3":    "#3A7A62",
    "text":       "#2A2025",   # texto principal muy oscuro
    "dim":        "#8A7A80",   # texto secundario
    "border":     "#D8D0CC",   # bordes sutiles
    "hover":      "#5E2A38",   # hover boton
    "success":    "#3A7A62",   # verde
    "warning":    "#9E6E38",   # naranja
    "error":      "#A85560",   # rojo
    "log_sunken": "#E8E2DE",   # fondo log hundido
    "log_bg":     "#E8E2DE",   # alias usado por el widget de log
    "log_fg":     "#2A2025",
    "entry_bg":   "#EDE8E5",
    "lbl_fg":     "#5E3040",   # etiquetas de campo
    "btn_sec":    "#D8D0CC",
    "btn_sec_fg": "#4A3038",
    "tab_bg":     "#F0EBE8",
    "tab_sel":    "#7A3B4A",
    
}

# -- Logo base64 --------------------------------------------------------------
LOGO_B64 = "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"

# =============================================================================
# UTILIDADES COMUNES
# =============================================================================

def md5(ruta: Path, chunk=65536) -> str:
    h = hashlib.md5()
    with open(ruta, 'rb') as f:
        while b := f.read(chunk):
            h.update(b)
    return h.hexdigest()

def fecha_exif(ruta: Path):
    if not PIL_OK or ruta.suffix.lower() not in EXT_FOTO:
        return None
    try:
        with Image.open(ruta) as img:
            ex = img._getexif()
            if ex:
                for tid, val in ex.items():
                    if TAGS.get(tid) in ('DateTimeOriginal','DateTimeDigitized','DateTime'):
                        return datetime.strptime(val, '%Y:%m:%d %H:%M:%S'), 'EXIF'
    except Exception:
        pass
    return None

def fecha_creacion(ruta: Path):
    """Fecha de creacion real del archivo (Windows) o mtime (Linux/Mac)."""
    try:
        # Windows: st_birthtime no existe, usamos st_ctime
        ct = ruta.stat().st_ctime
        mt = ruta.stat().st_mtime
        # st_ctime en Windows es fecha de creacion; en Unix es cambio de metadatos
        ts = min(ct, mt)   # la mas antigua es mas probable que sea la real
        return datetime.fromtimestamp(ts), 'creacion'
    except Exception:
        return datetime.fromtimestamp(ruta.stat().st_mtime), 'modificacion'

def obtener_fecha(ruta: Path):
    ex = fecha_exif(ruta)
    if ex:
        return ex
    return fecha_creacion(ruta)

def nombre_unico(carpeta: Path, nombre: str) -> Path:
    dst = carpeta / nombre
    if not dst.exists():
        return dst
    stem, suf = Path(nombre).stem, Path(nombre).suffix
    i = 1
    while dst.exists():
        dst = carpeta / f"{stem}_{i:03d}{suf}"
        i += 1
    return dst

def recopilar(carpeta: Path, extensiones: set, excluir: Path = None):
    res = []
    for p in carpeta.rglob('*'):
        if not p.is_file():
            continue
        if p.suffix.lower() not in extensiones:
            continue
        if excluir and str(p.resolve()).startswith(str(excluir)):
            continue
        res.append(p)
    return res

def construir_indice_hashes(carpeta: Path, extensiones: set, log_fn=None):
    """Devuelve dict hash->Path de todos los archivos en carpeta."""
    idx = {}
    if not carpeta.exists():
        return idx
    for p in carpeta.rglob('*'):
        if p.is_file() and p.suffix.lower() in extensiones:
            try:
                idx[md5(p)] = p
            except Exception as e:
                if log_fn:
                    log_fn(f"  No se pudo leer {p.name}: {e}", "warn")
    return idx

# =============================================================================
# MOTOR ORGANIZAR
# =============================================================================

def motor_organizar(cfg, log, prog, cancelar):
    origen     = Path(cfg['origen']).resolve()
    dst_fotos  = Path(cfg['destino_fotos']).resolve()
    dst_videos = Path(cfg['destino_videos']).resolve() if cfg.get('destino_videos') else dst_fotos
    accion     = cfg['accion']
    inc_video  = cfg['incluir_videos']
    seco       = cfg['modo_seco']
    ext_buscar = EXT_TODO if inc_video else EXT_FOTO
    accion_txt = "MOVER" if accion == "mover" else "COPIAR"

    log("─" * 58, "sep")
    log(f"  Inicio : {datetime.now().strftime('%d/%m/%Y  %H:%M:%S')}", "section")
    log(f"  Origen : {origen}", "info")
    log(f"  Destino fotos  : {dst_fotos}", "info")
    if inc_video:
        log(f"  Destino videos : {dst_videos}", "info")
    log(f"  Accion : {accion_txt}  |  Modo : {'SIMULACION' if seco else 'REAL'}", "warn" if seco else "info")
    log("─" * 58, "sep")

    # PASO 1: buscar archivos
    log("\n[ PASO 1/4 ]  Buscando archivos en origen...", "section")
    excluir_set = {str(dst_fotos), str(dst_videos)}

    def no_en_destino(p):
        sp = str(p.resolve())
        return not any(sp.startswith(ex) for ex in excluir_set)

    todos_origen  = [p for p in origen.rglob('*')
                     if p.is_file() and p.suffix.lower() in ext_buscar and no_en_destino(p)]
    fotos_origen  = [p for p in todos_origen if p.suffix.lower() in EXT_FOTO]
    videos_origen = [p for p in todos_origen if p.suffix.lower() in EXT_VIDEO] if inc_video else []

    log(f"  Fotos encontradas  : {len(fotos_origen)}", "ok")
    if inc_video:
        log(f"  Videos encontrados : {len(videos_origen)}", "ok")

    if not todos_origen:
        log("  No se encontraron archivos. Comprueba la ruta origen.", "warn")
        return

    # PASO 2: indexar destino
    log("\n[ PASO 2/4 ]  Comprobando archivos ya existentes en destino...", "section")
    log("  (Esto evita copiar duplicados)", "dim")
    idx_fotos  = construir_indice_hashes(dst_fotos,  EXT_FOTO,  log)
    idx_videos = construir_indice_hashes(dst_videos, EXT_VIDEO, log) if inc_video else {}
    log(f"  Ya organizadas en destino : {len(idx_fotos)} fotos" +
        (f" y {len(idx_videos)} videos" if inc_video else ""), "dim")

    # PASO 3: procesar
    def procesar_lote(archivos, idx_destino, dst_base, tipo):
        stats = {"copiados": 0, "omitidos": 0, "errores": 0,
                 "exif": 0, "creacion": 0, "modif": 0}
        prog(0, len(archivos))
        for i, archivo in enumerate(archivos):
            if cancelar():
                log("\n  Operacion cancelada por el usuario.", "error")
                return stats
            try:
                h = md5(archivo)
                if h in idx_destino:
                    if accion == 'mover' and not seco:
                        archivo.unlink()
                        log(f"  YA EXISTE — original borrado : {archivo.name}", "dim")
                    else:
                        log(f"  YA EXISTE — omitido          : {archivo.name}", "dim")
                    stats["omitidos"] += 1
                    prog(i + 1, len(archivos))
                    continue

                fecha, fuente = obtener_fecha(archivo)
                if   fuente == 'EXIF':     stats["exif"] += 1
                elif fuente == 'creacion': stats["creacion"] += 1
                else:                      stats["modif"] += 1

                carpeta_dst = dst_base / str(fecha.year) / MESES[fecha.month]

                if not seco:
                    carpeta_dst.mkdir(parents=True, exist_ok=True)
                    dst_archivo = nombre_unico(carpeta_dst, archivo.name)
                    if accion == 'mover':
                        shutil.move(str(archivo), str(dst_archivo))
                    else:
                        shutil.copy2(str(archivo), str(dst_archivo))
                    idx_destino[h] = dst_archivo

                prefijo = "[SIM]" if seco else (accion_txt)
                log(f"  {prefijo:<6}  {archivo.name}  ->  {fecha.year}/{MESES[fecha.month]}  [{fuente}]",
                    "warn" if seco else "ok")
                stats["copiados"] += 1
            except Exception as e:
                log(f"  ERROR  {archivo.name} : {e}", "error")
                stats["errores"] += 1
            prog(i + 1, len(archivos))
        return stats

    if fotos_origen:
        log(f"\n[ PASO 3/4 ]  {accion_txt[0]+accion_txt[1:].lower()}ando {len(fotos_origen)} fotos...", "section")
        sf = procesar_lote(fotos_origen, idx_fotos, dst_fotos, "foto")
    else:
        sf = {"copiados": 0, "omitidos": 0, "errores": 0, "exif": 0, "creacion": 0, "modif": 0}
        log("\n[ PASO 3/4 ]  Sin fotos que procesar.", "dim")

    if videos_origen:
        log(f"\n[ PASO 4/4 ]  {accion_txt[0]+accion_txt[1:].lower()}ando {len(videos_origen)} videos...", "section")
        sv = procesar_lote(videos_origen, idx_videos, dst_videos, "video")
    else:
        sv = {"copiados": 0, "omitidos": 0, "errores": 0, "exif": 0, "creacion": 0, "modif": 0}
        if inc_video:
            log("\n[ PASO 4/4 ]  Sin videos que procesar.", "dim")

    # RESUMEN FINAL
    total_ok  = sf["copiados"] + sv["copiados"]
    total_om  = sf["omitidos"] + sv["omitidos"]
    total_err = sf["errores"]  + sv["errores"]
    hora_fin  = datetime.now().strftime('%H:%M:%S')

    log("\n" + "═" * 58, "sep")
    log("  RESUMEN FINAL", "section")
    log("═" * 58, "sep")
    log(f"  Hora de fin          : {hora_fin}", "info")
    log(f"  Archivos {accion_txt.lower():<6}     : {total_ok}", "ok")
    log(f"  Ya existian (omitidos): {total_om}", "dim")
    log(f"  Errores              : {total_err}", "error" if total_err else "ok")
    log(f"  Fecha EXIF           : {sf['exif']+sv['exif']}", "dim")
    log(f"  Fecha creacion       : {sf['creacion']+sv['creacion']}", "dim")
    log(f"  Fecha modificacion   : {sf['modif']+sv['modif']}", "dim")
    if seco:
        log("\n  MODO SIMULACION: no se hizo ningun cambio real.", "warn")
        log("  Desactiva Simulacion y vuelve a ejecutar para aplicar los cambios.", "warn")
    else:
        verbo = "movidos" if accion == "mover" else "copiados"
        log(f"\n  {total_ok} archivos {verbo} correctamente.", "ok")
        if total_om:
            log(f"  {total_om} archivos omitidos porque ya existian en destino.", "dim")
        if total_err:
            log(f"  {total_err} archivos con error. Revisa los mensajes anteriores.", "error")
        log(f"\n  Fotos guardadas en  : {dst_fotos}", "ok")
        if inc_video and str(dst_videos) != str(dst_fotos):
            log(f"  Videos guardados en : {dst_videos}", "ok")
    log("═" * 58, "sep")


# =============================================================================
# MOTOR LIMPIAR DUPLICADOS
# =============================================================================

def motor_limpiar(cfg, log, prog, cancelar):
    carpeta = Path(cfg['carpeta']).resolve()
    seco    = cfg['modo_seco']
    ext     = EXT_TODO if cfg.get('incluir_videos') else EXT_FOTO

    log("─" * 58, "sep")
    log(f"  Inicio   : {datetime.now().strftime('%d/%m/%Y  %H:%M:%S')}", "section")
    log(f"  Carpeta  : {carpeta}", "info")
    log(f"  Modo     : {'SIMULACION (sin cambios)' if seco else 'REAL — SE BORRARAN ARCHIVOS'}", "warn" if seco else "error")
    log("─" * 58, "sep")

    # PASO 1: buscar
    log("\n[ PASO 1/3 ]  Buscando archivos en la carpeta...", "section")
    archivos = [p for p in carpeta.rglob('*')
                if p.is_file() and p.suffix.lower() in ext]

    if not archivos:
        log("  No se encontraron archivos en la carpeta indicada.", "warn")
        return

    log(f"  Archivos encontrados : {len(archivos)}", "ok")

    # PASO 2: calcular hashes
    log(f"\n[ PASO 2/3 ]  Comparando contenido para detectar duplicados...", "section")
    log("  (Analizando cada archivo, esto puede tardar unos minutos)", "dim")
    hashes = defaultdict(list)
    prog(0, len(archivos))

    for i, f in enumerate(archivos):
        if cancelar():
            log("\n  Operacion cancelada por el usuario.", "error")
            return
        try:
            hashes[md5(f)].append(f)
        except Exception as e:
            log(f"  No se pudo leer {f.name}: {e}", "warn")
        prog(i + 1, len(archivos))

    grupos = {h: lst for h, lst in hashes.items() if len(lst) > 1}
    n_dup  = sum(len(l) - 1 for l in grupos.values())
    mb_dup = sum(f.stat().st_size for lst in grupos.values()
                 for f in lst[1:]) / (1024 * 1024)

    if not grupos:
        log("\n  No se encontraron duplicados. La carpeta esta limpia.", "ok")
        log("─" * 58, "sep")
        log("  RESULTADO: ningún duplicado encontrado.", "section")
        log("─" * 58, "sep")
        return

    log(f"  Grupos de duplicados encontrados : {len(grupos)}", "warn")
    log(f"  Archivos que se pueden eliminar  : {n_dup}", "warn")
    log(f"  Espacio que se recuperaria       : {mb_dup:.1f} MB", "warn")

    # Detalle de cada grupo
    log("\n  Detalle de duplicados:", "section")
    mostrados = 0
    for h, lista in grupos.items():
        if mostrados >= 20:
            log(f"  ... y {len(grupos) - mostrados} grupos mas (ver log completo)", "dim")
            break
        ord_ = sorted(lista, key=lambda f: f.stat().st_size, reverse=True)
        log(f"\n  CONSERVAR  {ord_[0].name}  ({ord_[0].stat().st_size//1024} KB)", "ok")
        log(f"             {ord_[0].parent}", "dim")
        for b in ord_[1:]:
            log(f"  ELIMINAR   {b.name}  ({b.stat().st_size//1024} KB)", "error")
            log(f"             {b.parent}", "dim")
        mostrados += 1

    if seco:
        log("\n" + "═" * 58, "sep")
        log("  SIMULACION COMPLETADA — no se elimino nada", "section")
        log("═" * 58, "sep")
        log(f"  Duplicados que se eliminarian : {n_dup}", "warn")
        log(f"  Espacio que se recuperaria    : {mb_dup:.1f} MB", "warn")
        log("\n  Desactiva Simulacion y vuelve a ejecutar para borrar de verdad.", "warn")
        log("═" * 58, "sep")
        return

    # PASO 3: eliminar
    log(f"\n[ PASO 3/3 ]  Eliminando {n_dup} archivos duplicados...", "section")
    borrados = errores = 0
    for lista in grupos.values():
        if cancelar():
            log("  Cancelado a mitad del proceso.", "error")
            break
        ord_ = sorted(lista, key=lambda f: f.stat().st_size, reverse=True)
        for dup in ord_[1:]:
            try:
                dup.unlink()
                log(f"  ELIMINADO  {dup.name}  |  {dup.parent}", "dim")
                borrados += 1
            except Exception as e:
                log(f"  ERROR  {dup.name} : {e}", "error")
                errores += 1

    hora_fin = datetime.now().strftime('%H:%M:%S')
    log("\n" + "═" * 58, "sep")
    log("  LIMPIEZA COMPLETADA", "section")
    log("═" * 58, "sep")
    log(f"  Hora de fin                   : {hora_fin}", "info")
    log(f"  Archivos duplicados eliminados: {borrados}", "ok")
    log(f"  Espacio liberado              : {mb_dup:.1f} MB", "ok")
    log(f"  Errores                       : {errores}", "error" if errores else "ok")
    if errores:
        log("  Revisa los mensajes en rojo para ver que archivos fallaron.", "error")
    log("═" * 58, "sep")

def recurso(nombre: str) -> str:
        """Devuelve la ruta correcta tanto en desarrollo como en el .exe compilado."""
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, nombre)
        return os.path.join(os.path.abspath("."), nombre)
# =============================================================================
# INTERFAZ GRAFICA
# =============================================================================

class App(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Organizador de Fotos y Videos  v3")
        self.resizable(True, True)
        self.configure(bg=C["bg"])
        # Icono de la ventana (barra de título y barra de tareas)
        try:
            ico_path = recurso("Logo.ico")
            img_ico = tk.PhotoImage(file=ico_path)
            self.iconphoto(True, img_ico)
            self._ico_ref = img_ico  # evitar que el garbage collector lo elimine
        except Exception:
            try:
                self.iconbitmap(recurso("Logo.ico"))
            except Exception:
                pass  # Si no encuentra el .ico, ignora silenciosamente
        self.minsize(760, 680)
        self._cancelar   = False
        self._ejecutando = False
        self._ui_ctx     = {}
        self._ctx_activo = None

        # Variables pestana ORGANIZAR
        self.v_origen      = tk.StringVar()
        self.v_dst_fotos   = tk.StringVar()
        self.v_inc_video   = tk.BooleanVar(value=False)
        self.v_dst_videos  = tk.StringVar()
        self.v_accion      = tk.StringVar(value='copiar')
        self.v_seco_org    = tk.BooleanVar(value=True)

        # Variables pestana LIMPIAR
        self.v_carpeta_lim = tk.StringVar()
        self.v_inc_vid_lim = tk.BooleanVar(value=False)
        self.v_seco_lim    = tk.BooleanVar(value=True)

        self._ui()
        self._centrar(800, 720)

    

    # -------------------------------------------------------------------------
    # UI principal con pestanas
    # -------------------------------------------------------------------------
    def _ui(self):
        self.configure(bg=C["bg"])

        # Cabecera pastel con logo
        hdr = tk.Frame(self, bg=C["card"], pady=14)
        hdr.pack(fill="x")

        # Fila con logo + textos centrados
        hdr_inner = tk.Frame(hdr, bg=C["card"])
        hdr_inner.pack()

        # Cargar logo de archivo (Logo.png) y fallback a base64
        self._logo_img = None
        try:
            if Path(recurso("Logo.png")).exists():
                self._logo_img = tk.PhotoImage(file=recurso("Logo.png")).subsample(2, 2)
            else:
                self._logo_img = tk.PhotoImage(file=recurso("Logo.ico"))
        except Exception:
            try:
                import base64 as _b64
                from PIL import Image as _Img, ImageTk as _ImgTk
                import io as _io
                _img_data = _b64.b64decode(LOGO_B64)
                _img = _Img.open(_io.BytesIO(_img_data)).convert("RGBA")
                self._logo_img = _ImgTk.PhotoImage(_img)
            except Exception:
                self._logo_img = None

        if self._logo_img is not None:
            tk.Label(hdr_inner, image=self._logo_img,
                     bg=C["card"]).pack(side="left", padx=(0, 18))
            try:
                self.iconphoto(True, self._logo_img)
            except Exception:
                pass
        else:
            # Fallback visible en cabecera si no se puede cargar la imagen
            logo_fallback = tk.Canvas(
                hdr_inner, width=42, height=42,
                bg=C["card"], highlightthickness=0, bd=0
            )
            logo_fallback.pack(side="left", padx=(0, 18))
            logo_fallback.create_oval(2, 2, 40, 40, fill=C["accent"], outline=C["accent"])
            logo_fallback.create_text(
                21, 21, text="MG", fill="white",
                font=("Segoe UI", 10, "bold")
            )

        txt_frame = tk.Frame(hdr_inner, bg=C["card"])
        txt_frame.pack(side="left")
        tk.Label(txt_frame, text="Organizador de Fotos y Videos",
                 font=("Georgia", 19, "bold"),
                 bg=C["card"], fg="#2E2028").pack(anchor="w")
        tk.Label(txt_frame,
                 text="Organiza  ·  Copia  ·  Mueve  ·  Limpia duplicados",
                 font=("Segoe UI", 10), bg=C["card"], fg="#6B3342").pack(anchor="w", pady=(3,0))
        tk.Label(txt_frame, text="by  mónica g.",
                 font=("Georgia", 9, "italic"),
                 bg=C["card"], fg="#8C4A58").pack(anchor="w", pady=(2,0))

        if not PIL_OK:
            tk.Label(hdr,
                     text="  Pillow no instalado — fecha de modificacion en lugar de EXIF  "
                          "(instala: python -m pip install Pillow)  ",
                     font=("Segoe UI", 8), bg="#E8C9B0", fg="#7C4A00").pack(fill="x", pady=(6,0))

        # Notebook
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TNotebook",
                        background=C["bg"], borderwidth=0, tabmargins=0)
        style.configure("TNotebook.Tab",
                        background=C["tab_bg"], foreground=C["dim"],
                        font=("Segoe UI", 10, "bold"), padding=[20,9],
                        borderwidth=0)
        style.map("TNotebook.Tab",
                  background=[("selected", C["tab_sel"]), ("active", "#FADADD")],
                  foreground=[("selected", "white"),      ("active", C["accent"])])
        style.configure("B.Horizontal.TProgressbar",
                        troughcolor=C["btn_sec"], background=C["accent"],
                        darkcolor=C["accent"], lightcolor=C["accent"],
                        bordercolor=C["border"], thickness=10)

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True)

        tab1 = tk.Frame(nb, bg=C["bg"])
        nb.add(tab1, text="  📂  Organizar  ")
        self._tab_organizar(tab1)

        tab2 = tk.Frame(nb, bg=C["bg"])
        nb.add(tab2, text="  🧹  Limpiar duplicados  ")
        self._tab_limpiar(tab2)

    # -------------------------------------------------------------------------
    # Pestana ORGANIZAR
    # -------------------------------------------------------------------------
    def _tab_organizar(self, parent):
        main = tk.Frame(parent, bg=C["bg"], padx=24, pady=16)
        main.pack(fill="both", expand=True)

        # -- Carpetas ---------------------------------------------------------
        lf_rutas = self._lframe(main, "Carpetas")
        lf_rutas.pack(fill="x", pady=(0,10))

        self._fila_carpeta(lf_rutas, "Origen  (carpeta con tus fotos):",
                           self.v_origen, lambda: self._elegir_dir(self.v_origen))

        self._fila_carpeta(lf_rutas, "Destino fotos  (donde se organizaran las imagenes):",
                           self.v_dst_fotos, lambda: self._elegir_dir(self.v_dst_fotos))

        # Videos destino (se muestra/oculta)
        self.frame_vid_dst = tk.Frame(lf_rutas, bg=C["panel"])
        tk.Label(self.frame_vid_dst,
                 text="Destino videos  (opcional — carpeta separada para videos):",
                 font=("Segoe UI", 9), bg=C["panel"], fg=C["lbl_fg"],
                 anchor="w").pack(fill="x", pady=(8,3))
        fv = tk.Frame(self.frame_vid_dst, bg=C["panel"])
        fv.pack(fill="x")
        fv.columnconfigure(0, weight=1)
        tk.Entry(fv, textvariable=self.v_dst_videos,
                 font=("Segoe UI", 10), bg=C["entry_bg"], fg=C["text"],
                 insertbackground=C["accent"], relief="solid",
                 highlightthickness=1, highlightbackground=C["border"],
                 highlightcolor=C["accent"], bd=1).grid(
                     row=0, column=0, sticky="ew", ipady=5, padx=(0,8))
        tk.Button(fv, text="Explorar...",
                  command=lambda: self._elegir_dir(self.v_dst_videos),
                  font=("Segoe UI", 9), bg=C["accent"], fg="white",
                  activebackground=C["hover"], activeforeground="white",
                  relief="flat", cursor="hand2", padx=10
                  ).grid(row=0, column=1)
        tk.Label(self.frame_vid_dst,
                 text="Si se deja vacio, los videos van a la misma carpeta que las fotos.",
                 font=("Segoe UI", 8), bg=C["panel"], fg=C["dim"]).pack(anchor="w", pady=(3,0))

        # -- Opciones ---------------------------------------------------------
        lf_opts = self._lframe(main, "Opciones")
        lf_opts.pack(fill="x", pady=(0,10))

        # Accion
        fa = tk.Frame(lf_opts, bg=C["panel"])
        fa.pack(fill="x", pady=(0,8))
        tk.Label(fa, text="Accion:", font=("Segoe UI", 10, "bold"),
                 bg=C["panel"], fg=C["lbl_fg"]).pack(side="left", padx=(0,14))
        for val, txt, color in [
            ("copiar", "Copiar  (conserva originales)", C["success"]),
            ("mover",  "Mover   (borra originales)",    C["warning"]),
        ]:
            tk.Radiobutton(fa, text=txt, variable=self.v_accion, value=val,
                           font=("Segoe UI", 9),
                           bg=C["panel"], fg=color,
                           activebackground=C["panel"], activeforeground=color,
                           selectcolor=C["entry_bg"], cursor="hand2"
                           ).pack(side="left", padx=(0,20))

        # Videos + Simulacion en misma fila
        fvid = tk.Frame(lf_opts, bg=C["panel"])
        fvid.pack(fill="x", pady=(0,4))
        tk.Checkbutton(fvid,
                       text="Incluir videos  (.mp4  .mov  .avi  .mkv ...)",
                       variable=self.v_inc_video,
                       command=self._toggle_video_dst,
                       font=("Segoe UI", 9),
                       bg=C["panel"], fg=C["text"],
                       activebackground=C["panel"], activeforeground=C["accent"],
                       selectcolor=C["entry_bg"], cursor="hand2").pack(side="left", padx=(0,30))

        tk.Checkbutton(fvid,
                       text="Simulacion  (muestra que haria SIN hacer cambios)",
                       variable=self.v_seco_org,
                       font=("Segoe UI", 9),
                       bg=C["panel"], fg=C["text"],
                       activebackground=C["panel"], activeforeground=C["accent"],
                       selectcolor=C["entry_bg"], cursor="hand2").pack(side="left")

        self._toggle_video_dst()

        # Progreso + botones + log
        self._zona_ejecucion(main, self._iniciar_organizar, "ORGANIZAR AHORA", "organizar")

    def _toggle_video_dst(self):
        if self.v_inc_video.get():
            self.frame_vid_dst.pack(fill="x", pady=(6,0))
        else:
            self.frame_vid_dst.pack_forget()

    # -------------------------------------------------------------------------
    # Pestana LIMPIAR DUPLICADOS
    # -------------------------------------------------------------------------
    def _tab_limpiar(self, parent):
        main = tk.Frame(parent, bg=C["bg"], padx=24, pady=16)
        main.pack(fill="both", expand=True)

        lf = self._lframe(main, "Carpeta a analizar")
        lf.pack(fill="x", pady=(0,10))

        tk.Label(lf,
                 text="Selecciona la carpeta con las fotos organizadas. "
                      "Se buscaran duplicados en todas las subcarpetas.",
                 font=("Segoe UI", 9), bg=C["panel"], fg=C["dim"],
                 justify="left", anchor="w").pack(fill="x", pady=(0,8))

        self._fila_carpeta(lf, "Carpeta:", self.v_carpeta_lim,
                           lambda: self._elegir_dir(self.v_carpeta_lim))

        lf2 = self._lframe(main, "Opciones")
        lf2.pack(fill="x", pady=(0,10))

        frow = tk.Frame(lf2, bg=C["panel"])
        frow.pack(fill="x")
        tk.Checkbutton(frow,
                       text="Incluir videos al buscar duplicados",
                       variable=self.v_inc_vid_lim,
                       font=("Segoe UI", 9),
                       bg=C["panel"], fg=C["text"],
                       activebackground=C["panel"], activeforeground=C["accent"],
                       selectcolor=C["entry_bg"], cursor="hand2").pack(side="left", padx=(0,30))

        tk.Checkbutton(frow,
                       text="Simulacion  (muestra que borraria SIN eliminar nada)",
                       variable=self.v_seco_lim,
                       font=("Segoe UI", 9),
                       bg=C["panel"], fg=C["text"],
                       activebackground=C["panel"], activeforeground=C["accent"],
                       selectcolor=C["entry_bg"], cursor="hand2").pack(side="left")

        self._zona_ejecucion(main, self._iniciar_limpiar, "BUSCAR Y LIMPIAR DUPLICADOS", "limpiar")

    # -------------------------------------------------------------------------
    # Zona comun: progreso + botones + log
    # -------------------------------------------------------------------------
    def _zona_ejecucion(self, parent, cmd_iniciar, texto_btn, ctx_name):
        # Separador visual
        tk.Frame(parent, bg=C["border"], height=1).pack(fill="x", pady=(0,10))

        # Etiqueta de estado + barra de progreso
        pf = tk.Frame(parent, bg=C["bg"])
        pf.pack(fill="x", pady=(0,6))

        lbl_prog = tk.Label(pf, text="Listo para comenzar",
                            font=("Segoe UI", 9), bg=C["bg"],
                            fg=C["dim"], anchor="w")
        lbl_prog.pack(fill="x", pady=(0,4))

        barra = ttk.Progressbar(pf, style="B.Horizontal.TProgressbar",
                                orient="horizontal", mode="determinate")
        barra.pack(fill="x")

        # Botones
        br = tk.Frame(parent, bg=C["bg"])
        br.pack(fill="x", pady=(8,6))

        btn_ini = self._btn(br, texto_btn, cmd_iniciar, C["accent"], fg="white")
        btn_ini.pack(side="left", padx=(0,8))

        btn_can = self._btn(
            br, "Cancelar", lambda: self._cancelar_op(ctx_name),
            C["btn_sec"], fg=C["btn_sec_fg"]
        )
        btn_can.pack(side="left")
        btn_can.configure(state="disabled")

        self._btn(
            br, "Limpiar log", lambda: self._limpiar_log(ctx_name),
            C["btn_sec"], fg=C["btn_sec_fg"]
        ).pack(side="right")

        # Titulo del area de actividad
        tk.Label(parent, text="Actividad", font=("Segoe UI", 9, "bold"),
                 bg=C["bg"], fg=C["lbl_fg"], anchor="w").pack(fill="x")

        # Log con fondo blanco, bordes limpios
        lf = tk.Frame(parent, bg=C["border"], bd=1, relief="solid")
        lf.pack(fill="both", expand=True, pady=(4,0))

        log_widget = scrolledtext.ScrolledText(
            lf, font=("Consolas", 9),
            bg=C["log_bg"], fg=C["log_fg"],
            insertbackground=C["accent"],
            relief="flat", bd=0,
            wrap="word", state="disabled",
            padx=12, pady=10
        )
        log_widget.pack(fill="both", expand=True)

        log_widget.tag_config("ok",      foreground="#3D7A62", font=("Consolas",9))
        log_widget.tag_config("warn",    foreground="#9E6E38", font=("Consolas",9))
        log_widget.tag_config("error",   foreground="#A85560", font=("Consolas",9))
        log_widget.tag_config("info",    foreground="#2E2028", font=("Consolas",9))
        log_widget.tag_config("section", foreground="#6B3342", font=("Consolas",9,"bold"))
        log_widget.tag_config("dim",     foreground="#7A6570", font=("Consolas",9))
        log_widget.tag_config("sep",     foreground="#D9B8BC", font=("Consolas",9))
        log_widget.tag_config("normal",  foreground="#2E2028", font=("Consolas",9))
        log_widget.tag_config("fin",     foreground="#6B3342", font=("Consolas",10,"bold"))

        self._ui_ctx[ctx_name] = {
            "lbl_prog": lbl_prog,
            "barra": barra,
            "btn_ini": btn_ini,
            "btn_can": btn_can,
            "log_widget": log_widget,
        }
        self._log("  Configura las opciones y pulsa el boton para comenzar.", "dim", ctx_name=ctx_name)

    # -------------------------------------------------------------------------
    # Helpers UI
    # -------------------------------------------------------------------------
    def _lframe(self, parent, titulo):
        lf = tk.LabelFrame(parent, text=f"  {titulo}  ",
                            font=("Segoe UI", 10, "bold"),
                            bg=C["panel"], fg=C["lbl_fg"],
                            bd=1, relief="solid", padx=16, pady=12)
        return lf

    def _fila_carpeta(self, parent, label, var, cmd):
        tk.Label(parent, text=label, font=("Segoe UI", 9, "bold"),
                 bg=C["panel"], fg=C["lbl_fg"], anchor="w").pack(fill="x", pady=(6,3))
        f = tk.Frame(parent, bg=C["panel"])
        f.pack(fill="x")
        f.columnconfigure(0, weight=1)
        tk.Entry(f, textvariable=var,
                 font=("Segoe UI", 10), bg=C["entry_bg"], fg=C["text"],
                 insertbackground=C["accent"], relief="solid",
                 highlightthickness=0, bd=1,
                 highlightbackground=C["border"],
                 highlightcolor=C["accent"]).grid(row=0,column=0,sticky="ew",ipady=6,padx=(0,8))
        tk.Button(f, text="Explorar...", command=cmd,
                  font=("Segoe UI", 9), bg=C["accent"], fg="white",
                  activebackground=C["hover"], activeforeground="white",
                  relief="flat", cursor="hand2", padx=12, pady=5).grid(row=0,column=1)

    def _btn(self, parent, texto, cmd, bg, fg="white"):
        b = tk.Button(parent, text=texto, command=cmd,
                      font=("Segoe UI", 10, "bold"),
                      bg=bg, fg=fg,
                      activebackground=C["hover"], activeforeground="white",
                      relief="flat", cursor="hand2", padx=16, pady=8,
                      bd=0)
        b.bind("<Enter>", lambda e: b.config(bg=C["hover"]) if str(b["state"])!="disabled" else None)
        b.bind("<Leave>", lambda e: b.config(bg=bg)         if str(b["state"])!="disabled" else None)
        return b

    def _elegir_dir(self, var):
        r = filedialog.askdirectory()
        if r:
            var.set(r)

    # -------------------------------------------------------------------------
    # Acciones
    # -------------------------------------------------------------------------
    def _iniciar_organizar(self):
        if self._ejecutando: return
        origen     = self.v_origen.get().strip()
        dst_fotos  = self.v_dst_fotos.get().strip()
        inc_video  = self.v_inc_video.get()
        dst_videos = self.v_dst_videos.get().strip() if inc_video else ""
        accion     = self.v_accion.get()
        seco       = self.v_seco_org.get()

        if not origen:
            messagebox.showwarning("Falta origen", "Selecciona la carpeta de origen.")
            return
        if not dst_fotos:
            messagebox.showwarning("Falta destino", "Selecciona la carpeta de destino para las fotos.")
            return
        if not Path(origen).exists():
            messagebox.showerror("Error", f"La carpeta origen no existe:\n{origen}")
            return
        if accion == 'mover' and not seco:
            if not messagebox.askyesno("Estas segura?",
                "Vas a MOVER archivos (los originales se borraran).\n\nContinuar?",
                icon="warning"):
                return

        cfg = {
            'origen':        origen,
            'destino_fotos': dst_fotos,
            'destino_videos': dst_videos if dst_videos else dst_fotos,
            'accion':        accion,
            'incluir_videos': inc_video,
            'modo_seco':     seco,
        }
        self._lanzar(motor_organizar, cfg, "organizar")

    def _iniciar_limpiar(self):
        if self._ejecutando: return
        carpeta = self.v_carpeta_lim.get().strip()
        seco    = self.v_seco_lim.get()

        if not carpeta:
            messagebox.showwarning("Falta carpeta", "Selecciona la carpeta a limpiar.")
            return
        if not Path(carpeta).exists():
            messagebox.showerror("Error", f"La carpeta no existe:\n{carpeta}")
            return
        if not seco:
            if not messagebox.askyesno("Estas segura?",
                f"Se eliminaran archivos de forma permanente en:\n\n{carpeta}\n\nContinuar?",
                icon="warning"):
                return

        cfg = {
            'carpeta':        carpeta,
            'modo_seco':      seco,
            'incluir_videos': self.v_inc_vid_lim.get(),
        }
        self._lanzar(motor_limpiar, cfg, "limpiar")

    def _lanzar(self, motor, cfg, ctx_name):
        self._cancelar   = False
        self._ejecutando = True
        self._cfg_activo = cfg          # guardar para el aviso final
        self._motor_activo = motor
        self._ctx_activo = ctx_name
        ctx = self._ui_ctx[ctx_name]
        ctx["btn_ini"].configure(state="disabled")
        ctx["btn_can"].configure(state="normal")
        ctx["barra"]["value"] = 0
        self._log("\n" + "="*58 + "\n", "sep", ctx_name=ctx_name)
        self._log(f"  {datetime.now().strftime('%d/%m/%Y  %H:%M:%S')}\n", "section", ctx_name=ctx_name)

        threading.Thread(
            target=self._hilo, args=(motor, cfg), daemon=True
        ).start()

    def _hilo(self, motor, cfg):
        try:
            motor(cfg, self._log_t, self._prog_t, lambda: self._cancelar)
        except Exception as e:
            self._log_t(f"\nError inesperado: {e}", "error")
        finally:
            self.after(0, self._fin)

    def _fin(self):
        self._ejecutando = False
        ctx_name = self._ctx_activo
        ctx = self._ui_ctx.get(ctx_name, {})
        if ctx:
            ctx["btn_ini"].configure(state="normal")
            ctx["btn_can"].configure(state="disabled")
            ctx["barra"]["value"] = 0

        if self._cancelar:
            if ctx:
                ctx["lbl_prog"].configure(text="Cancelado")
            messagebox.showwarning("Cancelado", "La operacion fue cancelada.")
            return

        # Construir mensaje segun la operacion
        cfg = getattr(self, "_cfg_activo", {})
        motor = getattr(self, "_motor_activo", None)

        if motor is motor_limpiar:
            seco = cfg.get("modo_seco", False)
            if seco:
                titulo  = "Simulacion completada"
                mensaje = "Analisis terminado.\n\nRevisa el log para ver que duplicados se borrarian.\nDesactiva Simulacion y vuelve a ejecutar para borrar de verdad."
                icon    = "info"
            else:
                titulo  = "Limpieza completada"
                mensaje = "Los duplicados han sido eliminados correctamente.\n\nRevisa el log para ver el resumen."
                icon    = "info"
        else:
            seco   = cfg.get("modo_seco", False)
            accion = cfg.get("accion", "copiar")
            if seco:
                titulo  = "Simulacion completada"
                mensaje = "Simulacion terminada.\n\nRevisa el log para ver que se haria.\nDesactiva Simulacion y vuelve a ejecutar para aplicar los cambios."
                icon    = "info"
            elif accion == "mover":
                titulo  = "Mover completado"
                mensaje = "Los archivos han sido MOVIDOS correctamente.\n\nLos originales han sido eliminados.\nRevisa el log para ver el resumen."
                icon    = "info"
            else:
                titulo  = "Copia completada"
                mensaje = "Los archivos han sido COPIADOS correctamente.\n\nLos originales se conservan intactos.\nRevisa el log para ver el resumen."
                icon    = "info"

        hora = datetime.now().strftime("%H:%M:%S")
        if ctx:
            ctx["lbl_prog"].configure(text=f"Finalizado a las {hora}  OK")
        messagebox.showinfo(titulo, mensaje)

    def _cancelar_op(self, ctx_name=None):
        self._cancelar = True
        target = ctx_name or self._ctx_activo
        ctx = self._ui_ctx.get(target)
        if ctx:
            ctx["btn_can"].configure(state="disabled")

    def _limpiar_log(self, ctx_name=None):
        target = ctx_name or self._ctx_activo
        ctx = self._ui_ctx.get(target)
        if not ctx:
            return
        w = ctx["log_widget"]
        w.configure(state="normal")
        w.delete("1.0", "end")
        w.configure(state="disabled")

    def _log(self, msg, tag="normal", ctx_name=None):
        target = ctx_name or self._ctx_activo
        ctx = self._ui_ctx.get(target)
        if not ctx:
            return
        w = ctx["log_widget"]
        w.configure(state="normal")
        w.insert("end", msg + "\n", tag)
        w.see("end")
        w.configure(state="disabled")

    def _log_t(self, msg, tag="normal"):
        self.after(0, lambda: self._log(msg, tag, self._ctx_activo))

    def _prog_t(self, v, mx):
        def act():
            ctx = self._ui_ctx.get(self._ctx_activo)
            if not ctx:
                return
            if mx > 0:
                pct = int(v/mx*100)
                ctx["barra"]["value"] = pct
                ctx["lbl_prog"].configure(text=f"Procesando: {v}/{mx}  ({pct}%)")
        self.after(0, act)

    def _centrar(self, w, h):
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")


# =============================================================================
if __name__ == "__main__":
    App().mainloop()
